# VirtuAI Office - Multi-Agent Collaboration System
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
import logging

from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

from ..core.logging import get_logger

logger = get_logger('virtuai.collaboration')

# Collaboration Types
class CollaborationType(str, Enum):
    INDEPENDENT = "independent"    # Single agent task
    SEQUENTIAL = "sequential"      # Tasks depend on each other in order
    PARALLEL = "parallel"         # Tasks can be done simultaneously
    REVIEW = "review"             # One agent reviews another's work
    ITERATIVE = "iterative"       # Back-and-forth collaboration
    HANDOFF = "handoff"           # Work passes between agents

class CollaborationStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Data Structures
@dataclass
class CollaborationStep:
    agent_id: str
    agent_name: str
    task_description: str
    estimated_duration: float
    dependencies: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[str] = None
    feedback: Optional[str] = None

@dataclass
class CollaborationPlan:
    id: str
    primary_task_id: str
    collaboration_type: CollaborationType
    estimated_duration: float
    steps: List[CollaborationStep]
    agents_involved: Set[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: CollaborationStatus = CollaborationStatus.PLANNED
    context: Dict[str, Any] = field(default_factory=dict)

# Database Models
Base = declarative_base()

class TaskCollaboration(Base):
    __tablename__ = "task_collaborations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    primary_task_id = Column(String, nullable=False)
    collaboration_type = Column(String, nullable=False)
    status = Column(String, default="planned")
    
    # Collaboration metadata
    plan_data = Column(Text)  # JSON serialized CollaborationPlan
    agents_involved = Column(Text)  # JSON list of agent IDs
    estimated_duration = Column(Float)
    actual_duration = Column(Float)
    
    # Progress tracking
    current_step = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    total_steps = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    final_output = Column(Text)
    quality_score = Column(Float)
    feedback = Column(Text)

class CollaborationStep(Base):
    __tablename__ = "collaboration_steps"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collaboration_id = Column(String, ForeignKey("task_collaborations.id"))
    step_order = Column(Integer, nullable=False)
    
    # Step details
    agent_id = Column(String, nullable=False)
    agent_name = Column(String)
    task_description = Column(Text)
    estimated_duration = Column(Float)
    
    # Dependencies and outputs
    dependencies = Column(Text)  # JSON list of step IDs
    expected_outputs = Column(Text)  # JSON list of output types
    
    # Execution
    status = Column(String, default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    output = Column(Text)
    
    # Quality and feedback
    quality_score = Column(Float)
    feedback = Column(Text)
    revision_count = Column(Integer, default=0)

class AgentInteraction(Base):
    __tablename__ = "agent_interactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collaboration_id = Column(String, ForeignKey("task_collaborations.id"))
    
    # Interaction details
    from_agent_id = Column(String, nullable=False)
    to_agent_id = Column(String, nullable=False)
    interaction_type = Column(String)  # feedback, question, handoff, review
    
    # Content
    message = Column(Text)
    context_data = Column(Text)  # JSON additional context
    
    # Response
    response = Column(Text)
    response_time = Column(Float)  # seconds
    
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)

# Collaboration Manager
class CollaborationManager:
    def __init__(self, agent_manager, boss_ai):
        self.agent_manager = agent_manager
        self.boss_ai = boss_ai
        self.active_collaborations: Dict[str, CollaborationPlan] = {}
        self.collaboration_patterns = self._load_collaboration_patterns()
    
    def _load_collaboration_patterns(self) -> Dict[str, Dict]:
        """Load predefined collaboration patterns"""
        return {
            "frontend_to_backend": {
                "type": CollaborationType.SEQUENTIAL,
                "agents": ["ui_ux_designer", "frontend_developer", "backend_developer"],
                "description": "Design → Frontend → Backend integration"
            },
            "full_feature_development": {
                "type": CollaborationType.SEQUENTIAL,
                "agents": ["product_manager", "ui_ux_designer", "frontend_developer", "backend_developer", "qa_tester"],
                "description": "Complete feature development pipeline"
            },
            "code_review": {
                "type": CollaborationType.REVIEW,
                "agents": ["frontend_developer", "backend_developer", "qa_tester"],
                "description": "Multi-agent code review process"
            },
            "parallel_implementation": {
                "type": CollaborationType.PARALLEL,
                "agents": ["frontend_developer", "backend_developer"],
                "description": "Simultaneous frontend and backend development"
            },
            "iterative_design": {
                "type": CollaborationType.ITERATIVE,
                "agents": ["ui_ux_designer", "frontend_developer", "product_manager"],
                "description": "Iterative design refinement process"
            }
        }
    
    async def analyze_collaboration_needs(self, task_description: str, task_complexity: str) -> Optional[CollaborationType]:
        """Analyze if a task needs collaboration and what type"""
        
        collaboration_indicators = {
            CollaborationType.SEQUENTIAL: [
                "end-to-end", "complete feature", "full implementation",
                "from design to deployment", "entire workflow"
            ],
            CollaborationType.PARALLEL: [
                "frontend and backend", "simultaneous", "at the same time",
                "parallel development", "concurrent"
            ],
            CollaborationType.REVIEW: [
                "review", "feedback", "validation", "check", "assess",
                "evaluate", "audit", "quality assurance"
            ],
            CollaborationType.ITERATIVE: [
                "refine", "iterate", "improve", "multiple rounds",
                "back and forth", "collaborative refinement"
            ]
        }
        
        description_lower = task_description.lower()
        
        # Check for collaboration indicators
        for collab_type, indicators in collaboration_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                logger.info(f"Detected collaboration need: {collab_type.value}")
                return collab_type
        
        # Check complexity-based collaboration needs
        if task_complexity in ["complex", "epic"]:
            return CollaborationType.SEQUENTIAL
        
        # Check for multi-domain requirements
        domains = {
            "design": ["ui", "ux", "design", "mockup", "wireframe", "visual"],
            "frontend": ["react", "frontend", "ui", "interface", "component"],
            "backend": ["api", "backend", "database", "server", "endpoint"],
            "testing": ["test", "qa", "quality", "validation", "automation"]
        }
        
        involved_domains = []
        for domain, keywords in domains.items():
            if any(keyword in description_lower for keyword in keywords):
                involved_domains.append(domain)
        
        if len(involved_domains) > 2:
            return CollaborationType.SEQUENTIAL
        elif len(involved_domains) == 2:
            return CollaborationType.PARALLEL
        
        return None
    
    async def create_collaboration_plan(self,
                                      task_id: str,
                                      task_description: str,
                                      collaboration_type: CollaborationType,
                                      available_agents: List[Any],
                                      db: Session) -> CollaborationPlan:
        """Create a detailed collaboration plan"""
        
        plan_id = str(uuid.uuid4())
        
        # Select agents based on collaboration type and task requirements
        selected_agents = await self._select_agents_for_collaboration(
            task_description, collaboration_type, available_agents
        )
        
        # Create collaboration steps
        steps = await self._create_collaboration_steps(
            task_description, collaboration_type, selected_agents
        )
        
        # Estimate duration
        estimated_duration = sum(step.estimated_duration for step in steps)
        
        plan = CollaborationPlan(
            id=plan_id,
            primary_task_id=task_id,
            collaboration_type=collaboration_type,
            estimated_duration=estimated_duration,
            steps=steps,
            agents_involved={step.agent_id for step in steps}
        )
        
        # Store in database
        collaboration_record = TaskCollaboration(
            id=plan_id,
            primary_task_id=task_id,
            collaboration_type=collaboration_type.value,
            plan_data=json.dumps(self._serialize_plan(plan)),
            agents_involved=json.dumps(list(plan.agents_involved)),
            estimated_duration=estimated_duration,
            total_steps=len(steps)
        )
        
        db.add(collaboration_record)
        
        # Store individual steps
        for i, step in enumerate(steps):
            step_record = CollaborationStep(
                collaboration_id=plan_id,
                step_order=i,
                agent_id=step.agent_id,
                agent_name=step.agent_name,
                task_description=step.task_description,
                estimated_duration=step.estimated_duration,
                dependencies=json.dumps(step.dependencies),
                expected_outputs=json.dumps(step.outputs)
            )
            db.add(step_record)
        
        db.commit()
        
        # Cache active collaboration
        self.active_collaborations[plan_id] = plan
        
        logger.info(f"Created collaboration plan {plan_id} with {len(steps)} steps")
        return plan
    
    async def _select_agents_for_collaboration(self,
                                             task_description: str,
                                             collaboration_type: CollaborationType,
                                             available_agents: List[Any]) -> List[Any]:
        """Select appropriate agents for collaboration"""
        
        # Analyze task requirements
        required_skills = await self._analyze_required_skills(task_description)
        
        # Map skills to agent types
        skill_agent_map = {
            "product_management": ["product_manager"],
            "design": ["ui_ux_designer"],
            "frontend": ["frontend_developer"],
            "backend": ["backend_developer"],
            "testing": ["qa_tester"]
        }
        
        selected_types = set()
        for skill in required_skills:
            for skill_type, agent_types in skill_agent_map.items():
                if skill in skill_type or any(s in skill for s in skill_type.split("_")):
                    selected_types.update(agent_types)
        
        # Filter available agents by type
        selected_agents = [
            agent for agent in available_agents
            if agent.type.value in selected_types
        ]
        
        # Ensure minimum collaboration requirements
        if collaboration_type == CollaborationType.SEQUENTIAL and len(selected_agents) < 2:
            # Add complementary agents
            if any(agent.type.value == "frontend_developer" for agent in selected_agents):
                backend_agent = next((a for a in available_agents if a.type.value == "backend_developer"), None)
                if backend_agent:
                    selected_agents.append(backend_agent)
        
        logger.info(f"Selected {len(selected_agents)} agents for collaboration: {[a.name for a in selected_agents]}")
        return selected_agents
    
    async def _analyze_required_skills(self, task_description: str) -> List[str]:
        """Analyze what skills are required for the task"""
        
        skill_keywords = {
            "product_management": ["requirements", "user story", "specification", "planning"],
            "design": ["design", "ui", "ux", "mockup", "wireframe", "visual", "layout"],
            "frontend": ["react", "component", "interface", "frontend", "ui", "web"],
            "backend": ["api", "backend", "server", "database", "endpoint", "service"],
            "testing": ["test", "qa", "quality", "validation", "testing", "automation"]
        }
        
        description_lower = task_description.lower()
        required_skills = []
        
        for skill, keywords in skill_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                required_skills.append(skill)
        
        return required_skills
    
    async def _create_collaboration_steps(self,
                                        task_description: str,
                                        collaboration_type: CollaborationType,
                                        selected_agents: List[Any]) -> List[CollaborationStep]:
        """Create detailed collaboration steps"""
        
        steps = []
        
        if collaboration_type == CollaborationType.SEQUENTIAL:
            steps = await self._create_sequential_steps(task_description, selected_agents)
        elif collaboration_type == CollaborationType.PARALLEL:
            steps = await self._create_parallel_steps(task_description, selected_agents)
        elif collaboration_type == CollaborationType.REVIEW:
            steps = await self._create_review_steps(task_description, selected_agents)
        elif collaboration_type == CollaborationType.ITERATIVE:
            steps = await self._create_iterative_steps(task_description, selected_agents)
        
        return steps
    
    async def _create_sequential_steps(self, task_description: str, agents: List[Any]) -> List[CollaborationStep]:
        """Create sequential collaboration steps"""
        
        # Order agents by typical workflow
        agent_order = ["product_manager", "ui_ux_designer", "frontend_developer", "backend_developer", "qa_tester"]
        
        ordered_agents = []
        for agent_type in agent_order:
            agent = next((a for a in agents if a.type.value == agent_type), None)
            if agent:
                ordered_agents.append(agent)
        
        steps = []
        for i, agent in enumerate(ordered_agents):
            step_description = await self._generate_step_description(task_description, agent, i, len(ordered_agents))
            
            step = CollaborationStep(
                agent_id=agent.id,
                agent_name=agent.name,
                task_description=step_description,
                estimated_duration=self._estimate_step_duration(agent.type.value, task_description),
                dependencies=[steps[i-1].agent_id] if i > 0 else [],
                outputs=self._get_expected_outputs(agent.type.value)
            )
            steps.append(step)
        
        return steps
    
    async def _create_parallel_steps(self, task_description: str, agents: List[Any]) -> List[CollaborationStep]:
        """Create parallel collaboration steps"""
        
        steps = []
        for agent in agents:
            step_description = await self._generate_step_description(task_description, agent, 0, len(agents))
            
            step = CollaborationStep(
                agent_id=agent.id,
                agent_name=agent.name,
                task_description=step_description,
                estimated_duration=self._estimate_step_duration(agent.type.value, task_description),
                dependencies=[],
                outputs=self._get_expected_outputs(agent.type.value)
            )
            steps.append(step)
        
        # Add integration step if multiple agents
        if len(agents) > 1:
            integration_agent = agents[0]  # Use first agent for integration
            integration_step = CollaborationStep(
                agent_id=integration_agent.id,
                agent_name=integration_agent.name,
                task_description=f"Integrate and coordinate outputs from parallel development: {task_description}",
                estimated_duration=1.0,
                dependencies=[step.agent_id for step in steps],
                outputs=["integrated_solution", "coordination_report"]
            )
            steps.append(integration_step)
        
        return steps
    
    async def _create_review_steps(self, task_description: str, agents: List[Any]) -> List[CollaborationStep]:
        """Create review collaboration steps"""
        
        if len(agents) < 2:
            return []
        
        steps = []
        
        # Primary implementation step
        primary_agent = agents[0]
        primary_step = CollaborationStep(
            agent_id=primary_agent.id,
            agent_name=primary_agent.name,
            task_description=f"Initial implementation: {task_description}",
            estimated_duration=self._estimate_step_duration(primary_agent.type.value, task_description),
            dependencies=[],
            outputs=self._get_expected_outputs(primary_agent.type.value)
        )
        steps.append(primary_step)
        
        # Review steps
        for reviewer in agents[1:]:
            review_step = CollaborationStep(
                agent_id=reviewer.id,
                agent_name=reviewer.name,
                task_description=f"Review and provide feedback on: {task_description}",
                estimated_duration=self._estimate_step_duration(reviewer.type.value, task_description) * 0.5,
                dependencies=[primary_step.agent_id],
                outputs=["review_feedback", "improvement_suggestions"]
            )
            steps.append(review_step)
        
        # Revision step
        revision_step = CollaborationStep(
            agent_id=primary_agent.id,
            agent_name=primary_agent.name,
            task_description=f"Incorporate feedback and finalize: {task_description}",
            estimated_duration=self._estimate_step_duration(primary_agent.type.value, task_description) * 0.3,
            dependencies=[step.agent_id for step in steps[1:]],
            outputs=["final_implementation", "revision_notes"]
        )
        steps.append(revision_step)
        
        return steps
    
    async def _create_iterative_steps(self, task_description: str, agents: List[Any]) -> List[CollaborationStep]:
        """Create iterative collaboration steps"""
        
        if len(agents) < 2:
            return []
        
        steps = []
        iterations = 2  # Number of iterations
        
        for iteration in range(iterations):
            for i, agent in enumerate(agents):
                step_description = f"Iteration {iteration + 1}: {await self._generate_step_description(task_description, agent, i, len(agents))}"
                
                dependencies = []
                if iteration > 0:
                    # Depend on previous iteration
                    prev_step_index = len(steps) - len(agents) + i
                    if prev_step_index >= 0:
                        dependencies.append(steps[prev_step_index].agent_id)
                elif i > 0:
                    # Depend on previous agent in same iteration
                    dependencies.append(steps[-1].agent_id)
                
                step = CollaborationStep(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    task_description=step_description,
                    estimated_duration=self._estimate_step_duration(agent.type.value, task_description) * (0.8 if iteration > 0 else 1.0),
                    dependencies=dependencies,
                    outputs=self._get_expected_outputs(agent.type.value)
                )
                steps.append(step)
        
        return steps
    
    async def _generate_step_description(self, task_description: str, agent: Any, step_index: int, total_steps: int) -> str:
        """Generate a specific task description for an agent in the collaboration"""
        
        agent_responsibilities = {
            "product_manager": "Analyze requirements, create user stories, and define acceptance criteria",
            "ui_ux_designer": "Create wireframes, design mockups, and define user experience",
            "frontend_developer": "Implement user interface components and frontend functionality",
            "backend_developer": "Develop API endpoints, database models, and server-side logic",
            "qa_tester": "Create test plans, perform testing, and ensure quality standards"
        }
        
        base_responsibility = agent_responsibilities.get(agent.type.value, "Contribute expertise")
        
        if total_steps == 1:
            return f"{base_responsibility} for: {task_description}"
        else:
            step_context = f"Step {step_index + 1} of {total_steps}"
            return f"{step_context} - {base_responsibility} for: {task_description}"
    
    def _estimate_step_duration(self, agent_type: str, task_description: str) -> float:
        """Estimate duration for a collaboration step"""
        
        base_durations = {
            "product_manager": 2.0,
            "ui_ux_designer": 3.0,
            "frontend_developer": 4.0,
            "backend_developer": 4.0,
            "qa_tester": 2.5
        }
        
        base_duration = base_durations.get(agent_type, 3.0)
        
        # Adjust based on task complexity
        complexity_multipliers = {
            "simple": 0.5,
            "basic": 0.7,
            "standard": 1.0,
            "complex": 1.5,
            "advanced": 2.0
        }
        
        description_lower = task_description.lower()
        multiplier = 1.0
        
        for complexity, mult in complexity_multipliers.items():
            if complexity in description_lower:
                multiplier = mult
                break
        
        return base_duration * multiplier
    
    def _get_expected_outputs(self, agent_type: str) -> List[str]:
        """Get expected outputs for an agent type"""
        
        outputs_map = {
            "product_manager": ["user_stories", "requirements_document", "acceptance_criteria"],
            "ui_ux_designer": ["wireframes", "mockups", "design_specifications"],
            "frontend_developer": ["react_components", "css_styles", "frontend_code"],
            "backend_developer": ["api_endpoints", "database_models", "backend_code"],
            "qa_tester": ["test_plans", "test_cases", "quality_report"]
        }
        
        return outputs_map.get(agent_type, ["deliverable"])
    
    async def execute_collaboration(self, collaboration_id: str, db: Session) -> Dict[str, Any]:
        """Execute a collaboration plan"""
        
        if collaboration_id not in self.active_collaborations:
            # Load from database
            collaboration_record = db.query(TaskCollaboration).filter(
                TaskCollaboration.id == collaboration_id
            ).first()
            
            if not collaboration_record:
                raise ValueError(f"Collaboration {collaboration_id} not found")
            
            plan = self._deserialize_plan(json.loads(collaboration_record.plan_data))
            self.active_collaborations[collaboration_id] = plan
        
        plan = self.active_collaborations[collaboration_id]
        plan.status = CollaborationStatus.ACTIVE
        
        # Update database
        db.query(TaskCollaboration).filter(
            TaskCollaboration.id == collaboration_id
        ).update({
            "status": "active",
            "started_at": datetime.utcnow()
        })
        db.commit()
        
        logger.info(f"Starting collaboration execution: {collaboration_id}")
        
        try:
            results = await self._execute_collaboration_steps(plan, db)
            
            # Compile final output
            final_output = await self._compile_collaboration_output(plan, results)
            
            # Update completion status
            plan.status = CollaborationStatus.COMPLETED
            
            db.query(TaskCollaboration).filter(
                TaskCollaboration.id == collaboration_id
            ).update({
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "final_output": final_output,
                "completed_steps": len(plan.steps)
            })
            db.commit()
            
            logger.info(f"Collaboration {collaboration_id} completed successfully")
            
            return {
                "collaboration_id": collaboration_id,
                "status": "completed",
                "final_output": final_output,
                "steps_completed": len(plan.steps),
                "total_duration": sum(step.estimated_duration for step in plan.steps if step.completed_at)
            }
            
        except Exception as e:
            logger.error(f"Collaboration {collaboration_id} failed: {str(e)}")
            
            plan.status = CollaborationStatus.FAILED
            
            db.query(TaskCollaboration).filter(
                TaskCollaboration.id == collaboration_id
            ).update({
                "status": "failed",
                "feedback": str(e)
            })
            db.commit()
            
            raise
    
    async def _execute_collaboration_steps(self, plan: CollaborationPlan, db: Session) -> Dict[str, Any]:
        """Execute individual collaboration steps"""
        
        results = {}
        step_outputs = {}
        
        if plan.collaboration_type == CollaborationType.SEQUENTIAL:
            # Execute steps in order
            for step in plan.steps:
                result = await self._execute_single_step(step, step_outputs, db)
                results[step.agent_id] = result
                step_outputs[step.agent_id] = result.get("output", "")
                
        elif plan.collaboration_type == CollaborationType.PARALLEL:
            # Execute steps concurrently (except dependencies)
            parallel_steps = [step for step in plan.steps if not step.dependencies]
            dependent_steps = [step for step in plan.steps if step.dependencies]
            
            # Execute parallel steps
            if parallel_steps:
                parallel_results = await asyncio.gather(*[
                    self._execute_single_step(step, step_outputs, db)
                    for step in parallel_steps
                ])
                
                for i, step in enumerate(parallel_steps):
                    results[step.agent_id] = parallel_results[i]
                    step_outputs[step.agent_id] = parallel_results[i].get("output", "")
            
            # Execute dependent steps
            for step in dependent_steps:
                result = await self._execute_single_step(step, step_outputs, db)
                results[step.agent_id] = result
                step_outputs[step.agent_id] = result.get("output", "")
                
        elif plan.collaboration_type in [CollaborationType.REVIEW, CollaborationType.ITERATIVE]:
            # Execute steps with feedback loops
            for step in plan.steps:
                # Provide context from previous steps
                context = self._build_step_context(step, step_outputs)
                result = await self._execute_single_step(step, step_outputs, db, context)
                results[step.agent_id] = result
                step_outputs[step.agent_id] = result.get("output", "")
        
        return results
    
    async def _execute_single_step(self,
                                 step: CollaborationStep,
                                 previous_outputs: Dict[str, str],
                                 db: Session,
                                 additional_context: str = "") -> Dict[str, Any]:
        """Execute a single collaboration step"""
        
        step.started_at = datetime.utcnow()
        step.status = "in_progress"
        
        # Update database
        db.query(CollaborationStep).filter(
            CollaborationStep.agent_id == step.agent_id
        ).update({
            "status": "in_progress",
            "started_at": step.started_at
        })
        db.commit()
        
        try:
            # Get agent
            agent = self.agent_manager.get_agent_by_id(step.agent_id)
            if not agent:
                raise ValueError(f"Agent {step.agent_id} not found")
            
            # Build context from previous outputs
            context = self._build_collaboration_context(step, previous_outputs, additional_context)
            
            # Execute step
            logger.info(f"Executing step: {step.agent_name} - {step.task_description}")
            
            # Create a mock task object for agent processing
            mock_task = type('Task', (), {
                'title': f"Collaboration Step: {step.task_description}",
                'description': step.task_description + "\n\n" + context,
                'priority': 'medium'
            })()
            
            output = await agent.process_task(mock_task)
            
            # Update step completion
            step.completed_at = datetime.utcnow()
            step.status = "completed"
            step.output = output
            
            # Calculate quality score (simplified)
            quality_score = self._assess_step_quality(output, step.outputs)
            step.quality_score = quality_score
            
            # Update database
            db.query(CollaborationStep).filter(
                CollaborationStep.agent_id == step.agent_id
            ).update({
                "status": "completed",
                "completed_at": step.completed_at,
                "output": output,
                "quality_score": quality_score
            })
            db.commit()
            
            logger.info(f"Step completed: {step.agent_name} (Quality: {quality_score:.2f})")
            
            return {
                "agent_id": step.agent_id,
                "agent_name": step.agent_name,
                "output": output,
                "quality_score": quality_score,
                "duration": (step.completed_at - step.started_at).total_seconds() / 3600
            }
            
        except Exception as e:
            step.status = "failed"
            step.feedback = str(e)
            
            db.query(CollaborationStep).filter(
                CollaborationStep.agent_id == step.agent_id
            ).update({
                "status": "failed",
                "feedback": str(e)
            })
            db.commit()
            
            logger.error(f"Step failed: {step.agent_name} - {str(e)}")
            raise
    
    def _build_collaboration_context(self,
                                   current_step: CollaborationStep,
                                   previous_outputs: Dict[str, str],
                                   additional_context: str = "") -> str:
        """Build context for the current collaboration step"""
        
        context_parts = []
        
        # Add collaboration context
        context_parts.append("=== COLLABORATION CONTEXT ===")
        context_parts.append(f"You are working on a collaborative task with other AI agents.")
        context_parts.append(f"Your role: {current_step.agent_name}")
        context_parts.append(f"Task: {current_step.task_description}")
        
        # Add previous outputs if available
        if previous_outputs:
            context_parts.append("\n=== PREVIOUS WORK ===")
            for agent_id, output in previous_outputs.items():
                if agent_id in current_step.dependencies:
                    context_parts.append(f"Input from previous step ({agent_id}):")
                    context_parts.append(output[:1000] + "..." if len(output) > 1000 else output)
                    context_parts.append("")
        
        # Add expected outputs
        if current_step.outputs:
            context_parts.append("=== EXPECTED OUTPUTS ===")
            context_parts.append("Please provide:")
            for output_type in current_step.outputs:
                context_parts.append(f"- {output_type.replace('_', ' ').title()}")
        
        # Add additional context
        if additional_context:
            context_parts.append("\n=== ADDITIONAL CONTEXT ===")
            context_parts.append(additional_context)
        
        context_parts.append("\n=== INSTRUCTIONS ===")
        context_parts.append("Build upon the previous work and coordinate with the overall goal.")
        context_parts.append("Provide detailed, high-quality output that the next agent can use.")
        
        return "\n".join(context_parts)
    
    def _build_step_context(self, step: CollaborationStep, step_outputs: Dict[str, str]) -> str:
        """Build context for review/iterative collaboration"""
        
        if not step_outputs:
            return ""
        
        context_parts = ["=== COLLABORATION HISTORY ==="]
        
        for agent_id, output in step_outputs.items():
            if agent_id != step.agent_id:  # Don't include own previous output
                context_parts.append(f"Previous contribution:")
                context_parts.append(output[:500] + "..." if len(output) > 500 else output)
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _assess_step_quality(self, output: str, expected_outputs: List[str]) -> float:
        """Assess the quality of a collaboration step output"""
        
        if not output:
            return 0.0
        
        quality_score = 0.0
        
        # Length assessment
        if len(output) > 100:
            quality_score += 0.3
        
        # Structure assessment
        if any(marker in output for marker in ['#', '##', '**', '*', '1.', '2.']):
            quality_score += 0.2
        
        # Content completeness based on expected outputs
        if expected_outputs:
            matched_outputs = 0
            for expected in expected_outputs:
                expected_keywords = expected.replace('_', ' ').split()
                if any(keyword.lower() in output.lower() for keyword in expected_keywords):
                    matched_outputs += 1
            
            completeness_score = matched_outputs / len(expected_outputs)
            quality_score += completeness_score * 0.5
        else:
            quality_score += 0.5  # Default if no expected outputs specified
        
        return min(quality_score, 1.0)
    
    async def _compile_collaboration_output(self, plan: CollaborationPlan, results: Dict[str, Any]) -> str:
        """Compile final output from all collaboration steps"""
        
        output_parts = []
        
        # Header
        output_parts.append(f"# Collaborative Task Result")
        output_parts.append(f"**Collaboration Type:** {plan.collaboration_type.value.title()}")
        output_parts.append(f"**Agents Involved:** {len(plan.agents_involved)}")
        output_parts.append(f"**Completed Steps:** {len(plan.steps)}")
        output_parts.append("")
        
        # Summary
        output_parts.append("## Executive Summary")
        
        # Determine primary output based on collaboration type
        if plan.collaboration_type == CollaborationType.SEQUENTIAL:
            # Use output from last step
            last_step = plan.steps[-1]
            if last_step.agent_id in results:
                primary_result = results[last_step.agent_id]
                output_parts.append(f"Final deliverable completed by {last_step.agent_name}:")
                output_parts.append("")
                output_parts.append(primary_result.get("output", ""))
        
        elif plan.collaboration_type == CollaborationType.PARALLEL:
            output_parts.append("Parallel development completed with coordinated outputs:")
            output_parts.append("")
            
            for step in plan.steps:
                if step.agent_id in results:
                    result = results[step.agent_id]
                    output_parts.append(f"### {step.agent_name} Contribution")
                    output_parts.append(result.get("output", ""))
                    output_parts.append("")
        
        elif plan.collaboration_type == CollaborationType.REVIEW:
            # Use final revised output
            review_steps = [s for s in plan.steps if "review" not in s.task_description.lower()]
            if review_steps and review_steps[-1].agent_id in results:
                final_result = results[review_steps[-1].agent_id]
                output_parts.append("Final reviewed and refined deliverable:")
                output_parts.append("")
                output_parts.append(final_result.get("output", ""))
        
        elif plan.collaboration_type == CollaborationType.ITERATIVE:
            # Use output from final iteration
            final_step = plan.steps[-1]
            if final_step.agent_id in results:
                final_result = results[final_step.agent_id]
                output_parts.append("Final iteratively refined deliverable:")
                output_parts.append("")
                output_parts.append(final_result.get("output", ""))
        
        # Add collaboration metadata
        output_parts.append("\n---\n")
        output_parts.append("## Collaboration Details")
        
        total_duration = sum(r.get("duration", 0) for r in results.values())
        avg_quality = sum(r.get("quality_score", 0) for r in results.values()) / len(results) if results else 0
        
        output_parts.append(f"- **Total Duration:** {total_duration:.1f} hours")
        output_parts.append(f"- **Average Quality Score:** {avg_quality:.2f}/1.0")
        output_parts.append(f"- **Collaboration Efficiency:** {self._calculate_collaboration_efficiency(plan, total_duration):.1f}%")
        
        # Individual contributions summary
        output_parts.append("\n### Individual Contributions")
        for step in plan.steps:
            if step.agent_id in results:
                result = results[step.agent_id]
                output_parts.append(f"- **{step.agent_name}:** {step.task_description}")
                output_parts.append(f"  - Duration: {result.get('duration', 0):.1f}h")
                output_parts.append(f"  - Quality: {result.get('quality_score', 0):.2f}/1.0")
        
        return "\n".join(output_parts)
    
    def _calculate_collaboration_efficiency(self, plan: CollaborationPlan, actual_duration: float) -> float:
        """Calculate collaboration efficiency percentage"""
        
        if plan.estimated_duration == 0:
            return 100.0
        
        efficiency = (plan.estimated_duration / actual_duration) * 100
        return min(efficiency, 200.0)  # Cap at 200% efficiency
    
    def _serialize_plan(self, plan: CollaborationPlan) -> Dict[str, Any]:
        """Serialize collaboration plan for database storage"""
        
        return {
            "id": plan.id,
            "primary_task_id": plan.primary_task_id,
            "collaboration_type": plan.collaboration_type.value,
            "estimated_duration": plan.estimated_duration,
            "agents_involved": list(plan.agents_involved),
            "created_at": plan.created_at.isoformat(),
            "status": plan.status.value,
            "context": plan.context,
            "steps": [
                {
                    "agent_id": step.agent_id,
                    "agent_name": step.agent_name,
                    "task_description": step.task_description,
                    "estimated_duration": step.estimated_duration,
                    "dependencies": step.dependencies,
                    "outputs": step.outputs,
                    "status": step.status
                }
                for step in plan.steps
            ]
        }
    
    def _deserialize_plan(self, data: Dict[str, Any]) -> CollaborationPlan:
        """Deserialize collaboration plan from database"""
        
        steps = []
        for step_data in data.get("steps", []):
            step = CollaborationStep(
                agent_id=step_data["agent_id"],
                agent_name=step_data["agent_name"],
                task_description=step_data["task_description"],
                estimated_duration=step_data["estimated_duration"],
                dependencies=step_data.get("dependencies", []),
                outputs=step_data.get("outputs", []),
                status=step_data.get("status", "pending")
            )
            steps.append(step)
        
        return CollaborationPlan(
            id=data["id"],
            primary_task_id=data["primary_task_id"],
            collaboration_type=CollaborationType(data["collaboration_type"]),
            estimated_duration=data["estimated_duration"],
            steps=steps,
            agents_involved=set(data.get("agents_involved", [])),
            created_at=datetime.fromisoformat(data["created_at"]),
            status=CollaborationStatus(data.get("status", "planned")),
            context=data.get("context", {})
        )
    
    async def get_collaboration_status(self, collaboration_id: str, db: Session) -> Dict[str, Any]:
        """Get current status of a collaboration"""
        
        collaboration = db.query(TaskCollaboration).filter(
            TaskCollaboration.id == collaboration_id
        ).first()
        
        if not collaboration:
            raise ValueError(f"Collaboration {collaboration_id} not found")
        
        # Get step details
        steps = db.query(CollaborationStep).filter(
            CollaborationStep.collaboration_id == collaboration_id
        ).order_by(CollaborationStep.step_order).all()
        
        step_status = []
        for step in steps:
            step_info = {
                "agent_name": step.agent_name,
                "task_description": step.task_description,
                "status": step.status,
                "estimated_duration": step.estimated_duration,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                "quality_score": step.quality_score
            }
            step_status.append(step_info)
        
        # Calculate progress
        completed_steps = len([s for s in steps if s.status == "completed"])
        progress_percentage = (completed_steps / len(steps)) * 100 if steps else 0
        
        return {
            "collaboration_id": collaboration_id,
            "status": collaboration.status,
            "collaboration_type": collaboration.collaboration_type,
            "progress_percentage": progress_percentage,
            "completed_steps": completed_steps,
            "total_steps": len(steps),
            "estimated_duration": collaboration.estimated_duration,
            "created_at": collaboration.created_at.isoformat(),
            "started_at": collaboration.started_at.isoformat() if collaboration.started_at else None,
            "completed_at": collaboration.completed_at.isoformat() if collaboration.completed_at else None,
            "agents_involved": json.loads(collaboration.agents_involved) if collaboration.agents_involved else [],
            "steps": step_status,
            "final_output": collaboration.final_output
        }
    
    async def cancel_collaboration(self, collaboration_id: str, reason: str, db: Session):
        """Cancel an active collaboration"""
        
        collaboration = db.query(TaskCollaboration).filter(
            TaskCollaboration.id == collaboration_id
        ).first()
        
        if not collaboration:
            raise ValueError(f"Collaboration {collaboration_id} not found")
        
        if collaboration.status in ["completed", "cancelled"]:
            raise ValueError(f"Cannot cancel collaboration in status: {collaboration.status}")
        
        # Update collaboration status
        collaboration.status = "cancelled"
        collaboration.feedback = f"Cancelled: {reason}"
        
        # Cancel any pending steps
        db.query(CollaborationStep).filter(
            CollaborationStep.collaboration_id == collaboration_id,
            CollaborationStep.status.in_(["pending", "in_progress"])
        ).update({
            "status": "cancelled",
            "feedback": f"Cancelled due to collaboration cancellation: {reason}"
        })
        
        db.commit()
        
        # Remove from active collaborations
        if collaboration_id in self.active_collaborations:
            del self.active_collaborations[collaboration_id]
        
        logger.info(f"Collaboration {collaboration_id} cancelled: {reason}")
    
    async def get_collaboration_metrics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get collaboration performance metrics"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get collaborations from the specified period
        collaborations = db.query(TaskCollaboration).filter(
            TaskCollaboration.created_at >= cutoff_date
        ).all()
        
        if not collaborations:
            return {
                "total_collaborations": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "collaboration_types": {},
                "agent_participation": {}
            }
        
        # Calculate metrics
        total_collaborations = len(collaborations)
        successful_collaborations = len([c for c in collaborations if c.status == "completed"])
        success_rate = (successful_collaborations / total_collaborations) * 100
        
        # Duration metrics
        completed_collaborations = [c for c in collaborations if c.completed_at and c.started_at]
        if completed_collaborations:
            durations = [(c.completed_at - c.started_at).total_seconds() / 3600 for c in completed_collaborations]
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0
        
        # Collaboration type distribution
        type_distribution = {}
        for collab in collaborations:
            collab_type = collab.collaboration_type
            type_distribution[collab_type] = type_distribution.get(collab_type, 0) + 1
        
        # Agent participation
        agent_participation = {}
        for collab in collaborations:
            if collab.agents_involved:
                agents = json.loads(collab.agents_involved)
                for agent_id in agents:
                    agent_participation[agent_id] = agent_participation.get(agent_id, 0) + 1
        
        return {
            "period_days": days,
            "total_collaborations": total_collaborations,
            "successful_collaborations": successful_collaborations,
            "success_rate": success_rate,
            "avg_duration_hours": avg_duration,
            "collaboration_types": type_distribution,
            "agent_participation": agent_participation,
            "efficiency_trends": self._calculate_efficiency_trends(collaborations)
        }
    
    def _calculate_efficiency_trends(self, collaborations: List[TaskCollaboration]) -> Dict[str, float]:
        """Calculate efficiency trends over time"""
        
        completed_collaborations = [c for c in collaborations if c.status == "completed" and c.estimated_duration]
        
        if not completed_collaborations:
            return {"avg_efficiency": 0, "efficiency_trend": 0}
        
        efficiencies = []
        for collab in completed_collaborations:
            if collab.actual_duration and collab.estimated_duration:
                efficiency = (collab.estimated_duration / collab.actual_duration) * 100
                efficiencies.append(min(efficiency, 200))  # Cap at 200%
        
        avg_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 0
        
        # Simple trend calculation (positive means improving efficiency)
        if len(efficiencies) >= 2:
            first_half = efficiencies[:len(efficiencies)//2]
            second_half = efficiencies[len(efficiencies)//2:]
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            efficiency_trend = second_avg - first_avg
        else:
            efficiency_trend = 0
        
        return {
            "avg_efficiency": avg_efficiency,
            "efficiency_trend": efficiency_trend
        }
