# VirtuAI Office - Background Task Processing Service
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue
import threading
import time
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.logging import get_logger, log_error_with_context
from ..models.database import Task, Agent, TaskStatus, TaskPriority
from ..agents.agent_manager import AgentManager
from ..services.websocket_manager import WebSocketManager
from ..services.apple_silicon_optimizer import AppleSiliconOptimizer


class TaskQueuePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class BackgroundTask:
    id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskQueuePriority = TaskQueuePriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    timeout_seconds: int = 300  # 5 minutes default timeout
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


class BackgroundTaskProcessor:
    """Handles background task processing for VirtuAI Office"""
    
    def __init__(self,
                 db_session_factory: Callable[[], Session],
                 agent_manager: AgentManager,
                 websocket_manager: WebSocketManager,
                 apple_silicon_optimizer: Optional[AppleSiliconOptimizer] = None,
                 max_workers: int = 4,
                 max_concurrent_ai_tasks: int = 2):
        
        self.db_session_factory = db_session_factory
        self.agent_manager = agent_manager
        self.websocket_manager = websocket_manager
        self.apple_silicon_optimizer = apple_silicon_optimizer
        self.max_workers = max_workers
        self.max_concurrent_ai_tasks = max_concurrent_ai_tasks
        
        # Task queues by priority
        self.task_queues: Dict[TaskQueuePriority, queue.PriorityQueue] = {
            priority: queue.PriorityQueue() for priority in TaskQueuePriority
        }
        
        # Active tasks tracking
        self.active_tasks: Dict[str, BackgroundTask] = {}
        self.active_ai_tasks = 0
        self.task_lock = threading.Lock()
        
        # Worker threads
        self.workers: List[threading.Thread] = []
        self.running = False
        
        # Task handlers registry
        self.task_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
        
        # Performance tracking
        self.task_stats = {
            'completed': 0,
            'failed': 0,
            'retried': 0,
            'total_processing_time': 0.0
        }
        
        self.logger = get_logger('virtuai.background_tasks')
    
    def _register_default_handlers(self):
        """Register default task handlers"""
        self.task_handlers.update({
            'process_ai_task': self._handle_ai_task_processing,
            'send_notification': self._handle_notification,
            'cleanup_completed_tasks': self._handle_cleanup,
            'generate_standup_report': self._handle_standup_generation,
            'optimize_system_performance': self._handle_performance_optimization,
            'download_ai_model': self._handle_model_download,
            'benchmark_performance': self._handle_performance_benchmark,
            'backup_database': self._handle_database_backup,
            'update_agent_performance': self._handle_agent_performance_update,
            'process_collaboration_workflow': self._handle_collaboration_workflow
        })
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a custom task handler"""
        self.task_handlers[task_type] = handler
        self.logger.info(f"Registered handler for task type: {task_type}")
    
    def start(self):
        """Start the background task processor"""
        if self.running:
            self.logger.warning("Background task processor is already running")
            return
        
        self.running = True
        self.logger.info(f"Starting background task processor with {self.max_workers} workers")
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"BackgroundWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        # Start scheduler thread
        scheduler = threading.Thread(
            target=self._scheduler_loop,
            name="TaskScheduler",
            daemon=True
        )
        scheduler.start()
        self.workers.append(scheduler)
        
        self.logger.info("Background task processor started successfully")
    
    def stop(self):
        """Stop the background task processor"""
        if not self.running:
            return
        
        self.logger.info("Stopping background task processor...")
        self.running = False
        
        # Wait for workers to finish current tasks
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=10)
        
        self.workers.clear()
        self.logger.info("Background task processor stopped")
    
    def add_task(self,
                 task_type: str,
                 payload: Dict[str, Any],
                 priority: TaskQueuePriority = TaskQueuePriority.NORMAL,
                 scheduled_at: Optional[datetime] = None,
                 timeout_seconds: int = 300,
                 max_retries: int = 3) -> str:
        """Add a task to the background queue"""
        
        task = BackgroundTask(
            id=str(uuid.uuid4()),
            task_type=task_type,
            payload=payload,
            priority=priority,
            scheduled_at=scheduled_at,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries
        )
        
        if scheduled_at and scheduled_at > datetime.utcnow():
            # Scheduled task - will be picked up by scheduler
            with self.task_lock:
                self.active_tasks[task.id] = task
        else:
            # Immediate task
            self.task_queues[priority].put((time.time(), task))
        
        self.logger.info(f"Added background task: {task_type} (ID: {task.id}, Priority: {priority.name})")
        return task.id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a background task"""
        with self.task_lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return {
                    'id': task.id,
                    'type': task.task_type,
                    'status': 'running',
                    'retry_count': task.retry_count,
                    'created_at': task.created_at.isoformat(),
                    'scheduled_at': task.scheduled_at.isoformat() if task.scheduled_at else None
                }
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a background task"""
        with self.task_lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                self.logger.info(f"Cancelled background task: {task_id}")
                return True
        return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get background task queue statistics"""
        stats = {
            'queues': {},
            'active_tasks': len(self.active_tasks),
            'active_ai_tasks': self.active_ai_tasks,
            'workers': len(self.workers),
            'running': self.running,
            'performance': self.task_stats.copy()
        }
        
        for priority, task_queue in self.task_queues.items():
            stats['queues'][priority.name] = task_queue.qsize()
        
        return stats
    
    def _worker_loop(self):
        """Main worker loop for processing tasks"""
        self.logger.info(f"Worker {threading.current_thread().name} started")
        
        while self.running:
            try:
                task = self._get_next_task()
                if task:
                    self._process_task(task)
                else:
                    # No tasks available, sleep briefly
                    time.sleep(0.1)
            except Exception as e:
                log_error_with_context(
                    'virtuai.background_tasks',
                    e,
                    {'worker': threading.current_thread().name}
                )
                time.sleep(1)  # Prevent tight error loops
        
        self.logger.info(f"Worker {threading.current_thread().name} stopped")
    
    def _scheduler_loop(self):
        """Scheduler loop for handling delayed tasks"""
        self.logger.info("Task scheduler started")
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                scheduled_tasks = []
                
                with self.task_lock:
                    for task_id, task in list(self.active_tasks.items()):
                        if (task.scheduled_at and
                            task.scheduled_at <= current_time):
                            scheduled_tasks.append(task)
                            del self.active_tasks[task_id]
                
                # Add scheduled tasks to appropriate queues
                for task in scheduled_tasks:
                    self.task_queues[task.priority].put((time.time(), task))
                    self.logger.info(f"Scheduled task ready: {task.task_type} (ID: {task.id})")
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                log_error_with_context('virtuai.background_tasks', e, {'component': 'scheduler'})
                time.sleep(5)
        
        self.logger.info("Task scheduler stopped")
    
    def _get_next_task(self) -> Optional[BackgroundTask]:
        """Get the next task from queues (highest priority first)"""
        # Check queues in priority order
        for priority in reversed(list(TaskQueuePriority)):
            task_queue = self.task_queues[priority]
            try:
                # Non-blocking get with timeout
                _, task = task_queue.get(timeout=0.1)
                
                # Check if we can process AI tasks
                if task.task_type == 'process_ai_task':
                    with self.task_lock:
                        if self.active_ai_tasks >= self.max_concurrent_ai_tasks:
                            # Put task back and try later
                            task_queue.put((time.time(), task))
                            continue
                        self.active_ai_tasks += 1
                
                with self.task_lock:
                    self.active_tasks[task.id] = task
                
                return task
                
            except queue.Empty:
                continue
        
        return None
    
    def _process_task(self, task: BackgroundTask):
        """Process a single background task"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing task: {task.task_type} (ID: {task.id})")
            
            # Get handler for task type
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Execute task with timeout
            try:
                if asyncio.iscoroutinefunction(handler):
                    # Async handler
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            asyncio.wait_for(handler(task), timeout=task.timeout_seconds)
                        )
                    finally:
                        loop.close()
                else:
                    # Sync handler
                    result = handler(task)
                
                # Task completed successfully
                processing_time = time.time() - start_time
                self.task_stats['completed'] += 1
                self.task_stats['total_processing_time'] += processing_time
                
                self.logger.info(
                    f"Task completed: {task.task_type} (ID: {task.id}) in {processing_time:.2f}s"
                )
                
            except asyncio.TimeoutError:
                raise TimeoutError(f"Task timed out after {task.timeout_seconds} seconds")
            
        except Exception as e:
            self._handle_task_failure(task, e)
        
        finally:
            # Clean up
            with self.task_lock:
                if task.id in self.active_tasks:
                    del self.active_tasks[task.id]
                
                if task.task_type == 'process_ai_task':
                    self.active_ai_tasks = max(0, self.active_ai_tasks - 1)
    
    def _handle_task_failure(self, task: BackgroundTask, error: Exception):
        """Handle task failure and retry logic"""
        self.logger.error(f"Task failed: {task.task_type} (ID: {task.id}) - {str(error)}")
        
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # Retry task with exponential backoff
            delay_seconds = min(300, 2 ** task.retry_count)  # Max 5 minutes
            retry_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
            
            task.scheduled_at = retry_time
            
            with self.task_lock:
                self.active_tasks[task.id] = task
            
            self.task_stats['retried'] += 1
            self.logger.info(
                f"Retrying task: {task.task_type} (ID: {task.id}) in {delay_seconds} seconds "
                f"(attempt {task.retry_count}/{task.max_retries})"
            )
        else:
            # Max retries exceeded
            self.task_stats['failed'] += 1
            self.logger.error(
                f"Task permanently failed: {task.task_type} (ID: {task.id}) "
                f"after {task.retry_count} attempts"
            )
            
            # Notify about permanent failure
            asyncio.create_task(self._notify_task_failure(task, error))
    
    async def _notify_task_failure(self, task: BackgroundTask, error: Exception):
        """Notify about permanent task failure"""
        await self.websocket_manager.broadcast({
            'type': 'background_task_failed',
            'task_id': task.id,
            'task_type': task.task_type,
            'error': str(error),
            'retry_count': task.retry_count
        })
    
    # Task Handlers
    
    async def _handle_ai_task_processing(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle AI task processing"""
        task_id = task.payload.get('task_id')
        if not task_id:
            raise ValueError("Missing task_id in payload")
        
        db = self.db_session_factory()
        try:
            # Get task from database
            db_task = db.query(Task).filter(Task.id == task_id).first()
            if not db_task:
                raise ValueError(f"Task {task_id} not found in database")
            
            # Update task status
            db_task.status = TaskStatus.IN_PROGRESS
            db_task.started_at = datetime.utcnow()
            db.commit()
            
            # Notify status change
            await self.websocket_manager.broadcast({
                'type': 'task_update',
                'task_id': task_id,
                'status': 'in_progress'
            })
            
            # Get optimal agent
            agent = None
            if db_task.agent_id:
                agent_db = db.query(Agent).filter(Agent.id == db_task.agent_id).first()
                if agent_db:
                    agent = self.agent_manager.get_agent(agent_db.type)
            
            if not agent:
                # Auto-assign agent
                agent = self.agent_manager.find_best_agent(db_task.description)
                if agent:
                    # Find or create agent in database
                    agent_db = db.query(Agent).filter(Agent.type == agent.type).first()
                    if not agent_db:
                        agent_db = Agent(
                            name=agent.name,
                            type=agent.type,
                            description=agent.description,
                            expertise=json.dumps(agent.expertise)
                        )
                        db.add(agent_db)
                        db.commit()
                    
                    db_task.agent_id = agent_db.id
                    db.commit()
            
            if not agent:
                raise ValueError("No suitable agent found for task")
            
            # Optimize model selection for Apple Silicon
            if self.apple_silicon_optimizer:
                optimal_model = await self.apple_silicon_optimizer.auto_select_model(
                    task.payload.get('complexity', 'medium')
                )
                agent.model = optimal_model
            
            # Process task with agent
            self.logger.info(f"Processing task {task_id} with agent {agent.name}")
            output = await agent.process_task(db_task)
            
            # Update task with results
            db_task.output = output
            db_task.status = TaskStatus.COMPLETED
            db_task.completed_at = datetime.utcnow()
            
            # Calculate effort
            if db_task.started_at and db_task.completed_at:
                duration = (db_task.completed_at - db_task.started_at).total_seconds() / 3600
                db_task.actual_effort = max(1, int(duration))
            
            db.commit()
            
            # Notify completion
            await self.websocket_manager.broadcast({
                'type': 'task_completed',
                'task_id': task_id,
                'agent_name': agent.name,
                'output_preview': output[:200] + "..." if len(output) > 200 else output
            })
            
            return {
                'task_id': task_id,
                'status': 'completed',
                'agent': agent.name,
                'output_length': len(output)
            }
            
        finally:
            db.close()
    
    async def _handle_notification(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle notification sending"""
        notification_data = task.payload
        await self.websocket_manager.broadcast(notification_data)
        return {'status': 'sent', 'type': notification_data.get('type')}
    
    def _handle_cleanup(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle cleanup of completed tasks"""
        days_old = task.payload.get('days_old', 30)
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        db = self.db_session_factory()
        try:
            # Delete old completed tasks
            deleted_count = db.query(Task).filter(
                and_(
                    Task.status == TaskStatus.COMPLETED,
                    Task.completed_at < cutoff_date
                )
            ).delete()
            
            db.commit()
            
            self.logger.info(f"Cleaned up {deleted_count} old completed tasks")
            return {'deleted_count': deleted_count}
            
        finally:
            db.close()
    
    async def _handle_standup_generation(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle daily standup report generation"""
        db = self.db_session_factory()
        try:
            # Generate standup using Boss AI
            from ..services.boss_ai import BossAI
            boss_ai = BossAI(self.agent_manager)
            
            standup_data = await boss_ai.conduct_daily_standup(db)
            
            # Broadcast standup report
            await self.websocket_manager.broadcast({
                'type': 'standup_generated',
                'data': standup_data
            })
            
            return standup_data
            
        finally:
            db.close()
    
    async def _handle_performance_optimization(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle system performance optimization"""
        if not self.apple_silicon_optimizer:
            return {'status': 'skipped', 'reason': 'Apple Silicon optimizer not available'}
        
        optimization_results = await self.apple_silicon_optimizer.optimize_system()
        
        await self.websocket_manager.broadcast({
            'type': 'system_optimized',
            'results': optimization_results
        })
        
        return optimization_results
    
    async def _handle_model_download(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle AI model download"""
        model_name = task.payload.get('model_name')
        if not model_name:
            raise ValueError("Missing model_name in payload")
        
        # Download model using ollama
        import ollama
        
        try:
            self.logger.info(f"Starting download of model: {model_name}")
            ollama.pull(model_name)
            
            await self.websocket_manager.broadcast({
                'type': 'model_downloaded',
                'model_name': model_name
            })
            
            self.logger.info(f"Successfully downloaded model: {model_name}")
            return {'status': 'completed', 'model_name': model_name}
            
        except Exception as e:
            self.logger.error(f"Failed to download model {model_name}: {e}")
            raise
    
    async def _handle_performance_benchmark(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle performance benchmarking"""
        if not self.apple_silicon_optimizer:
            return {'status': 'skipped', 'reason': 'Apple Silicon optimizer not available'}
        
        db = self.db_session_factory()
        try:
            benchmark_results = await self.apple_silicon_optimizer.benchmark_performance(db)
            
            await self.websocket_manager.broadcast({
                'type': 'benchmark_completed',
                'results': benchmark_results
            })
            
            return benchmark_results
            
        finally:
            db.close()
    
    def _handle_database_backup(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle database backup"""
        backup_path = task.payload.get('backup_path', 'backups/')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Simple SQLite backup implementation
        import shutil
        import os
        
        try:
            source_db = task.payload.get('database_path', 'virtuai_office.db')
            if os.path.exists(source_db):
                os.makedirs(backup_path, exist_ok=True)
                backup_file = os.path.join(backup_path, f'backup_{timestamp}.db')
                shutil.copy2(source_db, backup_file)
                
                self.logger.info(f"Database backup created: {backup_file}")
                return {'status': 'completed', 'backup_file': backup_file}
            else:
                return {'status': 'skipped', 'reason': 'Database file not found'}
                
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            raise
    
    async def _handle_agent_performance_update(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle agent performance metrics update"""
        agent_id = task.payload.get('agent_id')
        if not agent_id:
            raise ValueError("Missing agent_id in payload")
        
        db = self.db_session_factory()
        try:
            # Update agent performance metrics
            from ..services.performance_analytics import PerformanceAnalytics
            analytics = PerformanceAnalytics()
            
            completed_tasks = db.query(Task).filter(
                and_(
                    Task.agent_id == agent_id,
                    Task.status == TaskStatus.COMPLETED,
                    Task.completed_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).all()
            
            performance_data = analytics.analyze_agent_performance(agent_id, completed_tasks, db)
            
            return {
                'agent_id': agent_id,
                'performance': performance_data,
                'tasks_analyzed': len(completed_tasks)
            }
            
        finally:
            db.close()
    
    async def _handle_collaboration_workflow(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle multi-agent collaboration workflow"""
        workflow_id = task.payload.get('workflow_id')
        primary_task_id = task.payload.get('primary_task_id')
        
        if not workflow_id or not primary_task_id:
            raise ValueError("Missing workflow_id or primary_task_id in payload")
        
        db = self.db_session_factory()
        try:
            # Execute collaboration workflow
            from ..services.collaboration_manager import AgentCollaborationManager
            collaboration_manager = AgentCollaborationManager(self.agent_manager)
            
            primary_task = db.query(Task).filter(Task.id == primary_task_id).first()
            if not primary_task:
                raise ValueError(f"Primary task {primary_task_id} not found")
            
            # This would be implemented based on the collaboration plan
            result = await collaboration_manager.execute_workflow(workflow_id, primary_task, db)
            
            return {
                'workflow_id': workflow_id,
                'primary_task_id': primary_task_id,
                'status': 'completed',
                'result': result
            }
            
        finally:
            db.close()


# Convenience functions for common background tasks

def queue_ai_task_processing(processor: BackgroundTaskProcessor,
                           task_id: str,
                           priority: TaskQueuePriority = TaskQueuePriority.NORMAL) -> str:
    """Queue an AI task for processing"""
    return processor.add_task(
        task_type='process_ai_task',
        payload={'task_id': task_id},
        priority=priority
    )


def queue_notification(processor: BackgroundTaskProcessor,
                      notification_data: Dict[str, Any]) -> str:
    """Queue a notification for sending"""
    return processor.add_task(
        task_type='send_notification',
        payload=notification_data,
        priority=TaskQueuePriority.HIGH
    )


def queue_cleanup_tasks(processor: BackgroundTaskProcessor,
                       days_old: int = 30) -> str:
    """Queue cleanup of old completed tasks"""
    return processor.add_task(
        task_type='cleanup_completed_tasks',
        payload={'days_old': days_old},
        priority=TaskQueuePriority.LOW,
        scheduled_at=datetime.utcnow() + timedelta(hours=24)  # Run daily
    )


def queue_standup_generation(processor: BackgroundTaskProcessor) -> str:
    """Queue daily standup report generation"""
    return processor.add_task(
        task_type='generate_standup_report',
        payload={},
        priority=TaskQueuePriority.NORMAL
    )


def queue_model_download(processor: BackgroundTaskProcessor,
                        model_name: str) -> str:
    """Queue AI model download"""
    return processor.add_task(
        task_type='download_ai_model',
        payload={'model_name': model_name},
        priority=TaskQueuePriority.NORMAL,
        timeout_seconds=1800  # 30 minutes for model download
    )
