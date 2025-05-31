# VirtuAI Office - Agents API Endpoints
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models.database import Agent, Task, TaskStatus
from ..models.pydantic import AgentResponse, AgentPerformanceResponse
from ..database import get_db
from ..orchestration.performance import PerformanceAnalytics

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("/", response_model=List[AgentResponse])
async def get_all_agents(db: Session = Depends(get_db)):
    """Get all available AI agents with their current status"""
    
    agents = db.query(Agent).filter(Agent.is_active == True).all()
    result = []
    
    for agent in agents:
        # Get task counts
        total_tasks = db.query(Task).filter(Task.agent_id == agent.id).count()
        completed_tasks = db.query(Task).filter(
            Task.agent_id == agent.id,
            Task.status == TaskStatus.COMPLETED
        ).count()
        
        # Get current workload
        active_tasks = db.query(Task).filter(
            Task.agent_id == agent.id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        ).count()
        
        result.append(AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type,
            description=agent.description,
            expertise=json.loads(agent.expertise) if agent.expertise else [],
            is_active=agent.is_active,
            task_count=total_tasks,
            completed_tasks=completed_tasks,
            current_workload=active_tasks
        ))
    
    return result

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_details(agent_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific agent"""
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Calculate agent metrics
    total_tasks = db.query(Task).filter(Task.agent_id == agent.id).count()
    completed_tasks = db.query(Task).filter(
        Task.agent_id == agent.id,
        Task.status == TaskStatus.COMPLETED
    ).count()
    
    active_tasks = db.query(Task).filter(
        Task.agent_id == agent.id,
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
    ).count()
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        type=agent.type,
        description=agent.description,
        expertise=json.loads(agent.expertise) if agent.expertise else [],
        is_active=agent.is_active,
        task_count=total_tasks,
        completed_tasks=completed_tasks,
        current_workload=active_tasks
    )

@router.get("/{agent_id}/tasks")
async def get_agent_tasks(
    agent_id: str,
    status: Optional[TaskStatus] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all tasks assigned to a specific agent"""
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    query = db.query(Task).filter(Task.agent_id == agent_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "output": task.output,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "actual_effort": task.actual_effort
        }
        for task in tasks
    ]

@router.get("/{agent_id}/performance", response_model=AgentPerformanceResponse)
async def get_agent_performance(agent_id: str, days: int = 30, db: Session = Depends(get_db)):
    """Get detailed performance analytics for an agent"""
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get tasks from specified time period
    start_date = datetime.utcnow() - timedelta(days=days)
    completed_tasks = db.query(Task).filter(
        Task.agent_id == agent_id,
        Task.status == TaskStatus.COMPLETED,
        Task.completed_at >= start_date
    ).all()
    
    # Calculate performance metrics
    analytics = PerformanceAnalytics()
    performance_data = analytics.analyze_agent_performance(agent_id, completed_tasks, db)
    
    # Get collaboration count
    collaboration_count = db.query(Task).join(
        Task, Task.agent_id == agent_id
    ).filter(Task.requires_collaboration == True).count()
    
    # Get task type distribution
    task_types = {}
    for task in completed_tasks:
        task_type = getattr(task, 'task_type', 'unknown')
        task_types[task_type] = task_types.get(task_type, 0) + 1
    
    # Get recent tasks
    recent_tasks = completed_tasks[:5]
    recent_task_data = [
        {
            "id": task.id,
            "title": task.title,
            "completed_at": task.completed_at,
            "effort_hours": task.actual_effort
        }
        for task in recent_tasks
    ]
    
    return AgentPerformanceResponse(
        agent={
            "id": agent.id,
            "name": agent.name,
            "type": agent.type
        },
        performance=performance_data,
        collaboration_count=collaboration_count,
        task_distribution=task_types,
        recent_tasks=recent_task_data
    )

@router.post("/{agent_id}/activate")
async def activate_agent(agent_id: str, db: Session = Depends(get_db)):
    """Activate an agent for task assignment"""
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.is_active = True
    db.commit()
    
    return {"message": f"Agent {agent.name} activated successfully"}

@router.post("/{agent_id}/deactivate")
async def deactivate_agent(agent_id: str, db: Session = Depends(get_db)):
    """Deactivate an agent (no new tasks will be assigned)"""
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if agent has active tasks
    active_tasks = db.query(Task).filter(
        Task.agent_id == agent_id,
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
    ).count()
    
    if active_tasks > 0:
        return {
            "message": f"Warning: Agent {agent.name} has {active_tasks} active tasks",
            "active_tasks": active_tasks,
            "deactivated": False
        }
    
    agent.is_active = False
    db.commit()
    
    return {"message": f"Agent {agent.name} deactivated successfully"}

@router.get("/{agent_id}/workload")
async def get_agent_workload(agent_id: str, db: Session = Depends(get_db)):
    """Get current workload information for an agent"""
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Count tasks by status
    pending_tasks = db.query(Task).filter(
        Task.agent_id == agent_id,
        Task.status == TaskStatus.PENDING
    ).count()
    
    in_progress_tasks = db.query(Task).filter(
        Task.agent_id == agent_id,
        Task.status == TaskStatus.IN_PROGRESS
    ).count()
    
    # Calculate estimated hours for active tasks
    active_tasks = db.query(Task).filter(
        Task.agent_id == agent_id,
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
    ).all()
    
    estimated_hours = sum([
        task.estimated_effort or 3 for task in active_tasks
    ])
    
    # Get recent completion rate
    last_week = datetime.utcnow() - timedelta(days=7)
    recent_completed = db.query(Task).filter(
        Task.agent_id == agent_id,
        Task.status == TaskStatus.COMPLETED,
        Task.completed_at >= last_week
    ).count()
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "pending_tasks": pending_tasks,
        "in_progress_tasks": in_progress_tasks,
        "total_active_tasks": pending_tasks + in_progress_tasks,
        "estimated_hours": estimated_hours,
        "recent_completions": recent_completed,
        "availability": "high" if estimated_hours < 10 else "medium" if estimated_hours < 20 else "low"
    }

@router.get("/{agent_id}/specialization")
async def get_agent_specialization(agent_id: str, db: Session = Depends(get_db)):
    """Get agent's specialization and task affinity analysis"""
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get completed tasks for analysis
    completed_tasks = db.query(Task).filter(
        Task.agent_id == agent_id,
        Task.status == TaskStatus.COMPLETED
    ).all()
    
    # Analyze task keywords and patterns
    task_keywords = {}
    for task in completed_tasks:
        # Simple keyword extraction from task descriptions
        words = task.description.lower().split()
        for word in words:
            if len(word) > 3 and word.isalpha():
                task_keywords[word] = task_keywords.get(word, 0) + 1
    
    # Get top keywords
    top_keywords = sorted(task_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Calculate success rate by task complexity
    complex_tasks = [t for t in completed_tasks if len(t.description.split()) > 50]
    simple_tasks = [t for t in completed_tasks if len(t.description.split()) <= 20]
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "expertise_areas": json.loads(agent.expertise) if agent.expertise else [],
        "task_patterns": {
            "total_tasks": len(completed_tasks),
            "complex_tasks": len(complex_tasks),
            "simple_tasks": len(simple_tasks),
            "avg_task_length": sum([len(t.description.split()) for t in completed_tasks]) / len(completed_tasks) if completed_tasks else 0
        },
        "common_keywords": [{"keyword": k, "frequency": v} for k, v in top_keywords],
        "performance_summary": {
            "completion_rate": 1.0 if completed_tasks else 0.0,
            "avg_effort_hours": sum([t.actual_effort or 0 for t in completed_tasks]) / len(completed_tasks) if completed_tasks else 0,
            "specialization_score": len(set([k for k, v in top_keywords])) / 10.0 if top_keywords else 0.0
        }
    }

@router.post("/{agent_id}/optimize")
async def optimize_agent_performance(agent_id: str, db: Session = Depends(get_db)):
    """Apply performance optimizations for a specific agent"""
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get performance history
    completed_tasks = db.query(Task).filter(
        Task.agent_id == agent_id,
        Task.status == TaskStatus.COMPLETED
    ).all()
    
    if not completed_tasks:
        return {
            "message": "No completed tasks found for optimization",
            "optimizations_applied": []
        }
    
    optimizations = []
    
    # Analyze average effort vs estimated effort
    effort_data = [(t.estimated_effort or 3, t.actual_effort or 3) for t in completed_tasks if t.actual_effort]
    if effort_data:
        avg_accuracy = sum([abs(est - act) for est, act in effort_data]) / len(effort_data)
        if avg_accuracy > 2:
            optimizations.append("effort_estimation_tuning")
    
    # Check for task type preferences
    task_lengths = [len(t.description.split()) for t in completed_tasks]
    if task_lengths:
        avg_length = sum(task_lengths) / len(task_lengths)
        if avg_length > 100:
            optimizations.append("complex_task_specialization")
        elif avg_length < 20:
            optimizations.append("quick_task_optimization")
    
    # Update agent optimization timestamp
    agent.last_optimized = datetime.utcnow()
    db.commit()
    
    return {
        "message": f"Optimization analysis completed for {agent.name}",
        "optimizations_applied": optimizations,
        "performance_insights": {
            "total_tasks_analyzed": len(completed_tasks),
            "avg_task_complexity": sum(task_lengths) / len(task_lengths) if task_lengths else 0,
            "effort_accuracy": f"{100 - (avg_accuracy * 10):.1f}%" if 'avg_accuracy' in locals() else "N/A"
        }
    }
