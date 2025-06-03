# Apple Silicon Performance Monitor
# Real-time system performance monitoring for M1/M2/M3 Macs

import asyncio
import subprocess
import psutil
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

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
    timestamp: datetime

class AppleSiliconMonitor:
    def __init__(self):
        self.baseline_metrics = None
        self.monitoring_active = False
        self.performance_history = []
        self.max_history_length = 1000
    
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
        
        performance = SystemPerformance(
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            memory_pressure=memory_pressure,
            thermal_state=thermal_state,
            power_mode=power_mode,
            battery_level=battery_level,
            inference_speed=inference_speed,
            model_load_time=model_load_time,
            timestamp=datetime.utcnow()
        )
        
        # Store in history
        self._add_to_history(performance)
        
        return performance
    
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
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to psutil-based estimation
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return "critical"
            elif memory.percent > 75:
                return "warning"
            else:
                return "normal"
    
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
            elif "thermal_state" in output:
                # Parse thermal state number
                lines = output.split('\n')
                for line in lines:
                    if "thermal_state" in line and "0" not in line:
                        return "elevated"
                return "normal"
            else:
                return "normal"
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to CPU frequency monitoring
            try:
                cpu_freq = psutil.cpu_freq()
                if cpu_freq and cpu_freq.current < cpu_freq.max * 0.8:
                    return "throttling"
                else:
                    return "normal"
            except:
                return "unknown"
    
    async def _get_power_mode(self) -> str:
        """Get current power mode"""
        try:
            result = subprocess.run(
                ["pmset", "-g", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            if "battery power" in output:
                return "battery"
            elif "ac power" in output:
                return "ac_power"
            else:
                return "unknown"
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to battery status
            battery = psutil.sensors_battery()
            if battery:
                return "battery" if not battery.power_plugged else "ac_power"
            return "unknown"
    
    async def _get_battery_level(self) -> Optional[float]:
        """Get battery level if on laptop"""
        try:
            battery = psutil.sensors_battery()
            return battery.percent if battery else None
        except:
            return None
    
    async def _measure_inference_speed(self) -> float:
        """Measure current AI inference speed"""
        try:
            # Import ollama here to avoid import issues if not installed
            import ollama
            
            start_time = time.time()
            
            # Simple inference test with short prompt
            test_response = await asyncio.to_thread(
                ollama.generate,
                model="llama2:7b",
                prompt="Hello",
                stream=False
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Estimate tokens per second (rough approximation)
            response_length = len(test_response.get('response', '').split())
            tokens_per_second = response_length / duration if duration > 0 else 0
            
            return max(0, tokens_per_second)
            
        except Exception as e:
            logger.debug(f"Inference speed measurement failed: {e}")
            return 0.0
    
    async def _measure_model_load_time(self) -> float:
        """Measure model loading time"""
        try:
            import ollama
            
            start_time = time.time()
            
            # Test model availability (lightweight operation)
            models = ollama.list()
            
            end_time = time.time()
            return max(0, end_time - start_time)
            
        except Exception as e:
            logger.debug(f"Model load time measurement failed: {e}")
            return 0.0
    
    def _add_to_history(self, performance: SystemPerformance):
        """Add performance data to history"""
        self.performance_history.append(performance)
        
        # Keep history size manageable
        if len(self.performance_history) > self.max_history_length:
            self.performance_history = self.performance_history[-self.max_history_length:]
    
    def get_performance_history(self, hours: int = 24) -> list:
        """Get performance history for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            p for p in self.performance_history
            if p.timestamp >= cutoff_time
        ]
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary statistics"""
        history = self.get_performance_history(hours)
        
        if not history:
            return {
                "period_hours": hours,
                "data_points": 0,
                "avg_cpu_usage": 0,
                "avg_memory_usage": 0,
                "avg_inference_speed": 0,
                "thermal_issues": 0,
                "memory_pressure_events": 0
            }
        
        # Calculate averages
        avg_cpu = sum(p.cpu_usage for p in history) / len(history)
        avg_memory = sum(p.memory_usage for p in history) / len(history)
        avg_inference = sum(p.inference_speed for p in history if p.inference_speed > 0)
        avg_inference = avg_inference / len([p for p in history if p.inference_speed > 0]) if avg_inference else 0
        
        # Count issues
        thermal_issues = len([p for p in history if p.thermal_state in ["throttling", "elevated"]])
        memory_pressure_events = len([p for p in history if p.memory_pressure in ["warning", "critical"]])
        
        return {
            "period_hours": hours,
            "data_points": len(history),
            "avg_cpu_usage": round(avg_cpu, 2),
            "avg_memory_usage": round(avg_memory, 2),
            "avg_inference_speed": round(avg_inference, 2),
            "thermal_issues": thermal_issues,
            "memory_pressure_events": memory_pressure_events,
            "performance_score": self._calculate_performance_score(history)
        }
    
    def _calculate_performance_score(self, history: list) -> float:
        """Calculate overall performance score (0-100)"""
        if not history:
            return 0.0
        
        score = 100.0
        
        # CPU usage penalty
        avg_cpu = sum(p.cpu_usage for p in history) / len(history)
        if avg_cpu > 80:
            score -= 20
        elif avg_cpu > 60:
            score -= 10
        
        # Memory usage penalty
        avg_memory = sum(p.memory_usage for p in history) / len(history)
        if avg_memory > 85:
            score -= 15
        elif avg_memory > 70:
            score -= 8
        
        # Thermal issues penalty
        thermal_issues = len([p for p in history if p.thermal_state == "throttling"])
        score -= min(thermal_issues * 5, 25)
        
        # Memory pressure penalty
        pressure_events = len([p for p in history if p.memory_pressure == "critical"])
        score -= min(pressure_events * 3, 20)
        
        # Inference speed bonus
        avg_inference = sum(p.inference_speed for p in history if p.inference_speed > 0)
        if avg_inference:
            avg_inference = avg_inference / len([p for p in history if p.inference_speed > 0])
            if avg_inference > 15:
                score += 10
            elif avg_inference > 8:
                score += 5
        
        return max(0.0, min(100.0, score))
    
    async def start_continuous_monitoring(self, interval_seconds: int = 60):
        """Start continuous performance monitoring"""
        self.monitoring_active = True
        logger.info(f"Starting continuous Apple Silicon monitoring (interval: {interval_seconds}s)")
        
        while self.monitoring_active:
            try:
                await self.get_system_performance()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval_seconds)
        
        logger.info("Apple Silicon monitoring stopped")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current system status summary"""
        if not self.performance_history:
            return {"status": "no_data", "message": "No performance data available"}
        
        latest = self.performance_history[-1]
        
        # Determine overall status
        status = "optimal"
        issues = []
        
        if latest.thermal_state == "throttling":
            status = "warning"
            issues.append("Thermal throttling detected")
        elif latest.thermal_state == "elevated":
            if status == "optimal":
                status = "caution"
            issues.append("Elevated temperature")
        
        if latest.memory_pressure == "critical":
            status = "warning"
            issues.append("Critical memory pressure")
        elif latest.memory_pressure == "warning":
            if status == "optimal":
                status = "caution"
            issues.append("Memory pressure warning")
        
        if latest.cpu_usage > 90:
            status = "warning"
            issues.append("High CPU usage")
        elif latest.cpu_usage > 75:
            if status == "optimal":
                status = "caution"
            issues.append("Elevated CPU usage")
        
        return {
            "status": status,
            "timestamp": latest.timestamp.isoformat(),
            "cpu_usage": latest.cpu_usage,
            "memory_usage": latest.memory_usage,
            "memory_pressure": latest.memory_pressure,
            "thermal_state": latest.thermal_state,
            "power_mode": latest.power_mode,
            "battery_level": latest.battery_level,
            "inference_speed": latest.inference_speed,
            "issues": issues,
            "recommendations": self._get_recommendations(latest, issues)
        }
    
    def _get_recommendations(self, performance: SystemPerformance, issues: list) -> list:
        """Get performance optimization recommendations"""
        recommendations = []
        
        if performance.thermal_state == "throttling":
            recommendations.append("Reduce CPU-intensive tasks to prevent thermal throttling")
            recommendations.append("Ensure adequate ventilation and cooling")
        
        if performance.memory_pressure in ["critical", "warning"]:
            recommendations.append("Close unnecessary applications to free memory")
            recommendations.append("Consider using smaller AI models")
        
        if performance.cpu_usage > 80:
            recommendations.append("Limit concurrent AI tasks to reduce CPU load")
        
        if performance.power_mode == "battery" and performance.battery_level and performance.battery_level < 20:
            recommendations.append("Connect to power for optimal AI performance")
        
        if performance.inference_speed < 5:
            recommendations.append("AI inference speed is low - check system resources")
        
        if not issues:
            recommendations.append("System is performing optimally for AI workloads")
        
        return recommendations
    
    def export_performance_data(self, hours: int = 24) -> Dict[str, Any]:
        """Export performance data for analysis"""
        history = self.get_performance_history(hours)
        
        return {
            "export_timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "data_points": len(history),
            "summary": self.get_performance_summary(hours),
            "raw_data": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "cpu_usage": p.cpu_usage,
                    "memory_usage": p.memory_usage,
                    "memory_pressure": p.memory_pressure,
                    "thermal_state": p.thermal_state,
                    "power_mode": p.power_mode,
                    "battery_level": p.battery_level,
                    "inference_speed": p.inference_speed,
                    "model_load_time": p.model_load_time
                }
                for p in history
            ]
        }
