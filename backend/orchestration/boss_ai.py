# VirtuAI Office - Boss AI Orchestration System
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging
import re
from enum import Enum
import math
from dataclasses import dataclass, field

import ollama
from sqlalchemy.orm import Session

from ..core.logging import get_logger, log_boss_decision
from ..models.database import Task, Agent, TaskStatus, TaskPriority, AgentType

logger = get_logger('virtuai.boss_ai')

# Enhanced Enums
class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EPIC = "epic"

class TaskType(str, Enum):
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    RESEARCH = "research"
    DESIGN = "design"
    DOCUMENTATION = "documentation"
    TESTING = "testing"

class CollaborationType(str, Enum):
    INDEPENDENT = "independent"  # Single agent task
    SEQUENTIAL = "sequential"    # Tasks depend on each other
    PARALLEL = "parallel"       # Tasks can be done simultaneously
    REVIEW = "review"           # One agent reviews another's work

# Data Classes for Orchestration
@dataclass
class AgentCapability:
    skill: str
    proficiency: float  # 0.0 to 1.0
    recent_performance: float  # 0.0 to 2.0
    
@dataclass
class TaskAnalysis:
    complexity: TaskComplexity
    estimated_effort: float  # hours
    required_skills: List[str]
    keywords: List[str]
    collaboration_needed: bool
    suggested_agents: List[str]
    confidence: float  # 0.0 to 1.0
    task_type: TaskType = TaskType.FEATURE

@dataclass
class CollaborationPlan:
    primary_agent: str
    supporting_agents: List[str]
    collaboration_type: CollaborationType
    workflow_steps: List[Dict[str, Any]]
    estimated_duration: float

@dataclass
class AgentPerformance:
    agent_id: str
    completion_rate: float
    avg_quality_score: float
    avg_response_time: float
    recent_tasks: int
    workload_score: float

# Boss AI - The Orchestration Engine
class BossAI:
    def __init__(self, agent_manager):
        self.agent_manager = agent_manager
        self.model = "llama2:7b"
        self.performance_history = {}
        self.decision_history = []
        self.collaboration_patterns = {}
        
    async def analyze_task(self, task_description: str, task_title: str) -> TaskAnalysis:
        """Analyze a task to determine complexity, requirements, and optimal assignment"""
        
        analysis_prompt = f"""You are the Boss AI, an expert project manager analyzing development tasks.

Task Title: {task_title}
Task Description: {task_description}

Analyze this task and provide a detailed assessment:

1. COMPLEXITY ANALYSIS:
   - Rate complexity: simple, medium, complex, or epic
   - Consider scope, technical requirements, and interdependencies

2. EFFORT ESTIMATION:
   - Estimate hours needed (0.5 to 40 hours)
   - Factor in research, implementation, testing, documentation

3. SKILL REQUIREMENTS:
   - Identify required skills from: react, python, design, testing, product-management, 
     api, database, ui-ux, qa, documentation, architecture, devops
   - Prioritize most critical skills

4. TECHNICAL KEYWORDS:
   - Extract key technical terms and concepts
   - Identify technologies, frameworks, methodologies mentioned

5. COLLABORATION ASSESSMENT:
   - Determine if multiple agents needed
   - Consider if task crosses domain boundaries

6. TASK TYPE:
   - Classify as: feature, bug_fix, research, design, documentation, testing

Respond in valid JSON format:
{{
    "complexity": "medium",
    "estimated_effort": 4.5,
    "required_skills": ["react", "ui-ux", "testing"],
    "keywords": ["component", "responsive", "form", "validation"],
    "collaboration_needed": true,
    "task_type": "feature",
    "confidence": 0.87,
    "reasoning": "Medium complexity due to UI components requiring both development and design input"
}}
"""
        
        try:
            response = await self._call_ollama(analysis_prompt)
            # Parse JSON response
            analysis_data = self._parse_json_response(response)
            
            task_analysis = TaskAnalysis(
                complexity=TaskComplexity(analysis_data.get("complexity", "medium")),
                estimated_effort=analysis_data.get("estimated_effort", 3.0),
                required_skills=analysis_data.get("required_skills", []),
                keywords=analysis_data.get("keywords", []),
                collaboration_needed=analysis_data.get("collaboration_needed", False),
                task_type=TaskType(analysis_data.get("task_type", "feature")),
                suggested_agents=[],
                confidence=analysis_data.get("confidence", 0.7)
            )
            
            logger.info(f"Task analysis completed: {task_analysis.complexity} complexity, "
                       f"{task_analysis.estimated_effort}h effort, "
                       f"skills: {', '.join(task_analysis.required_skills)}")
            
            return task_analysis
            
        except Exception as e:
            logger.warning(f"Boss AI analysis failed, using fallback: {e}")
            # Fallback analysis
            return self._fallback_analysis(task_description, task_title)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from AI model"""
        try:
            # Extract JSON from response (handle cases where AI adds extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: try to parse entire response
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response}")
            raise
    
    def _fallback_analysis(self, task_description: str, task_title: str) -> TaskAnalysis:
        """Fallback analysis using heuristics"""
        text = f"{task_title} {task_description}".lower()
        word_count = len(task_description.split())
        
        # Complexity estimation
        complexity_keywords = {
            TaskComplexity.SIMPLE: ["simple", "basic", "quick", "small", "minor"],
            TaskComplexity.MEDIUM: ["medium", "moderate", "standard", "typical"],
            TaskComplexity.COMPLEX: ["complex", "advanced", "comprehensive", "detailed"],
            TaskComplexity.EPIC: ["epic", "large", "complete", "full", "entire", "system"]
        }
        
        complexity = TaskComplexity.MEDIUM  # default
        for comp, keywords in complexity_keywords.items():
            if any(keyword in text for keyword in keywords):
                complexity = comp
                break
        
        # Effort estimation based on complexity and word count
        effort_map = {
            TaskComplexity.SIMPLE: 1.0 + (word_count / 100),
            TaskComplexity.MEDIUM: 3.0 + (word_count / 50),
            TaskComplexity.COMPLEX: 8.0 + (word_count / 25),
            TaskComplexity.EPIC: 20.0 + (word_count / 10)
        }
        
        estimated_effort = min(effort_map[complexity], 40.0)
        
        # Skill detection
        skill_keywords = {
            "react": ["react", "component", "jsx", "frontend", "ui"],
            "python": ["python", "api", "backend", "fastapi", "django"],
            "design": ["design", "ui", "ux", "mockup", "wireframe"],
            "testing": ["test", "testing", "qa", "bug", "validation"],
            "database": ["database", "sql", "data", "model", "schema"],
            "product-management": ["user story", "requirement", "roadmap", "planning"],
            "documentation": ["document", "guide", "manual", "readme", "wiki"]
        }
        
        required_skills = []
        for skill, keywords in skill_keywords.items():
            if any(keyword in text for keyword in keywords):
                required_skills.append(skill)
        
        if not required_skills:
            required_skills = ["general"]
        
        # Keywords extraction
        technical_words = re.findall(r'\b\w+\b', text)
        keywords = list(set([w for w in technical_words if len(w) > 3 and w in [
            "component", "api", "database", "design", "test", "user", "interface",
            "authentication", "responsive", "form", "validation", "backend", "frontend"
        ]]))[:10]
        
        # Collaboration assessment
        collaboration_needed = (
            len(required_skills) > 2 or
            complexity in [TaskComplexity.COMPLEX, TaskComplexity.EPIC] or
            word_count > 100
        )
        
        # Task type detection
        task_type = TaskType.FEATURE  # default
        type_keywords = {
            TaskType.BUG_FIX: ["bug", "fix", "error", "issue", "problem"],
            TaskType.RESEARCH: ["research", "investigate", "analyze", "explore"],
            TaskType.DESIGN: ["design", "mockup", "wireframe", "prototype"],
            TaskType.DOCUMENTATION: ["document", "guide", "manual", "readme"],
            TaskType.TESTING: ["test", "qa", "validation", "verify"]
        }
        
        for ttype, keywords_list in type_keywords.items():
            if any(keyword in text for keyword in keywords_list):
                task_type = ttype
                break
        
        return TaskAnalysis(
            complexity=complexity,
            estimated_effort=estimated_effort,
            required_skills=required_skills,
            keywords=keywords,
            collaboration_needed=collaboration_needed,
            task_type=task_type,
            suggested_agents=[],
            confidence=0.6  # Lower confidence for fallback
        )
    
    async def assign_optimal_agent(self, task_analysis: TaskAnalysis, available_agents: List,
                                  workloads: Dict[str, float]) -> Tuple[str, float]:
        """Assign the optimal agent based on skills, workload, and performance"""
        
        if not available_agents:
            raise ValueError("No available agents for assignment")
        
        best_agent = None
        best_score = 0.0
        scoring_details = {}
        
        for agent in available_agents:
            score, details = self._calculate_agent_score(agent, task_analysis, workloads.get(agent.id, 0.0))
            scoring_details[agent.name] = details
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        # Log the decision process
        log_boss_decision(
            decision_type="agent_assignment",
            reasoning=f"Selected {best_agent.name} with score {best_score:.3f}",
            task_complexity=task_analysis.complexity.value,
            required_skills=task_analysis.required_skills,
            scoring_details=scoring_details
        )
        
        return best_agent.id if best_agent else None, best_score
    
    def _calculate_agent_score(self, agent, task_analysis: TaskAnalysis,
                              current_workload: float) -> Tuple[float, Dict[str, float]]:
        """Calculate how suitable an agent is for a task"""
        
        # Parse agent expertise
        try:
            agent_skills = set(json.loads(agent.expertise) if agent.expertise else [])
        except (json.JSONDecodeError, TypeError):
            agent_skills = set()
        
        required_skills = set(task_analysis.required_skills)
        
        # Skill match score (0-1)
        if required_skills:
            skill_overlap = len(agent_skills.intersection(required_skills))
            skill_score = min(skill_overlap / len(required_skills), 1.0)
        else:
            skill_score = 0.5  # Neutral if no specific skills required
        
        # Workload penalty (0-1, lower workload = higher score)
        max_workload = 40.0  # hours per week
        workload_score = max(0.0, 1.0 - (current_workload / max_workload))
        
        # Performance bonus (0.5-1.5)
        performance_score = self.performance_history.get(agent.id, 1.0)
        performance_score = max(0.5, min(performance_score, 1.5))
        
        # Agent type bonus for specific task types
        type_bonus = self._get_type_bonus(agent.type, task_analysis)
        
        # Complexity alignment (agents may have preferences for certain complexities)
        complexity_bonus = self._get_complexity_bonus(agent.type, task_analysis.complexity)
        
        # Recent activity penalty (avoid overloading recently active agents)
        recent_activity = self._get_recent_activity_penalty(agent.id)
        
        # Combined score with weights
        weights = {
            'skill': 0.35,
            'workload': 0.25,
            'performance': 0.20,
            'type_bonus': 0.10,
            'complexity': 0.05,
            'recent_activity': 0.05
        }
        
        total_score = (
            skill_score * weights['skill'] +
            workload_score * weights['workload'] +
            performance_score * weights['performance'] +
            type_bonus * weights['type_bonus'] +
            complexity_bonus * weights['complexity'] +
            recent_activity * weights['recent_activity']
        )
        
        # Score details for debugging
        details = {
            'skill_score': skill_score,
            'workload_score': workload_score,
            'performance_score': performance_score,
            'type_bonus': type_bonus,
            'complexity_bonus': complexity_bonus,
            'recent_activity': recent_activity,
            'total_score': total_score,
            'current_workload': current_workload,
            'skill_overlap': len(agent_skills.intersection(required_skills)),
            'agent_skills': list(agent_skills),
            'required_skills': list(required_skills)
        }
        
        return total_score, details
    
    def _get_type_bonus(self, agent_type, task_analysis: TaskAnalysis) -> float:
        """Bonus score based on agent type alignment with task"""
        type_bonuses = {
            AgentType.PRODUCT_MANAGER: {
                TaskType.DOCUMENTATION: 0.3,
                TaskType.RESEARCH: 0.2,
                TaskComplexity.EPIC: 0.2
            },
            AgentType.FRONTEND_DEVELOPER: {
                TaskType.FEATURE: 0.2,
                TaskType.DESIGN: 0.1
            },
            AgentType.BACKEND_DEVELOPER: {
                TaskType.FEATURE: 0.2,
                TaskType.BUG_FIX: 0.1
            },
            AgentType.UI_UX_DESIGNER: {
                TaskType.DESIGN: 0.3,
                TaskType.FEATURE: 0.1
            },
            AgentType.QA_TESTER: {
                TaskType.TESTING: 0.3,
                TaskType.BUG_FIX: 0.2
            }
        }
        
        bonuses = type_bonuses.get(agent_type, {})
        task_type_bonus = bonuses.get(task_analysis.task_type, 0.0)
        complexity_bonus = bonuses.get(task_analysis.complexity, 0.0)
        
        return max(task_type_bonus, complexity_bonus)
    
    def _get_complexity_bonus(self, agent_type, complexity: TaskComplexity) -> float:
        """Bonus based on agent's preference for task complexity"""
        complexity_preferences = {
            AgentType.PRODUCT_MANAGER: {
                TaskComplexity.COMPLEX: 0.1,
                TaskComplexity.EPIC: 0.2
            },
            AgentType.FRONTEND_DEVELOPER: {
                TaskComplexity.SIMPLE: 0.1,
                TaskComplexity.MEDIUM: 0.1
            },
            AgentType.BACKEND_DEVELOPER: {
                TaskComplexity.MEDIUM: 0.1,
                TaskComplexity.COMPLEX: 0.1
            },
            AgentType.UI_UX_DESIGNER: {
                TaskComplexity.SIMPLE: 0.1,
                TaskComplexity.MEDIUM: 0.1
            },
            AgentType.QA_TESTER: {
                TaskComplexity.SIMPLE: 0.05,
                TaskComplexity.MEDIUM: 0.1
            }
        }
        
        preferences = complexity_preferences.get(agent_type, {})
        return preferences.get(complexity, 0.0)
    
    def _get_recent_activity_penalty(self, agent_id: str) -> float:
        """Penalty for agents who have been very active recently"""
        # This would track recent task assignments
        # For now, return neutral score
        return 0.0
    
    async def plan_collaboration(self, task_analysis: TaskAnalysis, primary_agent_id: str,
                               available_agents: List) -> Optional[CollaborationPlan]:
        """Create a collaboration plan if the task requires multiple agents"""
        
        if not task_analysis.collaboration_needed:
            return None
        
        collaboration_prompt = f"""You are the Boss AI planning a collaborative development task.

Task Analysis:
- Complexity: {task_analysis.complexity}
- Required Skills: {', '.join(task_analysis.required_skills)}
- Estimated Effort: {task_analysis.estimated_effort} hours
- Task Type: {task_analysis.task_type}

Primary Agent: {primary_agent_id}

Available Supporting Agents:
"""
        
        for agent in available_agents:
            if agent.id != primary_agent_id:
                expertise = json.loads(agent.expertise) if agent.expertise else []
                collaboration_prompt += f"- {agent.name} ({agent.type.value}): {', '.join(expertise)}\n"
        
        collaboration_prompt += """
Plan the optimal collaboration workflow:

1. SUPPORTING AGENTS:
   - Which agents should support the primary agent?
   - Consider skill complementarity and workload

2. COLLABORATION TYPE:
   - sequential: Agents work one after another in a specific order
   - parallel: Agents work simultaneously on different aspects
   - review: Supporting agents review and improve primary agent's work

3. WORKFLOW STEPS:
   - Define specific tasks for each agent
   - Estimate duration for each step
   - Consider dependencies and handoffs

4. ESTIMATED DURATION:
   - Total time for collaborative effort
   - Factor in coordination overhead

Respond in valid JSON format:
{
    "supporting_agents": ["agent_id_1", "agent_id_2"],
    "collaboration_type": "sequential",
    "workflow_steps": [
        {"agent": "agent_id_1", "task": "Create initial design mockups", "duration": 2.0, "order": 1},
        {"agent": "primary", "task": "Implement component based on design", "duration": 4.0, "order": 2},
        {"agent": "agent_id_2", "task": "Review and create test cases", "duration": 1.5, "order": 3}
    ],
    "estimated_duration": 7.5,
    "coordination_overhead": 0.5
}
"""
        
        try:
            response = await self._call_ollama(collaboration_prompt)
            plan_data = self._parse_json_response(response)
            
            collaboration_plan = CollaborationPlan(
                primary_agent=primary_agent_id,
                supporting_agents=plan_data.get("supporting_agents", []),
                collaboration_type=CollaborationType(plan_data.get("collaboration_type", "sequential")),
                workflow_steps=plan_data.get("workflow_steps", []),
                estimated_duration=plan_data.get("estimated_duration", task_analysis.estimated_effort)
            )
            
            log_boss_decision(
                decision_type="collaboration_planning",
                reasoning=f"Planned {collaboration_plan.collaboration_type} collaboration with "
                         f"{len(collaboration_plan.supporting_agents)} supporting agents",
                primary_agent=primary_agent_id,
                supporting_agents=collaboration_plan.supporting_agents,
                workflow_steps=len(collaboration_plan.workflow_steps)
            )
            
            return collaboration_plan
            
        except Exception as e:
            logger.warning(f"Collaboration planning failed: {e}")
            return None
    
    async def conduct_daily_standup(self, db: Session) -> Dict[str, Any]:
        """Generate AI-powered daily standup insights"""
        
        # Get recent data
        yesterday = datetime.utcnow() - timedelta(days=1)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Query recent tasks
        completed_yesterday = db.query(Task).filter(
            Task.completed_at >= yesterday,
            Task.status == TaskStatus.COMPLETED
        ).all()
        
        in_progress = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).all()
        upcoming = db.query(Task).filter(Task.status == TaskStatus.PENDING).limit(10).all()
        
        # Analyze team performance
        weekly_completed = db.query(Task).filter(
            Task.completed_at >= week_ago,
            Task.status == TaskStatus.COMPLETED
        ).count()
        
        weekly_created = db.query(Task).filter(Task.created_at >= week_ago).count()
        
        standup_prompt = f"""You are the Boss AI conducting a daily standup for the AI development team.

TEAM STATUS SUMMARY:
- Yesterday: {len(completed_yesterday)} tasks completed
- Currently: {len(in_progress)} tasks in progress
- Queue: {len(upcoming)} tasks pending
- This week: {weekly_completed} completed, {weekly_created} created

COMPLETED YESTERDAY:
"""
        
        for task in completed_yesterday[:5]:  # Top 5 tasks
            agent_name = task.agent.name if task.agent else "Unknown"
            standup_prompt += f"- {task.title} (by {agent_name})\n"
        
        standup_prompt += f"\nIN PROGRESS TODAY:\n"
        for task in in_progress[:5]:  # Top 5 tasks
            agent_name = task.agent.name if task.agent else "Unknown"
            standup_prompt += f"- {task.title} (by {agent_name})\n"
        
        standup_prompt += f"""
ANALYSIS REQUIREMENTS:
1. Assess overall team health and productivity
2. Identify key achievements and momentum
3. Highlight current focus areas and priorities
4. Spot potential blockers or risks
5. Provide actionable recommendations for today

Be encouraging yet realistic. Focus on actionable insights.
Provide a professional standup summary that a development team would find valuable.

Respond with insights in a structured format."""
        
        try:
            insights = await self._call_ollama(standup_prompt)
            
            # Calculate team metrics
            velocity = len(completed_yesterday)
            throughput = weekly_completed / 7 if weekly_completed > 0 else 0
            queue_health = "healthy" if len(upcoming) < 20 else "backlogged"
            
            recommendations = self._generate_recommendations(completed_yesterday, in_progress, upcoming)
            
            standup_data = {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "ai_insights": insights,
                "team_metrics": {
                    "velocity": velocity,
                    "work_in_progress": len(in_progress),
                    "queue_size": len(upcoming),
                    "weekly_throughput": round(throughput, 2),
                    "queue_health": queue_health
                },
                "completed_yesterday": [
                    {
                        "task_id": task.id,
                        "title": task.title,
                        "agent_name": task.agent.name if task.agent else "Unknown",
                        "effort": task.actual_effort
                    } for task in completed_yesterday
                ],
                "in_progress_today": [
                    {
                        "task_id": task.id,
                        "title": task.title,
                        "agent_name": task.agent.name if task.agent else "Unknown",
                        "started_at": task.started_at.isoformat() if task.started_at else None
                    } for task in in_progress
                ],
                "upcoming_tasks": [
                    {
                        "task_id": task.id,
                        "title": task.title,
                        "priority": task.priority.value,
                        "estimated_effort": task.estimated_effort
                    } for task in upcoming
                ],
                "recommendations": recommendations
            }
            
            log_boss_decision(
                decision_type="daily_standup",
                reasoning="Generated daily standup insights",
                completed_yesterday=len(completed_yesterday),
                in_progress=len(in_progress),
                upcoming=len(upcoming),
                velocity=velocity
            )
            
            return standup_data
            
        except Exception as e:
            logger.error(f"Standup generation failed: {e}")
            return {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "ai_insights": "Unable to generate detailed insights at this time",
                "team_metrics": {
                    "velocity": len(completed_yesterday),
                    "work_in_progress": len(in_progress),
                    "queue_size": len(upcoming)
                },
                "error": str(e)
            }
    
    def _generate_recommendations(self, completed, in_progress, upcoming) -> List[str]:
        """Generate actionable recommendations based on team status"""
        recommendations = []
        
        # Workload analysis
        if len(in_progress) > 10:
            recommendations.append("Consider limiting work in progress to improve focus and flow")
        
        if len(upcoming) > 25:
            recommendations.append("High backlog detected - prioritize tasks or consider capacity planning")
        elif len(upcoming) < 5:
            recommendations.append("Low task queue - ensure continuous work pipeline")
        
        # Productivity analysis
        if len(completed) == 0:
            recommendations.append("No tasks completed recently - investigate potential blockers")
        elif len(completed) > 5:
            recommendations.append("High productivity detected - excellent team momentum!")
        
        # Balance analysis
        if len(in_progress) > len(upcoming):
            recommendations.append("More tasks in progress than queued - prepare next sprint items")
        
        # Quality focus
        if len(completed) > 0:
            avg_effort = sum(task.actual_effort or 0 for task in completed) / len(completed)
            if avg_effort < 1:
                recommendations.append("Quick task completion - consider quality checkpoints")
            elif avg_effort > 8:
                recommendations.append("High effort tasks - consider breaking down complex work")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def optimize_team_workload(self, db: Session) -> Dict[str, Any]:
        """Analyze and optimize team workload distribution"""
        
        # Get current workload distribution
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        workload_analysis = {}
        
        for agent in agents:
            active_tasks = db.query(Task).filter(
                Task.agent_id == agent.id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            ).all()
            
            total_effort = sum(task.estimated_effort or 3 for task in active_tasks)
            task_count = len(active_tasks)
            
            workload_analysis[agent.id] = {
                'agent_name': agent.name,
                'agent_type': agent.type.value,
                'active_tasks': task_count,
                'total_effort': total_effort,
                'tasks': [{'id': t.id, 'title': t.title, 'effort': t.estimated_effort or 3} for t in active_tasks]
            }
        
        # Calculate optimization suggestions
        total_effort = sum(data['total_effort'] for data in workload_analysis.values())
        avg_effort = total_effort / len(agents) if agents else 0
        
        overloaded_agents = [
            agent_id for agent_id, data in workload_analysis.items()
            if data['total_effort'] > avg_effort * 1.5
        ]
        
        underloaded_agents = [
            agent_id for agent_id, data in workload_analysis.items()
            if data['total_effort'] < avg_effort * 0.5
        ]
        
        optimization_suggestions = []
        
        if overloaded_agents and underloaded_agents:
            optimization_suggestions.append({
                'type': 'workload_rebalancing',
                'overloaded_agents': [workload_analysis[aid]['agent_name'] for aid in overloaded_agents],
                'underloaded_agents': [workload_analysis[aid]['agent_name'] for aid in underloaded_agents],
                'suggestion': 'Consider reassigning some tasks from overloaded to underloaded agents'
            })
        
        if len(overloaded_agents) > 0:
            optimization_suggestions.append({
                'type': 'capacity_warning',
                'agents': [workload_analysis[aid]['agent_name'] for aid in overloaded_agents],
                'suggestion': 'Some agents are heavily loaded - monitor for bottlenecks'
            })
        
        log_boss_decision(
            decision_type="workload_optimization",
            reasoning="Analyzed team workload distribution",
            total_effort=total_effort,
            avg_effort=avg_effort,
            overloaded_count=len(overloaded_agents),
            underloaded_count=len(underloaded_agents)
        )
        
        return {
            'workload_analysis': workload_analysis,
            'optimization_suggestions': optimization_suggestions,
            'metrics': {
                'total_effort': total_effort,
                'average_effort': round(avg_effort, 2),
                'overloaded_agents': len(overloaded_agents),
                'underloaded_agents': len(underloaded_agents),
                'balance_score': self._calculate_balance_score(workload_analysis)
            }
        }
    
    def _calculate_balance_score(self, workload_analysis: Dict) -> float:
        """Calculate a balance score (0-1) for workload distribution"""
        if not workload_analysis:
            return 1.0
        
        efforts = [data['total_effort'] for data in workload_analysis.values()]
        if not efforts:
            return 1.0
        
        mean_effort = sum(efforts) / len(efforts)
        variance = sum((effort - mean_effort) ** 2 for effort in efforts) / len(efforts)
        
        # Convert variance to balance score (lower variance = higher balance)
        if mean_effort == 0:
            return 1.0
        
        coefficient_of_variation = (variance ** 0.5) / mean_effort if mean_effort > 0 else 0
        balance_score = max(0.0, 1.0 - coefficient_of_variation)
        
        return round(balance_score, 3)
    
    async def predict_task_completion_time(self, task_analysis: TaskAnalysis, agent_id: str) -> Dict[str, Any]:
        """Predict when a task will be completed based on agent performance and workload"""
        
        # Get historical performance for this agent
        agent_performance = self.performance_history.get(agent_id, {
            'avg_completion_time': 1.0,
            'efficiency_factor': 1.0,
            'complexity_adjustment': {}
        })
        
        # Base estimate from task analysis
        base_estimate = task_analysis.estimated_effort
        
        # Adjust for agent efficiency
        efficiency_factor = agent_performance.get('efficiency_factor', 1.0)
        adjusted_estimate = base_estimate * efficiency_factor
        
        # Adjust for task complexity
        complexity_adjustments = agent_performance.get('complexity_adjustment', {})
        complexity_factor = complexity_adjustments.get(task_analysis.complexity.value, 1.0)
        final_estimate = adjusted_estimate * complexity_factor
        
        # Add buffer for collaboration if needed
        if task_analysis.collaboration_needed:
            final_estimate *= 1.3  # 30% overhead for collaboration
        
        # Predict completion time
        current_time = datetime.utcnow()
        estimated_completion = current_time + timedelta(hours=final_estimate)
        
        prediction = {
            'estimated_hours': round(final_estimate, 2),
            'estimated_completion': estimated_completion.isoformat(),
            'confidence': task_analysis.confidence * 0.8,  # Slightly lower confidence for time prediction
            'factors': {
                'base_estimate': base_estimate,
                'efficiency_factor': efficiency_factor,
                'complexity_factor': complexity_factor,
                'collaboration_overhead': 1.3 if task_analysis.collaboration_needed else 1.0
            }
        }
        
        logger.info(f"Task completion prediction: {final_estimate:.2f} hours for agent {agent_id}")
        
        return prediction
    
    async def analyze_team_performance_trends(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Analyze team performance trends over time"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get completed tasks in the period
        completed_tasks = db.query(Task).filter(
            Task.completed_at >= start_date,
            Task.status == TaskStatus.COMPLETED
        ).all()
        
        if not completed_tasks:
            return {
                'period_days': days,
                'total_tasks': 0,
                'message': 'No completed tasks in the analysis period'
            }
        
        # Analyze by day
        daily_stats = {}
        for task in completed_tasks:
            day = task.completed_at.date().isoformat()
            if day not in daily_stats:
                daily_stats[day] = {
                    'completed': 0,
                    'total_effort': 0,
                    'avg_effort': 0
                }
            
            daily_stats[day]['completed'] += 1
            daily_stats[day]['total_effort'] += task.actual_effort or 0
        
        # Calculate averages
        for day_data in daily_stats.values():
            day_data['avg_effort'] = (
                day_data['total_effort'] / day_data['completed']
                if day_data['completed'] > 0 else 0
            )
        
        # Analyze by agent
        agent_stats = {}
        for task in completed_tasks:
            if not task.agent_id:
                continue
            
            agent_name = task.agent.name if task.agent else 'Unknown'
            if agent_name not in agent_stats:
                agent_stats[agent_name] = {
                    'completed': 0,
                    'total_effort': 0,
                    'avg_effort': 0,
                    'complexities': {}
                }
            
            stats = agent_stats[agent_name]
            stats['completed'] += 1
            stats['total_effort'] += task.actual_effort or 0
            
            # Track complexity distribution
            complexity = getattr(task, 'complexity', 'medium')
            stats['complexities'][complexity] = stats['complexities'].get(complexity, 0) + 1
        
        # Calculate agent averages
        for agent_data in agent_stats.values():
            agent_data['avg_effort'] = (
                agent_data['total_effort'] / agent_data['completed']
                if agent_data['completed'] > 0 else 0
            )
        
        # Calculate trends
        sorted_days = sorted(daily_stats.keys())
        if len(sorted_days) >= 7:
            # Calculate weekly trend
            recent_week = sorted_days[-7:]
            earlier_week = sorted_days[-14:-7] if len(sorted_days) >= 14 else sorted_days[:-7]
            
            recent_avg = sum(daily_stats[day]['completed'] for day in recent_week) / len(recent_week)
            earlier_avg = sum(daily_stats[day]['completed'] for day in earlier_week) / len(earlier_week) if earlier_week else recent_avg
            
            trend = (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0
        else:
            trend = 0
        
        # Overall statistics
        total_completed = len(completed_tasks)
        avg_daily_completion = total_completed / days
        total_effort = sum(task.actual_effort or 0 for task in completed_tasks)
        avg_task_effort = total_effort / total_completed if total_completed > 0 else 0
        
        analysis = {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'total_tasks': total_completed,
            'avg_daily_completion': round(avg_daily_completion, 2),
            'avg_task_effort': round(avg_task_effort, 2),
            'trend_percentage': round(trend * 100, 1),
            'trend_direction': 'improving' if trend > 0.1 else 'declining' if trend < -0.1 else 'stable',
            'daily_stats': daily_stats,
            'agent_performance': agent_stats,
            'insights': self._generate_performance_insights(trend, avg_daily_completion, agent_stats)
        }
        
        log_boss_decision(
            decision_type="performance_analysis",
            reasoning=f"Analyzed {days}-day performance trends",
            total_tasks=total_completed,
            trend_direction=analysis['trend_direction'],
            avg_daily_completion=avg_daily_completion
        )
        
        return analysis
    
    def _generate_performance_insights(self, trend: float, avg_daily: float, agent_stats: Dict) -> List[str]:
        """Generate insights from performance analysis"""
        insights = []
        
        # Trend insights
        if trend > 0.2:
            insights.append("📈 Team productivity is improving significantly")
        elif trend < -0.2:
            insights.append("📉 Team productivity has declined - investigate blockers")
        else:
            insights.append("📊 Team productivity is stable")
        
        # Workload insights
        if avg_daily > 5:
            insights.append("🚀 High task completion rate - excellent team velocity")
        elif avg_daily < 1:
            insights.append("⚠️ Low task completion rate - consider smaller task sizes")
        
        # Agent insights
        if agent_stats:
            top_performer = max(agent_stats.items(), key=lambda x: x[1]['completed'])
            insights.append(f"⭐ Top performer: {top_performer[0]} with {top_performer[1]['completed']} completed tasks")
            
            # Check for workload imbalances
            completion_counts = [stats['completed'] for stats in agent_stats.values()]
            if max(completion_counts) > min(completion_counts) * 2:
                insights.append("⚖️ Workload imbalance detected among agents")
        
        return insights
    
    async def suggest_task_prioritization(self, db: Session, limit: int = 10) -> Dict[str, Any]:
        """Suggest task prioritization based on various factors"""
        
        # Get pending tasks
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).all()
        
        if not pending_tasks:
            return {
                'message': 'No pending tasks to prioritize',
                'suggestions': []
            }
        
        # Score each task for prioritization
        task_scores = []
        
        for task in pending_tasks:
            score = self._calculate_priority_score(task)
            task_scores.append({
                'task': task,
                'score': score,
                'factors': score['factors']
            })
        
        # Sort by score
        task_scores.sort(key=lambda x: x['score']['total'], reverse=True)
        
        # Get top suggestions
        top_tasks = task_scores[:limit]
        
        suggestions = []
        for i, item in enumerate(top_tasks, 1):
            task = item['task']
            suggestions.append({
                'rank': i,
                'task_id': task.id,
                'title': task.title,
                'current_priority': task.priority.value,
                'suggested_priority': self._suggest_priority_level(item['score']['total']),
                'score': round(item['score']['total'], 3),
                'reasoning': self._explain_priority_reasoning(item['factors'])
            })
        
        log_boss_decision(
            decision_type="task_prioritization",
            reasoning=f"Analyzed {len(pending_tasks)} pending tasks",
            top_suggestions=len(suggestions)
        )
        
        return {
            'total_pending': len(pending_tasks),
            'analyzed': len(task_scores),
            'suggestions': suggestions,
            'prioritization_factors': [
                'Business priority (urgent, high, medium, low)',
                'Task age (how long it has been waiting)',
                'Estimated effort (quicker wins scored higher)',
                'Dependencies (tasks blocking others scored higher)',
                'Strategic alignment (feature > bug_fix > documentation)'
            ]
        }
    
    def _calculate_priority_score(self, task) -> Dict[str, Any]:
        """Calculate a priority score for a task"""
        
        # Base priority score
        priority_scores = {
            TaskPriority.URGENT: 1.0,
            TaskPriority.HIGH: 0.8,
            TaskPriority.MEDIUM: 0.5,
            TaskPriority.LOW: 0.2
        }
        priority_score = priority_scores.get(task.priority, 0.5)
        
        # Age factor (older tasks get slight priority boost)
        age_days = (datetime.utcnow() - task.created_at).days
        age_score = min(age_days / 30, 0.3)  # Max 0.3 boost for tasks over 30 days old
        
        # Effort factor (prefer quick wins)
        estimated_effort = getattr(task, 'estimated_effort', 3) or 3
        effort_score = max(0.1, 1.0 - (estimated_effort / 20))  # Normalize to 0.1-1.0
        
        # Task type factor
        type_scores = {
            'feature': 0.8,
            'bug_fix': 0.6,
            'research': 0.5,
            'design': 0.7,
            'documentation': 0.4,
            'testing': 0.6
        }
        task_type = getattr(task, 'task_type', 'feature')
        type_score = type_scores.get(task_type, 0.5)
        
        # Combine scores with weights
        weights = {
            'priority': 0.4,
            'age': 0.2,
            'effort': 0.25,
            'type': 0.15
        }
        
        total_score = (
            priority_score * weights['priority'] +
            age_score * weights['age'] +
            effort_score * weights['effort'] +
            type_score * weights['type']
        )
        
        return {
            'total': total_score,
            'factors': {
                'priority_score': priority_score,
                'age_score': age_score,
                'effort_score': effort_score,
                'type_score': type_score,
                'age_days': age_days,
                'estimated_effort': estimated_effort
            }
        }
    
    def _suggest_priority_level(self, score: float) -> str:
        """Suggest priority level based on score"""
        if score >= 0.8:
            return 'urgent'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _explain_priority_reasoning(self, factors: Dict) -> str:
        """Generate human-readable reasoning for priority suggestion"""
        reasons = []
        
        if factors['priority_score'] >= 0.8:
            reasons.append("high business priority")
        
        if factors['age_days'] > 7:
            reasons.append(f"waiting {factors['age_days']} days")
        
        if factors['effort_score'] >= 0.7:
            reasons.append("quick win (low effort)")
        
        if factors['type_score'] >= 0.7:
            reasons.append("strategic task type")
        
        return ", ".join(reasons) or "balanced factors"
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for Boss AI decisions"""
        try:
            response = await asyncio.to_thread(
                ollama.generate,
                model=self.model,
                prompt=prompt,
                stream=False
            )
            return response['response']
        except Exception as e:
            logger.error(f"Boss AI Ollama call failed: {e}")
            raise
    
    def update_agent_performance(self, agent_id: str, task_completion_data: Dict):
        """Update agent performance history"""
        if agent_id not in self.performance_history:
            self.performance_history[agent_id] = {
                'avg_completion_time': 1.0,
                'efficiency_factor': 1.0,
                'complexity_adjustment': {},
                'task_count': 0,
                'quality_scores': []
            }
        
        performance = self.performance_history[agent_id]
        
        # Update efficiency factor based on estimated vs actual effort
        if 'estimated_effort' in task_completion_data and 'actual_effort' in task_completion_data:
            estimated = task_completion_data['estimated_effort']
            actual = task_completion_data['actual_effort']
            
            if estimated > 0 and actual > 0:
                efficiency = estimated / actual
                # Exponential moving average
                alpha = 0.3
                performance['efficiency_factor'] = (
                    alpha * efficiency + (1 - alpha) * performance['efficiency_factor']
                )
        
        # Update task count
        performance['task_count'] += 1
        
        # Update quality scores if provided
        if 'quality_score' in task_completion_data:
            performance['quality_scores'].append(task_completion_data['quality_score'])
            # Keep only last 10 scores
            performance['quality_scores'] = performance['quality_scores'][-10:]
        
        logger.debug(f"Updated performance for agent {agent_id}: efficiency={performance['efficiency_factor']:.3f}")
    
    def get_decision_history(self, limit: int = 20) -> List[Dict]:
        """Get recent Boss AI decisions"""
        return self.decision_history[-limit:] if self.decision_history else []
    
    def record_decision(self, decision_data: Dict):
        """Record a Boss AI decision"""
        decision_data['timestamp'] = datetime.utcnow().isoformat()
        self.decision_history.append(decision_data)
        
        # Keep only last 100 decisions
        self.decision_history = self.decision_history[-100:]
