# Apple Silicon Model Management System
# Intelligent model selection, downloading, and optimization for M1/M2/M3 Macs

import asyncio
import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import ollama
import psutil
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from .detector import ChipType, AppleSiliconSpecs

logger = logging.getLogger(__name__)

Base = declarative_base()

class ModelSize(str, Enum):
    SMALL = "7b"
    MEDIUM = "13b"
    LARGE = "34b"
    XLARGE = "70b"

class ModelType(str, Enum):
    GENERAL = "general"
    CODE = "code"
    CHAT = "chat"
    INSTRUCT = "instruct"

class QuantizationType(str, Enum):
    F16 = "f16"      # Full precision
    Q8_0 = "q8_0"    # 8-bit quantization
    Q4_K_M = "q4_k_m" # 4-bit quantization (medium)
    Q4_0 = "q4_0"    # 4-bit quantization
    Q2_K = "q2_k"    # 2-bit quantization (experimental)

@dataclass
class ModelSpec:
    name: str
    display_name: str
    size: ModelSize
    model_type: ModelType
    base_size_gb: float
    quantizations: List[QuantizationType]
    min_memory_gb: int
    recommended_memory_gb: int
    performance_tier: int  # 1-5, higher is better
    specializations: List[str]
    apple_silicon_optimized: bool = True

@dataclass
class ModelPerformance:
    model_name: str
    chip_type: ChipType
    memory_gb: int
    tokens_per_second: float
    load_time_seconds: float
    memory_usage_gb: float
    cpu_usage_percent: float
    thermal_impact: str  # low, medium, high
    quality_score: float  # 0-1
    benchmark_date: datetime

# Database Models
class InstalledModel(Base):
    __tablename__ = "installed_models"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    display_name = Column(String)
    size_gb = Column(Float)
    quantization = Column(String)
    install_date = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Performance metrics
    avg_tokens_per_second = Column(Float, default=0.0)
    avg_load_time = Column(Float, default=0.0)
    avg_memory_usage = Column(Float, default=0.0)
    
    # Apple Silicon specific
    chip_type = Column(String)
    optimized_for_chip = Column(Boolean, default=False)

class ModelDownload(Base):
    __tablename__ = "model_downloads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, downloading, completed, failed
    progress_percent = Column(Float, default=0.0)
    size_gb = Column(Float)
    downloaded_gb = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)

class ModelBenchmark(Base):
    __tablename__ = "model_benchmarks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String, nullable=False)
    chip_type = Column(String, nullable=False)
    memory_gb = Column(Integer, nullable=False)
    
    # Performance metrics
    tokens_per_second = Column(Float)
    load_time_seconds = Column(Float)
    memory_usage_gb = Column(Float)
    cpu_usage_percent = Column(Float)
    thermal_state = Column(String)
    
    # Quality metrics
    coherence_score = Column(Float)
    accuracy_score = Column(Float)
    response_quality = Column(Float)
    
    # Test details
    test_prompts_count = Column(Integer)
    benchmark_date = Column(DateTime, default=datetime.utcnow)
    benchmark_duration_seconds = Column(Float)

class AppleSiliconModelManager:
    def __init__(self, detector, monitor):
        self.detector = detector
        self.monitor = monitor
        self.model_catalog = self._load_model_catalog()
        self.download_progress = {}
        self.performance_cache = {}
    
    def _load_model_catalog(self) -> Dict[str, ModelSpec]:
        """Load comprehensive model catalog optimized for Apple Silicon"""
        return {
            # Llama2 Models
            "llama2:7b": ModelSpec(
                name="llama2:7b",
                display_name="Llama 2 7B",
                size=ModelSize.SMALL,
                model_type=ModelType.GENERAL,
                base_size_gb=3.8,
                quantizations=[QuantizationType.F16, QuantizationType.Q8_0, QuantizationType.Q4_0],
                min_memory_gb=8,
                recommended_memory_gb=16,
                performance_tier=3,
                specializations=["general_conversation", "text_generation", "analysis"],
                apple_silicon_optimized=True
            ),
            "llama2:7b-q4_0": ModelSpec(
                name="llama2:7b-q4_0",
                display_name="Llama 2 7B (Quantized)",
                size=ModelSize.SMALL,
                model_type=ModelType.GENERAL,
                base_size_gb=2.8,
                quantizations=[QuantizationType.Q4_0],
                min_memory_gb=6,
                recommended_memory_gb=8,
                performance_tier=4,
                specializations=["general_conversation", "fast_inference"],
                apple_silicon_optimized=True
            ),
            "llama2:13b": ModelSpec(
                name="llama2:13b",
                display_name="Llama 2 13B",
                size=ModelSize.MEDIUM,
                model_type=ModelType.GENERAL,
                base_size_gb=7.3,
                quantizations=[QuantizationType.F16, QuantizationType.Q8_0, QuantizationType.Q4_K_M],
                min_memory_gb=16,
                recommended_memory_gb=24,
                performance_tier=4,
                specializations=["advanced_reasoning", "complex_tasks", "high_quality"],
                apple_silicon_optimized=True
            ),
            "llama2:13b-q4_0": ModelSpec(
                name="llama2:13b-q4_0",
                display_name="Llama 2 13B (Quantized)",
                size=ModelSize.MEDIUM,
                model_type=ModelType.GENERAL,
                base_size_gb=5.1,
                quantizations=[QuantizationType.Q4_0],
                min_memory_gb=12,
                recommended_memory_gb=16,
                performance_tier=5,
                specializations=["advanced_reasoning", "fast_inference", "balanced"],
                apple_silicon_optimized=True
            ),
            "llama2:70b": ModelSpec(
                name="llama2:70b",
                display_name="Llama 2 70B",
                size=ModelSize.XLARGE,
                model_type=ModelType.GENERAL,
                base_size_gb=39.0,
                quantizations=[QuantizationType.Q4_K_M, QuantizationType.Q4_0],
                min_memory_gb=64,
                recommended_memory_gb=128,
                performance_tier=5,
                specializations=["expert_reasoning", "complex_analysis", "highest_quality"],
                apple_silicon_optimized=True
            ),
            
            # CodeLlama Models
            "codellama:7b": ModelSpec(
                name="codellama:7b",
                display_name="Code Llama 7B",
                size=ModelSize.SMALL,
                model_type=ModelType.CODE,
                base_size_gb=3.8,
                quantizations=[QuantizationType.F16, QuantizationType.Q4_0],
                min_memory_gb=8,
                recommended_memory_gb=16,
                performance_tier=4,
                specializations=["code_generation", "debugging", "refactoring", "documentation"],
                apple_silicon_optimized=True
            ),
            "codellama:7b-instruct": ModelSpec(
                name="codellama:7b-instruct",
                display_name="Code Llama 7B Instruct",
                size=ModelSize.SMALL,
                model_type=ModelType.INSTRUCT,
                base_size_gb=3.8,
                quantizations=[QuantizationType.F16, QuantizationType.Q4_0],
                min_memory_gb=8,
                recommended_memory_gb=16,
                performance_tier=4,
                specializations=["code_explanation", "guided_programming", "tutorials"],
                apple_silicon_optimized=True
            ),
            "codellama:13b": ModelSpec(
                name="codellama:13b",
                display_name="Code Llama 13B",
                size=ModelSize.MEDIUM,
                model_type=ModelType.CODE,
                base_size_gb=7.3,
                quantizations=[QuantizationType.F16, QuantizationType.Q4_K_M],
                min_memory_gb=16,
                recommended_memory_gb=24,
                performance_tier=5,
                specializations=["advanced_coding", "architecture", "complex_algorithms"],
                apple_silicon_optimized=True
            ),
            "codellama:34b": ModelSpec(
                name="codellama:34b",
                display_name="Code Llama 34B",
                size=ModelSize.LARGE,
                model_type=ModelType.CODE,
                base_size_gb=19.0,
                quantizations=[QuantizationType.Q4_K_M, QuantizationType.Q4_0],
                min_memory_gb=32,
                recommended_memory_gb=48,
                performance_tier=5,
                specializations=["expert_programming", "system_design", "enterprise_code"],
                apple_silicon_optimized=True
            ),
            
            # Specialized Models
            "mistral:7b": ModelSpec(
                name="mistral:7b",
                display_name="Mistral 7B",
                size=ModelSize.SMALL,
                model_type=ModelType.GENERAL,
                base_size_gb=4.1,
                quantizations=[QuantizationType.F16, QuantizationType.Q4_0],
                min_memory_gb=8,
                recommended_memory_gb=16,
                performance_tier=4,
                specializations=["fast_reasoning", "multilingual", "efficient"],
                apple_silicon_optimized=True
            ),
            "neural-chat:7b": ModelSpec(
                name="neural-chat:7b",
                display_name="Neural Chat 7B",
                size=ModelSize.SMALL,
                model_type=ModelType.CHAT,
                base_size_gb=3.8,
                quantizations=[QuantizationType.F16, QuantizationType.Q4_0],
                min_memory_gb=8,
                recommended_memory_gb=16,
                performance_tier=3,
                specializations=["conversation", "assistance", "friendly"],
                apple_silicon_optimized=True
            )
        }
    
    async def get_recommendations_for_system(self, chip_type: ChipType, memory_gb: int, use_case: str = "general") -> Dict[str, Any]:
        """Get model recommendations optimized for specific Apple Silicon system"""
        
        recommendations = {
            "chip_type": chip_type.value,
            "memory_gb": memory_gb,
            "use_case": use_case,
            "essential": [],      # Must-have models
            "recommended": [],    # Highly recommended
            "optional": [],       # Nice to have if space allows
            "not_suitable": [],   # Don't recommend for this system
            "total_size_gb": 0
        }
        
        # Get current installed models
        installed_models = await self._get_installed_models()
        installed_names = {model['name'] for model in installed_models}
        
        for model_name, spec in self.model_catalog.items():
            suitability = self._assess_model_suitability(spec, chip_type, memory_gb, use_case)
            model_info = {
                "name": model_name,
                "display_name": spec.display_name,
                "size_gb": spec.base_size_gb,
                "performance_tier": spec.performance_tier,
                "specializations": spec.specializations,
                "already_installed": model_name in installed_names,
                "suitability_score": suitability["score"],
                "reasons": suitability["reasons"]
            }
            
            if suitability["category"] == "essential":
                recommendations["essential"].append(model_info)
            elif suitability["category"] == "recommended":
                recommendations["recommended"].append(model_info)
            elif suitability["category"] == "optional":
                recommendations["optional"].append(model_info)
            else:
                recommendations["not_suitable"].append(model_info)
        
        # Sort by performance tier and suitability score
        for category in ["essential", "recommended", "optional"]:
            recommendations[category].sort(
                key=lambda x: (x["performance_tier"], x["suitability_score"]),
                reverse=True
            )
        
        # Calculate total recommended size
        total_size = sum(
            model["size_gb"] for model in
            recommendations["essential"] + recommendations["recommended"]
            if not model["already_installed"]
        )
        recommendations["total_size_gb"] = round(total_size, 1)
        
        return recommendations
    
    def _assess_model_suitability(self, spec: ModelSpec, chip_type: ChipType, memory_gb: int, use_case: str) -> Dict[str, Any]:
        """Assess how suitable a model is for the given system and use case"""
        
        score = 0.0
        reasons = []
        
        # Memory assessment
        if memory_gb >= spec.recommended_memory_gb:
            score += 0.4
            reasons.append(f"Plenty of memory ({memory_gb}GB >= {spec.recommended_memory_gb}GB recommended)")
        elif memory_gb >= spec.min_memory_gb:
            score += 0.2
            reasons.append(f"Sufficient memory ({memory_gb}GB >= {spec.min_memory_gb}GB minimum)")
        else:
            score = 0.0
            reasons.append(f"Insufficient memory ({memory_gb}GB < {spec.min_memory_gb}GB minimum)")
            return {"score": score, "reasons": reasons, "category": "not_suitable"}
        
        # Apple Silicon optimization
        if spec.apple_silicon_optimized:
            score += 0.2
            reasons.append("Optimized for Apple Silicon")
        
        # Use case matching
        use_case_keywords = {
            "general": ["general_conversation", "text_generation", "analysis"],
            "coding": ["code_generation", "debugging", "refactoring"],
            "design": ["creative", "visual", "design"],
            "research": ["analysis", "reasoning", "research"],
            "chat": ["conversation", "assistance", "friendly"]
        }
        
        relevant_keywords = use_case_keywords.get(use_case, use_case_keywords["general"])
        matching_specializations = [s for s in spec.specializations if any(k in s for k in relevant_keywords)]
        
        if matching_specializations:
            score += 0.2
            reasons.append(f"Matches use case: {', '.join(matching_specializations)}")
        
        # Performance tier bonus
        score += spec.performance_tier * 0.02
        
        # Chip-specific optimizations
        chip_bonuses = {
            ChipType.M1: {"7b": 0.1, "13b": 0.05},
            ChipType.M1_PRO: {"7b": 0.15, "13b": 0.1, "34b": 0.05},
            ChipType.M1_MAX: {"13b": 0.15, "34b": 0.1, "70b": 0.05},
            ChipType.M2: {"7b": 0.15, "13b": 0.1},
            ChipType.M2_PRO: {"7b": 0.2, "13b": 0.15, "34b": 0.1},
            ChipType.M2_MAX: {"13b": 0.2, "34b": 0.15, "70b": 0.1},
            ChipType.M3: {"7b": 0.2, "13b": 0.15},
            ChipType.M3_PRO: {"7b": 0.25, "13b": 0.2, "34b": 0.15},
            ChipType.M3_MAX: {"13b": 0.25, "34b": 0.2, "70b": 0.15}
        }
        
        chip_bonus = chip_bonuses.get(chip_type, {}).get(spec.size.value, 0)
        if chip_bonus > 0:
            score += chip_bonus
            reasons.append(f"Optimized for {chip_type.value.upper()}")
        
        # Categorize based on score
        if score >= 0.8:
            category = "essential"
        elif score >= 0.5:
            category = "recommended"
        elif score >= 0.3:
            category = "optional"
        else:
            category = "not_suitable"
        
        return {
            "score": round(score, 3),
            "reasons": reasons,
            "category": category
        }
    
    async def download_model(self, model_name: str, background_callback=None) -> str:
        """Download a model with progress tracking"""
        
        if model_name in self.download_progress:
            return f"Model {model_name} is already being downloaded"
        
        try:
            # Initialize progress tracking
            self.download_progress[model_name] = {
                "status": "starting",
                "progress": 0.0,
                "started_at": datetime.utcnow(),
                "error": None
            }
            
            # Record download start in database
            download_record = ModelDownload(
                model_name=model_name,
                status="downloading",
                progress_percent=0.0
            )
            
            # Start download (this is a blocking operation)
            logger.info(f"Starting download of {model_name}")
            self.download_progress[model_name]["status"] = "downloading"
            
            # Use Ollama to pull the model
            await asyncio.to_thread(ollama.pull, model_name)
            
            # Update progress
            self.download_progress[model_name].update({
                "status": "completed",
                "progress": 100.0,
                "completed_at": datetime.utcnow()
            })
            
            # Record successful installation
            await self._record_installed_model(model_name)
            
            logger.info(f"Successfully downloaded {model_name}")
            return f"Model {model_name} downloaded successfully"
            
        except Exception as e:
            error_msg = f"Failed to download {model_name}: {str(e)}"
            logger.error(error_msg)
            
            self.download_progress[model_name].update({
                "status": "failed",
                "error": str(e)
            })
            
            return error_msg
    
    async def _record_installed_model(self, model_name: str):
        """Record a newly installed model in the database"""
        
        spec = self.model_catalog.get(model_name)
        chip_type, _ = self.detector.detect_apple_silicon()
        
        installed_model = InstalledModel(
            name=model_name,
            display_name=spec.display_name if spec else model_name,
            size_gb=spec.base_size_gb if spec else 0.0,
            quantization=self._detect_quantization(model_name),
            chip_type=chip_type.value if chip_type else "unknown",
            optimized_for_chip=spec.apple_silicon_optimized if spec else False
        )
        
        # Would need database session to actually save
        logger.info(f"Recorded installation of {model_name}")
    
    def _detect_quantization(self, model_name: str) -> str:
        """Detect quantization type from model name"""
        if "q4_0" in model_name.lower():
            return "q4_0"
        elif "q8_0" in model_name.lower():
            return "q8_0"
        elif "q4_k_m" in model_name.lower():
            return "q4_k_m"
        elif "q2_k" in model_name.lower():
            return "q2_k"
        else:
            return "f16"
    
    async def _get_installed_models(self) -> List[Dict[str, Any]]:
        """Get list of currently installed models"""
        try:
            result = ollama.list()
            models = []
            
            for model in result.get('models', []):
                model_info = {
                    "name": model['name'],
                    "size": model.get('size', 0),
                    "modified": model.get('modified', ''),
                    "digest": model.get('digest', ''),
                    "details": model.get('details', {})
                }
                models.append(model_info)
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to get installed models: {e}")
            return []
    
    async def benchmark_model(self, model_name: str, quick: bool = False) -> ModelPerformance:
        """Benchmark a model's performance on current system"""
        
        chip_type, specs = self.detector.detect_apple_silicon()
        if not specs:
            raise Exception("Apple Silicon not detected for benchmarking")
        
        logger.info(f"Benchmarking {model_name} on {chip_type.value}")
        
        # Test prompts for benchmarking
        test_prompts = [
            "Write a Python function to calculate fibonacci numbers.",
            "Explain the concept of machine learning in simple terms.",
            "Create a React component for a button with hover effects.",
        ] if quick else [
            "Write a comprehensive Python class for handling user authentication with JWT tokens.",
            "Explain the differences between various sorting algorithms and their time complexities.",
            "Create a React component library with TypeScript for a design system.",
            "Design a database schema for an e-commerce platform with proper relationships.",
            "Write a detailed technical specification for a microservices architecture.",
            "Create unit tests for a REST API using pytest with proper mocking.",
            "Analyze the trade-offs between different state management solutions in React.",
            "Write a deployment script for a web application using Docker and Kubernetes."
        ]
        
        # Performance metrics
        total_tokens = 0
        total_time = 0
        memory_usage_samples = []
        cpu_usage_samples = []
        load_times = []
        
        # Initial system state
        initial_performance = await self.monitor.get_system_performance()
        
        for prompt in test_prompts:
            # Measure model load time
            load_start = time.time()
            
            try:
                # Generate response
                start_time = time.time()
                response = await asyncio.to_thread(
                    ollama.generate,
                    model=model_name,
                    prompt=prompt,
                    stream=False
                )
                end_time = time.time()
                
                # Record metrics
                duration = end_time - start_time
                load_time = time.time() - load_start
                tokens = len(response.get('response', '').split())
                
                total_tokens += tokens
                total_time += duration
                load_times.append(load_time)
                
                # System resource usage
                current_memory = psutil.virtual_memory().percent
                current_cpu = psutil.cpu_percent()
                
                memory_usage_samples.append(current_memory)
                cpu_usage_samples.append(current_cpu)
                
            except Exception as e:
                logger.warning(f"Benchmark prompt failed: {e}")
                continue
        
        # Calculate averages
        avg_tokens_per_second = total_tokens / total_time if total_time > 0 else 0
        avg_load_time = sum(load_times) / len(load_times) if load_times else 0
        avg_memory_usage = sum(memory_usage_samples) / len(memory_usage_samples) if memory_usage_samples else 0
        avg_cpu_usage = sum(cpu_usage_samples) / len(cpu_usage_samples) if cpu_usage_samples else 0
        
        # Final system state
        final_performance = await self.monitor.get_system_performance()
        
        # Assess thermal impact
        thermal_impact = "low"
        if final_performance.thermal_state == "throttling":
            thermal_impact = "high"
        elif final_performance.thermal_state == "elevated":
            thermal_impact = "medium"
        
        # Quality assessment (simplified)
        quality_score = min(1.0, avg_tokens_per_second / 20.0)  # Normalize to 0-1
        
        performance = ModelPerformance(
            model_name=model_name,
            chip_type=chip_type,
            memory_gb=specs.unified_memory_gb,
            tokens_per_second=avg_tokens_per_second,
            load_time_seconds=avg_load_time,
            memory_usage_gb=avg_memory_usage / 100 * specs.unified_memory_gb,
            cpu_usage_percent=avg_cpu_usage,
            thermal_impact=thermal_impact,
            quality_score=quality_score,
            benchmark_date=datetime.utcnow()
        )
        
        # Cache the results
        self.performance_cache[model_name] = performance
        
        logger.info(f"Benchmark completed: {model_name} - {avg_tokens_per_second:.1f} tokens/sec")
        
        return performance
    
    async def optimize_model_selection(self, task_complexity: str, current_models: List[str]) -> str:
        """Select optimal model for task complexity from available models"""
        
        if not current_models:
            return "llama2:7b"  # Default fallback
        
        # Model preference by complexity
        complexity_preferences = {
            "simple": ["7b", "neural-chat", "mistral"],
            "medium": ["7b", "13b", "mistral"],
            "complex": ["13b", "34b", "70b"],
            "expert": ["34b", "70b", "13b"]
        }
        
        preferred_sizes = complexity_preferences.get(task_complexity, ["7b", "13b"])
        
        # Score available models
        model_scores = {}
        for model in current_models:
            score = 0
            
            # Size preference
            for i, pref_size in enumerate(preferred_sizes):
                if pref_size in model:
                    score += (len(preferred_sizes) - i) * 10
                    break
            
            # Model type bonuses
            if "codellama" in model.lower():
                score += 5  # Bonus for code tasks
            if "instruct" in model.lower():
                score += 3  # Bonus for instruction following
            if "q4_0" in model.lower():
                score += 2  # Bonus for quantized (faster)
            
            # Performance cache bonus
            if model in self.performance_cache:
                perf = self.performance_cache[model]
                score += perf.tokens_per_second / 10
            
            model_scores[model] = score
        
        # Return highest scoring model
        best_model = max(model_scores.items(), key=lambda x: x[1])[0]
        
        logger.info(f"Selected {best_model} for {task_complexity} task (score: {model_scores[best_model]})")
        
        return best_model
    
    def get_download_progress(self) -> Dict[str, Dict[str, Any]]:
        """Get current download progress for all models"""
        return dict(self.download_progress)
    
    async def cleanup_unused_models(self, days_unused: int = 30) -> List[str]:
        """Remove models that haven't been used in specified days"""
        
        try:
            installed_models = await self._get_installed_models()
            removed_models = []
            
            # This would need database integration to track last_used dates
            # For now, return empty list
            logger.info(f"Cleanup check completed, {len(removed_models)} models removed")
            
            return removed_models
            
        except Exception as e:
            logger.error(f"Model cleanup failed: {e}")
            return []
    
    async def get_model_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all installed models"""
        
        try:
            installed_models = await self._get_installed_models()
            
            stats = {
                "total_models": len(installed_models),
                "total_size_gb": sum(model.get('size', 0) for model in installed_models) / (1024**3),
                "models": [],
                "most_used": None,
                "least_used": None,
                "performance_leader": None
            }
            
            for model in installed_models:
                model_stats = {
                    "name": model['name'],
                    "size_gb": model.get('size', 0) / (1024**3),
                    "usage_count": 0,  # Would come from database
                    "last_used": None,  # Would come from database
                    "avg_performance": self.performance_cache.get(model['name'])
                }
                stats["models"].append(model_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get model usage stats: {e}")
            return {"error": str(e)}
    
    async def suggest_model_upgrades(self, chip_type: ChipType, memory_gb: int) -> List[Dict[str, Any]]:
        """Suggest model upgrades based on system capabilities"""
        
        installed_models = await self._get_installed_models()
        installed_names = {model['name'] for model in installed_models}
        
        suggestions = []
        
        # Check for quantized -> full precision upgrades
        for installed_model in installed_names:
            if "q4_0" in installed_model:
                base_model = installed_model.replace("-q4_0", "")
                if base_model in self.model_catalog and base_model not in installed_names:
                    spec = self.model_catalog[base_model]
                    if memory_gb >= spec.recommended_memory_gb:
                        suggestions.append({
                            "type": "upgrade",
                            "from": installed_model,
                            "to": base_model,
                            "reason": "Upgrade to full precision for better quality",
                            "memory_required": spec.min_memory_gb,
                            "size_increase_gb": spec.base_size_gb - self.model_catalog[installed_model].base_size_gb
                        })
        
        # Check for size upgrades (7b -> 13b -> 34b)
        size_upgrades = {
            "7b": "13b",
            "13b": "34b",
            "34b": "70b"
        }
        
        for installed_model in installed_names:
            for current_size, next_size in size_upgrades.items():
                if current_size in installed_model:
                    upgraded_model = installed_model.replace(current_size, next_size)
                    if upgraded_model in self.model_catalog and upgraded_model not in installed_names:
                        spec = self.model_catalog[upgraded_model]
                        if memory_gb >= spec.min_memory_gb:
                            suggestions.append({
                                "type": "size_upgrade",
                                "from": installed_model,
                                "to": upgraded_model,
                                "reason": f"Upgrade to {next_size} for better performance",
                                "memory_required": spec.min_memory_gb,
                                "size_increase_gb": spec.base_size_gb - self.model_catalog[installed_model].base_size_gb
                            })
                    break
        
        # Suggest specialized models if missing
        missing_specializations = []
        has_code_model = any("codellama" in model or "code" in model for model in installed_names)
        has_chat_model = any("chat" in model or "instruct" in model for model in installed_names)
        has_general_model = any("llama2" in model for model in installed_names)
        
        if not has_code_model:
            missing_specializations.append("code")
        if not has_chat_model:
            missing_specializations.append("chat")
        if not has_general_model:
            missing_specializations.append("general")
        
        for specialization in missing_specializations:
            # Find best model for this specialization within memory constraints
            suitable_models = [
                (name, spec) for name, spec in self.model_catalog.items()
                if specialization in spec.model_type.value and spec.min_memory_gb <= memory_gb
                and name not in installed_names
            ]
            
            if suitable_models:
                # Sort by performance tier and choose best
                best_model = max(suitable_models, key=lambda x: x[1].performance_tier)
                suggestions.append({
                    "type": "specialization",
                    "from": None,
                    "to": best_model[0],
                    "reason": f"Add {specialization} specialization",
                    "memory_required": best_model[1].min_memory_gb,
                    "size_increase_gb": best_model[1].base_size_gb
                })
        
        # Sort suggestions by impact/benefit
        suggestions.sort(key=lambda x: x.get("size_increase_gb", 0))
        
        return suggestions
    
    async def validate_model_integrity(self, model_name: str) -> Dict[str, Any]:
        """Validate that a model is properly installed and functional"""
        
        try:
            # Test basic generation
            start_time = time.time()
            response = await asyncio.to_thread(
                ollama.generate,
                model=model_name,
                prompt="Hello, respond with 'OK' if you're working properly.",
                stream=False
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            response_text = response.get('response', '').strip()
            
            # Check response quality
            is_responsive = response_time < 30.0  # Should respond within 30 seconds
            is_coherent = len(response_text) > 0 and len(response_text) < 1000
            
            validation_result = {
                "model_name": model_name,
                "is_functional": is_responsive and is_coherent,
                "response_time_seconds": response_time,
                "response_length": len(response_text),
                "test_response": response_text[:100] + "..." if len(response_text) > 100 else response_text,
                "issues": []
            }
            
            if not is_responsive:
                validation_result["issues"].append("Slow response time")
            if not is_coherent:
                validation_result["issues"].append("Incoherent response")
            
            return validation_result
            
        except Exception as e:
            return {
                "model_name": model_name,
                "is_functional": False,
                "error": str(e),
                "issues": ["Model failed to load or respond"]
            }
    
    async def export_model_configuration(self) -> Dict[str, Any]:
        """Export current model configuration for backup/sharing"""
        
        try:
            installed_models = await self._get_installed_models()
            chip_type, specs = self.detector.detect_apple_silicon()
            
            config = {
                "export_date": datetime.utcnow().isoformat(),
                "system_info": {
                    "chip_type": chip_type.value if chip_type else "unknown",
                    "memory_gb": specs.unified_memory_gb if specs else 0,
                    "cpu_cores": specs.cpu_cores if specs else 0
                },
                "installed_models": [],
                "performance_data": {},
                "preferences": {
                    "auto_select_optimal": True,
                    "prefer_quantized": True,
                    "max_concurrent_models": 2
                }
            }
            
            for model in installed_models:
                model_config = {
                    "name": model['name'],
                    "size_bytes": model.get('size', 0),
                    "modified": model.get('modified', ''),
                    "digest": model.get('digest', '')
                }
                config["installed_models"].append(model_config)
                
                # Add performance data if available
                if model['name'] in self.performance_cache:
                    perf = self.performance_cache[model['name']]
                    config["performance_data"][model['name']] = {
                        "tokens_per_second": perf.tokens_per_second,
                        "load_time_seconds": perf.load_time_seconds,
                        "memory_usage_gb": perf.memory_usage_gb,
                        "quality_score": perf.quality_score
                    }
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to export model configuration: {e}")
            return {"error": str(e)}
    
    async def import_model_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Import model configuration and suggest installations"""
        
        try:
            current_models = await self._get_installed_models()
            current_names = {model['name'] for model in current_models}
            
            import_plan = {
                "models_to_install": [],
                "models_already_present": [],
                "models_incompatible": [],
                "total_download_size_gb": 0
            }
            
            chip_type, specs = self.detector.detect_apple_silicon()
            current_memory = specs.unified_memory_gb if specs else 8
            
            for model_config in config.get("installed_models", []):
                model_name = model_config["name"]
                
                if model_name in current_names:
                    import_plan["models_already_present"].append(model_name)
                elif model_name in self.model_catalog:
                    spec = self.model_catalog[model_name]
                    if current_memory >= spec.min_memory_gb:
                        import_plan["models_to_install"].append({
                            "name": model_name,
                            "size_gb": spec.base_size_gb,
                            "memory_required": spec.min_memory_gb
                        })
                        import_plan["total_download_size_gb"] += spec.base_size_gb
                    else:
                        import_plan["models_incompatible"].append({
                            "name": model_name,
                            "reason": f"Requires {spec.min_memory_gb}GB, have {current_memory}GB"
                        })
                else:
                    import_plan["models_incompatible"].append({
                        "name": model_name,
                        "reason": "Model not in catalog"
                    })
            
            return import_plan
            
        except Exception as e:
            logger.error(f"Failed to import model configuration: {e}")
            return {"error": str(e)}
    
    async def schedule_model_updates(self) -> Dict[str, Any]:
        """Check for and schedule model updates"""
        
        try:
            installed_models = await self._get_installed_models()
            update_plan = {
                "updates_available": [],
                "no_updates": [],
                "check_date": datetime.utcnow().isoformat()
            }
            
            for model in installed_models:
                model_name = model['name']
                # In a real implementation, this would check for newer versions
                # For now, we'll simulate update availability
                
                # Check if model is outdated (older than 90 days)
                if 'modified' in model:
                    try:
                        modified_date = datetime.fromisoformat(model['modified'].replace('Z', '+00:00'))
                        days_old = (datetime.utcnow() - modified_date.replace(tzinfo=None)).days
                        
                        if days_old > 90:
                            update_plan["updates_available"].append({
                                "name": model_name,
                                "current_version": model.get('digest', 'unknown')[:12],
                                "days_old": days_old,
                                "update_reason": "Model is more than 90 days old"
                            })
                        else:
                            update_plan["no_updates"].append(model_name)
                    except:
                        update_plan["no_updates"].append(model_name)
                else:
                    update_plan["no_updates"].append(model_name)
            
            return update_plan
            
        except Exception as e:
            logger.error(f"Failed to check for model updates: {e}")
            return {"error": str(e)}

class ModelPerformanceTracker:
    """Track and analyze model performance over time"""
    
    def __init__(self):
        self.performance_history = {}
        self.usage_stats = {}
    
    def record_usage(self, model_name: str, task_type: str, duration: float, tokens: int, quality_score: float):
        """Record model usage statistics"""
        
        if model_name not in self.usage_stats:
            self.usage_stats[model_name] = {
                "total_uses": 0,
                "total_duration": 0.0,
                "total_tokens": 0,
                "task_types": {},
                "quality_scores": [],
                "first_used": datetime.utcnow(),
                "last_used": datetime.utcnow()
            }
        
        stats = self.usage_stats[model_name]
        stats["total_uses"] += 1
        stats["total_duration"] += duration
        stats["total_tokens"] += tokens
        stats["quality_scores"].append(quality_score)
        stats["last_used"] = datetime.utcnow()
        
        if task_type not in stats["task_types"]:
            stats["task_types"][task_type] = 0
        stats["task_types"][task_type] += 1
    
    def get_performance_summary(self, model_name: str) -> Dict[str, Any]:
        """Get performance summary for a model"""
        
        if model_name not in self.usage_stats:
            return {"error": "No usage data for this model"}
        
        stats = self.usage_stats[model_name]
        
        return {
            "model_name": model_name,
            "total_uses": stats["total_uses"],
            "avg_tokens_per_second": stats["total_tokens"] / stats["total_duration"] if stats["total_duration"] > 0 else 0,
            "avg_quality_score": sum(stats["quality_scores"]) / len(stats["quality_scores"]) if stats["quality_scores"] else 0,
            "most_common_task": max(stats["task_types"].items(), key=lambda x: x[1])[0] if stats["task_types"] else "unknown",
            "days_since_first_use": (datetime.utcnow() - stats["first_used"]).days,
            "days_since_last_use": (datetime.utcnow() - stats["last_used"]).days
        }
    
    def compare_models(self, model_names: List[str], metric: str = "performance") -> Dict[str, Any]:
        """Compare multiple models on specified metric"""
        
        comparison = {
            "metric": metric,
            "models": [],
            "winner": None,
            "comparison_date": datetime.utcnow().isoformat()
        }
        
        for model_name in model_names:
            if model_name in self.usage_stats:
                summary = self.get_performance_summary(model_name)
                comparison["models"].append(summary)
        
        if comparison["models"]:
            if metric == "performance":
                winner = max(comparison["models"], key=lambda x: x.get("avg_tokens_per_second", 0))
            elif metric == "quality":
                winner = max(comparison["models"], key=lambda x: x.get("avg_quality_score", 0))
            elif metric == "usage":
                winner = max(comparison["models"], key=lambda x: x.get("total_uses", 0))
            else:
                winner = comparison["models"][0]
            
            comparison["winner"] = winner["model_name"]
        
        return comparison

# Utility functions for model management
def format_model_size(size_bytes: int) -> str:
    """Format model size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def estimate_download_time(size_gb: float, speed_mbps: float = 50.0) -> str:
    """Estimate download time for a model"""
    size_mb = size_gb * 1024
    time_minutes = size_mb / (speed_mbps / 8) / 60  # Convert Mbps to MBps then to minutes
    
    if time_minutes < 1:
        return "< 1 minute"
    elif time_minutes < 60:
        return f"{int(time_minutes)} minutes"
    else:
        hours = int(time_minutes // 60)
        minutes = int(time_minutes % 60)
        return f"{hours}h {minutes}m"

def get_model_recommendations_by_use_case(use_case: str) -> List[str]:
    """Get model recommendations for specific use cases"""
    
    recommendations = {
        "coding": ["codellama:7b", "codellama:13b", "codellama:7b-instruct"],
        "writing": ["llama2:7b", "llama2:13b", "neural-chat:7b"],
        "analysis": ["llama2:13b", "llama2:7b", "mistral:7b"],
        "conversation": ["neural-chat:7b", "llama2:7b", "mistral:7b"],
        "research": ["llama2:13b", "llama2:70b", "mistral:7b"],
        "general": ["llama2:7b", "mistral:7b", "neural-chat:7b"]
    }
    
    return recommendations.get(use_case.lower(), recommendations["general"])
