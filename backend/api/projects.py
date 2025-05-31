# VirtuAI Office - Projects API Endpoints

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from ..database import get_db
from ..models.database import Project, Task, TaskStatus
from ..models.pydantic import ProjectResponse, ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project"""
    
    # Check if project name already exists
    existing_project = db.query(Project).filter(Project.name == project_data.name).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Project name already exists")
    
    project = Project(
        id=str(uuid.uuid4()),
        name=project_data.name,
        description=project_data.description or "",
        created_at=datetime.utcnow()
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Get task counts
    task_count = db.query(Task).filter(Task.project_id == project.id).count()
    completed_tasks = db.query(Task).filter(
        Task.project_id == project.id,
        Task.status == TaskStatus.COMPLETED
    ).count()
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        task_count=task_count,
        completed_tasks=completed_tasks,
        created_at=project.created_at
    )

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all projects with optional search and pagination"""
    
    query = db.query(Project)
    
    # Apply search filter
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))
    
    # Apply pagination
    projects = query.order_by(Project.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for project in projects:
        # Get task statistics
        task_count = db.query(Task).filter(Task.project_id == project.id).count()
        completed_tasks = db.query(Task).filter(
            Task.project_id == project.id,
            Task.status == TaskStatus.COMPLETED
        ).count()
        
        result.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            task_count=task_count,
            completed_tasks=completed_tasks,
            created_at=project.created_at
        ))
    
    return result

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific project by ID"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get task statistics
    task_count = db.query(Task).filter(Task.project_id == project.id).count()
    completed_tasks = db.query(Task).filter(
        Task.project_id == project.id,
        Task.status == TaskStatus.COMPLETED
    ).count()
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        task_count=task_count,
        completed_tasks=completed_tasks,
        created_at=project.created_at
    )

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if new name already exists (if changing name)
    if project_data.name and project_data.name != project.name:
        existing_project = db.query(Project).filter(
            Project.name == project_data.name,
            Project.id != project_id
        ).first()
        if existing_project:
            raise HTTPException(status_code=400, detail="Project name already exists")
    
    # Update project fields
    if project_data.name:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    
    db.commit()
    db.refresh(project)
    
    # Get task statistics
    task_count = db.query(Task).filter(Task.project_id == project.id).count()
    completed_tasks = db.query(Task).filter(
        Task.project_id == project.id,
        Task.status == TaskStatus.COMPLETED
    ).count()
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        task_count=task_count,
        completed_tasks=completed_tasks,
        created_at=project.created_at
    )

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project and optionally its tasks"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if project has tasks
    task_count = db.query(Task).filter(Task.project_id == project_id).count()
    if task_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete project with {task_count} tasks. Remove tasks first or use force_delete=true"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": f"Project '{project.name}' deleted successfully"}

@router.delete("/{project_id}/force")
async def force_delete_project(project_id: str, db: Session = Depends(get_db)):
    """Force delete a project and all its tasks"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete all tasks in the project
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    for task in tasks:
        db.delete(task)
    
    # Delete the project
    db.delete(project)
    db.commit()
    
    return {"message": f"Project '{project.name}' and {len(tasks)} tasks deleted successfully"}

@router.get("/{project_id}/analytics")
async def get_project_analytics(project_id: str, db: Session = Depends(get_db)):
    """Get detailed analytics for a project"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all tasks for this project
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    # Calculate statistics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
    pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
    failed_tasks = len([t for t in tasks if t.status == TaskStatus.FAILED])
    
    # Calculate completion rate
    completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
    
    # Calculate average effort
    completed_with_effort = [t for t in tasks if t.status == TaskStatus.COMPLETED and t.actual_effort]
    avg_effort = sum(t.actual_effort for t in completed_with_effort) / len(completed_with_effort) if completed_with_effort else 0
    
    # Task distribution by priority
    priority_distribution = {}
    for task in tasks:
        priority = task.priority.value if task.priority else 'unknown'
        priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
    
    # Agent involvement
    agent_stats = {}
    for task in tasks:
        if task.agent_id:
            agent_name = task.agent.name if task.agent else 'Unknown'
            if agent_name not in agent_stats:
                agent_stats[agent_name] = {'total': 0, 'completed': 0}
            agent_stats[agent_name]['total'] += 1
            if task.status == TaskStatus.COMPLETED:
                agent_stats[agent_name]['completed'] += 1
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_tasks = [t for t in tasks if t.created_at >= week_ago]
    recent_completions = [t for t in tasks if t.completed_at and t.completed_at >= week_ago]
    
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat()
        },
        "task_summary": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "pending_tasks": pending_tasks,
            "failed_tasks": failed_tasks,
            "completion_rate": round(completion_rate, 3)
        },
        "performance": {
            "avg_effort_hours": round(avg_effort, 2),
            "total_effort_hours": sum(t.actual_effort for t in completed_with_effort),
            "tasks_with_effort_data": len(completed_with_effort)
        },
        "distributions": {
            "priority": priority_distribution,
            "agent_involvement": agent_stats
        },
        "recent_activity": {
            "tasks_created_last_week": len(recent_tasks),
            "tasks_completed_last_week": len(recent_completions)
        }
    }

@router.get("/{project_id}/timeline")
async def get_project_timeline(
    project_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get project timeline showing task creation and completion over time"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get tasks within date range
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.created_at >= start_date
    ).order_by(Task.created_at).all()
    
    # Build timeline data
    timeline = []
    for task in tasks:
        # Task creation event
        timeline.append({
            "date": task.created_at.isoformat(),
            "type": "task_created",
            "task_id": task.id,
            "task_title": task.title,
            "agent_name": task.agent.name if task.agent else None,
            "priority": task.priority.value if task.priority else None
        })
        
        # Task completion event (if completed)
        if task.completed_at and task.completed_at >= start_date:
            timeline.append({
                "date": task.completed_at.isoformat(),
                "type": "task_completed",
                "task_id": task.id,
                "task_title": task.title,
                "agent_name": task.agent.name if task.agent else None,
                "effort_hours": task.actual_effort
            })
    
    # Sort timeline by date
    timeline.sort(key=lambda x: x["date"])
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "timeline": timeline,
        "summary": {
            "total_events": len(timeline),
            "tasks_created": len([e for e in timeline if e["type"] == "task_created"]),
            "tasks_completed": len([e for e in timeline if e["type"] == "task_completed"])
        }
    }

@router.post("/{project_id}/archive")
async def archive_project(project_id: str, db: Session = Depends(get_db)):
    """Archive a project (mark as inactive but keep data)"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Add archived flag (assuming you add this field to the model)
    # For now, we'll add it to description as a marker
    if not project.description:
        project.description = "[ARCHIVED]"
    elif "[ARCHIVED]" not in project.description:
        project.description = f"[ARCHIVED] {project.description}"
    
    db.commit()
    
    return {"message": f"Project '{project.name}' archived successfully"}

@router.post("/{project_id}/duplicate")
async def duplicate_project(
    project_id: str,
    new_name: str = Query(..., description="Name for the duplicated project"),
    db: Session = Depends(get_db)
):
    """Duplicate a project (with or without tasks)"""
    
    original_project = db.query(Project).filter(Project.id == project_id).first()
    if not original_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if new name already exists
    existing_project = db.query(Project).filter(Project.name == new_name).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Project name already exists")
    
    # Create duplicate project
    new_project = Project(
        id=str(uuid.uuid4()),
        name=new_name,
        description=f"Duplicate of: {original_project.description}" if original_project.description else "Duplicated project",
        created_at=datetime.utcnow()
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return {
        "message": f"Project duplicated successfully",
        "original_project": original_project.name,
        "new_project": new_project.name,
        "new_project_id": new_project.id
    }
