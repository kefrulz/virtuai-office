# VirtuAI Office - Performance Analytics & Optimization System
import asyncio
import time
import psutil
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from collections import defaultdict, deque

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

logger = logging.getLogger('virtuai.performance')


class PerformanceMetricType(str, Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    INFERENCE_SPEED = "inference_speed"
    TASK_COMPLETION_TIME = "task_completion_time"
    MODEL_LOAD_TIME = "model_load_time"
    AGENT_RESPONSE_TIME = "agent_response_time"
    SYSTEM_THROUGHPUT = "system_throughput"
    ERROR_RATE = "error_rate"
    QUEUE_LENGTH = "queue_length"
    THERMAL_STATE = "thermal_state"


class PerformanceLevel(str, Enum):
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 70-89%
    FAIR = "fair"           # 50-69%
    POOR = "poor"           # 0-49%


@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str
    timestamp: datetime
    component: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBenchmark:
    agent_id: str
    task_complexity: str
    model_name: str
    inference_speed: float  # tokens/second
    completion_time: float  # seconds
    memory_usage: float     # MB
    cpu_usage: float        # percentage
    quality_score: float    # 0-1
    timestamp: datetime


@dataclass
class SystemPerformanceSnapshot:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    memory_pressure: str
    active_tasks: int
    completed_tasks_last_hour: int
    average_response_time: float
    error_rate: float
    system_load: float


class PerformanceCollector:
    """Collects system and application performance metrics"""
    
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.metrics_buffer = deque(maxlen=1000)  # Store last 1000 metrics
        self.is_collecting = False
        self.collection_task = None
        
    async def start_collection(self):
        """Start continuous metrics collection"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Performance metrics collection started")
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance metrics collection stopped")
    
    async def _collection_loop(self):
        """Main collection loop"""
        while self.is_collecting:
            try:
                metrics = await self.collect_system_metrics()
                for metric in metrics:
                    self.metrics_buffer.append(metric)
                
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance collection: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def collect_system_metrics(self) -> List[PerformanceMetric]:
        """Collect current system metrics"""
        timestamp = datetime.utcnow()
        metrics = []
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(PerformanceMetric(
                name=PerformanceMetricType.CPU_USAGE,
                value=cpu_percent,
                unit="percent",
                timestamp=timestamp,
                component="system"
            ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.append(PerformanceMetric(
                name=PerformanceMetricType.MEMORY_USAGE,
                value=memory.percent,
                unit="percent",
                timestamp=timestamp,
                component="system",
                metadata={
                    "available_gb": round(memory.available / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2)
                }
            ))
            
            # System load
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()[0]  # 1-minute load average
                metrics.append(PerformanceMetric(
                    name="system_load",
                    value=load_avg,
                    unit="load",
                    timestamp=timestamp,
                    component="system"
                ))
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.append(PerformanceMetric(
                    name="disk_read_rate",
                    value=disk_io.read_bytes,
                    unit="bytes",
                    timestamp=timestamp,
                    component="system"
                ))
                metrics.append(PerformanceMetric(
                    name="disk_write_rate",
                    value=disk_io.write_bytes,
                    unit="bytes",
                    timestamp=timestamp,
                    component="system"
                ))
            
            # Network I/O
            network_io = psutil.net_io_counters()
            if network_io:
                metrics.append(PerformanceMetric(
                    name="network_sent",
                    value=network_io.bytes_sent,
                    unit="bytes",
                    timestamp=timestamp,
                    component="system"
                ))
                metrics.append(PerformanceMetric(
                    name="network_received",
                    value=network_io.bytes_recv,
                    unit="bytes",
                    timestamp=timestamp,
                    component="system"
                ))
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def get_recent_metrics(self, metric_name: str = None,
                          component: str = None,
                          minutes: int = 60) -> List[PerformanceMetric]:
        """Get recent metrics matching criteria"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        filtered_metrics = []
        for metric in self.metrics_buffer:
            if metric.timestamp < cutoff_time:
                continue
            
            if metric_name and metric.name != metric_name:
                continue
            
            if component and metric.component != component:
                continue
            
            filtered_metrics.append(metric)
        
        return filtered_metrics


class PerformanceAnalyzer:
    """Analyzes performance metrics and provides insights"""
    
    def __init__(self, collector: PerformanceCollector):
        self.collector = collector
        self.benchmarks = deque(maxlen=500)  # Store recent benchmarks
        
        # Performance thresholds
        self.thresholds = {
            PerformanceMetricType.CPU_USAGE: {"good": 70, "fair": 85, "poor": 95},
            PerformanceMetricType.MEMORY_USAGE: {"good": 70, "fair": 85, "poor": 95},
            PerformanceMetricType.INFERENCE_SPEED: {"good": 10, "fair": 5, "poor": 2},  # tokens/sec
            PerformanceMetricType.TASK_COMPLETION_TIME: {"good": 30, "fair": 60, "poor": 120},  # seconds
            PerformanceMetricType.ERROR_RATE: {"good": 5, "fair": 10, "poor": 20},  # percent
        }
    
    def analyze_current_performance(self) -> Dict[str, Any]:
        """Analyze current system performance"""
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_score": 0,
            "level": PerformanceLevel.POOR,
            "metrics": {},
            "bottlenecks": [],
            "recommendations": []
        }
        
        # Get recent metrics (last 5 minutes)
        recent_metrics = self.collector.get_recent_metrics(minutes=5)
        
        if not recent_metrics:
            analysis["error"] = "No recent metrics available"
            return analysis
        
        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_type[metric.name].append(metric.value)
        
        scores = []
        
        # Analyze each metric type
        for metric_type, values in metrics_by_type.items():
            if not values:
                continue
            
            avg_value = statistics.mean(values)
            analysis["metrics"][metric_type] = {
                "current": avg_value,
                "trend": self._calculate_trend(values),
                "level": self._assess_metric_level(metric_type, avg_value)
            }
            
            # Calculate score for this metric
            score = self._calculate_metric_score(metric_type, avg_value)
            scores.append(score)
            
            # Check for bottlenecks
            if score < 50:
                bottleneck = self._identify_bottleneck(metric_type, avg_value)
                if bottleneck:
                    analysis["bottlenecks"].append(bottleneck)
        
        # Calculate overall score
        if scores:
            analysis["overall_score"] = statistics.mean(scores)
            analysis["level"] = self._get_performance_level(analysis["overall_score"])
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def analyze_agent_performance(self, agent_id: str, db: Session) -> Dict[str, Any]:
        """Analyze individual agent performance"""
        # Get recent tasks for this agent
        from backend.models import Task, TaskStatus
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_tasks = db.query(Task).filter(
            and_(
                Task.agent_id == agent_id,
                Task.completed_at >= week_ago,
                Task.status == TaskStatus.COMPLETED
            )
        ).all()
        
        if not recent_tasks:
            return {
                "agent_id": agent_id,
                "error": "No completed tasks in the last week"
            }
        
        # Calculate performance metrics
        completion_times = []
        effort_hours = []
        success_rate_data = []
        
        for task in recent_tasks:
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                completion_times.append(duration)
            
            if task.actual_effort:
                effort_hours.append(task.actual_effort)
            
            success_rate_data.append(1 if task.status == TaskStatus.COMPLETED else 0)
        
        analysis = {
            "agent_id": agent_id,
            "period": "last_7_days",
            "total_tasks": len(recent_tasks),
            "avg_completion_time": statistics.mean(completion_times) if completion_times else 0,
            "avg_effort_hours": statistics.mean(effort_hours) if effort_hours else 0,
            "success_rate": statistics.mean(success_rate_data) if success_rate_data else 0,
            "performance_score": 0,
            "level": PerformanceLevel.POOR,
            "trends": {},
            "recommendations": []
        }
        
        # Calculate performance score
        score_components = []
        
        # Success rate score (0-40 points)
        success_score = analysis["success_rate"] * 40
        score_components.append(success_score)
        
        # Speed score (0-30 points)
        if completion_times:
            avg_time = analysis["avg_completion_time"]
            if avg_time <= 30:
                speed_score = 30
            elif avg_time <= 60:
                speed_score = 20
            elif avg_time <= 120:
                speed_score = 10
            else:
                speed_score = 0
            score_components.append(speed_score)
        
        # Consistency score (0-30 points)
        if len(completion_times) > 1:
            time_std = statistics.stdev(completion_times)
            time_mean = statistics.mean(completion_times)
            cv = time_std / time_mean if time_mean > 0 else 1
            
            if cv <= 0.2:
                consistency_score = 30
            elif cv <= 0.4:
                consistency_score = 20
            elif cv <= 0.6:
                consistency_score = 10
            else:
                consistency_score = 0
            score_components.append(consistency_score)
        
        analysis["performance_score"] = sum(score_components)
        analysis["level"] = self._get_performance_level(analysis["performance_score"])
        
        # Generate agent-specific recommendations
        analysis["recommendations"] = self._generate_agent_recommendations(analysis)
        
        return analysis
    
    def benchmark_agent(self, agent_id: str, task_id: str,
                       model_name: str, task_complexity: str) -> PerformanceBenchmark:
        """Create a performance benchmark for an agent task"""
        start_time = time.time()
        start_memory = psutil.virtual_memory().used
        start_cpu = psutil.cpu_percent()
        
        # This would be called at the end of task processing
        def finish_benchmark(quality_score: float = 0.8) -> PerformanceBenchmark:
            end_time = time.time()
            end_memory = psutil.virtual_memory().used
            end_cpu = psutil.cpu_percent()
            
            completion_time = end_time - start_time
            memory_used = (end_memory - start_memory) / (1024 * 1024)  # MB
            avg_cpu = (start_cpu + end_cpu) / 2
            
            # Estimate inference speed (tokens per second)
            # This is a rough estimate - in real implementation,
            # you'd track actual token generation
            estimated_tokens = len(task_id) * 10  # Rough estimate
            inference_speed = estimated_tokens / completion_time if completion_time > 0 else 0
            
            benchmark = PerformanceBenchmark(
                agent_id=agent_id,
                task_complexity=task_complexity,
                model_name=model_name,
                inference_speed=inference_speed,
                completion_time=completion_time,
                memory_usage=memory_used,
                cpu_usage=avg_cpu,
                quality_score=quality_score,
                timestamp=datetime.utcnow()
            )
            
            self.benchmarks.append(benchmark)
            
            logger.info(f"Agent {agent_id} benchmark: {completion_time:.2f}s, "
                       f"{inference_speed:.1f} tokens/sec, {memory_used:.1f}MB")
            
            return benchmark
        
        return finish_benchmark
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.collector.metrics_buffer if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"error": "No metrics available for trend analysis"}
        
        # Group metrics by hour
        hourly_data = defaultdict(lambda: defaultdict(list))
        
        for metric in recent_metrics:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_data[hour_key][metric.name].append(metric.value)
        
        # Calculate trends
        trends = {}
        for hour, metrics in sorted(hourly_data.items()):
            hour_str = hour.isoformat()
            trends[hour_str] = {}
            
            for metric_name, values in metrics.items():
                trends[hour_str][metric_name] = {
                    "avg": statistics.mean(values),
                    "max": max(values),
                    "min": min(values),
                    "count": len(values)
                }
        
        return {
            "period_hours": hours,
            "data_points": len(recent_metrics),
            "trends": trends,
            "summary": self._summarize_trends(trends)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear trend
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        if abs(slope) < 0.1:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _assess_metric_level(self, metric_type: str, value: float) -> PerformanceLevel:
        """Assess the performance level for a specific metric"""
        if metric_type not in self.thresholds:
            return PerformanceLevel.GOOD
        
        thresholds = self.thresholds[metric_type]
        
        # For metrics where lower is better (like CPU usage, completion time)
        if metric_type in [PerformanceMetricType.CPU_USAGE,
                          PerformanceMetricType.MEMORY_USAGE,
                          PerformanceMetricType.TASK_COMPLETION_TIME,
                          PerformanceMetricType.ERROR_RATE]:
            if value <= thresholds["good"]:
                return PerformanceLevel.EXCELLENT
            elif value <= thresholds["fair"]:
                return PerformanceLevel.GOOD
            elif value <= thresholds["poor"]:
                return PerformanceLevel.FAIR
            else:
                return PerformanceLevel.POOR
        
        # For metrics where higher is better (like inference speed)
        else:
            if value >= thresholds["good"]:
                return PerformanceLevel.EXCELLENT
            elif value >= thresholds["fair"]:
                return PerformanceLevel.GOOD
            elif value >= thresholds["poor"]:
                return PerformanceLevel.FAIR
            else:
                return PerformanceLevel.POOR
    
    def _calculate_metric_score(self, metric_type: str, value: float) -> float:
        """Calculate a 0-100 score for a metric"""
        if metric_type not in self.thresholds:
            return 75.0  # Default score
        
        thresholds = self.thresholds[metric_type]
        
        # For metrics where lower is better
        if metric_type in [PerformanceMetricType.CPU_USAGE,
                          PerformanceMetricType.MEMORY_USAGE,
                          PerformanceMetricType.TASK_COMPLETION_TIME,
                          PerformanceMetricType.ERROR_RATE]:
            if value <= thresholds["good"]:
                return 100.0
            elif value <= thresholds["fair"]:
                return 75.0
            elif value <= thresholds["poor"]:
                return 50.0
            else:
                return 25.0
        
        # For metrics where higher is better
        else:
            if value >= thresholds["good"]:
                return 100.0
            elif value >= thresholds["fair"]:
                return 75.0
            elif value >= thresholds["poor"]:
                return 50.0
            else:
                return 25.0
    
    def _get_performance_level(self, score: float) -> PerformanceLevel:
        """Convert numeric score to performance level"""
        if score >= 90:
            return PerformanceLevel.EXCELLENT
        elif score >= 70:
            return PerformanceLevel.GOOD
        elif score >= 50:
            return PerformanceLevel.FAIR
        else:
            return PerformanceLevel.POOR
    
    def _identify_bottleneck(self, metric_type: str, value: float) -> Optional[Dict[str, Any]]:
        """Identify specific bottlenecks"""
        bottlenecks = {
            PerformanceMetricType.CPU_USAGE: {
                "type": "CPU Bottleneck",
                "description": f"High CPU usage ({value:.1f}%)",
                "impact": "Tasks may process slowly",
                "suggestions": ["Close unnecessary applications", "Limit concurrent tasks"]
            },
            PerformanceMetricType.MEMORY_USAGE: {
                "type": "Memory Bottleneck",
                "description": f"High memory usage ({value:.1f}%)",
                "impact": "System may become unstable",
                "suggestions": ["Use smaller AI models", "Restart the application"]
            }
        }
        
        return bottlenecks.get(metric_type)
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        overall_score = analysis.get("overall_score", 0)
        
        if overall_score < 50:
            recommendations.append("🔴 System performance is poor - consider system optimization")
        elif overall_score < 70:
            recommendations.append("🟡 System performance could be improved")
        else:
            recommendations.append("🟢 System performance is good")
        
        # Add specific recommendations based on bottlenecks
        for bottleneck in analysis.get("bottlenecks", []):
            recommendations.extend(bottleneck.get("suggestions", []))
        
        return recommendations
    
    def _generate_agent_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate agent-specific recommendations"""
        recommendations = []
        score = analysis.get("performance_score", 0)
        
        if analysis.get("success_rate", 0) < 0.8:
            recommendations.append("Improve task success rate - check for common failure patterns")
        
        if analysis.get("avg_completion_time", 0) > 60:
            recommendations.append("Optimize task processing speed - consider using smaller models")
        
        if score < 50:
            recommendations.append("Agent performance needs attention - review task assignments")
        
        return recommendations
    
    def _summarize_trends(self, trends: Dict[str, Any]) -> Dict[str, str]:
        """Summarize overall trends"""
        summary = {}
        
        # Extract all CPU values across time
        cpu_values = []
        memory_values = []
        
        for hour_data in trends.values():
            if PerformanceMetricType.CPU_USAGE in hour_data:
                cpu_values.append(hour_data[PerformanceMetricType.CPU_USAGE]["avg"])
            if PerformanceMetricType.MEMORY_USAGE in hour_data:
                memory_values.append(hour_data[PerformanceMetricType.MEMORY_USAGE]["avg"])
        
        if cpu_values:
            summary["cpu_trend"] = self._calculate_trend(cpu_values)
        if memory_values:
            summary["memory_trend"] = self._calculate_trend(memory_values)
        
        return summary


class PerformanceOptimizer:
    """Optimizes system performance based on analysis"""
    
    def __init__(self, analyzer: PerformanceAnalyzer):
        self.analyzer = analyzer
        
    async def optimize_system_performance(self) -> Dict[str, Any]:
        """Optimize overall system performance"""
        analysis = self.analyzer.analyze_current_performance()
        optimizations = []
        
        # CPU optimization
        cpu_level = analysis.get("metrics", {}).get(PerformanceMetricType.CPU_USAGE, {}).get("level")
        if cpu_level in [PerformanceLevel.FAIR, PerformanceLevel.POOR]:
            optimization = await self._optimize_cpu_usage()
            if optimization:
                optimizations.append(optimization)
        
        # Memory optimization
        memory_level = analysis.get("metrics", {}).get(PerformanceMetricType.MEMORY_USAGE, {}).get("level")
        if memory_level in [PerformanceLevel.FAIR, PerformanceLevel.POOR]:
            optimization = await self._optimize_memory_usage()
            if optimization:
                optimizations.append(optimization)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": analysis,
            "optimizations_applied": optimizations,
            "success": len(optimizations) > 0
        }
    
    async def _optimize_cpu_usage(self) -> Optional[Dict[str, str]]:
        """Optimize CPU usage"""
        try:
            # Reduce process priority for non-critical tasks
            import os
            current_priority = os.getpriority(os.PRIO_PROCESS, 0)
            if current_priority < 5:
                os.setpriority(os.PRIO_PROCESS, 0, 5)
                return {
                    "type": "CPU Optimization",
                    "action": "Reduced process priority",
                    "details": f"Changed priority from {current_priority} to 5"
                }
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
        
        return None
    
    async def _optimize_memory_usage(self) -> Optional[Dict[str, str]]:
        """Optimize memory usage"""
        try:
            import gc
            gc.collect()
            
            return {
                "type": "Memory Optimization",
                "action": "Garbage collection performed",
                "details": "Freed unused memory objects"
            }
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
        
        return None


class PerformanceMonitor:
    """Main performance monitoring coordinator"""
    
    def __init__(self):
        self.collector = PerformanceCollector()
        self.analyzer = PerformanceAnalyzer(self.collector)
        self.optimizer = PerformanceOptimizer(self.analyzer)
        self.monitoring_active = False
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            return
        
        await self.collector.start_collection()
        self.monitoring_active = True
        logger.info("🔍 Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        if not self.monitoring_active:
            return
        
        await self.collector.stop_collection()
        self.monitoring_active = False
        logger.info("🛑 Performance monitoring stopped")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current performance status"""
        return {
            "monitoring_active": self.monitoring_active,
            "metrics_collected": len(self.collector.metrics_buffer),
            "last_collection": max([m.timestamp for m in self.collector.metrics_buffer]) if self.collector.metrics_buffer else None,
            "analysis": self.analyzer.analyze_current_performance()
        }
    
    async def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            "report_period_hours": hours,
            "generated_at": datetime.utcnow().isoformat(),
            "current_analysis": self.analyzer.analyze_current_performance(),
            "trends": self.analyzer.get_performance_trends(hours),
            "system_snapshot": await self._get_system_snapshot(),
            "recommendations": self._get_optimization_recommendations()
        }
    
    async def _get_system_snapshot(self) -> SystemPerformanceSnapshot:
        """Get current system performance snapshot"""
        return SystemPerformanceSnapshot(
            timestamp=datetime.utcnow(),
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            memory_pressure="normal",  # This would be determined by system-specific checks
            active_tasks=0,  # This would be queried from task database
            completed_tasks_last_hour=0,  # This would be queried from task database
            average_response_time=0.0,  # This would be calculated from recent metrics
            error_rate=0.0,  # This would be calculated from recent error logs
            system_load=psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
        )
    
    def _get_optimization_recommendations(self) -> List[str]:
        """Get system optimization recommendations"""
        analysis = self.analyzer.analyze_current_performance()
        return analysis.get("recommendations", [])


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


# Convenience functions
async def start_performance_monitoring():
    """Start global performance monitoring"""
    monitor = get_performance_monitor()
    await monitor.start_monitoring()


async def stop_performance_monitoring():
    """Stop global performance monitoring"""
    monitor = get_performance_monitor()
    await monitor.stop_monitoring()


def log_performance_metric(name: str, value: float, unit: str, component: str = "app"):
    """Log a custom performance metric"""
    monitor = get_performance_monitor()
    metric = PerformanceMetric(
        name=name,
        value=value,
        unit=unit,
        timestamp=datetime.utcnow(),
        component=component
    )
    monitor.collector.metrics_buffer.append(metric)


async def get_performance_status() -> Dict[str, Any]:
    """Get current performance status"""
    monitor = get_performance_monitor()
    return monitor.get_current_status()


async def generate_performance_report(hours: int = 24) -> Dict[str, Any]:
    """Generate performance report"""
    monitor = get_performance_monitor()
    return await monitor.generate_performance_report(hours)
