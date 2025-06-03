# Apple Silicon Hardware Detection Module
import subprocess
import platform
import psutil
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

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
    
    def detect_apple_silicon(self) -> Tuple[ChipType, Optional[AppleSiliconSpecs]]:
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
    
    def get_system_info(self) -> Dict[str, any]:
        """Get comprehensive system information"""
        chip_type, specs = self.detect_apple_silicon()
        
        system_info = {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "chip_type": chip_type.value,
            "is_apple_silicon": chip_type not in [ChipType.INTEL, ChipType.UNKNOWN],
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total // (1024 * 1024 * 1024),
            "specifications": None
        }
        
        if specs:
            system_info["specifications"] = {
                "unified_memory_gb": specs.unified_memory_gb,
                "cpu_cores": specs.cpu_cores,
                "gpu_cores": specs.gpu_cores,
                "neural_engine": specs.neural_engine,
                "memory_bandwidth_gbps": specs.memory_bandwidth_gbps,
                "max_power_watts": specs.max_power_watts,
                "optimal_models": specs.optimal_models,
                "max_concurrent_agents": specs.max_concurrent_agents
            }
        
        return system_info
    
    def get_performance_profile(self) -> Dict[str, str]:
        """Get performance profile based on detected hardware"""
        chip_type, specs = self.detect_apple_silicon()
        
        if not specs:
            return {
                "profile": "standard",
                "description": "Standard performance profile",
                "recommendations": ["Use smaller models", "Limit concurrent tasks"]
            }
        
        memory_gb = specs.unified_memory_gb
        
        if memory_gb >= 32:
            return {
                "profile": "high_performance",
                "description": "High-performance Apple Silicon configuration",
                "recommendations": [
                    "Use large models (13B+) for best quality",
                    "Enable multiple concurrent agents",
                    "Consider 70B models for complex tasks"
                ]
            }
        elif memory_gb >= 16:
            return {
                "profile": "balanced",
                "description": "Balanced performance and efficiency",
                "recommendations": [
                    "Use 7B-13B models for optimal balance",
                    "Moderate concurrent task limit",
                    "Enable Apple Silicon optimizations"
                ]
            }
        else:
            return {
                "profile": "efficient",
                "description": "Optimized for efficiency",
                "recommendations": [
                    "Use quantized models (q4_0) for speed",
                    "Limit to 2-3 concurrent agents",
                    "Monitor memory pressure"
                ]
            }
    
    def is_optimization_available(self) -> bool:
        """Check if Apple Silicon optimizations are available"""
        chip_type, _ = self.detect_apple_silicon()
        return chip_type not in [ChipType.INTEL, ChipType.UNKNOWN]
    
    def get_thermal_headroom(self) -> Optional[str]:
        """Get thermal performance headroom (macOS only)"""
        if platform.system() != "Darwin":
            return None
        
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
