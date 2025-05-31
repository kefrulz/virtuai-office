# VirtuAI Office - Boss AI API Endpoints
# Epic 4: AI Orchestration & Collaboration System

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import logging

from ..models.database import get_db
from ..models.pydantic import *
from ..orchestration.boss_ai import BossAI
from ..orchestration.task_assignment import SmartTaskAssignment
from ..orchestration.collaboration import AgentCollaborationManager
from ..orchestration.performance import PerformanceAnalytics
from ..agents.agent_manager import agent_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/boss", tags=["Boss AI"])

# Initialize Boss AI system
boss_ai = BossAI(agent_manager)
smart_assignment = SmartTaskAssignment(boss_ai, agent_manager)
collaboration_manager = AgentCollaborationManager(agent_manager)
performance_analytics = PerformanceAnalytics()

@router.get("/insights")
async def get_boss_insights(db: Session = Depends(get_db)):
    """Get comprehensive Boss AI insights and recommendations"""
    
    try:
        # Generate daily standup insights
        standup_data = await boss_ai.conduct_daily_standup(db)
        
        # Get recent Boss AI decisions
        recent_decisions = db.query(BossDecision).order_by(
            BossDecision.created_at.desc()
        ).limit(10).all()
        
        decision_summaries = []
        for decision in recent_decisions:
            decision_summaries.append({
                "type": decision.decision_type,
                "reasoning": decision.reasoning,
                "created_at": decision.created_at.isoformat(),
                "outcome": json.loads(decision.outcome) if decision.outcome else {}
            })
        
        # Generate system recommendations
        system_recommendations = await _generate_system_recommendations(db)
        
        # Get team health metrics
        team_health = await _calculate_team_health(db)
        
        return {
            "standup": standup_data,
            "recent_decisions": decision_summaries,
            "system_recommendations": system_recommendations,
            "team_health": team_health,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Boss insights generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Insights generation failed: {str(e)}")

@router.post("/optimize-assignments")
async def optimize_task_assignments(db: Session = Depends(get_db)):
    """Let Boss AI optimize current task assignments"""
    
    try:
        # Get all pending tasks
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).all()
        
        if not pending_tasks:
            return {
                "optimized_tasks": 0,
                "total_tasks": 0,
                "message": "No pending tasks to optimize"
            }
        
        optimization_results = []
        
        for task in pending_tasks:
            try:
                if not task.agent_id:  # Only optimize unassigned tasks
                    result = await smart_assignment.assign_task_intelligently(task, db)
                    optimization_results.append({
                        "task_id": task.id,
                        "task_title": task.title,
                        "optimized": True,
                        "assigned_to": result["assigned_agent_id"],
                        "confidence": result["confidence"],
                        "reasoning": result.get("analysis", {}).get("reasoning", "Optimized assignment")
                    })
                else:
                    optimization_results.append({
                        "task_id": task.id,
                        "task_title": task.title,
                        "optimized": False,
                        "reason": "Already assigned to agent"
                    })
            except Exception as e:
                optimization_results.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "optimized": False,
                    "error": str(e)
                })
        
        db.commit()
        
        optimized_count = len([r for r in optimization_results if r.get("optimized")])
        
        # Record the optimization decision
        _record_boss_decision(
            "bulk_optimization",
            {
                "total_tasks": len(pending_tasks),
                "optimized_tasks": optimized_count
            },
            f"Bulk optimized {optimized_count} out of {len(pending_tasks)} pending tasks",
            {"optimization_results": optimization_results},
            db
        )
        
        return {
            "optimized_tasks": optimized_count,
            "total_tasks": len(pending_tasks),
            "results": optimization_results,
            "message": f"Successfully optimized {optimized_count} task assignments"
        }
        
    except Exception as e:
        logger.error(f"Task assignment optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.post("/rebalance-workload")
async def rebalance_team_workload(db: Session = Depends(get_db)):
    """Boss AI rebalances workload across agents"""
    
    try:
        # Get current workloads
        workloads = smart_assignment._get_agent_workloads(db)
        
        if not workloads:
            return {
                "rebalanced": False,
                "message": "No active tasks to rebalance"
            }
        
        # Get agent details
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        
        # Calculate workload statistics
        avg_workload = sum(workloads.values()) / len(workloads) if workloads else 0
        overloaded_agents = {aid: load for aid, load in workloads.items() if load > avg_workload * 1.5}
        underloaded_agents = {aid: load for aid, load in workloads.items() if load < avg_workload * 0.5}
        
        # Generate Boss AI analysis
        rebalancing_analysis = await boss_ai._call_ollama(f"""
You are the Boss AI analyzing team workload distribution.

Current workload statistics:
- Average workload: {avg_workload:.1f} tasks per agent
- Overloaded agents: {len(overloaded_agents)}
- Underloaded agents: {len(underloaded_agents)}

Analyze and provide recommendations for optimal team performance.
Focus on maintaining team morale and delivery timelines.
        """)
        
        rebalancing_actions = []
        
        # Simple rebalancing logic
        if overloaded_agents and underloaded_agents:
            for overloaded_agent_id in list(overloaded_agents.keys())[:3]:  # Limit to top 3
                # Get pending tasks from overloaded agent
                pending_tasks = db.query(Task).filter(
                    Task.agent_id == overloaded_agent_id,
                    Task.status == TaskStatus.PENDING
                ).order_by(Task.priority.desc()).limit(2).all()
                
                for task in pending_tasks:
                    # Find best underloaded agent for this task
                    for underloaded_agent_id in underloaded_agents:
                        underloaded_agent = db.query(Agent).filter(Agent.id == underloaded_agent_id).first()
                        overloaded_agent = db.query(Agent).filter(Agent.id == overloaded_agent_id).first()
                        
                        if underloaded_agent and overloaded_agent:
                            # Check if underloaded agent can handle this task type
                            agent_instance = agent_manager.get_agent(underloaded_agent.type)
                            if agent_instance and agent_instance.can_handle_task(task.description) > 0.3:
                                # Reassign task
                                task.agent_id = underloaded_agent_id
                                
                                rebalancing_actions.append({
                                    "task_id": task.id,
                                    "task_title": task.title,
                                    "from_agent": overloaded_agent.name,
                                    "to_agent": underloaded_agent.name,
                                    "reason": "workload_balancing",
                                    "confidence": agent_instance.can_handle_task(task.description)
                                })
                                
                                # Update workload tracking
                                workloads[overloaded_agent_id] -= 1
                                workloads[underloaded_agent_id] = workloads.get(underloaded_agent_id, 0) + 1
                                break
        
        db.commit()
        
        # Record the rebalancing decision
        _record_boss_decision(
            "workload_rebalancing",
            {
                "initial_workloads": dict(workloads),
                "overloaded_agents": list(overloaded_agents.keys()),
                "underloaded_agents": list(underloaded_agents.keys()),
                "avg_workload": avg_workload
            },
            rebalancing_analysis,
            {
                "actions_taken": len(rebalancing_actions),
                "rebalancing_actions": rebalancing_actions
            },
            db
        )
        
        return {
            "rebalanced": len(rebalancing_actions) > 0,
            "actions_taken": len(rebalancing_actions),
            "workload_analysis": rebalancing_analysis,
            "rebalancing_actions": rebalancing_actions,
            "workload_stats": {
                "average_workload": avg_workload,
                "overloaded_agents": len(overloaded_agents),
                "underloaded_agents": len(underloaded_agents),
                "total_agents": len(agents)
            },
            "new_workloads": smart_assignment._get_agent_workloads(db)
        }
        
    except Exception as e:
        logger.error(f"Workload rebalancing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rebalancing failed: {str(e)}")

@router.post("/analyze-task")
async def analyze_task_complexity(
    title: str,
    description: str,
    db: Session = Depends(get_db)
):
    """Analyze task complexity and get Boss AI recommendations"""
    
    try:
        # Use Boss AI to analyze the task
        analysis = await boss_ai.analyze_task(description, title)
        
        # Get optimal agent recommendation
        available_agents = db.query(Agent).filter(Agent.is_active == True).all()
        workloads = smart_assignment._get_agent_workloads(db)
        
        optimal_agent_id, confidence = await boss_ai.assign_optimal_agent(
            analysis, available_agents, workloads
        )
        
        optimal_agent = db.query(Agent).filter(Agent.id == optimal_agent_id).first()
        
        # Check if collaboration is recommended
        collaboration_plan = None
        if analysis.collaboration_needed:
            collaboration_plan = await boss_ai.plan_collaboration(
                analysis, optimal_agent_id, available_agents
            )
        
        return {
            "analysis": {
                "complexity": analysis.complexity.value,
                "estimated_effort": analysis.estimated_effort,
                "required_skills": analysis.required_skills,
                "keywords": analysis.keywords,
                "collaboration_needed": analysis.collaboration_needed,
                "confidence": analysis.confidence
            },
            "recommendations": {
                "optimal_agent": {
                    "id": optimal_agent.id,
                    "name": optimal_agent.name,
                    "type": optimal_agent.type.value,
                    "confidence": confidence
                } if optimal_agent else None,
                "collaboration_plan": {
                    "type": collaboration_plan.collaboration_type.value,
                    "supporting_agents": len(collaboration_plan.supporting_agents),
                    "estimated_duration": collaboration_plan.estimated_duration,
                    "workflow_steps": len(collaboration_plan.workflow_steps)
                } if collaboration_plan else None
            },
            "current_workloads": workloads
        }
        
    except Exception as e:
        logger.error(f"Task analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/team-performance")
async def get_team_performance(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get comprehensive team performance analytics"""
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get tasks completed in the specified period
        completed_tasks = db.query(Task).filter(
            Task.completed_at >= start_date,
            Task.status == TaskStatus.COMPLETED
        ).all()
        
        # Get agent performance metrics
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        agent_performance = []
        
        for agent in agents:
            agent_tasks = [t for t in completed_tasks if t.agent_id == agent.id]
            
            if agent_tasks:
                performance_data = performance_analytics.analyze_agent_performance(
                    agent.id, agent_tasks, db
                )
                
                agent_performance.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "agent_type": agent.type.value,
                    "tasks_completed": len(agent_tasks),
                    "performance_score": performance_data["performance_score"],
                    "efficiency": performance_data["efficiency"],
                    "quality": performance_data["quality"],
                    "avg_completion_time": performance_data["avg_completion_time"]
                })
        
        # Team-wide metrics
        total_tasks = len(completed_tasks)
        avg_completion_time = sum([
            (task.completed_at - task.started_at).total_seconds() / 3600
            for task in completed_tasks if task.started_at and task.completed_at
        ]) / total_tasks if total_tasks > 0 else 0
        
        # Collaboration metrics
        collaborations = db.query(TaskCollaboration).filter(
            TaskCollaboration.created_at >= start_date
        ).count()
        
        return {
            "period_days": days,
            "team_metrics": {
                "total_tasks_completed": total_tasks,
                "average_completion_time_hours": round(avg_completion_time, 2),
                "collaborations": collaborations,
                "tasks_per_day": round(total_tasks / days, 1),
                "team_velocity": round(total_tasks / len(agents), 1) if agents else 0
            },
            "agent_performance": sorted(
                agent_performance,
                key=lambda x: x["performance_score"],
                reverse=True
            ),
            "insights": await _generate_performance_insights(agent_performance, total_tasks, days)
        }
        
    except Exception as e:
        logger.error(f"Team performance analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")

@router.post("/decisions/record")
async def record_manual_decision(
    decision_type: str,
    context: Dict[str, Any],
    reasoning: str,
    outcome: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Record a manual Boss AI decision"""
    
    try:
        _record_boss_decision(decision_type, context, reasoning, outcome, db)
        
        return {
            "recorded": True,
            "decision_type": decision_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Decision recording failed: {e}")
        raise HTTPException(status_code=500, detail=f"Recording failed: {str(e)}")

@router.get("/decisions/history")
async def get_decision_history(
    limit: int = 50,
    decision_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get Boss AI decision history"""
    
    try:
        query = db.query(BossDecision).order_by(BossDecision.created_at.desc())
        
        if decision_type:
            query = query.filter(BossDecision.decision_type == decision_type)
        
        decisions = query.limit(limit).all()
        
        decision_history = []
        for decision in decisions:
            decision_history.append({
                "id": decision.id,
                "decision_type": decision.decision_type,
                "context": json.loads(decision.context) if decision.context else {},
                "reasoning": decision.reasoning,
                "outcome": json.loads(decision.outcome) if decision.outcome else {},
                "created_at": decision.created_at.isoformat()
            })
        
        # Get decision type statistics
        type_stats = {}
        for decision in decisions:
            type_stats[decision.decision_type] = type_stats.get(decision.decision_type, 0) + 1
        
        return {
            "decisions": decision_history,
            "total_count": len(decisions),
            "decision_types": type_stats,
            "period_analyzed": f"Last {limit} decisions"
        }
        
    except Exception as e:
        logger.error(f"Decision history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

# Helper Functions

def _record_boss_decision(
    decision_type: str,
    context: Dict[str, Any],
    reasoning: str,
    outcome: Dict[str, Any],
    db: Session
):
    """Record Boss AI decision for analysis and learning"""
    decision = BossDecision(
        decision_type=decision_type,
        context=json.dumps(context, default=str),
        reasoning=reasoning,
        outcome=json.dumps(outcome, default=str)
    )
    db.add(decision)
    db.commit()

async def _generate_system_recommendations(db: Session) -> List[str]:
    """Generate system-wide recommendations based on current state"""
    
    recommendations = []
    
    # Check task queue health
    pending_count = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
    in_progress_count = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    failed_count = db.query(Task).filter(Task.status == TaskStatus.FAILED).count()
    
    if pending_count > 20:
        recommendations.append("High number of pending tasks - consider increasing processing capacity or optimizing assignments")
    
    if in_progress_count > 15:
        recommendations.append("Many tasks in progress - monitor for potential bottlenecks or stuck processes")
    
    if failed_count > 5:
        recommendations.append("Multiple failed tasks detected - review system stability and error handling")
    
    # Check agent utilization
    agents = db.query(Agent).filter(Agent.is_active == True).all()
    workloads = smart_assignment._get_agent_workloads(db)
    
    if workloads:
        max_workload = max(workloads.values())
        min_workload = min(workloads.values())
        
        if max_workload > min_workload * 2:
            recommendations.append("Workload imbalance detected - run workload rebalancing to distribute tasks more evenly")
    
    # Check collaboration usage
    recent_collaborations = db.query(TaskCollaboration).filter(
        TaskCollaboration.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    if recent_collaborations == 0 and pending_count > 5:
        recommendations.append("No recent collaborations - complex tasks might benefit from multi-agent coordination")
    
    # Performance recommendations
    recent_tasks = db.query(Task).filter(
        Task.completed_at >= datetime.utcnow() - timedelta(days=1)
    ).count()
    
    if recent_tasks == 0:
        recommendations.append("No tasks completed recently - check system health and agent availability")
    
    if not recommendations:
        recommendations.append("System is operating optimally - all metrics within normal ranges")
    
    return recommendations

async def _calculate_team_health(db: Session) -> Dict[str, Any]:
    """Calculate overall team health metrics"""
    
    # Get recent task statistics
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    total_tasks = db.query(Task).filter(Task.created_at >= week_ago).count()
    completed_tasks = db.query(Task).filter(
        Task.created_at >= week_ago,
        Task.status == TaskStatus.COMPLETED
    ).count()
    failed_tasks = db.query(Task).filter(
        Task.created_at >= week_ago,
        Task.status == TaskStatus.FAILED
    ).count()
    
    # Calculate health scores
    completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
    failure_rate = failed_tasks / total_tasks if total_tasks > 0 else 0
    
    # Agent activity
    active_agents = db.query(Agent).filter(Agent.is_active == True).count()
    agents_with_tasks = db.query(Task).filter(
        Task.created_at >= week_ago
    ).distinct(Task.agent_id).count()
    
    agent_utilization = agents_with_tasks / active_agents if active_agents > 0 else 0
    
    # Overall health score (0-100)
    health_score = (
        completion_rate * 40 +
        (1 - failure_rate) * 30 +
        agent_utilization * 20 +
        min(total_tasks / 7, 10) * 1  # Daily task volume bonus
    )
    
    health_status = "excellent" if health_score >= 80 else \
                    "good" if health_score >= 60 else \
                    "fair" if health_score >= 40 else "needs_attention"
    
    return {
        "health_score": round(health_score, 1),
        "health_status": health_status,
        "metrics": {
            "completion_rate": round(completion_rate * 100, 1),
            "failure_rate": round(failure_rate * 100, 1),
            "agent_utilization": round(agent_utilization * 100, 1),
            "daily_task_volume": round(total_tasks / 7, 1)
        },
        "period": "Last 7 days"
    }

async def _generate_performance_insights(
    agent_performance: List[Dict],
    total_tasks: int,
    days: int
) -> List[str]:
    """Generate actionable performance insights"""
    
    insights = []
    
    if not agent_performance:
        insights.append("No completed tasks in the analyzed period")
        return insights
    
    # Best performing agent
    best_agent = max(agent_performance, key=lambda x: x["performance_score"])
    insights.append(f"🏆 Top performer: {best_agent['agent_name']} with {best_agent['performance_score']:.1f} performance score")
    
    # Efficiency insights
    efficient_agents = [a for a in agent_performance if a["efficiency"] > 1.2]
    if efficient_agents:
        insights.append(f"⚡ {len(efficient_agents)} agents consistently deliver faster than estimated")
    
    # Quality insights
    high_quality_agents = [a for a in agent_performance if a["quality"] > 0.8]
    if high_quality_agents:
        insights.append(f"⭐ {len(high_quality_agents)} agents produce high-quality outputs")
    
    # Team velocity
    avg_tasks_per_day = total_tasks / days
    if avg_tasks_per_day > 5:
        insights.append(f"🚀 High team velocity: {avg_tasks_per_day:.1f} tasks completed per day")
    elif avg_tasks_per_day < 1:
        insights.append("📈 Team velocity could be improved - consider workload optimization")
    
    # Agent utilization
    working_agents = len([a for a in agent_performance if a["tasks_completed"] > 0])
    if working_agents < len(agent_performance):
        unused_agents = len(agent_performance) - working_agents
        insights.append(f"💡 {unused_agents} agents available for additional work")
    
    return insights
