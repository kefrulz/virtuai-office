# VirtuAI Office - Ollama Service Manager
import asyncio
import json
import time
import subprocess
import psutil
import aiohttp
import ollama
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import logging
import os
import threading
from contextlib import asynccontextmanager

from ..core.logging import get_logger, log_error_with_context, log_performance_warning


class ModelSize(Enum):
    TINY = "tiny"      # < 1GB
    SMALL = "small"    # 1-4GB
    MEDIUM = "medium"  # 4-8GB
    LARGE = "large"    # 8-16GB
    XLARGE = "xlarge"  # 16GB+


@dataclass
class ModelInfo:
    name: str
    size_gb: float
    family: str
    capabilities: List[str]
    recommended_ram_gb: int
    performance_tier: str
    download_url: Optional[str] = None
    local_path: Optional[str] = None
    is_installed: bool = False
    last_used: Optional[datetime] = None
    usage_count: int = 0
    average_response_time: float = 0.0


@dataclass
class OllamaConfig:
    host: str = "localhost"
    port: int = 11434
    timeout_seconds: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    num_threads: Optional[int] = None
    num_gpu: int = 0
    max_loaded_models: int = 1
    keep_alive: int = 300  # 5 minutes
    metal_enabled: bool = True  # For Apple Silicon
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class GenerationRequest:
    model: str
    prompt: str
    system: Optional[str] = None
    template: Optional[str] = None
    context: Optional[List[int]] = None
    stream: bool = False
    raw: bool = False
    format: Optional[str] = None
    keep_alive: Optional[int] = None
    options: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResponse:
    model: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class OllamaService:
    """Comprehensive Ollama service manager for VirtuAI Office"""
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.logger = get_logger('virtuai.ollama')
        
        # Connection and session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._connection_pool_size = 10
        self._connection_timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        
        # Model management
        self.installed_models: Dict[str, ModelInfo] = {}
        self.model_registry: Dict[str, ModelInfo] = {}
        self._load_model_registry()
        
        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'model_usage': {},
            'error_counts': {}
        }
        
        # Service status
        self.is_running = False
        self.service_start_time: Optional[datetime] = None
        self.last_health_check: Optional[datetime] = None
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Thread safety
        self._lock = asyncio.Lock()
    
    def _load_model_registry(self):
        """Load known model registry with specifications"""
        models = [
            # Llama 2 models
            ModelInfo("llama2:7b", 3.8, "llama2", ["text", "chat"], 8, "medium"),
            ModelInfo("llama2:7b-q4_0", 2.8, "llama2", ["text", "chat"], 6, "fast"),
            ModelInfo("llama2:7b-q8_0", 3.8, "llama2", ["text", "chat"], 8, "quality"),
            ModelInfo("llama2:13b", 7.3, "llama2", ["text", "chat"], 16, "high"),
            ModelInfo("llama2:13b-q4_0", 5.1, "llama2", ["text", "chat"], 12, "balanced"),
            ModelInfo("llama2:70b", 39.0, "llama2", ["text", "chat"], 64, "premium"),
            ModelInfo("llama2:70b-q4_0", 26.0, "llama2", ["text", "chat"], 48, "large"),
            
            # Code Llama models
            ModelInfo("codellama:7b", 3.8, "codellama", ["code", "text"], 8, "medium"),
            ModelInfo("codellama:7b-instruct", 3.8, "codellama", ["code", "instruct"], 8, "medium"),
            ModelInfo("codellama:13b", 7.3, "codellama", ["code", "text"], 16, "high"),
            ModelInfo("codellama:13b-instruct", 7.3, "codellama", ["code", "instruct"], 16, "high"),
            ModelInfo("codellama:34b", 19.0, "codellama", ["code", "text"], 32, "premium"),
            ModelInfo("codellama:34b-instruct", 19.0, "codellama", ["code", "instruct"], 32, "premium"),
            
            # Mistral models
            ModelInfo("mistral:7b", 4.1, "mistral", ["text", "chat"], 8, "medium"),
            ModelInfo("mistral:7b-instruct", 4.1, "mistral", ["text", "instruct"], 8, "medium"),
            
            # Neural Chat
            ModelInfo("neural-chat:7b", 4.1, "neural-chat", ["chat", "assistant"], 8, "medium"),
            
            # Orca models
            ModelInfo("orca-mini:3b", 1.9, "orca", ["text", "chat"], 4, "fast"),
            ModelInfo("orca-mini:7b", 3.8, "orca", ["text", "chat"], 8, "medium"),
            ModelInfo("orca-mini:13b", 7.3, "orca", ["text", "chat"], 16, "high"),
        ]
        
        for model in models:
            self.model_registry[model.name] = model
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()
    
    async def initialize(self):
        """Initialize the Ollama service"""
        self.logger.info("Initializing Ollama service...")
        
        # Create HTTP session
        connector = aiohttp.TCPConnector(
            limit=self._connection_pool_size,
            limit_per_host=self._connection_pool_size,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=self._connection_timeout,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check if Ollama is running
        await self._wait_for_ollama_startup()
        
        # Load installed models
        await self.refresh_installed_models()
        
        # Apply configuration
        await self._apply_configuration()
        
        # Start background tasks
        self._monitoring_task = asyncio.create_task(self._monitor_service())
        self._cleanup_task = asyncio.create_task(self._cleanup_unused_models())
        
        self.is_running = True
        self.service_start_time = datetime.utcnow()
        
        self.logger.info(f"Ollama service initialized successfully with {len(self.installed_models)} models")
    
    async def shutdown(self):
        """Shutdown the Ollama service"""
        self.logger.info("Shutting down Ollama service...")
        
        self.is_running = False
        
        # Cancel background tasks
        for task in [self._monitoring_task, self._cleanup_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close HTTP session
        if self._session:
            await self._session.close()
        
        self.logger.info("Ollama service shutdown complete")
    
    async def _wait_for_ollama_startup(self, max_wait_seconds: int = 30):
        """Wait for Ollama service to be available"""
        self.logger.info("Waiting for Ollama service to be available...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                await self.health_check()
                self.logger.info("Ollama service is available")
                return
            except Exception:
                await asyncio.sleep(1)
        
        raise ConnectionError(f"Ollama service not available after {max_wait_seconds} seconds")
    
    async def _apply_configuration(self):
        """Apply Ollama configuration"""
        env_vars = {}
        
        # Set number of threads
        if self.config.num_threads:
            env_vars['OLLAMA_NUM_THREADS'] = str(self.config.num_threads)
        
        # Set GPU usage
        if self.config.num_gpu > 0:
            env_vars['OLLAMA_NUM_GPU'] = str(self.config.num_gpu)
        
        # Set max loaded models
        env_vars['OLLAMA_MAX_LOADED_MODELS'] = str(self.config.max_loaded_models)
        
        # Enable Metal for Apple Silicon
        if self.config.metal_enabled:
            env_vars['OLLAMA_METAL'] = '1'
        
        # Apply environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
            self.logger.info(f"Set {key}={value}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama service health"""
        try:
            async with self._session.get(f"{self.config.base_url}/api/version") as response:
                if response.status == 200:
                    version_data = await response.json()
                    
                    self.last_health_check = datetime.utcnow()
                    
                    return {
                        'status': 'healthy',
                        'version': version_data.get('version', 'unknown'),
                        'uptime': self._get_uptime(),
                        'models_loaded': len(self.installed_models),
                        'last_check': self.last_health_check.isoformat()
                    }
                else:
                    raise ConnectionError(f"Health check failed with status {response.status}")
        
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise
    
    async def list_models(self, include_details: bool = False) -> List[Dict[str, Any]]:
        """List all available models"""
        try:
            # Use ollama library for consistency
            models_data = await asyncio.to_thread(ollama.list)
            
            models = []
            for model_data in models_data.get('models', []):
                model_name = model_data['name']
                model_info = {
                    'name': model_name,
                    'size': model_data.get('size', 0),
                    'modified_at': model_data.get('modified_at'),
                    'digest': model_data.get('digest', ''),
                    'details': model_data.get('details', {}) if include_details else None
                }
                
                # Add registry information if available
                if model_name in self.model_registry:
                    registry_info = self.model_registry[model_name]
                    model_info.update({
                        'family': registry_info.family,
                        'capabilities': registry_info.capabilities,
                        'recommended_ram_gb': registry_info.recommended_ram_gb,
                        'performance_tier': registry_info.performance_tier
                    })
                
                # Add usage statistics
                if model_name in self.performance_stats['model_usage']:
                    model_info['usage_stats'] = self.performance_stats['model_usage'][model_name]
                
                models.append(model_info)
            
            return models
            
        except Exception as e:
            log_error_with_context('virtuai.ollama', e, {'operation': 'list_models'})
            raise
    
    async def refresh_installed_models(self):
        """Refresh the list of installed models"""
        try:
            models_data = await self.list_models(include_details=True)
            
            self.installed_models.clear()
            for model_data in models_data:
                model_name = model_data['name']
                
                if model_name in self.model_registry:
                    model_info = self.model_registry[model_name]
                    model_info.is_installed = True
                    model_info.local_path = model_data.get('digest', '')
                    self.installed_models[model_name] = model_info
                else:
                    # Create model info for unknown models
                    model_info = ModelInfo(
                        name=model_name,
                        size_gb=model_data.get('size', 0) / (1024**3),
                        family='unknown',
                        capabilities=['text'],
                        recommended_ram_gb=8,
                        performance_tier='unknown',
                        is_installed=True,
                        local_path=model_data.get('digest', '')
                    )
                    self.installed_models[model_name] = model_info
            
            self.logger.info(f"Refreshed model list: {len(self.installed_models)} models installed")
            
        except Exception as e:
            log_error_with_context('virtuai.ollama', e, {'operation': 'refresh_models'})
            raise
    
    async def pull_model(self, model_name: str, progress_callback: Optional[callable] = None) -> bool:
        """Download and install a model"""
        self.logger.info(f"Starting download of model: {model_name}")
        
        try:
            # Use ollama library for pulling
            def pull_with_progress():
                try:
                    for progress in ollama.pull(model_name, stream=True):
                        if progress_callback:
                            progress_callback(progress)
                    return True
                except Exception as e:
                    self.logger.error(f"Model pull failed: {e}")
                    return False
            
            success = await asyncio.to_thread(pull_with_progress)
            
            if success:
                await self.refresh_installed_models()
                self.logger.info(f"Successfully downloaded model: {model_name}")
                return True
            else:
                self.logger.error(f"Failed to download model: {model_name}")
                return False
                
        except Exception as e:
            log_error_with_context('virtuai.ollama', e, {
                'operation': 'pull_model',
                'model': model_name
            })
            return False
    
    async def delete_model(self, model_name: str) -> bool:
        """Delete a model"""
        self.logger.info(f"Deleting model: {model_name}")
        
        try:
            await asyncio.to_thread(ollama.delete, model_name)
            
            # Remove from installed models
            if model_name in self.installed_models:
                del self.installed_models[model_name]
            
            self.logger.info(f"Successfully deleted model: {model_name}")
            return True
            
        except Exception as e:
            log_error_with_context('virtuai.ollama', e, {
                'operation': 'delete_model',
                'model': model_name
            })
            return False
    
    async def generate(self, request: GenerationRequest) -> Union[GenerationResponse, AsyncGenerator[GenerationResponse, None]]:
        """Generate text using a model"""
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        # Initialize model usage tracking
        if request.model not in self.performance_stats['model_usage']:
            self.performance_stats['model_usage'][request.model] = {
                'requests': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'last_used': None
            }
        
        try:
            # Check if model is installed
            if request.model not in self.installed_models:
                available_models = list(self.installed_models.keys())
                if available_models:
                    self.logger.warning(f"Model {request.model} not found, suggesting alternatives: {available_models[:3]}")
                raise ValueError(f"Model {request.model} is not installed. Available models: {list(self.installed_models.keys())}")
            
            # Prepare request parameters
            params = {
                'model': request.model,
                'prompt': request.prompt,
                'stream': request.stream,
                'raw': request.raw,
                'keep_alive': request.keep_alive or self.config.keep_alive
            }
            
            if request.system:
                params['system'] = request.system
            if request.template:
                params['template'] = request.template
            if request.context:
                params['context'] = request.context
            if request.format:
                params['format'] = request.format
            if request.options:
                params['options'] = request.options
            
            # Make request
            if request.stream:
                return self._generate_streaming(params, start_time)
            else:
                return await self._generate_single(params, start_time)
                
        except Exception as e:
            self.performance_stats['failed_requests'] += 1
            
            error_type = type(e).__name__
            if error_type not in self.performance_stats['error_counts']:
                self.performance_stats['error_counts'][error_type] = 0
            self.performance_stats['error_counts'][error_type] += 1
            
            log_error_with_context('virtuai.ollama', e, {
                'operation': 'generate',
                'model': request.model,
                'prompt_length': len(request.prompt)
            })
            raise
    
    async def _generate_single(self, params: Dict[str, Any], start_time: float) -> GenerationResponse:
        """Generate a single response"""
        try:
            # Use ollama library
            response_data = await asyncio.to_thread(ollama.generate, **params)
            
            # Update performance statistics
            end_time = time.time()
            response_time = end_time - start_time
            
            self._update_performance_stats(params['model'], response_time)
            
            # Create response object
            response = GenerationResponse(
                model=response_data['model'],
                response=response_data['response'],
                done=response_data.get('done', True),
                context=response_data.get('context'),
                total_duration=response_data.get('total_duration'),
                load_duration=response_data.get('load_duration'),
                prompt_eval_count=response_data.get('prompt_eval_count'),
                prompt_eval_duration=response_data.get('prompt_eval_duration'),
                eval_count=response_data.get('eval_count'),
                eval_duration=response_data.get('eval_duration')
            )
            
            # Log performance if slow
            if response_time > 10.0:
                log_performance_warning(
                    'ollama',
                    'response_time',
                    response_time,
                    10.0
                )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise
    
    async def _generate_streaming(self, params: Dict[str, Any], start_time: float) -> AsyncGenerator[GenerationResponse, None]:
        """Generate streaming responses"""
        try:
            # Use ollama library for streaming
            def stream_generator():
                return ollama.generate(**params)
            
            stream = await asyncio.to_thread(stream_generator)
            
            for chunk in stream:
                response = GenerationResponse(
                    model=chunk['model'],
                    response=chunk['response'],
                    done=chunk.get('done', False),
                    context=chunk.get('context'),
                    total_duration=chunk.get('total_duration'),
                    load_duration=chunk.get('load_duration'),
                    prompt_eval_count=chunk.get('prompt_eval_count'),
                    prompt_eval_duration=chunk.get('prompt_eval_duration'),
                    eval_count=chunk.get('eval_count'),
                    eval_duration=chunk.get('eval_duration')
                )
                
                yield response
                
                if chunk.get('done', False):
                    # Update performance stats for completed stream
                    response_time = time.time() - start_time
                    self._update_performance_stats(params['model'], response_time)
                    break
                    
        except Exception as e:
            self.logger.error(f"Streaming generation failed: {e}")
            raise
    
    def _update_performance_stats(self, model: str, response_time: float):
        """Update performance statistics"""
        self.performance_stats['successful_requests'] += 1
        self.performance_stats['total_response_time'] += response_time
        
        model_stats = self.performance_stats['model_usage'][model]
        model_stats['requests'] += 1
        model_stats['total_time'] += response_time
        model_stats['avg_time'] = model_stats['total_time'] / model_stats['requests']
        model_stats['last_used'] = datetime.utcnow().isoformat()
        
        # Update model info
        if model in self.installed_models:
            model_info = self.installed_models[model]
            model_info.last_used = datetime.utcnow()
            model_info.usage_count += 1
            model_info.average_response_time = (
                (model_info.average_response_time * (model_info.usage_count - 1) + response_time) /
                model_info.usage_count
            )
    
    async def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat with a model using conversation format"""
        try:
            # Use ollama library for chat
            response = await asyncio.to_thread(
                ollama.chat,
                model=model,
                messages=messages,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            log_error_with_context('virtuai.ollama', e, {
                'operation': 'chat',
                'model': model,
                'message_count': len(messages)
            })
            raise
    
    async def embeddings(self, model: str, prompt: str) -> List[float]:
        """Generate embeddings for text"""
        try:
            response = await asyncio.to_thread(
                ollama.embeddings,
                model=model,
                prompt=prompt
            )
            
            return response.get('embedding', [])
            
        except Exception as e:
            log_error_with_context('virtuai.ollama', e, {
                'operation': 'embeddings',
                'model': model,
                'prompt_length': len(prompt)
            })
            raise
    
    def get_model_recommendations(self, available_ram_gb: int) -> List[str]:
        """Get model recommendations based on available RAM"""
        recommendations = []
        
        for model_name, model_info in self.model_registry.items():
            if model_info.recommended_ram_gb <= available_ram_gb:
                recommendations.append(model_name)
        
        # Sort by performance tier and size
        tier_order = {'fast': 0, 'medium': 1, 'balanced': 2, 'high': 3, 'premium': 4}
        recommendations.sort(key=lambda x: (
            tier_order.get(self.model_registry[x].performance_tier, 5),
            self.model_registry[x].size_gb
        ))
        
        return recommendations
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        stats = self.performance_stats.copy()
        
        # Calculate additional metrics
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_requests'] / stats['total_requests']
            stats['failure_rate'] = stats['failed_requests'] / stats['total_requests']
            stats['avg_response_time'] = stats['total_response_time'] / stats['successful_requests'] if stats['successful_requests'] > 0 else 0
        else:
            stats['success_rate'] = 0
            stats['failure_rate'] = 0
            stats['avg_response_time'] = 0
        
        # Add service info
        stats['service_info'] = {
            'is_running': self.is_running,
            'uptime': self._get_uptime(),
            'installed_models': len(self.installed_models),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
        }
        
        return stats
    
    def _get_uptime(self) -> Optional[float]:
        """Get service uptime in seconds"""
        if self.service_start_time:
            return (datetime.utcnow() - self.service_start_time).total_seconds()
        return None
    
    async def _monitor_service(self):
        """Background task to monitor service health"""
        while self.is_running:
            try:
                await self.health_check()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.warning(f"Health check failed: {e}")
                await asyncio.sleep(30)  # Retry sooner if failed
    
    async def _cleanup_unused_models(self):
        """Background task to cleanup unused models"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                # Find models not used in the last 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                unused_models = []
                
                for model_name, model_info in self.installed_models.items():
                    if (model_info.last_used and
                        model_info.last_used < cutoff_time and
                        model_info.usage_count < 5):  # Low usage threshold
                        unused_models.append(model_name)
                
                # Log unused models (don't auto-delete for safety)
                if unused_models:
                    self.logger.info(f"Unused models detected: {unused_models}")
                    
            except Exception as e:
                log_error_with_context('virtuai.ollama', e, {'operation': 'cleanup'})
                await asyncio.sleep(1800)  # Wait 30 minutes on error


# Convenience functions and utilities

async def create_ollama_service(config: Optional[OllamaConfig] = None) -> OllamaService:
    """Create and initialize an Ollama service"""
    service = OllamaService(config)
    await service.initialize()
    return service


def get_recommended_models_for_system(ram_gb: int, use_case: str = "general") -> List[str]:
    """Get recommended models for a specific system configuration"""
    service = OllamaService()  # Just for model registry access
    
    recommendations = service.get_model_recommendations(ram_gb)
    
    # Filter by use case
    if use_case == "coding":
        recommendations = [m for m in recommendations if "codellama" in m or "code" in service.model_registry[m].capabilities]
    elif use_case == "chat":
        recommendations = [m for m in recommendations if "chat" in service.model_registry[m].capabilities]
    
    return recommendations[:5]  # Return top 5 recommendations


async def quick_generate(model: str, prompt: str, **kwargs) -> str:
    """Quick text generation utility"""
    async with OllamaService() as service:
        request = GenerationRequest(
            model=model,
            prompt=prompt,
            **kwargs
        )
        response = await service.generate(request)
        return response.response


# Global service instance management
_global_service: Optional[OllamaService] = None


async def get_global_ollama_service(config: Optional[OllamaConfig] = None) -> OllamaService:
    """Get or create the global Ollama service instance"""
    global _global_service
    
    if _global_service is None or not _global_service.is_running:
        _global_service = OllamaService(config)
        await _global_service.initialize()
    
    return _global_service


async def shutdown_global_ollama_service():
    """Shutdown the global Ollama service instance"""
    global _global_service
    
    if _global_service:
        await _global_service.shutdown()
        _global_service = None
