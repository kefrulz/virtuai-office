# VirtuAI Office - Task API Endpoints
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from ..database import get_db
from ..models.database import Task, Agent, Project
from ..models.pydantic import TaskCreate, TaskResponse, TaskUpdate
from ..orchestration.boss_ai import BossAI
from ..orchestration.task_assignment import SmartTaskAssignment
from ..agents.agent_manager import AgentManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Initialize components
boss_ai = BossAI()
agent_manager = AgentManager()
smart_assignment = SmartTaskAssignment(boss_ai, agent_manager)

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new task"""
    
    try:
        # Create task in database
        task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            project_id=task_data.project_id
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Add background task to process it
        background_tasks.add_task(process_task_background, task.id, db)
        
        logger.info(f"Created task {task.id}: {task.title}")
        
        return _build_task_response(task, db)
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@router.post("/smart-assign", response_model=dict)
async def smart_assign_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create and intelligently assign a task using Boss AI"""
    
    try:
        # Create task
        task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            project_id=task_data.project_id
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Smart assignment
        assignment_result = await smart_assignment.assign_task_intelligently(task, db)
        db.commit()
        
        # Process task in background
        background_tasks.add_task(process_task_with_collaboration, task.id, assignment_result, db)
        
        logger.info(f"Smart assigned task {task.id} to {assignment_result.get('assigned_agent_id')}")
        
        return {
            "task_id": task.id,
            "assignment": assignment_result,
            "message": "Task created and intelligently assigned"
        }
        
    except Exception as e:
        logger.error(f"Smart assignment failed: {e}")
        # Fallback to regular assignment
        background_tasks.add_task(process_task_background, task.id, db)
        return {
            "task_id": task.id,
            "message": "Task created with fallback assignment",
            "warning": str(e)
        }

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    project_id: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get tasks with optional filtering"""
    
    try:
        query = db.query(Task)
        
        # Apply filters
        if status:
            query = query.filter(Task.status == status)
        if agent_id:
            query = query.filter(Task.agent_id == agent_id)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if priority:
            query = query.filter(Task.priority == priority)
        
        # Apply pagination and ordering
        tasks = (query
                .order_by(Task.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all())
        
        return [_build_task_response(task, db) for task in tasks]
        
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return _build_task_response(task, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task"""
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Prevent updating tasks in progress unless it's status change
        if task.status == "in_progress" and task_update.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Cannot update task in progress except to change status to pending"
            )
        
        # Update fields
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        db.commit()
        db.refresh(task)
        
        logger.info(f"Updated task {task_id}")
        
        return _build_task_response(task, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry a failed task"""
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status != "failed":
            raise HTTPException(status_code=400, detail="Only failed tasks can be retried")
        
        # Reset task status
        task.status = "pending"
        task.output = None
        task.started_at = None
        task.completed_at = None
        task.actual_effort = None
        
        db.commit()
        
        # Add background task to process it
        background_tasks.add_task(process_task_background, task.id, db)
        
        logger.info(f"Retrying task {task_id}")
        
        return {"message": "Task queued for retry", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry task: {str(e)}")

@router.delete("/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task"""
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status == "in_progress":
            raise HTTPException(status_code=400, detail="Cannot delete task in progress")
        
        db.delete(task)
        db.commit()
        
        logger.info(f"Deleted task {task_id}")
        
        return {"message": "Task deleted successfully", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

@router.post("/{task_id}/assign/{agent_id}")
async def assign_task_to_agent(
    task_id: str,
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Manually assign a task to a specific agent"""
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status == "in_progress":
            raise HTTPException(status_code=400, detail="Cannot reassign task in progress")
        
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if not agent.is_active:
            raise HTTPException(status_code=400, detail="Agent is not active")
        
        task.agent_id = agent_id
        db.commit()
        
        logger.info(f"Assigned task {task_id} to agent {agent_id}")
        
        return {
            "message": f"Task assigned to {agent.name}",
            "task_id": task_id,
            "agent_id": agent_id,
            "agent_name": agent.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign task {task_id} to agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")

@router.post("/bulk", response_model=List[TaskResponse])
async def bulk_create_tasks(
    tasks_data: List[TaskCreate],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create multiple tasks at once"""
    
    try:
        created_tasks = []
        
        for task_data in tasks_data:
            task = Task(
                title=task_data.title,
                description=task_data.description,
                priority=task_data.priority,
                project_id=task_data.project_id
            )
            
            db.add(task)
            created_tasks.append(task)
        
        db.commit()
        
        # Refresh all tasks to get IDs
        for task in created_tasks:
            db.refresh(task)
            # Add background processing
            background_tasks.add_task(process_task_background, task.id, db)
        
        logger.info(f"Created {len(created_tasks)} tasks in bulk")
        
        return [_build_task_response(task, db) for task in created_tasks]
        
    except Exception as e:
        logger.error(f"Failed to create tasks in bulk: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create tasks: {str(e)}")

@router.patch("/bulk")
async def bulk_update_tasks(
    task_ids: List[str],
    updates: dict,
    db: Session = Depends(get_db)
):
    """Update multiple tasks at once"""
    
    try:
        tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
        
        if len(tasks) != len(task_ids):
            raise HTTPException(status_code=404, detail="One or more tasks not found")
        
        # Check for tasks in progress
        in_progress_tasks = [t for t in tasks if t.status == "in_progress"]
        if in_progress_tasks:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot update tasks in progress: {[t.id for t in in_progress_tasks]}"
            )
        
        # Apply updates
        for task in tasks:
            for field, value in updates.items():
                if hasattr(task, field):
                    setattr(task, field, value)
        
        db.commit()
        
        logger.info(f"Updated {len(tasks)} tasks in bulk")
        
        return {
            "message": f"Updated {len(tasks)} tasks successfully",
            "updated_task_ids": task_ids,
            "updates_applied": updates
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update tasks in bulk: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update tasks: {str(e)}")

# Helper Functions

def _build_task_response(task: Task, db: Session) -> TaskResponse:
    """Build a TaskResponse from a Task model"""
    
    agent_name = None
    if task.agent:
        agent_name = task.agent.name
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        agent_id=task.agent_id,
        agent_name=agent_name,
        project_id=task.project_id,
        output=task.output,
        estimated_effort=task.estimated_effort,
        actual_effort=task.actual_effort,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    )

# Background Task Processing Functions

async def process_task_background(task_id: str, db: Session):
    """Background task processor"""
    from ..orchestration.task_processor import TaskProcessor
    
    try:
        processor = TaskProcessor(agent_manager, boss_ai)
        await processor.process_task(task_id, db)
        
    except Exception as e:
        logger.error(f"Background task processing failed for {task_id}: {e}")
        
        # Update task status to failed
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.output = f"Processing failed: {str(e)}"
            db.commit()

async def process_task_with_collaboration(task_id: str, assignment_result: dict, db: Session):
    """Enhanced task processing that handles collaboration"""
    from ..orchestration.task_processor import CollaborativeTaskProcessor
    
    try:
        processor = CollaborativeTaskProcessor(agent_manager, boss_ai)
        await processor.process_task_with_collaboration(task_id, assignment_result, db)
        
    except Exception as e:
        logger.error(f"Collaborative task processing failed for {task_id}: {e}")
        
        # Update task status to failed
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.output = f"Collaborative processing failed: {str(e)}"
            db.commit()
