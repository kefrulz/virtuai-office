# VirtuAI Office - Apple Silicon Optimization Module
"""
Apple Silicon optimization package for VirtuAI Office.

This module provides hardware detection, performance optimization,
and intelligent model management for Apple Silicon Macs (M1/M2/M3).

Key Components:
- AppleSiliconDetector: Hardware detection and specification analysis
- AppleSiliconOptimizer: System optimization and configuration
- AppleSiliconMonitor: Real-time performance monitoring
- AppleSiliconModelManager: Intelligent model selection and management
"""

from .detector import AppleSiliconDetector, ChipType, AppleSiliconSpecs
from .optimizer import AppleSiliconOptimizer, OptimizationLevel
from .monitor import AppleSiliconMonitor, SystemPerformance
from .models import AppleSiliconModelManager
from .dashboard import AppleSiliconDashboard
from .agent_manager import AppleSiliconAgentManager

__version__ = "1.0.0"
__author__ = "VirtuAI Office Team"

# Export main classes
__all__ = [
    # Core classes
    "AppleSiliconDetector",
    "AppleSiliconOptimizer",
    "AppleSiliconMonitor",
    "AppleSiliconModelManager",
    "AppleSiliconDashboard",
    "AppleSiliconAgentManager",
    
    # Data classes and enums
    "ChipType",
    "AppleSiliconSpecs",
    "SystemPerformance",
    "OptimizationLevel",
]

# Module initialization
def initialize_apple_silicon():
    """Initialize Apple Silicon optimization system."""
    detector = AppleSiliconDetector()
    chip_type, specs = detector.detect_apple_silicon()
    
    if chip_type != ChipType.INTEL and specs:
        print(f"🍎 Apple Silicon detected: {chip_type.value}")
        print(f"   Memory: {specs.unified_memory_gb}GB unified memory")
        print(f"   CPU: {specs.cpu_cores} cores")
        print(f"   GPU: {specs.gpu_cores} cores")
        return True
    
    return False

# Auto-detect on import
APPLE_SILICON_AVAILABLE = initialize_apple_silicon()
