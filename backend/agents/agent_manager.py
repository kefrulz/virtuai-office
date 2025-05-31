import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from .agent_factory import AgentFactory
from .base_agent import BaseAgent
from ..models.database import Task, Agent, TaskStatus, AgentType

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages AI agents and task assignment"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_workloads: Dict[str, int] = {}
        self.performance_cache: Dict[str, Dict] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available agents"""
        try:
            self.agents = AgentFactory.create_all_agents()
            self.agent_workloads = {agent_type: 0 for agent_type in self.agents.keys()}
            logger.info(f"Initialized {len(self.agents)} AI agents")
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Get agent by type"""
        return self.agents.get(agent_type)
    
    def get_all_agents(self) -> List[BaseAgent]:
        """Get all available agents"""
        return list(self.agents.values())
    
    def find_best_agent(self, task_description: str, exclude_busy: bool = True) -> Tuple[BaseAgent, float]:
        """Find the best agent for a given task"""
        best_agent = None
        best_score = 0.0
        
        for agent_type, agent in self.agents.items():
            # Skip busy agents if requested
            if exclude_busy and self._is_agent_busy(agent_type):
                continue
            
            # Calculate agent suitability score
            confidence = agent.can_handle_task(task_description)
            workload_penalty = self.agent_workloads.get(agent_type, 0) * 0.1
            performance_bonus = self._get_performance_bonus(agent_type)
            
            total_score = confidence + performance_bonus - workload_penalty
            
            if total_score > best_score:
                best_score = total_score
                best_agent = agent
        
        # Fallback to any available agent
        if not best_agent and exclude_busy:
            return self.find_best_agent(task_description, exclude_busy=False)
        
        return best_agent, best_score
    
    def assign_task(self, task: Task, db: Session) -> Optional[str]:
        """Assign a task to the best available agent"""
        try:
            best_agent, confidence = self.find_best_agent(task.description)
            
            if not best_agent:
                logger.warning("No available agents for task assignment")
                return None
            
            # Find or create agent in database
            agent_db = db.query(Agent).filter(Agent.type == best_agent.type).first()
            if not agent_db:
                agent_db = Agent(
                    name=best_agent.name,
                    type=best_agent.type,
                    description=best_agent.description,
                    expertise=','.join(best_agent.expertise)
                )
                db.add(agent_db)
                db.commit()
                db.refresh(agent_db)
            
            # Assign task to agent
            task.agent_id = agent_db.id
            self._increment_workload(best_agent.type.value)
            
            logger.info(f"Assigned task {task.id} to {best_agent.name} (confidence: {confidence:.2f})")
            return agent_db.id
            
        except Exception as e:
            logger.error(f"Failed to assign task: {e}")
            return None
    
    async def process_task(self, task: Task, db: Session) -> str:
        """Process a task with the assigned agent"""
        if not task.agent_id:
            raise ValueError("Task has no assigned agent")
        
        # Get agent from database
        agent_db = db.query(Agent).filter(Agent.id == task.agent_id).first()
        if not agent_db:
            raise ValueError("Agent not found in database")
        
        # Get agent instance
        agent = self.get_agent(agent_db.type.value)
        if not agent:
            raise ValueError(f"Agent type {agent_db.type} not available")
        
        try:
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.utcnow()
            db.commit()
            
            # Process the task
            logger.info(f"Processing task {task.id} with {agent.name}")
            output = await agent.process_task(task)
            
            # Update task with results
            task.output = output
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            # Calculate effort (mock estimation based on output length)
            task.actual_effort = max(1, len(output) // 500)
            
            # Update performance tracking
            self._update_performance(agent_db.type.value, True, task.actual_effort or 1)
            
            db.commit()
            
            # Decrement workload
            self._decrement_workload(agent_db.type.value)
            
            logger.info(f"Task {task.id} completed successfully by {agent.name}")
            return output
            
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            
            # Update task status to failed
            task.status = TaskStatus.FAILED
            task.output = f"Error processing task: {str(e)}"
            task.completed_at = datetime.utcnow()
            
            # Update performance tracking
            self._update_performance(agent_db.type.value, False, 0)
            
            db.commit()
            
            # Decrement workload
            self._decrement_workload(agent_db.type.value)
            
            raise
    
    def get_agent_status(self, db: Session) -> List[Dict]:
        """Get status of all agents"""
        status_list = []
        
        for agent_type, agent in self.agents.items():
            # Get agent from database
            agent_db = db.query(Agent).filter(Agent.type == agent_type).first()
            if not agent_db:
                continue
            
            # Get task counts
            total_tasks = db.query(Task).filter(Task.agent_id == agent_db.id).count()
            completed_tasks = db.query(Task).filter(
                Task.agent_id == agent_db.id,
                Task.status == TaskStatus.COMPLETED
            ).count()
            in_progress_tasks = db.query(Task).filter(
                Task.agent_id == agent_db.id,
                Task.status == TaskStatus.IN_PROGRESS
            ).count()
            
            status_list.append({
                'id': agent_db.id,
                'name': agent.name,
                'type': agent_type,
                'description': agent.description,
                'expertise': agent.expertise,
                'is_active': True,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'current_workload': self.agent_workloads.get(agent_type, 0),
                'performance_score': self._get_performance_score(agent_type)
            })
        
        return status_list
    
    def _is_agent_busy(self, agent_type: str, max_concurrent: int = 3) -> bool:
        """Check if agent is too busy to take new tasks"""
        return self.agent_workloads.get(agent_type, 0) >= max_concurrent
    
    def _increment_workload(self, agent_type: str):
        """Increment agent workload counter"""
        self.agent_workloads[agent_type] = self.agent_workloads.get(agent_type, 0) + 1
    
    def _decrement_workload(self, agent_type: str):
        """Decrement agent workload counter"""
        current = self.agent_workloads.get(agent_type, 0)
        self.agent_workloads[agent_type] = max(0, current - 1)
    
    def _get_performance_bonus(self, agent_type: str) -> float:
        """Get performance bonus for agent"""
        performance = self.performance_cache.get(agent_type, {})
        success_rate = performance.get('success_rate', 0.5)
        return (success_rate - 0.5) * 0.2  # Bonus/penalty up to ±0.1
    
    def _get_performance_score(self, agent_type: str) -> float:
        """Get overall performance score for agent"""
        performance = self.performance_cache.get(agent_type, {})
        return performance.get('success_rate', 0.5)
    
    def _update_performance(self, agent_type: str, success: bool, effort: int):
        """Update agent performance tracking"""
        if agent_type not in self.performance_cache:
            self.performance_cache[agent_type] = {
                'total_tasks': 0,
                'successful_tasks': 0,
                'total_effort': 0,
                'success_rate': 0.5
            }
        
        perf = self.performance_cache[agent_type]
        perf['total_tasks'] += 1
        perf['total_effort'] += effort
        
        if success:
            perf['successful_tasks'] += 1
        
        # Update success rate
        perf['success_rate'] = perf['successful_tasks'] / perf['total_tasks']
    
    def get_workload_distribution(self) -> Dict[str, int]:
        """Get current workload distribution across agents"""
        return self.agent_workloads.copy()
    
    def rebalance_workload(self, db: Session) -> Dict[str, Any]:
        """Rebalance workload across agents"""
        # Get pending tasks
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).all()
        
        rebalanced_count = 0
        
        for task in pending_tasks:
            if task.agent_id:
                current_agent_type = db.query(Agent).filter(Agent.id == task.agent_id).first()
                if current_agent_type and self._is_agent_busy(current_agent_type.type.value):
                    # Try to reassign to less busy agent
                    new_agent_id = self.assign_task(task, db)
                    if new_agent_id and new_agent_id != task.agent_id:
                        rebalanced_count += 1
        
        db.commit()
        
        return {
            'rebalanced_tasks': rebalanced_count,
            'current_distribution': self.get_workload_distribution()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents"""
        health_status = {
            'healthy_agents': 0,
            'total_agents': len(self.agents),
            'agent_details': []
        }
        
        for agent_type, agent in self.agents.items():
            try:
                # Simple health check - try to get system prompt
                system_prompt = agent.get_system_prompt()
                is_healthy = len(system_prompt) > 0
                
                if is_healthy:
                    health_status['healthy_agents'] += 1
                
                health_status['agent_details'].append({
                    'type': agent_type,
                    'name': agent.name,
                    'healthy': is_healthy,
                    'workload': self.agent_workloads.get(agent_type, 0)
                })
                
            except Exception as e:
                logger.error(f"Health check failed for {agent_type}: {e}")
                health_status['agent_details'].append({
                    'type': agent_type,
                    'name': agent.name,
                    'healthy': False,
                    'error': str(e)
                })
        
        return health_status
