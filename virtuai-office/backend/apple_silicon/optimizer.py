# VirtuAI Office - Apple Silicon Optimizer
# Advanced hardware detection, optimization, and performance tuning for M1/M2/M3 Macs

import asyncio
import json
import subprocess
import platform
import psutil
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Apple Silicon Detection and Optimization
class ChipType(str, Enum):
    M1 = "m1"
    M2 = "m2"
    M3 = "m3"
    M1_PRO = "m1_pro"
    M1_MAX = "m1_max"
    M1_ULTRA = "m1_ultra"
    M2_PRO = "m2_pro"
    M2_MAX = "m2_max"
    M2_ULTRA = "m2_ultra"
    M3_PRO = "m3_pro"
    M3_MAX = "m3_max"
    INTEL = "intel"
    UNKNOWN = "unknown"

class OptimizationLevel(str, Enum):
    CONSERVATIVE = "conservative"  # Safe defaults
    BALANCED = "balanced"         # Recommended settings
    AGGRESSIVE = "aggressive"     # Maximum performance
    CUSTOM = "custom"            # User-defined

@dataclass
class AppleSiliconSpecs:
    chip_type: ChipType
    unified_memory_gb: int
    cpu_cores: int
    gpu_cores: int
    neural_engine: bool
    memory_bandwidth_gbps: float
    max_power_watts: float
    optimal_models: List[str]
    max_concurrent_agents: int

@dataclass
class SystemPerformance:
    cpu_usage: float
    memory_usage: float
    memory_pressure: str
    thermal_state: str
    power_mode: str
    battery_level: Optional[float]
    inference_speed: float  # tokens/second
    model_load_time: float  # seconds

# Apple Silicon Hardware Detection
class AppleSiliconDetector:
    def __init__(self):
        self.specs_database = self._load_chip_specifications()
    
    def _load_chip_specifications(self) -> Dict[ChipType, AppleSiliconSpecs]:
        """Database of Apple Silicon chip specifications"""
        return {
            ChipType.M1: AppleSiliconSpecs(
                chip_type=ChipType.M1,
                unified_memory_gb=8,  # Base config
                cpu_cores=8,
                gpu_cores=7,  # Base M1
                neural_engine=True,
                memory_bandwidth_gbps=68.25,
                max_power_watts=20,
                optimal_models=["llama2:7b", "codellama:7b"],
                max_concurrent_agents=3
            ),
            ChipType.M1_PRO: AppleSiliconSpecs(
                chip_type=ChipType.M1_PRO,
                unified_memory_gb=16,
                cpu_cores=10,
                gpu_cores=16,
                neural_engine=True,
                memory_bandwidth_gbps=200,
                max_power_watts=30,
                optimal_models=["llama2:13b", "codellama:13b"],
                max_concurrent_agents=5
            ),
            ChipType.M1_MAX: AppleSiliconSpecs(
                chip_type=ChipType.M1_MAX,
                unified_memory_gb=32,
                cpu_cores=10,
                gpu_cores=32,
                neural_engine=True,
                memory_bandwidth_gbps=400,
                max_power_watts=60,
                optimal_models=["llama2:13b", "codellama:13b", "llama2:70b"],
                max_concurrent_agents=8
            ),
            ChipType.M2: AppleSiliconSpecs(
                chip_type=ChipType.M2,
                unified_memory_gb=8,
                cpu_cores=8,
                gpu_cores=10,
                neural_engine=True,
                memory_bandwidth_gbps=100,
                max_power_watts=20,
                optimal_models=["llama2:7b", "codellama:7b"],
                max_concurrent_agents=4
            ),
            ChipType.M2_PRO: AppleSiliconSpecs(
                chip_type=ChipType.M2_PRO,
                unified_memory_gb=16,
                cpu_cores=12,
                gpu_cores=19,
                neural_engine=True,
                memory_bandwidth_gbps=200,
                max_power_watts=30,
                optimal_models=["llama2:13b", "codellama:13b"],
                max_concurrent_agents=6
            ),
            ChipType.M2_MAX: AppleSiliconSpecs(
                chip_type=ChipType.M2_MAX,
                unified_memory_gb=64,
                cpu_cores=12,
                gpu_cores=38,
                neural_engine=True,
                memory_bandwidth_gbps=400,
                max_power_watts=60,
                optimal_models=["llama2:13b", "codellama:13b", "llama2:70b"],
                max_concurrent_agents=10
            ),
            ChipType.M3: AppleSiliconSpecs(
                chip_type=ChipType.M3,
                unified_memory_gb=8,
                cpu_cores=8,
                gpu_cores=10,
                neural_engine=True,
                memory_bandwidth_gbps=100,
                max_power_watts=22,
                optimal_models=["llama2:7b", "codellama:7b"],
                max_concurrent_agents=5
            ),
            ChipType.M3_PRO: AppleSiliconSpecs(
                chip_type=ChipType.M3_PRO,
                unified_memory_gb=18,
                cpu_cores=12,
                gpu_cores=18,
                neural_engine=True,
                memory_bandwidth_gbps=150,
                max_power_watts=30,
                optimal_models=["llama2:13b", "codellama:13b"],
                max_concurrent_agents=7
            ),
            ChipType.M3_MAX: AppleSiliconSpecs(
                chip_type=ChipType.M3_MAX,
                unified_memory_gb=64,
                cpu_cores=16,
                gpu_cores=40,
                neural_engine=True,
                memory_bandwidth_gbps=300,
                max_power_watts=60,
                optimal_models=["llama2:13b", "codellama:13b", "llama2:70b"],
                max_concurrent_agents=12
            )
        }
    
    def detect_apple_silicon(self) -> Tuple[ChipType, AppleSiliconSpecs]:
        """Detect Apple Silicon chip type and return specifications"""
        
        if platform.system() != "Darwin":
            return ChipType.INTEL, None
        
        try:
            # Get chip information from system
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                check=True
            )
            
            cpu_brand = result.stdout.strip()
            
            # Detect chip type
            if "Apple M1" in cpu_brand:
                if "Pro" in cpu_brand:
                    chip_type = ChipType.M1_PRO
                elif "Max" in cpu_brand:
                    chip_type = ChipType.M1_MAX
                elif "Ultra" in cpu_brand:
                    chip_type = ChipType.M1_ULTRA
                else:
                    chip_type = ChipType.M1
            elif "Apple M2" in cpu_brand:
                if "Pro" in cpu_brand:
                    chip_type = ChipType.M2_PRO
                elif "Max" in cpu_brand:
                    chip_type = ChipType.M2_MAX
                elif "Ultra" in cpu_brand:
                    chip_type = ChipType.M2_ULTRA
                else:
                    chip_type = ChipType.M2
            elif "Apple M3" in cpu_brand:
                if "Pro" in cpu_brand:
                    chip_type = ChipType.M3_PRO
                elif "Max" in cpu_brand:
                    chip_type = ChipType.M3_MAX
                else:
                    chip_type = ChipType.M3
            else:
                return ChipType.INTEL, None
            
            # Get base specs and adjust for actual system
            base_specs = self.specs_database.get(chip_type)
            if not base_specs:
                return ChipType.UNKNOWN, None
            
            # Get actual memory size
            actual_memory_gb = self._get_actual_memory_gb()
            
            # Create adjusted specs
            actual_specs = AppleSiliconSpecs(
                chip_type=chip_type,
                unified_memory_gb=actual_memory_gb,
                cpu_cores=base_specs.cpu_cores,
                gpu_cores=base_specs.gpu_cores,
                neural_engine=base_specs.neural_engine,
                memory_bandwidth_gbps=base_specs.memory_bandwidth_gbps,
                max_power_watts=base_specs.max_power_watts,
                optimal_models=self._adjust_optimal_models(base_specs.optimal_models, actual_memory_gb),
                max_concurrent_agents=self._adjust_max_agents(base_specs.max_concurrent_agents, actual_memory_gb)
            )
            
            return chip_type, actual_specs
            
        except subprocess.CalledProcessError:
            return ChipType.UNKNOWN, None
    
    def _get_actual_memory_gb(self) -> int:
        """Get actual system memory in GB"""
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                check=True
            )
            memory_bytes = int(result.stdout.strip())
            return memory_bytes // (1024 * 1024 * 1024)
        except:
            return psutil.virtual_memory().total // (1024 * 1024 * 1024)
    
    def _adjust_optimal_models(self, base_models: List[str], memory_gb: int) -> List[str]:
        """Adjust optimal models based on available memory"""
        if memory_gb >= 64:
            return ["llama2:70b", "codellama:34b", "llama2:13b", "codellama:13b"]
        elif memory_gb >= 32:
            return ["llama2:13b", "codellama:13b", "llama2:7b", "codellama:7b"]
        elif memory_gb >= 16:
            return ["llama2:7b", "codellama:7b", "llama2:13b-q4_0"]
        else:
            return ["llama2:7b-q4_0", "codellama:7b-q4_0"]
    
    def _adjust_max_agents(self, base_agents: int, memory_gb: int) -> int:
        """Adjust maximum concurrent agents based on memory"""
        memory_factor = memory_gb / 8  # Base is 8GB
        return max(1, int(base_agents * memory_factor * 0.8))  # Conservative adjustment

# Apple Silicon Performance Monitor
class AppleSiliconMonitor:
    def __init__(self):
        self.baseline_metrics = None
        self.monitoring_active = False
    
    async def get_system_performance(self) -> SystemPerformance:
        """Get current system performance metrics"""
        
        # CPU and Memory
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # macOS-specific metrics
        memory_pressure = await self._get_memory_pressure()
        thermal_state = await self._get_thermal_state()
        power_mode = await self._get_power_mode()
        battery_level = await self._get_battery_level()
        
        # AI-specific metrics
        inference_speed = await self._measure_inference_speed()
        model_load_time = await self._measure_model_load_time()
        
        return SystemPerformance(
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            memory_pressure=memory_pressure,
            thermal_state=thermal_state,
            power_mode=power_mode,
            battery_level=battery_level,
            inference_speed=inference_speed,
            model_load_time=model_load_time
        )
    
    async def _get_memory_pressure(self) -> str:
        """Get macOS memory pressure state"""
        try:
            result = subprocess.run(
                ["memory_pressure"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            if "critical" in output:
                return "critical"
            elif "warn" in output:
                return "warning"
            else:
                return "normal"
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return "unknown"
    
    async def _get_thermal_state(self) -> str:
        """Get thermal state information"""
        try:
            result = subprocess.run(
                ["pmset", "-g", "therm"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            if "cpu_speed_limit" in output:
                return "throttling"
            elif "thermal_state" in output and "0" not in output:
                return "elevated"
            else:
                return "normal"
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return "unknown"
    
    async def _get_power_mode(self) -> str:
        """Get current power mode"""
        try:
            result = subprocess.run(
                ["pmset", "-g", "custom"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            if "automaticrestartonimp" in output:
                return "automatic"
            elif "powernap" in output and "1" in output:
                return "power_nap"
            else:
                return "standard"
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return "unknown"
    
    async def _get_battery_level(self) -> Optional[float]:
        """Get battery level if on laptop"""
        try:
            if not psutil.sensors_battery():
                return None
            
            battery = psutil.sensors_battery()
            return battery.percent if battery else None
            
        except:
            return None
    
    async def _measure_inference_speed(self) -> float:
        """Measure current AI inference speed"""
        try:
            import ollama
            start_time = time.time()
            
            # Simple inference test
            test_response = await asyncio.to_thread(
                ollama.generate,
                model="llama2:7b",
                prompt="Hello, how are you?",
                stream=False
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Estimate tokens per second (rough approximation)
            response_length = len(test_response.get('response', '').split())
            tokens_per_second = response_length / duration if duration > 0 else 0
            
            return tokens_per_second
            
        except Exception as e:
            logger.warning(f"Inference speed measurement failed: {e}")
            return 0.0
    
    async def _measure_model_load_time(self) -> float:
        """Measure model loading time"""
        try:
            import ollama
            start_time = time.time()
            
            # Test model loading
            ollama.list()  # This triggers model verification
            
            end_time = time.time()
            return end_time - start_time
            
        except Exception as e:
            logger.warning(f"Model load time measurement failed: {e}")
            return 0.0

# Apple Silicon Optimizer
class AppleSiliconOptimizer:
    def __init__(self, detector: AppleSiliconDetector, monitor: AppleSiliconMonitor):
        self.detector = detector
        self.monitor = monitor
        self.current_profile = None
    
    async def create_optimization_profile(self) -> Dict[str, Any]:
        """Create or update optimization profile for current system"""
        
        chip_type, specs = self.detector.detect_apple_silicon()
        
        if chip_type == ChipType.INTEL:
            raise Exception("Apple Silicon optimization not available on Intel Macs")
        
        if not specs:
            raise Exception("Unable to detect Apple Silicon specifications")
        
        # Apply optimizations
        await self._apply_optimizations(specs)
        
        profile = {
            "chip_type": chip_type.value,
            "memory_gb": specs.unified_memory_gb,
            "cpu_cores": specs.cpu_cores,
            "gpu_cores": specs.gpu_cores,
            "preferred_models": specs.optimal_models,
            "max_concurrent_tasks": specs.max_concurrent_agents,
            "last_optimized": datetime.utcnow().isoformat()
        }
        
        self.current_profile = profile
        return profile
    
    async def _apply_optimizations(self, specs: AppleSiliconSpecs):
        """Apply Apple Silicon specific optimizations"""
        
        # Set optimal power management
        await self._optimize_power_management()
        
        # Configure memory settings
        await self._optimize_memory_settings()
        
        # Set optimal Ollama configurations
        await self._optimize_ollama_settings(specs)
        
        # Configure thermal management
        await self._optimize_thermal_settings()
    
    async def _optimize_power_management(self):
        """Optimize power management for AI workloads"""
        try:
            # Disable Power Nap during AI processing
            subprocess.run([
                "sudo", "pmset", "-c", "powernap", "0"
            ], check=True, capture_output=True)
            
            # Prevent system sleep during processing
            subprocess.run([
                "sudo", "pmset", "-c", "sleep", "0"
            ], check=True, capture_output=True)
            
            logger.info("✅ Power management optimized for AI workloads")
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Power optimization failed (requires sudo): {e}")
    
    async def _optimize_memory_settings(self):
        """Optimize memory settings for Apple Silicon"""
        try:
            # Increase file descriptor limits for AI processing
            os.system("ulimit -n 4096")
            
            # Set memory allocation preferences
            os.environ["MALLOC_ARENA_MAX"] = "2"
            os.environ["MALLOC_MMAP_THRESHOLD_"] = "131072"
            
            logger.info("✅ Memory settings optimized")
            
        except Exception as e:
            logger.warning(f"Memory optimization failed: {e}")
    
    async def _optimize_ollama_settings(self, specs: AppleSiliconSpecs):
        """Configure Ollama for optimal Apple Silicon performance"""
        try:
            # Set optimal thread count based on CPU cores
            optimal_threads = max(1, specs.cpu_cores - 2)  # Leave 2 cores for system
            os.environ["OLLAMA_NUM_THREADS"] = str(optimal_threads)
            
            # Configure memory usage based on available RAM
            memory_gb = specs.unified_memory_gb
            if memory_gb >= 32:
                os.environ["OLLAMA_MAX_LOADED_MODELS"] = "3"
            elif memory_gb >= 16:
                os.environ["OLLAMA_MAX_LOADED_MODELS"] = "2"
            else:
                os.environ["OLLAMA_MAX_LOADED_MODELS"] = "1"
            
            # Enable GPU acceleration for Apple Silicon
            os.environ["OLLAMA_METAL"] = "1"
            
            logger.info(f"✅ Ollama optimized for {specs.chip_type.value} with {optimal_threads} threads")
            
        except Exception as e:
            logger.warning(f"Ollama optimization failed: {e}")
    
    async def _optimize_thermal_settings(self):
        """Configure thermal management"""
        try:
            # Enable thermal monitoring
            os.environ["ENABLE_THERMAL_MONITORING"] = "1"
            
            logger.info("✅ Thermal monitoring enabled")
            
        except Exception as e:
            logger.warning(f"Thermal optimization failed: {e}")
    
    async def auto_select_model(self, task_complexity: str, specs: AppleSiliconSpecs) -> str:
        """Automatically select optimal model based on task and hardware"""
        
        complexity_model_map = {
            "simple": specs.optimal_models[0] if specs.optimal_models else "llama2:7b",
            "medium": specs.optimal_models[1] if len(specs.optimal_models) > 1 else specs.optimal_models[0],
            "complex": specs.optimal_models[-1] if specs.optimal_models else "llama2:7b"
        }
        
        selected_model = complexity_model_map.get(task_complexity, specs.optimal_models[0])
        
        # Verify model is available
        try:
            import ollama
            available_models = ollama.list()
            model_names = [model['name'] for model in available_models.get('models', [])]
            
            if selected_model not in model_names:
                # Fallback to available model
                for model in specs.optimal_models:
                    if model in model_names:
                        selected_model = model
                        break
                else:
                    selected_model = model_names[0] if model_names else "llama2:7b"
        
        except Exception as e:
            logger.warning(f"Model verification failed: {e}")
        
        return selected_model
    
    async def benchmark_performance(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark"""
        
        chip_type, specs = self.detector.detect_apple_silicon()
        if not specs:
            raise Exception("Apple Silicon not detected")
        
        benchmark_results = {
            "chip_type": chip_type.value,
            "memory_gb": specs.unified_memory_gb,
            "cpu_cores": specs.cpu_cores,
            "gpu_cores": specs.gpu_cores,
            "benchmarks": {}
        }
        
        # Test different models
        for model in specs.optimal_models[:2]:  # Test top 2 models
            try:
                model_results = await self._benchmark_model(model)
                benchmark_results["benchmarks"][model] = model_results
                
            except Exception as e:
                logger.warning(f"Benchmark failed for model {model}: {e}")
                benchmark_results["benchmarks"][model] = {"error": str(e)}
        
        return benchmark_results
    
    async def _benchmark_model(self, model: str) -> Dict[str, float]:
        """Benchmark specific model performance"""
        
        import ollama
        
        # Warm up
        try:
            await asyncio.to_thread(
                ollama.generate,
                model=model,
                prompt="Test",
                stream=False
            )
        except:
            pass
        
        # Measure load time
        start_time = time.time()
        try:
            ollama.list()  # Verify model
            load_time = time.time() - start_time
        except:
            load_time = 0.0
        
        # Measure inference speed
        test_prompts = [
            "Write a simple Python function to calculate fibonacci numbers.",
            "Explain the concept of machine learning in simple terms.",
            "Create a React component for a button with hover effects."
        ]
        
        total_tokens = 0
        total_time = 0
        cpu_usage_samples = []
        memory_usage_samples = []
        
        for prompt in test_prompts:
            start_cpu = psutil.cpu_percent()
            start_memory = psutil.virtual_memory().percent
            
            start_time = time.time()
            try:
                response = await asyncio.to_thread(
                    ollama.generate,
                    model=model,
                    prompt=prompt,
                    stream=False
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                tokens = len(response.get('response', '').split())
                total_tokens += tokens
                total_time += duration
                
                end_cpu = psutil.cpu_percent()
                end_memory = psutil.virtual_memory().percent
                
                cpu_usage_samples.append(end_cpu - start_cpu)
                memory_usage_samples.append(end_memory - start_memory)
                
            except Exception as e:
                logger.warning(f"Benchmark prompt failed: {e}")
        
        avg_tokens_per_second = total_tokens / total_time if total_time > 0 else 0
        avg_cpu_usage = sum(cpu_usage_samples) / len(cpu_usage_samples) if cpu_usage_samples else 0
        avg_memory_usage = sum(memory_usage_samples) / len(memory_usage_samples) if memory_usage_samples else 0
        
        return {
            "tokens_per_second": avg_tokens_per_second,
            "load_time": load_time,
            "cpu_usage": avg_cpu_usage,
            "memory_usage": avg_memory_usage,
            "test_prompts": len(test_prompts)
        }

# Apple Silicon Model Manager
class AppleSiliconModelManager:
    def __init__(self, detector: AppleSiliconDetector):
        self.detector = detector
        self.model_cache = {}
        self.download_progress = {}
    
    async def recommend_models(self) -> Dict[str, Any]:
        """Recommend optimal models for current Apple Silicon system"""
        
        chip_type, specs = self.detector.detect_apple_silicon()
        if not specs:
            return {"error": "Apple Silicon not detected"}
        
        # Get currently installed models
        try:
            import ollama
            installed_models = ollama.list()
            installed_names = [model['name'] for model in installed_models.get('models', [])]
        except:
            installed_names = []
        
        recommendations = {
            "chip_type": chip_type.value,
            "memory_gb": specs.unified_memory_gb,
            "recommended_models": [],
            "optional_models": [],
            "not_recommended": [],
            "currently_installed": installed_names
        }
        
        # Categorize models based on system specs
        all_models = [
            {"name": "llama2:7b", "size_gb": 3.8, "complexity": "medium", "speed": "fast"},
            {"name": "llama2:7b-q4_0", "size_gb": 2.8, "complexity": "medium", "speed": "very_fast"},
            {"name": "llama2:13b", "size_gb": 7.3, "complexity": "high", "speed": "medium"},
            {"name": "llama2:13b-q4_0", "size_gb": 5.1, "complexity": "high", "speed": "fast"},
            {"name": "llama2:70b", "size_gb": 39.0, "complexity": "very_high", "speed": "slow"},
            {"name": "codellama:7b", "size_gb": 3.8, "complexity": "medium", "speed": "fast"},
            {"name": "codellama:13b", "size_gb": 7.3, "complexity": "high", "speed": "medium"},
            {"name": "codellama:34b", "size_gb": 19.0, "complexity": "very_high", "speed": "slow"}
        ]
        
        for model in all_models:
            if model["size_gb"] <= specs.unified_memory_gb * 0.4:  # Use 40% of memory max
                if model["name"] in specs.optimal_models:
                    recommendations["recommended_models"].append(model)
                else:
                    recommendations["optional_models"].append(model)
            else:
                recommendations["not_recommended"].append(model)
        
        return recommendations
    
    async def download_recommended_models(self) -> Dict[str, str]:
        """Download recommended models for current system"""
        
        recommendations = await self.recommend_models()
        if "error" in recommendations:
            return recommendations
        
        download_status = {}
        
        for model in recommendations["recommended_models"]:
            model_name = model["name"]
            
            if model_name not in recommendations["currently_installed"]:
                # Start download in background
                asyncio.create_task(self._download_model(model_name))
                download_status[model_name] = "downloading"
                self.download_progress[model_name] = 0.0
            else:
                download_status[model_name] = "already_installed"
        
        return download_status
    
    async def _download_model(self, model_name: str):
        """Download a specific model with progress tracking"""
        
        try:
            import ollama
            logger.info(f"Starting download of {model_name}...")
            self.download_progress[model_name] = 0.1
            
            # Download model (this is a blocking operation)
            await asyncio.to_thread(ollama.pull, model_name)
            
            self.download_progress[model_name] = 1.0
            logger.info(f"✅ {model_name} downloaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to download {model_name}: {e}")
            self.download_progress[model_name] = -1  # Error state
    
    def get_download_progress(self) -> Dict[str, float]:
        """Get current download progress for all models"""
        return dict(self.download_progress)

# Apple Silicon Performance Dashboard
class AppleSiliconDashboard:
    def __init__(self, detector: AppleSiliconDetector, monitor: AppleSiliconMonitor, optimizer: AppleSiliconOptimizer):
        self.detector = detector
        self.monitor = monitor
        self.optimizer = optimizer
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for Apple Silicon optimization"""
        
        chip_type, specs = self.detector.detect_apple_silicon()
        current_performance = await self.monitor.get_system_performance()
        
        # Calculate optimization score
        optimization_score = await self._calculate_optimization_score(current_performance, specs)
        
        dashboard_data = {
            "system_info": {
                "chip_type": chip_type.value if chip_type else "unknown",
                "is_apple_silicon": chip_type != ChipType.INTEL,
                "memory_gb": specs.unified_memory_gb if specs else 0,
                "cpu_cores": specs.cpu_cores if specs else 0,
                "gpu_cores": specs.gpu_cores if specs else 0,
                "neural_engine": specs.neural_engine if specs else False
            },
