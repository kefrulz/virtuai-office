# VirtuAI Office - Advanced Workflow Orchestration System
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod

from ..core.logging import get_logger, log_error_with_context
from ..models.database import Task, Agent, TaskStatus, TaskPriority


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    WAITING = "waiting"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowTrigger(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    DEPENDENCY_COMPLETE = "dependency_complete"


@dataclass
class WorkflowStep:
    id: str
    name: str
    agent_type: str
    task_description: str
    depends_on: List[str] = field(default_factory=list)
    timeout_minutes: int = 30
    retry_count: int = 3
    status: StepStatus = StepStatus.WAITING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    trigger: WorkflowTrigger = WorkflowTrigger.MANUAL
    schedule: Optional[str] = None  # Cron expression for scheduled workflows
    timeout_minutes: int = 120
    max_retries: int = 1
    tags: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: Optional[str] = None
    error: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)


class WorkflowCondition(ABC):
    """Abstract base class for workflow conditions"""
    
    @abstractmethod
    async def evaluate(self, context: Dict[str, Any]) -> bool:
        pass


class SimpleCondition(WorkflowCondition):
    """Simple condition based on context values"""
    
    def __init__(self, key: str, operator: str, value: Any):
        self.key = key
        self.operator = operator
        self.value = value
    
    async def evaluate(self, context: Dict[str, Any]) -> bool:
        ctx_value = context.get(self.key)
        
        if self.operator == "==":
            return ctx_value == self.value
        elif self.operator == "!=":
            return ctx_value != self.value
        elif self.operator == ">":
            return ctx_value > self.value
        elif self.operator == "<":
            return ctx_value < self.value
        elif self.operator == ">=":
            return ctx_value >= self.value
        elif self.operator == "<=":
            return ctx_value <= self.value
        elif self.operator == "in":
            return ctx_value in self.value
        elif self.operator == "contains":
            return self.value in str(ctx_value)
        else:
            return False


class ConditionalStep(WorkflowStep):
    """Workflow step that only executes if condition is met"""
    
    def __init__(self, condition: WorkflowCondition, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.condition = condition


class ParallelStepGroup:
    """Group of steps that can execute in parallel"""
    
    def __init__(self, steps: List[WorkflowStep], wait_for_all: bool = True):
        self.steps = steps
        self.wait_for_all = wait_for_all  # If False, continues when first step completes


class WorkflowEngine:
    """Advanced workflow orchestration engine"""
    
    def __init__(self, agent_manager, task_processor):
        self.agent_manager = agent_manager
        self.task_processor = task_processor
        self.logger = get_logger('virtuai.workflow')
        
        # Workflow storage
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.running_executions: Set[str] = set()
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Scheduled workflows
        self.scheduler_running = False
        self.scheduler_task = None
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a workflow definition"""
        self.workflows[workflow.id] = workflow
        self.logger.info(f"Registered workflow: {workflow.name} ({workflow.id})")
    
    def unregister_workflow(self, workflow_id: str):
        """Unregister a workflow definition"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            self.logger.info(f"Unregistered workflow: {workflow_id}")
    
    async def execute_workflow(self, workflow_id: str,
                             trigger_context: Dict[str, Any] = None) -> str:
        """Execute a workflow and return execution ID"""
        
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        execution_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            started_at=datetime.utcnow(),
            context=trigger_context or {}
        )
        
        self.executions[execution_id] = execution
        self.running_executions.add(execution_id)
        
        self.logger.info(f"Starting workflow execution: {workflow.name} ({execution_id})")
        
        # Start execution in background
        asyncio.create_task(self._execute_workflow_steps(execution, workflow))
        
        return execution_id
    
    async def _execute_workflow_steps(self, execution: WorkflowExecution,
                                    workflow: WorkflowDefinition):
        """Execute workflow steps with dependency management"""
        
        try:
            execution.status = WorkflowStatus.RUNNING
            
            # Create execution graph
            step_graph = self._build_dependency_graph(workflow.steps)
            completed_steps = set()
            failed_steps = set()
            
            while len(completed_steps) + len(failed_steps) < len(workflow.steps):
                # Find ready steps
                ready_steps = []
                
                for step in workflow.steps:
                    if step.id in completed_steps or step.id in failed_steps:
                        continue
                    
                    if step.status in [StepStatus.RUNNING]:
                        continue
                    
                    # Check dependencies
                    dependencies_met = all(
                        dep_id in completed_steps for dep_id in step.depends_on
                    )
                    
                    if dependencies_met:
                        # Check conditional steps
                        if isinstance(step, ConditionalStep):
                            if not await step.condition.evaluate(execution.context):
                                step.status = StepStatus.SKIPPED
                                completed_steps.add(step.id)
                                continue
                        
                        ready_steps.append(step)
                
                if not ready_steps:
                    # Check if we're waiting for running steps
                    running_steps = [s for s in workflow.steps
                                   if s.status == StepStatus.RUNNING]
                    
                    if not running_steps:
                        # Deadlock or completion
                        break
                    
                    # Wait for running steps
                    await asyncio.sleep(1)
                    continue
                
                # Execute ready steps
                for step in ready_steps:
                    if isinstance(step, ParallelStepGroup):
                        await self._execute_parallel_group(step, execution, workflow)
                    else:
                        asyncio.create_task(
                            self._execute_step(step, execution, workflow)
                        )
                
                # Wait a bit before checking again
                await asyncio.sleep(0.5)
                
                # Update completed/failed sets
                for step in workflow.steps:
                    if step.status == StepStatus.COMPLETED and step.id not in completed_steps:
                        completed_steps.add(step.id)
                        self.logger.info(f"Step completed: {step.name} ({step.id})")
                    elif step.status == StepStatus.FAILED and step.id not in failed_steps:
                        failed_steps.add(step.id)
                        self.logger.error(f"Step failed: {step.name} ({step.id})")
            
            # Determine final status
            if failed_steps:
                execution.status = WorkflowStatus.FAILED
                execution.error = f"Steps failed: {', '.join(failed_steps)}"
            else:
                execution.status = WorkflowStatus.COMPLETED
            
            execution.completed_at = datetime.utcnow()
            
            # Emit completion event
            await self._emit_event('workflow_completed', {
                'execution_id': execution.id,
                'workflow_id': execution.workflow_id,
                'status': execution.status,
                'duration': (execution.completed_at - execution.started_at).total_seconds()
            })
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            
            log_error_with_context(
                'virtuai.workflow',
                e,
                {'execution_id': execution.id, 'workflow_id': execution.workflow_id}
            )
        
        finally:
            self.running_executions.discard(execution.id)
    
    async def _execute_step(self, step: WorkflowStep, execution: WorkflowExecution,
                          workflow: WorkflowDefinition):
        """Execute a single workflow step"""
        
        try:
            step.status = StepStatus.RUNNING
            step.started_at = datetime.utcnow()
            execution.current_step = step.id
            
            self.logger.info(f"Executing step: {step.name} ({step.id})")
            
            # Create task for the step
            task_data = {
                'title': f"Workflow Step: {step.name}",
                'description': step.task_description,
                'priority': TaskPriority.MEDIUM,
                'workflow_execution_id': execution.id,
                'workflow_step_id': step.id
            }
            
            # Add context variables to task description
            if execution.context:
                context_str = "\n\nContext:\n" + "\n".join([
                    f"- {k}: {v}" for k, v in execution.context.items()
                ])
                task_data['description'] += context_str
            
            # Add previous step results if available
            if execution.step_results:
                results_str = "\n\nPrevious Results:\n" + "\n".join([
                    f"- {k}: {v}" for k, v in execution.step_results.items()
                ])
                task_data['description'] += results_str
            
            # Find appropriate agent
            agents = await self.agent_manager.get_agents_by_type(step.agent_type)
            if not agents:
                raise ValueError(f"No agents available for type: {step.agent_type}")
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_step_with_agent(task_data, agents[0]),
                timeout=step.timeout_minutes * 60
            )
            
            step.output = result
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.utcnow()
            
            # Store result in execution context
            execution.step_results[step.id] = result
            
            # Update context with step variables
            if step.metadata.get('output_variables'):
                for var_name, var_path in step.metadata['output_variables'].items():
                    # Simple path extraction (could be enhanced)
                    execution.context[var_name] = result
            
        except asyncio.TimeoutError:
            step.status = StepStatus.FAILED
            step.error = f"Step timed out after {step.timeout_minutes} minutes"
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            
            # Retry logic
            if step.retry_count > 0:
                step.retry_count -= 1
                self.logger.warning(f"Retrying step {step.name}, {step.retry_count} retries left")
                await asyncio.sleep(5)  # Wait before retry
                await self._execute_step(step, execution, workflow)
            else:
                log_error_with_context(
                    'virtuai.workflow',
                    e,
                    {'step_id': step.id, 'execution_id': execution.id}
                )
    
    async def _execute_step_with_agent(self, task_data: Dict[str, Any], agent) -> str:
        """Execute a step using an agent"""
        
        # Create temporary task
        task = Task(
            title=task_data['title'],
            description=task_data['description'],
            priority=task_data['priority'],
            agent_id=agent.id
        )
        
        # Process with agent
        result = await agent.process_task(task)
        return result
    
    async def _execute_parallel_group(self, group: ParallelStepGroup,
                                    execution: WorkflowExecution,
                                    workflow: WorkflowDefinition):
        """Execute a group of parallel steps"""
        
        tasks = []
        for step in group.steps:
            task = asyncio.create_task(
                self._execute_step(step, execution, workflow)
            )
            tasks.append(task)
        
        if group.wait_for_all:
            # Wait for all steps to complete
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Wait for first completion
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build dependency graph for steps"""
        graph = {}
        
        for step in steps:
            graph[step.id] = step.depends_on.copy()
        
        return graph
    
    async def pause_execution(self, execution_id: str):
        """Pause a running workflow execution"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.PAUSED
                self.logger.info(f"Paused workflow execution: {execution_id}")
    
    async def resume_execution(self, execution_id: str):
        """Resume a paused workflow execution"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            if execution.status == WorkflowStatus.PAUSED:
                execution.status = WorkflowStatus.RUNNING
                self.logger.info(f"Resumed workflow execution: {execution_id}")
    
    async def cancel_execution(self, execution_id: str):
        """Cancel a workflow execution"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            self.running_executions.discard(execution_id)
            self.logger.info(f"Cancelled workflow execution: {execution_id}")
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get the status of a workflow execution"""
        return self.executions.get(execution_id)
    
    def list_executions(self, workflow_id: str = None) -> List[WorkflowExecution]:
        """List workflow executions"""
        executions = list(self.executions.values())
        
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        return sorted(executions, key=lambda x: x.started_at or datetime.min, reverse=True)
    
    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all registered workflows"""
        return list(self.workflows.values())
    
    async def _emit_event(self, event_name: str, data: Dict[str, Any]):
        """Emit workflow events"""
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                try:
                    await handler(data)
                except Exception as e:
                    self.logger.error(f"Event handler error: {e}")
    
    def on_event(self, event_name: str, handler: Callable):
        """Register event handler"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
    
    async def start_scheduler(self):
        """Start the workflow scheduler for scheduled workflows"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Workflow scheduler started")
    
    async def stop_scheduler(self):
        """Stop the workflow scheduler"""
        self.scheduler_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Workflow scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.scheduler_running:
            try:
                await self._check_scheduled_workflows()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                log_error_with_context('virtuai.workflow', e)
                await asyncio.sleep(60)
    
    async def _check_scheduled_workflows(self):
        """Check for scheduled workflows that need to run"""
        current_time = datetime.utcnow()
        
        for workflow in self.workflows.values():
            if workflow.trigger != WorkflowTrigger.SCHEDULED:
                continue
            
            if not workflow.schedule:
                continue
            
            # Simple cron-like scheduling (could be enhanced with proper cron parser)
            if self._should_run_scheduled_workflow(workflow, current_time):
                await self.execute_workflow(workflow.id, {
                    'scheduled_time': current_time.isoformat(),
                    'trigger': 'scheduled'
                })
    
    def _should_run_scheduled_workflow(self, workflow: WorkflowDefinition,
                                     current_time: datetime) -> bool:
        """Check if a scheduled workflow should run (simplified cron logic)"""
        # This is a simplified implementation
        # In production, you'd want to use a proper cron parser like croniter
        
        schedule = workflow.schedule.strip()
        
        # Handle simple cases
        if schedule == "* * * * *":  # Every minute
            return True
        elif schedule == "0 * * * *":  # Every hour
            return current_time.minute == 0
        elif schedule == "0 0 * * *":  # Every day at midnight
            return current_time.hour == 0 and current_time.minute == 0
        
        return False
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get workflow execution metrics"""
        total_executions = len(self.executions)
        running_executions = len(self.running_executions)
        
        status_counts = {}
        avg_duration = 0
        completed_count = 0
        
        for execution in self.executions.values():
            status = execution.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if execution.status == WorkflowStatus.COMPLETED and execution.started_at and execution.completed_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
                avg_duration += duration
                completed_count += 1
        
        if completed_count > 0:
            avg_duration = avg_duration / completed_count
        
        return {
            'total_executions': total_executions,
            'running_executions': running_executions,
            'status_distribution': status_counts,
            'average_duration_seconds': avg_duration,
            'registered_workflows': len(self.workflows),
            'scheduler_running': self.scheduler_running
        }


# Predefined workflow templates
class WorkflowTemplates:
    """Collection of predefined workflow templates"""
    
    @staticmethod
    def create_full_development_workflow() -> WorkflowDefinition:
        """Complete development workflow from requirements to deployment"""
        
        steps = [
            WorkflowStep(
                id="requirements",
                name="Gather Requirements",
                agent_type="product_manager",
                task_description="Analyze the project requirements and create detailed user stories with acceptance criteria."
            ),
            WorkflowStep(
                id="design",
                name="Create Design",
                agent_type="ui_ux_designer",
                task_description="Create wireframes and UI/UX design based on the requirements.",
                depends_on=["requirements"]
            ),
            WorkflowStep(
                id="backend_api",
                name="Develop Backend API",
                agent_type="backend_developer",
                task_description="Implement the backend API endpoints and database models based on requirements.",
                depends_on=["requirements"]
            ),
            WorkflowStep(
                id="frontend",
                name="Develop Frontend",
                agent_type="frontend_developer",
                task_description="Implement the frontend components and integrate with the backend API.",
                depends_on=["design", "backend_api"]
            ),
            WorkflowStep(
                id="testing",
                name="Create Tests",
                agent_type="qa_tester",
                task_description="Create comprehensive test plans and automated tests for the application.",
                depends_on=["frontend", "backend_api"]
            )
        ]
        
        return WorkflowDefinition(
            id="full_development_workflow",
            name="Full Development Workflow",
            description="Complete development workflow from requirements to testing",
            steps=steps,
            timeout_minutes=180
        )
    
    @staticmethod
    def create_code_review_workflow() -> WorkflowDefinition:
        """Code review and improvement workflow"""
        
        steps = [
            WorkflowStep(
                id="code_analysis",
                name="Analyze Code",
                agent_type="backend_developer",
                task_description="Analyze the provided code for potential issues, bugs, and improvements."
            ),
            WorkflowStep(
                id="security_review",
                name="Security Review",
                agent_type="qa_tester",
                task_description="Review the code for security vulnerabilities and best practices.",
                depends_on=["code_analysis"]
            ),
            WorkflowStep(
                id="performance_review",
                name="Performance Review",
                agent_type="backend_developer",
                task_description="Review the code for performance issues and optimization opportunities.",
                depends_on=["code_analysis"]
            ),
            WorkflowStep(
                id="documentation_review",
                name="Documentation Review",
                agent_type="product_manager",
                task_description="Review and improve code documentation and comments.",
                depends_on=["code_analysis"]
            )
        ]
        
        return WorkflowDefinition(
            id="code_review_workflow",
            name="Code Review Workflow",
            description="Comprehensive code review and improvement process",
            steps=steps,
            timeout_minutes=90
        )
    
    @staticmethod
    def create_api_development_workflow() -> WorkflowDefinition:
        """API development workflow"""
        
        steps = [
            WorkflowStep(
                id="api_design",
                name="Design API",
                agent_type="product_manager",
                task_description="Design the API endpoints, request/response formats, and documentation."
            ),
            WorkflowStep(
                id="api_implementation",
                name="Implement API",
                agent_type="backend_developer",
                task_description="Implement the API endpoints with proper error handling and validation.",
                depends_on=["api_design"]
            ),
            WorkflowStep(
                id="api_testing",
                name="Test API",
                agent_type="qa_tester",
                task_description="Create comprehensive API tests including unit tests and integration tests.",
                depends_on=["api_implementation"]
            ),
            WorkflowStep(
                id="api_documentation",
                name="Document API",
                agent_type="product_manager",
                task_description="Create comprehensive API documentation with examples and usage guides.",
                depends_on=["api_implementation"]
            )
        ]
        
        return WorkflowDefinition(
            id="api_development_workflow",
            name="API Development Workflow",
            description="Complete API development from design to documentation",
            steps=steps,
            timeout_minutes=120
        )
