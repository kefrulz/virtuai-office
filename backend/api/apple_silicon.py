# backend/api/apple_silicon.py
# Apple Silicon optimization API endpoints

import asyncio
import json
import subprocess
import platform
import psutil
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import ollama
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ..models.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/apple-silicon", tags=["Apple Silicon"])

# Apple Silicon Detection and Optimization Classes
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
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

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
    inference_speed: float
    model_load_time: float

# Apple Silicon Hardware Detection
class AppleSiliconDetector:
    def __init__(self):
        self.specs_database = self._load_chip_specifications()
    
    def _load_chip_specifications(self) -> Dict[ChipType, AppleSiliconSpecs]:
        """Database of Apple Silicon chip specifications"""
        return {
            ChipType.M1: AppleSiliconSpecs(
                chip_type=ChipType.M1,
                unified_memory_gb=8,
                cpu_cores=8,
                gpu_cores=7,
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
    
    def detect_apple_silicon(self) -> Tuple[ChipType, Optional[AppleSiliconSpecs]]:
        """Detect Apple Silicon chip type and return specifications"""
        
        if platform.system() != "Darwin":
            return ChipType.INTEL, None
        
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                check=True
            )
            
            cpu_brand = result.stdout.strip()
            
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
            
            base_specs = self.specs_database.get(chip_type)
            if not base_specs:
                return ChipType.UNKNOWN, None
            
            actual_memory_gb = self._get_actual_memory_gb()
            
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
        memory_factor = memory_gb / 8
        return max(1, int(base_agents * memory_factor * 0.8))

# Apple Silicon Performance Monitor
class AppleSiliconMonitor:
    def __init__(self):
        self.baseline_metrics = None
        self.monitoring_active = False
    
    async def get_system_performance(self) -> SystemPerformance:
        """Get current system performance metrics"""
        
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        memory_pressure = await self._get_memory_pressure()
        thermal_state = await self._get_thermal_state()
        power_mode = await self._get_power_mode()
        battery_level = await self._get_battery_level()
        
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
            start_time = time.time()
            
            test_response = await asyncio.to_thread(
                ollama.generate,
                model="llama2:7b",
                prompt="Hello, how are you?",
                stream=False
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            response_length = len(test_response.get('response', '').split())
            tokens_per_second = response_length / duration if duration > 0 else 0
            
            return tokens_per_second
            
        except Exception as e:
            logger.warning(f"Inference speed measurement failed: {e}")
            return 0.0
    
    async def _measure_model_load_time(self) -> float:
        """Measure model loading time"""
        try:
            start_time = time.time()
            ollama.list()
            end_time = time.time()
            return end_time - start_time
            
        except Exception as e:
            logger.warning(f"Model load time measurement failed: {e}")
            return 0.0

# Initialize global instances
detector = AppleSiliconDetector()
monitor = AppleSiliconMonitor()

# API Endpoints
@router.get("/detect")
async def detect_apple_silicon():
    """Detect Apple Silicon chip and return specifications"""
    chip_type, specs = detector.detect_apple_silicon()
    
    if chip_type == ChipType.INTEL:
        return {
            "is_apple_silicon": False,
            "chip_type": "intel",
            "message": "Intel Mac detected - Apple Silicon optimizations not available"
        }
    
    if not specs:
        return {
            "is_apple_silicon": False,
            "chip_type": "unknown",
            "message": "Unable to detect chip specifications"
        }
    
    return {
        "is_apple_silicon": True,
        "chip_type": chip_type.value,
        "specifications": {
            "unified_memory_gb": specs.unified_memory_gb,
            "cpu_cores": specs.cpu_cores,
            "gpu_cores": specs.gpu_cores,
            "neural_engine": specs.neural_engine,
            "memory_bandwidth_gbps": specs.memory_bandwidth_gbps,
            "max_power_watts": specs.max_power_watts,
            "optimal_models": specs.optimal_models,
            "max_concurrent_agents": specs.max_concurrent_agents
        }
    }

@router.post("/optimize")
async def optimize_for_apple_silicon(
    optimization_level: OptimizationLevel = OptimizationLevel.BALANCED
):
    """Apply Apple Silicon optimizations"""
    
    chip_type, specs = detector.detect_apple_silicon()
    
    if chip_type == ChipType.INTEL:
        raise HTTPException(status_code=400, detail="Apple Silicon not detected")
    
    if not specs:
        raise HTTPException(status_code=400, detail="Unable to detect chip specifications")
    
    try:
        # Apply optimizations
        await _apply_ollama_optimizations(specs)
        
        return {
            "optimized": True,
            "chip_type": chip_type.value,
            "memory_gb": specs.unified_memory_gb,
            "optimization_level": optimization_level.value,
            "preferred_models": specs.optimal_models,
            "max_concurrent_tasks": specs.max_concurrent_agents,
            "message": "Apple Silicon optimizations applied successfully"
        }
        
    except Exception as e:
        logger.error(f"Apple Silicon optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.get("/performance")
async def get_apple_silicon_performance():
    """Get current Apple Silicon performance metrics"""
    
    chip_type, specs = detector.detect_apple_silicon()
    
    if chip_type == ChipType.INTEL:
        raise HTTPException(status_code=400, detail="Apple Silicon not detected")
    
    try:
        performance = await monitor.get_system_performance()
        
        return {
            "chip_type": chip_type.value,
            "performance": {
                "cpu_usage": performance.cpu_usage,
                "memory_usage": performance.memory_usage,
                "memory_pressure": performance.memory_pressure,
                "thermal_state": performance.thermal_state,
                "power_mode": performance.power_mode,
                "battery_level": performance.battery_level,
                "inference_speed": performance.inference_speed,
                "model_load_time": performance.model_load_time
            },
            "status": {
                "optimal": performance.memory_pressure == "normal" and performance.thermal_state == "normal",
                "warning": performance.memory_pressure == "warning" or performance.thermal_state == "elevated",
                "critical": performance.memory_pressure == "critical" or performance.thermal_state == "throttling"
            }
        }
        
    except Exception as e:
        logger.error(f"Performance monitoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance monitoring failed: {str(e)}")

@router.get("/models/recommend")
async def recommend_models_for_apple_silicon():
    """Get model recommendations for current Apple Silicon system"""
    
    chip_type, specs = detector.detect_apple_silicon()
    
    if not specs:
        raise HTTPException(status_code=400, detail="Apple Silicon not detected")
    
    try:
        # Get currently installed models
        installed_models = ollama.list()
        installed_names = [model['name'] for model in installed_models.get('models', [])]
    except:
        installed_names = []
    
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
    
    recommendations = {
        "chip_type": chip_type.value,
        "memory_gb": specs.unified_memory_gb,
        "recommended_models": [],
        "optional_models": [],
        "not_recommended": [],
        "currently_installed": installed_names
    }
    
    for model in all_models:
        if model["size_gb"] <= specs.unified_memory_gb * 0.4:
            if model["name"] in specs.optimal_models:
                recommendations["recommended_models"].append(model)
            else:
                recommendations["optional_models"].append(model)
        else:
            recommendations["not_recommended"].append(model)
    
    return recommendations

@router.post("/models/download")
async def download_recommended_models(background_tasks: BackgroundTasks):
    """Download recommended models for Apple Silicon"""
    
    chip_type, specs = detector.detect_apple_silicon()
    
    if not specs:
        raise HTTPException(status_code=400, detail="Apple Silicon not detected")
    
    try:
        # Get currently installed models
        installed_models = ollama.list()
        installed_names = [model['name'] for model in installed_models.get('models', [])]
        
        download_status = {}
        
        for model_name in specs.optimal_models:
            if model_name not in installed_names:
                background_tasks.add_task(_download_model, model_name)
                download_status[model_name] = "downloading"
            else:
                download_status[model_name] = "already_installed"
        
        return {
            "download_initiated": True,
            "models": download_status,
            "message": "Model downloads started in background"
        }
        
    except Exception as e:
        logger.error(f"Model download failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model download failed: {str(e)}")

@router.post("/benchmark")
async def run_apple_silicon_benchmark():
    """Run comprehensive Apple Silicon performance benchmark"""
    
    chip_type, specs = detector.detect_apple_silicon()
    
    if not specs:
        raise HTTPException(status_code=400, detail="Apple Silicon not detected")
    
    try:
        benchmark_results = {
            "chip_type": chip_type.value,
            "memory_gb": specs.unified_memory_gb,
            "cpu_cores": specs.cpu_cores,
            "gpu_cores": specs.gpu_cores,
            "benchmarks": {}
        }
        
        # Test top 2 models
        for model in specs.optimal_models[:2]:
            try:
                model_results = await _benchmark_model(model)
                benchmark_results["benchmarks"][model] = model_results
            except Exception as e:
                logger.warning(f"Benchmark failed for model {model}: {e}")
                benchmark_results["benchmarks"][model] = {"error": str(e)}
        
        return {
            "benchmark_completed": True,
            "results": benchmark_results,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Benchmark completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")

@router.get("/dashboard")
async def get_apple_silicon_dashboard():
    """Get comprehensive Apple Silicon optimization dashboard"""
    
    chip_type, specs = detector.detect_apple_silicon()
    current_performance = await monitor.get_system_performance()
    
    optimization_score = await _calculate_optimization_score(current_performance, specs)
    
    dashboard_data = {
        "system_info": {
            "chip_type": chip_type.value if chip_type else "unknown",
            "is_apple_silicon": chip_type != ChipType.INTEL,
            "memory_gb": specs.unified_memory_gb if specs else 0,
            "cpu_cores": specs.cpu_cores if specs else 0,
            "gpu_cores": specs.gpu_cores if specs else 0,
            "neural_engine": specs.neural_engine if specs else False
        },
        "current_performance": {
            "cpu_usage": current_performance.cpu_usage,
            "memory_usage": current_performance.memory_usage,
            "memory_pressure": current_performance.memory_pressure,
            "thermal_state": current_performance.thermal_state,
            "power_mode": current_performance.power_mode,
            "battery_level": current_performance.battery_level,
            "inference_speed": current_performance.inference_speed,
            "model_load_time": current_performance.model_load_time
        },
        "optimization": {
            "score": optimization_score,
            "level": _get_optimization_level(),
            "recommendations": await _get_optimization_recommendations(current_performance, specs)
        }
    }
    
    return dashboard_data

# Helper functions
async def _apply_ollama_optimizations(specs: AppleSiliconSpecs):
    """Configure Ollama for optimal Apple Silicon performance"""
    optimal_threads = max(1, specs.cpu_cores - 2)
    os.environ["OLLAMA_NUM_THREADS"] = str(optimal_threads)
    
    memory_gb = specs.unified_memory_gb
    if memory_gb >= 32:
        os.environ["OLLAMA_MAX_LOADED_MODELS"] = "3"
    elif memory_gb >= 16:
        os.environ["OLLAMA_MAX_LOADED_MODELS"] = "2"
    else:
        os.environ["OLLAMA_MAX_LOADED_MODELS"] = "1"
    
    os.environ["OLLAMA_METAL"] = "1"
    
    logger.info(f"✅ Ollama optimized for {specs.chip_type.value} with {optimal_threads} threads")

async def _download_model(model_name: str):
    """Download a specific model"""
    try:
        logger.info(f"Starting download of {model_name}...")
        ollama.pull(model_name)
        logger.info(f"✅ {model_name} downloaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to download {model_name}: {e}")

async def _benchmark_model(model: str) -> Dict[str, float]:
    """Benchmark specific model performance"""
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
        "cpu_usage": avg_cpu_usage,
        "memory_usage": avg_memory_usage,
        "test_prompts": len(test_prompts)
    }

async def _calculate_optimization_score(performance: SystemPerformance, specs: Optional[AppleSiliconSpecs]) -> float:
    """Calculate overall optimization score (0-100)"""
    if not specs:
        return 0.0
    
    score = 100.0
    
    if performance.cpu_usage > 80:
        score -= 20
    elif performance.cpu_usage > 60:
        score -= 10
    
    if performance.memory_pressure == "critical":
        score -= 30
    elif performance.memory_pressure == "warning":
        score -= 15
    
    if performance.thermal_state == "throttling":
        score -= 25
    elif performance.thermal_state == "elevated":
        score -= 10
    
    if performance.inference_speed > 20:
        score += 10
    elif performance.inference_speed > 10:
        score += 5
    
    if performance.model_load_time < 2.0:
        score += 5
    
    return max(0.0, min(100.0, score))

def _get_optimization_level() -> str:
    """Get current optimization level"""
    if os.getenv("OLLAMA_NUM_THREADS") and os.getenv("OLLAMA_METAL") == "1":
        return "optimized"
    else:
        return "default"

async def _get_optimization_recommendations(performance: SystemPerformance, specs: Optional[AppleSiliconSpecs]) -> List[str]:
    """Get optimization recommendations"""
    recommendations = []
    
    if not specs:
        recommendations.append("Apple Silicon not detected - optimization unavailable")
        return recommendations
    
    if performance.memory_pressure == "critical":
        recommendations.append("🔴 Critical memory pressure - close unnecessary applications")
        recommendations.append("Consider using smaller AI models")
    
    if performance.thermal_state == "throttling":
        recommendations.append("🌡️ Thermal throttling detected - reduce workload or improve cooling")
    
    if performance.cpu_usage > 90:
        recommendations.append("📊 High CPU usage - limit concurrent AI tasks")
    
    if performance.inference_speed < 5:
        recommendations.append("⚡ Low inference speed - check model optimization")
    
    if os.getenv("OLLAMA_METAL") != "1":
        recommendations.append("🖥️ Enable Metal GPU acceleration for better performance")
    
    if not recommendations:
        recommendations.append("✅ System is well optimized for AI workloads")
    
    return recommendations
