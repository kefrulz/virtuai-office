# VirtuAI Office - Apple Silicon Dashboard
# Real-time performance monitoring and optimization dashboard for Apple Silicon Macs

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .detector import AppleSiliconDetector, ChipType
from .monitor import AppleSiliconMonitor, SystemPerformance
from .optimizer import AppleSiliconOptimizer
from ..models.database import PerformanceMetric, AppleSiliconProfile, Task, Agent

logger = logging.getLogger(__name__)

@dataclass
class DashboardMetrics:
    system_info: Dict[str, Any]
    current_performance: Dict[str, Any]
    optimization_status: Dict[str, Any]
    performance_history: List[Dict[str, Any]]
    model_performance: Dict[str, Any]
    agent_utilization: Dict[str, Any]
    recommendations: List[str]
    benchmark_results: Optional[Dict[str, Any]] = None

class AppleSiliconDashboard:
    def __init__(self, detector: AppleSiliconDetector, monitor: AppleSiliconMonitor, optimizer: AppleSiliconOptimizer):
        self.detector = detector
        self.monitor = monitor
        self.optimizer = optimizer
        self.performance_cache = {}
        self.cache_ttl = 30  # seconds
    
    async def get_dashboard_data(self, db: Session, include_history_hours: int = 24) -> DashboardMetrics:
        """Get comprehensive dashboard data for Apple Silicon optimization"""
        
        try:
            # Detect system capabilities
            chip_type, specs = self.detector.detect_apple_silicon()
            
            if chip_type == ChipType.INTEL:
                raise HTTPException(status_code=400, detail="Apple Silicon not detected")
            
            # Get current performance (with caching)
            current_performance = await self._get_cached_performance()
            
            # Get system information
            system_info = await self._get_system_info(chip_type, specs)
            
            # Get optimization status
            optimization_status = await self._get_optimization_status(db, current_performance, specs)
            
            # Get performance history
            performance_history = await self._get_performance_history(db, include_history_hours)
            
            # Get model performance statistics
            model_performance = await self._get_model_performance_stats(db)
            
            # Get agent utilization data
            agent_utilization = await self._get_agent_utilization(db)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(current_performance, specs, db)
            
            # Get benchmark results if available
            benchmark_results = await self._get_latest_benchmark_results(db)
            
            return DashboardMetrics(
                system_info=system_info,
                current_performance=current_performance,
                optimization_status=optimization_status,
                performance_history=performance_history,
                model_performance=model_performance,
                agent_utilization=agent_utilization,
                recommendations=recommendations,
                benchmark_results=benchmark_results
            )
            
        except Exception as e:
            logger.error(f"Dashboard data generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")
    
    async def _get_cached_performance(self) -> Dict[str, Any]:
        """Get current performance with caching to avoid frequent system calls"""
        
        cache_key = "current_performance"
        current_time = time.time()
        
        # Check if we have cached data that's still valid
        if cache_key in self.performance_cache:
            cached_data, timestamp = self.performance_cache[cache_key]
            if current_time - timestamp < self.cache_ttl:
                return cached_data
        
        # Get fresh performance data
        performance = await self.monitor.get_system_performance()
        performance_dict = {
            "cpu_usage": performance.cpu_usage,
            "memory_usage": performance.memory_usage,
            "memory_pressure": performance.memory_pressure,
            "thermal_state": performance.thermal_state,
            "power_mode": performance.power_mode,
            "battery_level": performance.battery_level,
            "inference_speed": performance.inference_speed,
            "model_load_time": performance.model_load_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache the data
        self.performance_cache[cache_key] = (performance_dict, current_time)
        
        return performance_dict
    
    async def _get_system_info(self, chip_type: ChipType, specs) -> Dict[str, Any]:
        """Get system information and capabilities"""
        
        if not specs:
            return {
                "chip_type": "unknown",
                "is_apple_silicon": False,
                "error": "Unable to detect Apple Silicon specifications"
            }
        
        return {
            "chip_type": chip_type.value,
            "is_apple_silicon": True,
            "chip_name": self._get_chip_friendly_name(chip_type),
            "memory_gb": specs.unified_memory_gb,
            "cpu_cores": specs.cpu_cores,
            "gpu_cores": specs.gpu_cores,
            "neural_engine": specs.neural_engine,
            "memory_bandwidth_gbps": specs.memory_bandwidth_gbps,
            "max_power_watts": specs.max_power_watts,
            "optimal_models": specs.optimal_models,
            "max_concurrent_agents": specs.max_concurrent_agents,
            "performance_tier": self._get_performance_tier(chip_type, specs.unified_memory_gb)
        }
    
    def _get_chip_friendly_name(self, chip_type: ChipType) -> str:
        """Get user-friendly chip name"""
        name_map = {
            ChipType.M1: "Apple M1",
            ChipType.M1_PRO: "Apple M1 Pro",
            ChipType.M1_MAX: "Apple M1 Max",
            ChipType.M1_ULTRA: "Apple M1 Ultra",
            ChipType.M2: "Apple M2",
            ChipType.M2_PRO: "Apple M2 Pro",
            ChipType.M2_MAX: "Apple M2 Max",
            ChipType.M2_ULTRA: "Apple M2 Ultra",
            ChipType.M3: "Apple M3",
            ChipType.M3_PRO: "Apple M3 Pro",
            ChipType.M3_MAX: "Apple M3 Max",
        }
        return name_map.get(chip_type, chip_type.value.upper())
    
    def _get_performance_tier(self, chip_type: ChipType, memory_gb: int) -> str:
        """Determine performance tier for the system"""
        if chip_type in [ChipType.M1_ULTRA, ChipType.M2_ULTRA] or memory_gb >= 64:
            return "Desktop Class"
        elif chip_type in [ChipType.M1_MAX, ChipType.M2_MAX, ChipType.M3_MAX] or memory_gb >= 32:
            return "Professional"
        elif chip_type in [ChipType.M1_PRO, ChipType.M2_PRO, ChipType.M3_PRO] or memory_gb >= 16:
            return "Advanced"
        else:
            return "Standard"
    
    async def _get_optimization_status(self, db: Session, performance: Dict[str, Any], specs) -> Dict[str, Any]:
        """Get current optimization status and score"""
        
        # Get optimization profile
        profile = db.query(AppleSiliconProfile).filter(
            AppleSiliconProfile.chip_type == specs.chip_type.value,
            AppleSiliconProfile.memory_gb == specs.unified_memory_gb
        ).first()
        
        # Calculate optimization score
        optimization_score = await self._calculate_optimization_score(performance, specs)
        
        # Get optimization level
        optimization_level = await self._get_optimization_level()
        
        # Get last optimization time
        last_optimized = None
        if profile:
            last_optimized = profile.last_optimized.isoformat()
        
        return {
            "score": optimization_score,
            "level": optimization_level,
            "last_optimized": last_optimized,
            "profile_exists": profile is not None,
            "optimization_available": True,
            "next_optimization_due": self._get_next_optimization_due(profile)
        }
    
    async def _calculate_optimization_score(self, performance: Dict[str, Any], specs) -> float:
        """Calculate overall optimization score (0-100)"""
        
        if not specs:
            return 0.0
        
        score = 100.0
        
        # Performance penalties
        cpu_usage = performance.get("cpu_usage", 0)
        if cpu_usage > 90:
            score -= 25
        elif cpu_usage > 75:
            score -= 15
        elif cpu_usage > 60:
            score -= 8
        
        # Memory pressure penalties
        memory_pressure = performance.get("memory_pressure", "normal")
        if memory_pressure == "critical":
            score -= 30
        elif memory_pressure == "warning":
            score -= 15
        
        # Thermal penalties
        thermal_state = performance.get("thermal_state", "normal")
        if thermal_state == "throttling":
            score -= 25
        elif thermal_state == "elevated":
            score -= 10
        
        # Inference speed bonuses
        inference_speed = performance.get("inference_speed", 0)
        if inference_speed > 25:
            score += 15
        elif inference_speed > 15:
            score += 10
        elif inference_speed > 8:
            score += 5
        
        # Model load time bonuses
        model_load_time = performance.get("model_load_time", 10)
        if model_load_time < 1.0:
            score += 10
        elif model_load_time < 2.0:
            score += 5
        
        # Battery level consideration (for laptops)
        battery_level = performance.get("battery_level")
        if battery_level is not None and battery_level < 20:
            score -= 10
        
        return max(0.0, min(100.0, score))
    
    async def _get_optimization_level(self) -> str:
        """Get current optimization level"""
        import os
        
        # Check for key optimization indicators
        has_metal = os.getenv("OLLAMA_METAL") == "1"
        has_threads = os.getenv("OLLAMA_NUM_THREADS") is not None
        has_memory_config = os.getenv("OLLAMA_MAX_LOADED_MODELS") is not None
        
        if has_metal and has_threads and has_memory_config:
            return "fully_optimized"
        elif has_metal or has_threads:
            return "partially_optimized"
        else:
            return "default"
    
    def _get_next_optimization_due(self, profile) -> Optional[str]:
        """Determine when next optimization should be run"""
        if not profile:
            return "immediately"
        
        last_optimized = profile.last_optimized
        next_due = last_optimized + timedelta(days=7)  # Weekly optimization check
        
        if datetime.utcnow() >= next_due:
            return "overdue"
        else:
            return next_due.isoformat()
    
    async def _get_performance_history(self, db: Session, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance history for charting"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.timestamp >= cutoff_time
        ).order_by(PerformanceMetric.timestamp.asc()).limit(100).all()
        
        history = []
        for metric in metrics:
            history.append({
                "timestamp": metric.timestamp.isoformat(),
                "cpu_usage": metric.cpu_usage,
                "memory_usage": metric.memory_usage,
                "memory_pressure": metric.memory_pressure,
                "thermal_state": metric.thermal_state,
                "inference_speed": metric.inference_speed,
                "model_name": metric.model_name,
                "processing_time": metric.processing_time
            })
        
        return history
    
    async def _get_model_performance_stats(self, db: Session) -> Dict[str, Any]:
        """Get model performance statistics"""
        
        # Get recent model performance data
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        
        model_stats = db.query(
            PerformanceMetric.model_name,
            func.avg(PerformanceMetric.inference_speed).label('avg_inference_speed'),
            func.avg(PerformanceMetric.model_load_time).label('avg_load_time'),
            func.avg(PerformanceMetric.processing_time).label('avg_processing_time'),
            func.count(PerformanceMetric.id).label('usage_count')
        ).filter(
            PerformanceMetric.timestamp >= recent_cutoff,
            PerformanceMetric.model_name.isnot(None)
        ).group_by(PerformanceMetric.model_name).all()
        
        models = {}
        for stat in model_stats:
            models[stat.model_name] = {
                "avg_inference_speed": round(stat.avg_inference_speed or 0, 2),
                "avg_load_time": round(stat.avg_load_time or 0, 2),
                "avg_processing_time": round(stat.avg_processing_time or 0, 2),
                "usage_count": stat.usage_count,
                "performance_rating": self._calculate_model_rating(
                    stat.avg_inference_speed or 0,
                    stat.avg_load_time or 0
                )
            }
        
        return {
            "models": models,
            "total_models_used": len(models),
            "most_used_model": max(models.keys(), key=lambda k: models[k]["usage_count"]) if models else None,
            "fastest_model": max(models.keys(), key=lambda k: models[k]["avg_inference_speed"]) if models else None
        }
    
    def _calculate_model_rating(self, inference_speed: float, load_time: float) -> str:
        """Calculate model performance rating"""
        if inference_speed > 20 and load_time < 2.0:
            return "excellent"
        elif inference_speed > 10 and load_time < 5.0:
            return "good"
        elif inference_speed > 5:
            return "fair"
        else:
            return "poor"
    
    async def _get_agent_utilization(self, db: Session) -> Dict[str, Any]:
        """Get agent utilization statistics"""
        
        # Get agent task counts
        agent_stats = db.query(
            Agent.id,
            Agent.name,
            Agent.type,
            func.count(Task.id).label('total_tasks'),
            func.sum(func.case([(Task.status == 'completed', 1)], else_=0)).label('completed_tasks'),
            func.sum(func.case([(Task.status == 'in_progress', 1)], else_=0)).label('active_tasks'),
            func.avg(Task.actual_effort).label('avg_effort')
        ).outerjoin(Task, Agent.id == Task.agent_id).group_by(Agent.id).all()
        
        agents = {}
        total_tasks = 0
        total_active = 0
        
        for stat in agent_stats:
            agent_total = stat.total_tasks or 0
            agent_completed = stat.completed_tasks or 0
            agent_active = stat.active_tasks or 0
            
            agents[stat.id] = {
                "name": stat.name,
                "type": stat.type.value if stat.type else "unknown",
                "total_tasks": agent_total,
                "completed_tasks": agent_completed,
                "active_tasks": agent_active,
                "completion_rate": agent_completed / agent_total if agent_total > 0 else 0,
                "avg_effort_hours": round(stat.avg_effort or 0, 2),
                "utilization": "high" if agent_active > 2 else "medium" if agent_active > 0 else "low"
            }
            
            total_tasks += agent_total
            total_active += agent_active
        
        return {
            "agents": agents,
            "total_agents": len(agents),
            "total_tasks_processed": total_tasks,
            "currently_active_tasks": total_active,
            "average_utilization": total_active / len(agents) if agents else 0,
            "most_utilized_agent": max(agents.keys(), key=lambda k: agents[k]["active_tasks"]) if agents else None
        }
    
    async def _generate_recommendations(self, performance: Dict[str, Any], specs, db: Session) -> List[str]:
        """Generate optimization recommendations based on current state"""
        
        recommendations = []
        
        if not specs:
            recommendations.append("⚠️ Apple Silicon not detected - optimization features unavailable")
            return recommendations
        
        # Memory pressure recommendations
        memory_pressure = performance.get("memory_pressure", "normal")
        if memory_pressure == "critical":
            recommendations.append("🔴 Critical memory pressure detected - close unnecessary applications immediately")
            recommendations.append("💾 Consider using smaller AI models (e.g., llama2:7b instead of llama2:13b)")
        elif memory_pressure == "warning":
            recommendations.append("🟡 Memory pressure elevated - monitor usage and consider optimizations")
        
        # Thermal recommendations
        thermal_state = performance.get("thermal_state", "normal")
        if thermal_state == "throttling":
            recommendations.append("🌡️ Thermal throttling detected - reduce workload or improve cooling")
            recommendations.append("❄️ Consider using fewer concurrent AI agents")
        elif thermal_state == "elevated":
            recommendations.append("🌡️ Temperature elevated - monitor thermal performance")
        
        # CPU usage recommendations
        cpu_usage = performance.get("cpu_usage", 0)
        if cpu_usage > 90:
            recommendations.append("📊 Very high CPU usage - limit concurrent AI tasks")
        elif cpu_usage > 75:
            recommendations.append("📊 High CPU usage - consider reducing active agents")
        
        # Inference speed recommendations
        inference_speed = performance.get("inference_speed", 0)
        if inference_speed < 3:
            recommendations.append("⚡ Low AI inference speed - check model optimization settings")
            recommendations.append("🚀 Consider running Apple Silicon optimization")
        elif inference_speed < 8:
            recommendations.append("⚡ AI inference could be faster - check for optimizations")
        
        # Battery recommendations (for laptops)
        battery_level = performance.get("battery_level")
        if battery_level is not None:
            if battery_level < 20:
                recommendations.append("🔋 Low battery - plug in for optimal AI performance")
            elif battery_level < 50:
                recommendations.append("🔋 Consider plugging in for sustained AI workloads")
        
        # Optimization level recommendations
        optimization_level = await self._get_optimization_level()
        if optimization_level == "default":
            recommendations.append("🍎 Run Apple Silicon optimization for 3-5x better performance")
        elif optimization_level == "partially_optimized":
            recommendations.append("🔧 Complete Apple Silicon optimization for maximum performance")
        
        # Model recommendations
        model_performance = await self._get_model_performance_stats(db)
        if not model_performance["models"]:
            recommendations.append("🤖 Download recommended AI models for your system")
        
        # Agent utilization recommendations
        agent_utilization = await self._get_agent_utilization(db)
        if agent_utilization["currently_active_tasks"] == 0:
            recommendations.append("✨ Your AI team is ready - create your first task!")
        elif agent_utilization["currently_active_tasks"] > specs.max_concurrent_agents:
            recommendations.append("⚠️ Too many concurrent tasks - may impact performance")
        
        # Default positive message if no issues
        if not recommendations:
            recommendations.append("✅ System is well optimized for AI workloads")
            recommendations.append("🚀 Your Apple Silicon Mac is performing excellently!")
        
        return recommendations
    
    async def _get_latest_benchmark_results(self, db: Session) -> Optional[Dict[str, Any]]:
        """Get the most recent benchmark results"""
        
        # This would integrate with the benchmark system
        # For now, return None or cached results
        return None
    
    async def get_real_time_metrics(self, db: Session) -> Dict[str, Any]:
        """Get real-time metrics for live dashboard updates"""
        
        try:
            performance = await self._get_cached_performance()
            
            # Get current task counts
            active_tasks = db.query(Task).filter(Task.status == 'in_progress').count()
            pending_tasks = db.query(Task).filter(Task.status == 'pending').count()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_usage": performance.get("cpu_usage", 0),
                "memory_usage": performance.get("memory_usage", 0),
                "memory_pressure": performance.get("memory_pressure", "normal"),
                "thermal_state": performance.get("thermal_state", "normal"),
                "inference_speed": performance.get("inference_speed", 0),
                "active_tasks": active_tasks,
                "pending_tasks": pending_tasks,
                "system_healthy": self._assess_system_health(performance)
            }
            
        except Exception as e:
            logger.error(f"Real-time metrics failed: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "system_healthy": False
            }
    
    def _assess_system_health(self, performance: Dict[str, Any]) -> bool:
        """Assess overall system health"""
        
        # Check critical indicators
        memory_pressure = performance.get("memory_pressure", "normal")
        thermal_state = performance.get("thermal_state", "normal")
        cpu_usage = performance.get("cpu_usage", 0)
        
        # System is unhealthy if any critical condition is met
        if memory_pressure == "critical":
            return False
        if thermal_state == "throttling":
            return False
        if cpu_usage > 95:
            return False
        
        return True
    
    async def export_performance_report(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """Export comprehensive performance report"""
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Get all metrics in date range
        metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.timestamp >= cutoff_time
        ).order_by(PerformanceMetric.timestamp.asc()).all()
        
        # Calculate summary statistics
        if metrics:
            cpu_usage_avg = sum(m.cpu_usage for m in metrics if m.cpu_usage) / len([m for m in metrics if m.cpu_usage])
            memory_usage_avg = sum(m.memory_usage for m in metrics if m.memory_usage) / len([m for m in metrics if m.memory_usage])
            inference_speed_avg = sum(m.inference_speed for m in metrics if m.inference_speed) / len([m for m in metrics if m.inference_speed])
        else:
            cpu_usage_avg = memory_usage_avg = inference_speed_avg = 0
        
        return {
            "report_period": {
                "start_date": cutoff_time.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "days": days
            },
            "summary": {
                "total_metrics": len(metrics),
                "avg_cpu_usage": round(cpu_usage_avg, 2),
                "avg_memory_usage": round(memory_usage_avg, 2),
                "avg_inference_speed": round(inference_speed_avg, 2)
            },
            "detailed_metrics": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "cpu_usage": m.cpu_usage,
                    "memory_usage": m.memory_usage,
                    "inference_speed": m.inference_speed,
                    "model_name": m.model_name,
                    "processing_time": m.processing_time
                } for m in metrics
            ]
        }
    
    def clear_performance_cache(self):
        """Clear the performance cache to force fresh data"""
        self.performance_cache.clear()
        logger.info("Performance cache cleared")
