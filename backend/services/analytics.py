# VirtuAI Office - Analytics Service
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics
import json

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from ..models.database import Task, Agent, Project, PerformanceMetric, TaskStatus, TaskPriority, AgentType
from ..core.logging import get_logger, log_performance_metric

logger = get_logger('virtuai.analytics')


class MetricType(str, Enum):
    PRODUCTIVITY = "productivity"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COLLABORATION = "collaboration"
    SYSTEM = "system"


class TimeRange(str, Enum):
    HOUR = "1h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "365d"


@dataclass
class AnalyticsMetric:
    name: str
    value: float
    unit: str
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentPerformanceReport:
    agent_id: str
    agent_name: str
    agent_type: AgentType
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_completion_time: float
    success_rate: float
    quality_score: float
    productivity_score: float
    collaboration_count: int
    recent_activity: List[Dict[str, Any]]
    performance_trend: List[Dict[str, Any]]


@dataclass
class TeamAnalytics:
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    failed_tasks: int
    completion_rate: float
    avg_task_completion_time: float
    productivity_score: float
    team_velocity: float
    bottlenecks: List[str]
    recommendations: List[str]
    agent_performance: List[AgentPerformanceReport]


@dataclass
class ProjectAnalytics:
    project_id: str
    project_name: str
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    estimated_completion: Optional[datetime]
    critical_path: List[str]
    resource_allocation: Dict[str, float]
    risk_factors: List[str]


class AnalyticsService:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)
    
    def _get_time_range_filter(self, time_range: TimeRange) -> datetime:
        """Get datetime filter for time range"""
        now = datetime.utcnow()
        
        range_map = {
            TimeRange.HOUR: timedelta(hours=1),
            TimeRange.DAY: timedelta(days=1),
            TimeRange.WEEK: timedelta(weeks=1),
            TimeRange.MONTH: timedelta(days=30),
            TimeRange.QUARTER: timedelta(days=90),
            TimeRange.YEAR: timedelta(days=365)
        }
        
        return now - range_map.get(time_range, timedelta(days=7))
    
    def _calculate_trend(self, current_value: float, previous_value: float) -> Tuple[float, str]:
        """Calculate percentage change and trend direction"""
        if previous_value == 0:
            return 0.0, "stable"
        
        change_pct = ((current_value - previous_value) / previous_value) * 100
        
        if abs(change_pct) < 5:
            trend = "stable"
        elif change_pct > 0:
            trend = "up"
        else:
            trend = "down"
        
        return change_pct, trend
    
    async def get_team_analytics(self, db: Session, time_range: TimeRange = TimeRange.WEEK) -> TeamAnalytics:
        """Get comprehensive team analytics"""
        
        cache_key = f"team_analytics_{time_range.value}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.utcnow() - timestamp < self.cache_ttl:
                return cached_data
        
        start_date = self._get_time_range_filter(time_range)
        
        # Basic task metrics
        total_tasks = db.query(Task).filter(Task.created_at >= start_date).count()
        completed_tasks = db.query(Task).filter(
            and_(Task.created_at >= start_date, Task.status == TaskStatus.COMPLETED)
        ).count()
        in_progress_tasks = db.query(Task).filter(
            and_(Task.created_at >= start_date, Task.status == TaskStatus.IN_PROGRESS)
        ).count()
        pending_tasks = db.query(Task).filter(
            and_(Task.created_at >= start_date, Task.status == TaskStatus.PENDING)
        ).count()
        failed_tasks = db.query(Task).filter(
            and_(Task.created_at >= start_date, Task.status == TaskStatus.FAILED)
        ).count()
        
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        # Average completion time
        completed_task_times = db.query(Task).filter(
            and_(
                Task.completed_at >= start_date,
                Task.status == TaskStatus.COMPLETED,
                Task.started_at.isnot(None),
                Task.completed_at.isnot(None)
            )
        ).all()
        
        completion_times = []
        for task in completed_task_times:
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds() / 3600
                completion_times.append(duration)
        
        avg_completion_time = statistics.mean(completion_times) if completion_times else 0
        
        # Team velocity (tasks completed per day)
        days_in_range = (datetime.utcnow() - start_date).days or 1
        team_velocity = completed_tasks / days_in_range
        
        # Agent performance reports
        agent_performance = await self._get_all_agent_performance(db, time_range)
        
        # Calculate productivity score (0-100)
        productivity_factors = [
            completion_rate * 40,  # 40% weight on completion rate
            min(team_velocity * 10, 30),  # 30% weight on velocity (capped)
            (1 - (failed_tasks / total_tasks if total_tasks > 0 else 0)) * 20,  # 20% failure penalty
            min(len([a for a in agent_performance if a.success_rate > 0.8]) / len(agent_performance) * 10, 10) if agent_performance else 0  # 10% high-performing agents
        ]
        productivity_score = sum(productivity_factors)
        
        # Identify bottlenecks
        bottlenecks = await self._identify_bottlenecks(db, time_range)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(db, completion_rate, team_velocity, bottlenecks)
        
        analytics = TeamAnalytics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            pending_tasks=pending_tasks,
            failed_tasks=failed_tasks,
            completion_rate=completion_rate,
            avg_task_completion_time=avg_completion_time,
            productivity_score=productivity_score,
            team_velocity=team_velocity,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            agent_performance=agent_performance
        )
        
        # Cache results
        self.cache[cache_key] = (analytics, datetime.utcnow())
        
        return analytics
    
    async def _get_all_agent_performance(self, db: Session, time_range: TimeRange) -> List[AgentPerformanceReport]:
        """Get performance reports for all agents"""
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        performance_reports = []
        
        for agent in agents:
            report = await self.get_agent_performance(db, agent.id, time_range)
            performance_reports.append(report)
        
        return performance_reports
    
    async def get_agent_performance(self, db: Session, agent_id: str, time_range: TimeRange = TimeRange.WEEK) -> AgentPerformanceReport:
        """Get detailed performance report for a specific agent"""
        
        start_date = self._get_time_range_filter(time_range)
        
        # Get agent info
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Basic task metrics
        total_tasks = db.query(Task).filter(
            and_(Task.agent_id == agent_id, Task.created_at >= start_date)
        ).count()
        
        completed_tasks = db.query(Task).filter(
            and_(
                Task.agent_id == agent_id,
                Task.created_at >= start_date,
                Task.status == TaskStatus.COMPLETED
            )
        ).count()
        
        failed_tasks = db.query(Task).filter(
            and_(
                Task.agent_id == agent_id,
                Task.created_at >= start_date,
                Task.status == TaskStatus.FAILED
            )
        ).count()
        
        success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        # Average completion time
        completed_task_objects = db.query(Task).filter(
            and_(
                Task.agent_id == agent_id,
                Task.completed_at >= start_date,
                Task.status == TaskStatus.COMPLETED,
                Task.started_at.isnot(None),
                Task.completed_at.isnot(None)
            )
        ).all()
        
        completion_times = []
        for task in completed_task_objects:
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds() / 3600
                completion_times.append(duration)
        
        avg_completion_time = statistics.mean(completion_times) if completion_times else 0
        
        # Quality score (based on output length, structure, etc.)
        quality_scores = []
        for task in completed_task_objects:
            if task.output:
                score = self._assess_output_quality(task.output)
                quality_scores.append(score)
        
        quality_score = statistics.mean(quality_scores) if quality_scores else 0
        
        # Productivity score
        productivity_factors = [
            success_rate * 50,  # 50% success rate
            (1 / (avg_completion_time + 1)) * 30,  # 30% speed (inverse of time)
            quality_score * 20  # 20% quality
        ]
        productivity_score = sum(productivity_factors)
        
        # Collaboration count (tasks involving multiple agents)
        collaboration_count = 0  # TODO: Implement when collaboration tracking is added
        
        # Recent activity
        recent_activity = await self._get_agent_recent_activity(db, agent_id, 10)
        
        # Performance trend
        performance_trend = await self._get_agent_performance_trend(db, agent_id, time_range)
        
        return AgentPerformanceReport(
            agent_id=agent_id,
            agent_name=agent.name,
            agent_type=agent.type,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            avg_completion_time=avg_completion_time,
            success_rate=success_rate,
            quality_score=quality_score,
            productivity_score=productivity_score,
            collaboration_count=collaboration_count,
            recent_activity=recent_activity,
            performance_trend=performance_trend
        )
    
    def _assess_output_quality(self, output: str) -> float:
        """Assess quality of agent output (0-1 score)"""
        if not output:
            return 0.0
        
        score = 0.0
        
        # Length factor (not too short, not too long)
        length = len(output)
        if 100 <= length <= 2000:
            score += 0.3
        elif 50 <= length < 100 or 2000 < length <= 5000:
            score += 0.2
        elif length > 5000:
            score += 0.1
        
        # Structure indicators
        has_headers = bool(re.search(r'(#{1,6}|\*\*[^*]+\*\*)', output))
        has_code = bool(re.search(r'```|`[^`]+`', output))
        has_lists = bool(re.search(r'(\n\s*[-*+]\s|\n\s*\d+\.\s)', output))
        
        if has_headers:
            score += 0.2
        if has_code:
            score += 0.2
        if has_lists:
            score += 0.2
        
        # Content quality indicators
        has_examples = 'example' in output.lower()
        has_explanations = any(word in output.lower() for word in ['because', 'since', 'therefore', 'due to'])
        
        if has_examples:
            score += 0.1
        if has_explanations:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _get_agent_recent_activity(self, db: Session, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity for an agent"""
        recent_tasks = db.query(Task).filter(
            Task.agent_id == agent_id
        ).order_by(Task.created_at.desc()).limit(limit).all()
        
        activity = []
        for task in recent_tasks:
            activity.append({
                'task_id': task.id,
                'title': task.title,
                'status': task.status.value,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'duration_hours': (
                    (task.completed_at - task.started_at).total_seconds() / 3600
                    if task.started_at and task.completed_at else None
                )
            })
        
        return activity
    
    async def _get_agent_performance_trend(self, db: Session, agent_id: str, time_range: TimeRange) -> List[Dict[str, Any]]:
        """Get performance trend data for an agent"""
        start_date = self._get_time_range_filter(time_range)
        
        # Get daily performance data
        trend_data = []
        current_date = start_date
        
        while current_date < datetime.utcnow():
            next_date = current_date + timedelta(days=1)
            
            daily_completed = db.query(Task).filter(
                and_(
                    Task.agent_id == agent_id,
                    Task.completed_at >= current_date,
                    Task.completed_at < next_date,
                    Task.status == TaskStatus.COMPLETED
                )
            ).count()
            
            daily_total = db.query(Task).filter(
                and_(
                    Task.agent_id == agent_id,
                    Task.created_at >= current_date,
                    Task.created_at < next_date
                )
            ).count()
            
            trend_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'completed_tasks': daily_completed,
                'total_tasks': daily_total,
                'success_rate': daily_completed / daily_total if daily_total > 0 else 0
            })
            
            current_date = next_date
        
        return trend_data
    
    async def _identify_bottlenecks(self, db: Session, time_range: TimeRange) -> List[str]:
        """Identify system bottlenecks"""
        bottlenecks = []
        start_date = self._get_time_range_filter(time_range)
        
        # Check for tasks stuck in pending status
        old_pending = db.query(Task).filter(
            and_(
                Task.status == TaskStatus.PENDING,
                Task.created_at < datetime.utcnow() - timedelta(hours=1)
            )
        ).count()
        
        if old_pending > 5:
            bottlenecks.append(f"{old_pending} tasks stuck in pending status for over 1 hour")
        
        # Check for overloaded agents
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        for agent in agents:
            active_tasks = db.query(Task).filter(
                and_(
                    Task.agent_id == agent.id,
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
                )
            ).count()
            
            if active_tasks > 10:
                bottlenecks.append(f"Agent {agent.name} is overloaded with {active_tasks} active tasks")
        
        # Check for high failure rate
        recent_failed = db.query(Task).filter(
            and_(
                Task.created_at >= start_date,
                Task.status == TaskStatus.FAILED
            )
        ).count()
        
        recent_total = db.query(Task).filter(Task.created_at >= start_date).count()
        
        if recent_total > 0 and (recent_failed / recent_total) > 0.2:
            bottlenecks.append(f"High failure rate: {(recent_failed/recent_total*100):.1f}% of recent tasks failed")
        
        return bottlenecks
    
    async def _generate_recommendations(self, db: Session, completion_rate: float,
                                      team_velocity: float, bottlenecks: List[str]) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        # Performance-based recommendations
        if completion_rate < 0.7:
            recommendations.append("Consider reviewing task complexity and breaking down large tasks")
        
        if team_velocity < 1.0:
            recommendations.append("Team velocity is low - consider optimizing agent assignments")
        
        # Bottleneck-based recommendations
        if any("stuck in pending" in b for b in bottlenecks):
            recommendations.append("Check Ollama service status and model availability")
        
        if any("overloaded" in b for b in bottlenecks):
            recommendations.append("Redistribute tasks more evenly across agents")
        
        if any("failure rate" in b for b in bottlenecks):
            recommendations.append("Review failed tasks and improve task descriptions")
        
        # System optimization recommendations
        system_metrics = await self._get_system_metrics(db)
        if system_metrics.get('avg_response_time', 0) > 30:
            recommendations.append("Consider using smaller AI models for better response times")
        
        if not recommendations:
            recommendations.append("Team is performing well! Consider taking on more complex challenges")
        
        return recommendations
    
    async def _get_system_metrics(self, db: Session) -> Dict[str, float]:
        """Get system performance metrics"""
        # Get recent performance metrics
        recent_metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).all()
        
        metrics = {}
        
        if recent_metrics:
            response_times = [m.processing_time for m in recent_metrics if m.processing_time]
            if response_times:
                metrics['avg_response_time'] = statistics.mean(response_times)
            
            cpu_usage = [m.cpu_usage for m in recent_metrics if m.cpu_usage]
            if cpu_usage:
                metrics['avg_cpu_usage'] = statistics.mean(cpu_usage)
            
            memory_usage = [m.memory_usage for m in recent_metrics if m.memory_usage]
            if memory_usage:
                metrics['avg_memory_usage'] = statistics.mean(memory_usage)
        
        return metrics
    
    async def get_project_analytics(self, db: Session, project_id: str) -> ProjectAnalytics:
        """Get analytics for a specific project"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Basic project metrics
        total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
        completed_tasks = db.query(Task).filter(
            and_(Task.project_id == project_id, Task.status == TaskStatus.COMPLETED)
        ).count()
        
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        # Resource allocation (agent distribution)
        resource_allocation = {}
        project_tasks = db.query(Task).filter(Task.project_id == project_id).all()
        
        for task in project_tasks:
            if task.agent and task.agent.name:
                resource_allocation[task.agent.name] = resource_allocation.get(task.agent.name, 0) + 1
        
        # Convert to percentages
        if total_tasks > 0:
            resource_allocation = {k: (v / total_tasks) * 100 for k, v in resource_allocation.items()}
        
        # Estimated completion (simple projection based on current rate)
        estimated_completion = None
        if completion_rate > 0 and completion_rate < 1:
            remaining_tasks = total_tasks - completed_tasks
            avg_completion_time = 24  # hours (simplified)
            days_remaining = (remaining_tasks * avg_completion_time) / 24
            estimated_completion = datetime.utcnow() + timedelta(days=days_remaining)
        
        # Risk factors
        risk_factors = []
        if completion_rate < 0.5 and total_tasks > 10:
            risk_factors.append("Low completion rate may indicate project complexity issues")
        
        pending_tasks = db.query(Task).filter(
            and_(Task.project_id == project_id, Task.status == TaskStatus.PENDING)
        ).count()
        
        if pending_tasks > total_tasks * 0.5:
            risk_factors.append("High number of pending tasks may cause delays")
        
        return ProjectAnalytics(
            project_id=project_id,
            project_name=project.name,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_rate=completion_rate,
            estimated_completion=estimated_completion,
            critical_path=[],  # TODO: Implement critical path analysis
            resource_allocation=resource_allocation,
            risk_factors=risk_factors
        )
    
    async def get_metrics_dashboard(self, db: Session, time_range: TimeRange = TimeRange.DAY) -> Dict[str, AnalyticsMetric]:
        """Get key metrics for dashboard display"""
        start_date = self._get_time_range_filter(time_range)
        previous_start = start_date - (datetime.utcnow() - start_date)
        
        metrics = {}
        
        # Task completion rate
        current_completed = db.query(Task).filter(
            and_(Task.completed_at >= start_date, Task.status == TaskStatus.COMPLETED)
        ).count()
        current_total = db.query(Task).filter(Task.created_at >= start_date).count()
        current_rate = current_completed / current_total if current_total > 0 else 0
        
        previous_completed = db.query(Task).filter(
            and_(
                Task.completed_at >= previous_start,
                Task.completed_at < start_date,
                Task.status == TaskStatus.COMPLETED
            )
        ).count()
        previous_total = db.query(Task).filter(
            and_(Task.created_at >= previous_start, Task.created_at < start_date)
        ).count()
        previous_rate = previous_completed / previous_total if previous_total > 0 else 0
        
        change_pct, trend = self._calculate_trend(current_rate, previous_rate)
        
        metrics['completion_rate'] = AnalyticsMetric(
            name="Task Completion Rate",
            value=current_rate * 100,
            unit="%",
            change_percentage=change_pct,
            trend=trend,
            timestamp=datetime.utcnow()
        )
        
        # Average response time
        current_metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.timestamp >= start_date
        ).all()
        
        if current_metrics:
            response_times = [m.processing_time for m in current_metrics if m.processing_time]
            if response_times:
                avg_response_time = statistics.mean(response_times)
                metrics['avg_response_time'] = AnalyticsMetric(
                    name="Average Response Time",
                    value=avg_response_time,
                    unit="seconds",
                    timestamp=datetime.utcnow()
                )
        
        # Active agents
        active_agents = db.query(Agent).filter(Agent.is_active == True).count()
        metrics['active_agents'] = AnalyticsMetric(
            name="Active Agents",
            value=active_agents,
            unit="agents",
            timestamp=datetime.utcnow()
        )
        
        # Tasks per hour
        hours_in_range = max(1, (datetime.utcnow() - start_date).total_seconds() / 3600)
        tasks_per_hour = current_total / hours_in_range
        
        metrics['tasks_per_hour'] = AnalyticsMetric(
            name="Tasks per Hour",
            value=tasks_per_hour,
            unit="tasks/hour",
            timestamp=datetime.utcnow()
        )
        
        return metrics
    
    async def export_analytics_report(self, db: Session, time_range: TimeRange = TimeRange.MONTH) -> Dict[str, Any]:
        """Export comprehensive analytics report"""
        team_analytics = await self.get_team_analytics(db, time_range)
        metrics_dashboard = await self.get_metrics_dashboard(db, time_range)
        
        # Get all projects analytics
        projects = db.query(Project).all()
        project_analytics = []
        for project in projects:
            try:
                analytics = await self.get_project_analytics(db, project.id)
                project_analytics.append(analytics)
            except Exception as e:
                logger.warning(f"Failed to get analytics for project {project.id}: {e}")
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'time_range': time_range.value,
            'team_analytics': {
                'total_tasks': team_analytics.total_tasks,
                'completed_tasks': team_analytics.completed_tasks,
                'completion_rate': team_analytics.completion_rate,
                'team_velocity': team_analytics.team_velocity,
                'productivity_score': team_analytics.productivity_score,
                'bottlenecks': team_analytics.bottlenecks,
                'recommendations': team_analytics.recommendations
            },
            'key_metrics': {
                name: {
                    'value': metric.value,
                    'unit': metric.unit,
                    'change_percentage': metric.change_percentage,
                    'trend': metric.trend
                } for name, metric in metrics_dashboard.items()
            },
            'agent_performance': [
                {
                    'agent_name': agent.agent_name,
                    'success_rate': agent.success_rate,
                    'productivity_score': agent.productivity_score,
                    'total_tasks': agent.total_tasks,
                    'avg_completion_time': agent.avg_completion_time
                } for agent in team_analytics.agent_performance
            ],
            'project_analytics': [
                {
                    'project_name': project.project_name,
                    'completion_rate': project.completion_rate,
                    'total_tasks': project.total_tasks,
                    'resource_allocation': project.resource_allocation,
                    'risk_factors': project.risk_factors
                } for project in project_analytics
            ]
        }
        
        return report


# Global analytics service instance
analytics_service = AnalyticsService()
