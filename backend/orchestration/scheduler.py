# VirtuAI Office - Advanced Task Scheduler & Orchestrator
import asyncio
import heapq
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging
from collections import defaultdict, deque
import time
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.logging import get_logger, log_performance_warning
from ..models.database import Task, Agent, TaskStatus, TaskPriority, AgentType


class SchedulerMode(str, Enum):
    FIFO = "fifo"  # First In, First Out
    PRIORITY = "priority"  # Priority-based scheduling
    LOAD_BALANCED = "load_balanced"  # Load balancing across agents
    DEADLINE = "deadline"  # Deadline-aware scheduling
    SMART = "smart"  # AI-powered intelligent scheduling


class TaskExecutionState(str, Enum):
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class ScheduledTask:
    """Represents a task in the scheduler queue"""
    task_id: str
    priority: int
    scheduled_time: datetime
    deadline: Optional[datetime] = None
    dependencies: Set[str] = field(default_factory=set)
    agent_requirements: Set[AgentType] = field(default_factory=set)
    estimated_duration: Optional[int] = None  # minutes
    retry_count: int = 0
    max_retries: int = 3
    state: TaskExecutionState = TaskExecutionState.QUEUED
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For heap ordering - higher priority and earlier time comes first"""
        if self.priority != other.priority:
            return self.priority > other.priority  # Higher priority first
        return self.scheduled_time < other.scheduled_time


@dataclass
class AgentResource:
    """Represents an agent's current resource state"""
    agent_id: str
    agent_type: AgentType
    current_load: int = 0
    max_capacity: int = 3
    current_tasks: Set[str] = field(default_factory=set)
    performance_score: float = 1.0
    last_task_completion: Optional[datetime] = None
    specialization_score: Dict[str, float] = field(default_factory=dict)
    
    @property
    def is_available(self) -> bool:
        return self.current_load < self.max_capacity
    
    @property
    def utilization_rate(self) -> float:
        return self.current_load / self.max_capacity if self.max_capacity > 0 else 0.0


class TaskScheduler:
    """Advanced task scheduler with multiple scheduling strategies"""
    
    def __init__(self,
                 mode: SchedulerMode = SchedulerMode.SMART,
                 max_concurrent_tasks: int = 10,
                 enable_preemption: bool = False,
                 scheduler_interval: float = 5.0):
        
        self.mode = mode
        self.max_concurrent_tasks = max_concurrent_tasks
        self.enable_preemption = enable_preemption
        self.scheduler_interval = scheduler_interval
        
        # Task queues
        self.task_queue: List[ScheduledTask] = []  # Priority heap
        self.executing_tasks: Dict[str, ScheduledTask] = {}
        self.completed_tasks: Dict[str, ScheduledTask] = {}
        self.failed_tasks: Dict[str, ScheduledTask] = {}
        
        # Agent management
        self.agents: Dict[str, AgentResource] = {}
        self.agent_assignments: Dict[str, str] = {}  # task_id -> agent_id
        
        # Dependency management
        self.task_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Performance tracking
        self.metrics = {
            'tasks_scheduled': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_wait_time': 0.0,
            'average_execution_time': 0.0,
            'throughput': 0.0,
            'agent_utilization': {}
        }
        
        # Scheduler state
        self.is_running = False
        self.scheduler_task = None
        self.logger = get_logger('virtuai.scheduler')
        
        # Callback handlers
        self.task_started_callbacks: List[Callable] = []
        self.task_completed_callbacks: List[Callable] = []
        self.task_failed_callbacks: List[Callable] = []
        
        # Thread pool for task execution
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info(f"Task scheduler started in {self.mode.value} mode")
    
    async def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all executing tasks
        for task_id in list(self.executing_tasks.keys()):
            await self.cancel_task(task_id)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("Task scheduler stopped")
    
    def register_agent(self,
                      agent_id: str,
                      agent_type: AgentType,
                      max_capacity: int = 3,
                      specializations: Dict[str, float] = None):
        """Register an agent with the scheduler"""
        self.agents[agent_id] = AgentResource(
            agent_id=agent_id,
            agent_type=agent_type,
            max_capacity=max_capacity,
            specialization_score=specializations or {}
        )
        self.metrics['agent_utilization'][agent_id] = 0.0
        self.logger.info(f"Registered agent {agent_id} ({agent_type.value}) with capacity {max_capacity}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            # Reassign or cancel tasks assigned to this agent
            tasks_to_reassign = [
                task_id for task_id, assigned_agent in self.agent_assignments.items()
                if assigned_agent == agent_id
            ]
            
            for task_id in tasks_to_reassign:
                asyncio.create_task(self._reassign_task(task_id))
            
            del self.agents[agent_id]
            if agent_id in self.metrics['agent_utilization']:
                del self.metrics['agent_utilization'][agent_id]
            
            self.logger.info(f"Unregistered agent {agent_id}")
    
    async def schedule_task(self,
                          task_id: str,
                          priority: TaskPriority = TaskPriority.MEDIUM,
                          deadline: Optional[datetime] = None,
                          dependencies: List[str] = None,
                          agent_requirements: List[AgentType] = None,
                          estimated_duration: Optional[int] = None,
                          metadata: Dict[str, Any] = None) -> bool:
        """Schedule a task for execution"""
        
        # Convert priority to numeric value
        priority_map = {
            TaskPriority.LOW: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.URGENT: 4
        }
        
        scheduled_task = ScheduledTask(
            task_id=task_id,
            priority=priority_map.get(priority, 2),
            scheduled_time=datetime.utcnow(),
            deadline=deadline,
            dependencies=set(dependencies or []),
            agent_requirements=set(agent_requirements or []),
            estimated_duration=estimated_duration,
            metadata=metadata or {}
        )
        
        # Check dependencies
        if dependencies:
            for dep_id in dependencies:
                if dep_id not in self.completed_tasks:
                    self.task_dependencies[task_id].add(dep_id)
                    self.dependency_graph[dep_id].add(task_id)
        
        # Add to queue
        heapq.heappush(self.task_queue, scheduled_task)
        self.metrics['tasks_scheduled'] += 1
        
        self.logger.info(f"Scheduled task {task_id} with priority {priority.value}")
        return True
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled or executing task"""
        # Check if task is in queue
        for i, task in enumerate(self.task_queue):
            if task.task_id == task_id:
                task.state = TaskExecutionState.CANCELLED
                self.task_queue.pop(i)
                heapq.heapify(self.task_queue)
                self.logger.info(f"Cancelled queued task {task_id}")
                return True
        
        # Check if task is executing
        if task_id in self.executing_tasks:
            task = self.executing_tasks[task_id]
            task.state = TaskExecutionState.CANCELLED
            
            # Remove from agent assignment
            if task_id in self.agent_assignments:
                agent_id = self.agent_assignments[task_id]
                if agent_id in self.agents:
                    self.agents[agent_id].current_tasks.discard(task_id)
                    self.agents[agent_id].current_load -= 1
                del self.agent_assignments[task_id]
            
            del self.executing_tasks[task_id]
            self.logger.info(f"Cancelled executing task {task_id}")
            return True
        
        return False
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                await self._schedule_pending_tasks()
                await self._check_completed_tasks()
                await self._handle_failed_tasks()
                await self._update_metrics()
                
                await asyncio.sleep(self.scheduler_interval)
                
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _schedule_pending_tasks(self):
        """Schedule pending tasks based on current mode"""
        if not self.task_queue:
            return
        
        available_agents = self._get_available_agents()
        if not available_agents:
            return
        
        # Get ready tasks (no pending dependencies)
        ready_tasks = []
        while self.task_queue and len(ready_tasks) < len(available_agents):
            task = heapq.heappop(self.task_queue)
            
            if self._are_dependencies_satisfied(task):
                ready_tasks.append(task)
            else:
                # Put back in queue
                heapq.heappush(self.task_queue, task)
                break
        
        # Schedule tasks based on mode
        if self.mode == SchedulerMode.SMART:
            await self._smart_schedule(ready_tasks, available_agents)
        elif self.mode == SchedulerMode.LOAD_BALANCED:
            await self._load_balanced_schedule(ready_tasks, available_agents)
        elif self.mode == SchedulerMode.PRIORITY:
            await self._priority_schedule(ready_tasks, available_agents)
        elif self.mode == SchedulerMode.DEADLINE:
            await self._deadline_schedule(ready_tasks, available_agents)
        else:  # FIFO
            await self._fifo_schedule(ready_tasks, available_agents)
    
    async def _smart_schedule(self, tasks: List[ScheduledTask], agents: List[AgentResource]):
        """AI-powered intelligent scheduling"""
        for task in tasks:
            if not agents:
                break
            
            # Calculate agent scores for this task
            agent_scores = []
            for agent in agents:
                score = self._calculate_agent_task_score(agent, task)
                agent_scores.append((score, agent))
            
            # Sort by score (highest first)
            agent_scores.sort(reverse=True)
            
            # Assign to best agent
            best_agent = agent_scores[0][1]
            await self._assign_task_to_agent(task, best_agent)
            agents.remove(best_agent)
    
    async def _load_balanced_schedule(self, tasks: List[ScheduledTask], agents: List[AgentResource]):
        """Load-balanced scheduling"""
        # Sort agents by current load (lowest first)
        agents.sort(key=lambda a: a.utilization_rate)
        
        for task, agent in zip(tasks, agents):
            await self._assign_task_to_agent(task, agent)
    
    async def _priority_schedule(self, tasks: List[ScheduledTask], agents: List[AgentResource]):
        """Priority-based scheduling"""
        # Tasks are already sorted by priority in the heap
        for task, agent in zip(tasks, agents):
            await self._assign_task_to_agent(task, agent)
    
    async def _deadline_schedule(self, tasks: List[ScheduledTask], agents: List[AgentResource]):
        """Deadline-aware scheduling"""
        # Sort tasks by deadline (earliest first)
        tasks_with_deadlines = [t for t in tasks if t.deadline]
        tasks_without_deadlines = [t for t in tasks if not t.deadline]
        
        tasks_with_deadlines.sort(key=lambda t: t.deadline)
        all_tasks = tasks_with_deadlines + tasks_without_deadlines
        
        for task, agent in zip(all_tasks, agents):
            await self._assign_task_to_agent(task, agent)
    
    async def _fifo_schedule(self, tasks: List[ScheduledTask], agents: List[AgentResource]):
        """First In, First Out scheduling"""
        # Sort by scheduled time
        tasks.sort(key=lambda t: t.scheduled_time)
        
        for task, agent in zip(tasks, agents):
            await self._assign_task_to_agent(task, agent)
    
    def _calculate_agent_task_score(self, agent: AgentResource, task: ScheduledTask) -> float:
        """Calculate how well an agent matches a task"""
        score = 0.0
        
        # Agent type match
        if task.agent_requirements:
            if agent.agent_type in task.agent_requirements:
                score += 10.0
            else:
                return 0.0  # Agent can't handle this task
        else:
            score += 5.0  # Default match
        
        # Performance score
        score += agent.performance_score * 3.0
        
        # Load factor (prefer less loaded agents)
        load_penalty = agent.utilization_rate * 2.0
        score -= load_penalty
        
        # Specialization match
        task_keywords = self._extract_task_keywords(task)
        for keyword in task_keywords:
            if keyword in agent.specialization_score:
                score += agent.specialization_score[keyword] * 2.0
        
        # Deadline urgency
        if task.deadline:
            time_to_deadline = (task.deadline - datetime.utcnow()).total_seconds() / 3600  # hours
            if time_to_deadline < 2:  # Less than 2 hours
                score += 5.0
            elif time_to_deadline < 24:  # Less than 24 hours
                score += 2.0
        
        return max(0.0, score)
    
    def _extract_task_keywords(self, task: ScheduledTask) -> List[str]:
        """Extract keywords from task metadata for specialization matching"""
        keywords = []
        
        if 'description' in task.metadata:
            description = task.metadata['description'].lower()
            # Simple keyword extraction
            if 'react' in description or 'frontend' in description:
                keywords.append('frontend')
            if 'api' in description or 'backend' in description:
                keywords.append('backend')
            if 'design' in description or 'ui' in description or 'ux' in description:
                keywords.append('design')
            if 'test' in description or 'qa' in description:
                keywords.append('testing')
            if 'product' in description or 'requirement' in description:
                keywords.append('product')
        
        return keywords
    
    async def _assign_task_to_agent(self, task: ScheduledTask, agent: AgentResource):
        """Assign a task to an agent and start execution"""
        task.state = TaskExecutionState.EXECUTING
        
        # Update agent state
        agent.current_tasks.add(task.task_id)
        agent.current_load += 1
        
        # Record assignment
        self.agent_assignments[task.task_id] = agent.agent_id
        self.executing_tasks[task.task_id] = task
        
        self.logger.info(f"Assigned task {task.task_id} to agent {agent.agent_id}")
        
        # Start task execution
        asyncio.create_task(self._execute_task(task, agent))
        
        # Call callbacks
        for callback in self.task_started_callbacks:
            try:
                await callback(task.task_id, agent.agent_id)
            except Exception as e:
                self.logger.error(f"Task started callback error: {e}")
    
    async def _execute_task(self, task: ScheduledTask, agent: AgentResource):
        """Execute a task with the assigned agent"""
        start_time = time.time()
        
        try:
            # This would be replaced with actual agent execution
            # For now, simulate task execution
            execution_time = task.estimated_duration or 5  # minutes
            await asyncio.sleep(execution_time * 60)  # Convert to seconds for simulation
            
            # Mark as completed
            task.state = TaskExecutionState.COMPLETED
            execution_duration = time.time() - start_time
            
            # Update agent state
            agent.current_tasks.discard(task.task_id)
            agent.current_load -= 1
            agent.last_task_completion = datetime.utcnow()
            
            # Move to completed
            self.completed_tasks[task.task_id] = task
            if task.task_id in self.executing_tasks:
                del self.executing_tasks[task.task_id]
            
            # Update metrics
            self.metrics['tasks_completed'] += 1
            
            # Process dependent tasks
            await self._process_dependent_tasks(task.task_id)
            
            self.logger.info(f"Task {task.task_id} completed in {execution_duration:.2f}s")
            
            # Call callbacks
            for callback in self.task_completed_callbacks:
                try:
                    await callback(task.task_id, agent.agent_id, execution_duration)
                except Exception as e:
                    self.logger.error(f"Task completed callback error: {e}")
        
        except Exception as e:
            # Handle task failure
            task.state = TaskExecutionState.FAILED
            task.retry_count += 1
            
            # Update agent state
            agent.current_tasks.discard(task.task_id)
            agent.current_load -= 1
            
            # Move to failed or retry
            if task.retry_count < task.max_retries:
                task.state = TaskExecutionState.RETRYING
                heapq.heappush(self.task_queue, task)
                self.logger.warning(f"Task {task.task_id} failed, retrying ({task.retry_count}/{task.max_retries})")
            else:
                self.failed_tasks[task.task_id] = task
                self.metrics['tasks_failed'] += 1
                self.logger.error(f"Task {task.task_id} failed permanently: {e}")
            
            if task.task_id in self.executing_tasks:
                del self.executing_tasks[task.task_id]
            
            # Call callbacks
            for callback in self.task_failed_callbacks:
                try:
                    await callback(task.task_id, agent.agent_id, str(e))
                except Exception as e:
                    self.logger.error(f"Task failed callback error: {e}")
    
    async def _process_dependent_tasks(self, completed_task_id: str):
        """Process tasks that were waiting for this task to complete"""
        if completed_task_id in self.dependency_graph:
            dependent_tasks = self.dependency_graph[completed_task_id]
            
            for dependent_task_id in dependent_tasks:
                if dependent_task_id in self.task_dependencies:
                    self.task_dependencies[dependent_task_id].discard(completed_task_id)
            
            del self.dependency_graph[completed_task_id]
    
    def _are_dependencies_satisfied(self, task: ScheduledTask) -> bool:
        """Check if all task dependencies are satisfied"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        
        return True
    
    def _get_available_agents(self) -> List[AgentResource]:
        """Get list of available agents"""
        return [agent for agent in self.agents.values() if agent.is_available]
    
    async def _check_completed_tasks(self):
        """Check for completed tasks and clean up"""
        # This is handled in _execute_task, but could be used for additional cleanup
        pass
    
    async def _handle_failed_tasks(self):
        """Handle failed tasks and retry logic"""
        # This is handled in _execute_task, but could be used for additional failure handling
        pass
    
    async def _update_metrics(self):
        """Update scheduler metrics"""
        # Update agent utilization
        for agent_id, agent in self.agents.items():
            self.metrics['agent_utilization'][agent_id] = agent.utilization_rate
        
        # Calculate throughput (tasks per minute)
        if hasattr(self, '_last_metrics_update'):
            time_diff = time.time() - self._last_metrics_update
            if time_diff > 0:
                completed_diff = self.metrics['tasks_completed'] - getattr(self, '_last_completed_count', 0)
                self.metrics['throughput'] = (completed_diff / time_diff) * 60  # per minute
        
        self._last_metrics_update = time.time()
        self._last_completed_count = self.metrics['tasks_completed']
    
    async def _reassign_task(self, task_id: str):
        """Reassign a task to a different agent"""
        if task_id in self.executing_tasks:
            task = self.executing_tasks[task_id]
            
            # Remove from current agent
            if task_id in self.agent_assignments:
                agent_id = self.agent_assignments[task_id]
                if agent_id in self.agents:
                    self.agents[agent_id].current_tasks.discard(task_id)
                    self.agents[agent_id].current_load -= 1
                del self.agent_assignments[task_id]
            
            # Put back in queue
            task.state = TaskExecutionState.QUEUED
            del self.executing_tasks[task_id]
            heapq.heappush(self.task_queue, task)
            
            self.logger.info(f"Reassigned task {task_id}")
    
    # Callback registration methods
    def on_task_started(self, callback: Callable[[str, str], None]):
        """Register callback for task started events"""
        self.task_started_callbacks.append(callback)
    
    def on_task_completed(self, callback: Callable[[str, str, float], None]):
        """Register callback for task completed events"""
        self.task_completed_callbacks.append(callback)
    
    def on_task_failed(self, callback: Callable[[str, str, str], None]):
        """Register callback for task failed events"""
        self.task_failed_callbacks.append(callback)
    
    # Status and monitoring methods
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'mode': self.mode.value,
            'is_running': self.is_running,
            'queue_size': len(self.task_queue),
            'executing_tasks': len(self.executing_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'registered_agents': len(self.agents),
            'available_agents': len(self._get_available_agents()),
            'metrics': self.metrics
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        return {
            'agent_id': agent.agent_id,
            'agent_type': agent.agent_type.value,
            'current_load': agent.current_load,
            'max_capacity': agent.max_capacity,
            'utilization_rate': agent.utilization_rate,
            'is_available': agent.is_available,
            'current_tasks': list(agent.current_tasks),
            'performance_score': agent.performance_score,
            'last_task_completion': agent.last_task_completion.isoformat() if agent.last_task_completion else None
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        # Check all task collections
        for tasks_dict in [self.executing_tasks, self.completed_tasks, self.failed_tasks]:
            if task_id in tasks_dict:
                task = tasks_dict[task_id]
                return {
                    'task_id': task.task_id,
                    'state': task.state.value,
                    'priority': task.priority,
                    'scheduled_time': task.scheduled_time.isoformat(),
                    'deadline': task.deadline.isoformat() if task.deadline else None,
                    'retry_count': task.retry_count,
                    'assigned_agent': self.agent_assignments.get(task_id),
                    'dependencies': list(task.dependencies),
                    'metadata': task.metadata
                }
        
        # Check queue
        for task in self.task_queue:
            if task.task_id == task_id:
                return {
                    'task_id': task.task_id,
                    'state': task.state.value,
                    'priority': task.priority,
                    'scheduled_time': task.scheduled_time.isoformat(),
                    'deadline': task.deadline.isoformat() if task.deadline else None,
                    'retry_count': task.retry_count,
                    'assigned_agent': None,
                    'dependencies': list(task.dependencies),
                    'metadata': task.metadata
                }
        
        return None
    
    async def set_mode(self, mode: SchedulerMode):
        """Change scheduler mode"""
        old_mode = self.mode
        self.mode = mode
        self.logger.info(f"Scheduler mode changed from {old_mode.value} to {mode.value}")
    
    async def adjust_agent_capacity(self, agent_id: str, new_capacity: int):
        """Adjust an agent's capacity"""
        if agent_id in self.agents:
            old_capacity = self.agents[agent_id].max_capacity
            self.agents[agent_id].max_capacity = new_capacity
            self.logger.info(f"Agent {agent_id} capacity changed from {old_capacity} to {new_capacity}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed scheduler metrics"""
        return {
            **self.metrics,
            'queue_depth': len(self.task_queue),
            'active_tasks': len(self.executing_tasks),
            'total_agents': len(self.agents),
            'available_agents': len(self._get_available_agents()),
            'scheduler_mode': self.mode.value,
            'uptime': time.time() - getattr(self, '_start_time', time.time())
        }
