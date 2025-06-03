# VirtuAI Office - FastAPI Backend Main Entry Point
import asyncio
import json
import uuid
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import ollama
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey, Enum as SQLEnum, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./virtuai_office.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Import models and components
from models.database import (
    Agent, Task, Project, TaskStatus, TaskPriority, AgentType,
    PerformanceMetric, AppleSiliconProfile, TaskDependency,
    AgentWorkload, TaskCollaboration, BossDecision
)
from agents.agent_manager import AgentManager
from orchestration.boss_ai import BossAI
from apple_silicon.detector import AppleSiliconDetector
from apple_silicon.optimizer import AppleSiliconOptimizer
from apple_silicon.monitor import AppleSiliconMonitor
from utils.websocket_manager import ConnectionManager

# Pydantic models for API
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    agent_id: Optional[str]
    agent_name: Optional[str]
    project_id: Optional[str]
    output: Optional[str]
    estimated_effort: Optional[int]
    actual_effort: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class AgentResponse(BaseModel):
    id: str
    name: str
    type: AgentType
    description: str
    expertise: List[str]
    is_active: bool
    task_count: int
    completed_tasks: int

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    task_count: int
    completed_tasks: int
    created_at: datetime

# Global managers
agent_manager = AgentManager()
connection_manager = ConnectionManager()
boss_ai = BossAI(agent_manager)

# Apple Silicon components
apple_silicon_detector = AppleSiliconDetector()
apple_silicon_monitor = AppleSiliconMonitor()
apple_silicon_optimizer = AppleSiliconOptimizer(apple_silicon_detector, apple_silicon_monitor)

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 VirtuAI Office starting up...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")
    
    # Initialize agents in database
    db = SessionLocal()
    try:
        await initialize_agents(db)
        await initialize_apple_silicon_optimization(db)
        logger.info("✅ AI agents initialized")
    finally:
        db.close()
    
    # Test Ollama connection
    try:
        models = ollama.list()
        logger.info(f"✅ Ollama connected, {len(models.get('models', []))} models available")
    except Exception as e:
        logger.warning(f"⚠️ Ollama connection failed: {e}")
        logger.info("Install Ollama and run 'ollama pull llama2:7b' to enable AI features")
    
    logger.info("🎉 VirtuAI Office ready! Your AI development team is standing by.")
    
    yield
    
    # Shutdown
    logger.info("👋 VirtuAI Office shutting down...")

# Create FastAPI app
app = FastAPI(
    title="VirtuAI Office API",
    description="Complete AI development team API with 5 specialized agents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize agents in database
async def initialize_agents(db: Session):
    """Initialize all AI agents in the database"""
    for agent in agent_manager.get_all_agents():
        existing = db.query(Agent).filter(Agent.type == agent.type).first()
        if not existing:
            db_agent = Agent(
                name=agent.name,
                type=agent.type,
                description=agent.description,
                expertise=json.dumps(agent.expertise)
            )
            db.add(db_agent)
            logger.info(f"✅ Initialized agent: {agent.name}")
    
    db.commit()
    logger.info(f"✅ {len(agent_manager.get_all_agents())} AI agents ready")

# Initialize Apple Silicon optimization
async def initialize_apple_silicon_optimization(db: Session):
    """Initialize Apple Silicon optimization if available"""
    try:
        chip_type, specs = apple_silicon_detector.detect_apple_silicon()
        
        if chip_type.value != "intel" and specs:
            logger.info(f"🍎 Apple Silicon detected: {chip_type.value}")
            logger.info(f"   Memory: {specs.unified_memory_gb}GB unified memory")
            logger.info(f"   CPU: {specs.cpu_cores} cores")
            logger.info(f"   GPU: {specs.gpu_cores} cores")
            logger.info(f"   Neural Engine: {'Yes' if specs.neural_engine else 'No'}")
            logger.info(f"   Optimal Models: {', '.join(specs.optimal_models[:3])}")
            logger.info(f"   Max Concurrent Agents: {specs.max_concurrent_agents}")
            
            # Apply basic optimizations
            await apple_silicon_optimizer._optimize_ollama_settings(specs)
            logger.info("✅ Basic Apple Silicon optimizations applied")
            logger.info("💡 Run POST /api/apple-silicon/optimize for advanced optimizations")
        else:
            logger.info("ℹ️  Non-Apple Silicon system detected")
            
    except Exception as e:
        logger.warning(f"⚠️  Apple Silicon detection failed: {e}")

# Background task processor
async def process_task_background(task_id: str, db: Session):
    """Background task processor with Apple Silicon optimization"""
    try:
        # Get task from database
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        # Update task status to in_progress
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Broadcast status update
        await connection_manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "status": "in_progress"
        }))
        
        # Get or assign agent
        if not task.agent_id:
            # Auto-assign best agent using Boss AI
            best_agent = agent_manager.find_best_agent(task.description)
            
            # Find or create agent in database
            agent_db = db.query(Agent).filter(Agent.type == best_agent.type).first()
            if not agent_db:
                agent_db = Agent(
                    name=best_agent.name,
                    type=best_agent.type,
                    description=best_agent.description,
                    expertise=json.dumps(best_agent.expertise)
                )
                db.add(agent_db)
                db.commit()
            
            task.agent_id = agent_db.id
            db.commit()
        
        # Get agent and process task
        agent_db = db.query(Agent).filter(Agent.id == task.agent_id).first()
        if not agent_db:
            raise Exception("Assigned agent not found")
        
        agent = agent_manager.get_agent(agent_db.type)
        if not agent:
            raise Exception(f"Agent implementation not found for type: {agent_db.type}")
        
        # Apply Apple Silicon optimization if available
        chip_type, specs = apple_silicon_detector.detect_apple_silicon()
        if specs:
            # Auto-select optimal model based on task complexity
            task_complexity = analyze_task_complexity(task.description)
            optimal_model = await apple_silicon_optimizer.auto_select_model(task_complexity, specs)
            agent.model = optimal_model
        
        # Process the task
        logger.info(f"Processing task {task_id} with agent {agent.name}")
        output = await agent.process_task(task)
        
        # Update task with output
        task.output = output
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        
        # Calculate effort (mock estimation based on output length)
        if task.started_at and task.completed_at:
            duration_hours = (task.completed_at - task.started_at).total_seconds() / 3600
            task.actual_effort = max(1, int(duration_hours))
        
        db.commit()
        
        # Broadcast completion
        await connection_manager.broadcast(json.dumps({
            "type": "task_completed",
            "task_id": task_id,
            "agent_name": agent.name,
            "output_preview": output[:200] + "..." if len(output) > 200 else output
        }))
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {e}")
        
        # Update task status to failed
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.output = f"Error processing task: {str(e)}"
            db.commit()
        
        # Broadcast failure
        await connection_manager.broadcast(json.dumps({
            "type": "task_failed",
            "task_id": task_id,
            "error": str(e)
        }))

def analyze_task_complexity(description: str) -> str:
    """Simple task complexity analysis"""
    description_lower = description.lower()
    word_count = len(description.split())
    
    complex_keywords = [
        "complex", "advanced", "comprehensive", "detailed", "architecture",
        "system", "integration", "optimization", "performance", "scalable"
    ]
    
    simple_keywords = [
        "simple", "basic", "quick", "small", "minor", "fix", "update"
    ]
    
    complex_score = sum(1 for keyword in complex_keywords if keyword in description_lower)
    simple_score = sum(1 for keyword in simple_keywords if keyword in description_lower)
    
    if word_count > 100 or complex_score > 2:
        return "complex"
    elif word_count < 20 or simple_score > 1:
        return "simple"
    else:
        return "medium"

# API Routes

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "🤖 VirtuAI Office API",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "http://localhost:3000"
    }

@app.get("/api/status")
async def get_status():
    """Get API status and health check"""
    try:
        # Test Ollama connection
        models = ollama.list()
        ollama_status = "connected"
        available_models = [model['name'] for model in models.get('models', [])]
    except Exception as e:
        ollama_status = f"error: {str(e)}"
        available_models = []
    
    # Get Apple Silicon info
    chip_type, specs = apple_silicon_detector.detect_apple_silicon()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ollama_status": ollama_status,
        "available_models": available_models,
        "agents_count": len(agent_manager.get_all_agents()),
        "apple_silicon": {
            "detected": chip_type.value != "intel",
            "chip_type": chip_type.value,
            "memory_gb": specs.unified_memory_gb if specs else 0
        }
    }

@app.get("/api/agents", response_model=List[AgentResponse])
async def get_agents(db: Session = Depends(get_db)):
    """Get all available agents"""
    agents = db.query(Agent).all()
    result = []
    
    for agent in agents:
        task_count = db.query(Task).filter(Task.agent_id == agent.id).count()
        completed_tasks = db.query(Task).filter(
            Task.agent_id == agent.id,
            Task.status == TaskStatus.COMPLETED
        ).count()
        
        result.append(AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type,
            description=agent.description,
            expertise=json.loads(agent.expertise) if agent.expertise else [],
            is_active=agent.is_active,
            task_count=task_count,
            completed_tasks=completed_tasks
        ))
    
    return result

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new task and assign it to the best agent"""
    
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
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        agent_id=task.agent_id,
        agent_name=None,
        project_id=task.project_id,
        output=task.output,
        estimated_effort=task.estimated_effort,
        actual_effort=task.actual_effort,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    )

@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    agent_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get tasks with optional filtering"""
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    if agent_id:
        query = query.filter(Task.agent_id == agent_id)
    
    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
    
    result = []
    for task in tasks:
        agent_name = None
        if task.agent:
            agent_name = task.agent.name
        
        result.append(TaskResponse(
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
        ))
    
    return result

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
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

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    project = Project(name=project_data.name, description=project_data.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        task_count=0,
        completed_tasks=0,
        created_at=project.created_at
    )

@app.get("/api/projects", response_model=List[ProjectResponse])
async def get_projects(db: Session = Depends(get_db)):
    """Get all projects"""
    projects = db.query(Project).all()
    result = []
    
    for project in projects:
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

@app.get("/api/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """Get platform analytics and metrics"""
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
    in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
    
    # Agent performance
    agent_stats = []
    agents = db.query(Agent).all()
    
    for agent in agents:
        agent_tasks = db.query(Task).filter(Task.agent_id == agent.id).count()
        agent_completed = db.query(Task).filter(
            Task.agent_id == agent.id,
            Task.status == TaskStatus.COMPLETED
        ).count()
        
        avg_effort = db.query(Task).filter(
            Task.agent_id == agent.id,
            Task.actual_effort.isnot(None)
        ).with_entities(Task.actual_effort).all()
        
        avg_effort_hours = sum([e[0] for e in avg_effort]) / len(avg_effort) if avg_effort else 0
        
        agent_stats.append({
            "agent_id": agent.id,
            "agent_name": agent.name,
            "agent_type": agent.type.value,
            "total_tasks": agent_tasks,
            "completed_tasks": agent_completed,
            "completion_rate": agent_completed / agent_tasks if agent_tasks > 0 else 0,
            "avg_effort_hours": round(avg_effort_hours, 2)
        })
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "pending_tasks": pending_tasks,
        "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
        "agent_performance": agent_stats
    }

@app.post("/api/standup")
async def generate_standup(db: Session = Depends(get_db)):
    """Generate a daily standup report"""
    # Get recent activity
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    # Tasks completed yesterday
    completed_yesterday = db.query(Task).filter(
        Task.completed_at >= yesterday,
        Task.status == TaskStatus.COMPLETED
    ).all()
    
    # Tasks in progress
    in_progress = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).all()
    
    # Pending tasks
    pending = db.query(Task).filter(Task.status == TaskStatus.PENDING).limit(10).all()
    
    standup_report = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "completed_yesterday": [
            {
                "task_id": task.id,
                "title": task.title,
                "agent_name": task.agent.name if task.agent else "Unknown"
            } for task in completed_yesterday
        ],
        "in_progress_today": [
            {
                "task_id": task.id,
                "title": task.title,
                "agent_name": task.agent.name if task.agent else "Unknown"
            } for task in in_progress
        ],
        "upcoming_tasks": [
            {
                "task_id": task.id,
                "title": task.title,
                "priority": task.priority.value
            } for task in pending
        ],
        "team_summary": f"Yesterday: {len(completed_yesterday)} tasks completed. Today: {len(in_progress)} tasks in progress, {len(pending)} tasks pending."
    }
    
    return standup_report

@app.post("/api/demo/populate")
async def populate_demo_data(db: Session = Depends(get_db)):
    """Populate database with demo data for testing"""
    
    # Create demo project
    demo_project = Project(
        name="E-commerce Platform",
        description="Building a modern e-commerce platform with React and Python"
    )
    db.add(demo_project)
    db.commit()
    db.refresh(demo_project)
    
    # Demo tasks
    demo_tasks = [
        {
            "title": "Create user login page",
            "description": "Design and implement a responsive user login page with form validation, remember me functionality, and forgot password link. Should integrate with our authentication API.",
            "priority": TaskPriority.HIGH
        },
        {
            "title": "Design shopping cart interface",
            "description": "Create a modern shopping cart interface that shows product images, quantities, prices, and total. Include add/remove functionality and proceed to checkout button.",
            "priority": TaskPriority.MEDIUM
        },
        {
            "title": "Build user authentication API",
            "description": "Implement REST API endpoints for user registration, login, logout, and password reset. Include JWT token management and proper error handling.",
            "priority": TaskPriority.HIGH
        },
        {
            "title": "Write user stories for checkout flow",
            "description": "Create comprehensive user stories for the entire checkout process including payment, shipping selection, order confirmation, and email notifications.",
            "priority": TaskPriority.MEDIUM
        },
        {
            "title": "Create test plan for payment system",
            "description": "Develop comprehensive test plan for payment processing including credit card validation, payment gateway integration, error handling, and security testing.",
            "priority": TaskPriority.HIGH
        }
    ]
    
    for task_data in demo_tasks:
        task = Task(
            title=task_data["title"],
            description=task_data["description"],
            priority=task_data["priority"],
            project_id=demo_project.id
        )
        db.add(task)
    
    db.commit()
    
    return {"message": f"Created demo project with {len(demo_tasks)} tasks"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await connection_manager.send_personal_message(f"Received: {data}", websocket)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

# Apple Silicon endpoints
@app.get("/api/apple-silicon/detect")
async def detect_apple_silicon():
    """Detect Apple Silicon chip and return specifications"""
    chip_type, specs = apple_silicon_detector.detect_apple_silicon()
    
    if chip_type.value == "intel":
        return {
            "is_apple_silicon": False,
            "chip_type": "intel",
            "message": "Intel Mac detected - Apple Silicon optimizations not available"
        }
    
    if not specs:
        return {
            "is_apple_silicon": False,
            "chip_type": "unknown",
            "message": "Unable to detect chip specifications"
        }
    
    return {
        "is_apple_silicon": True,
        "chip_type": chip_type.value,
        "specifications": {
            "unified_memory_gb": specs.unified_memory_gb,
            "cpu_cores": specs.cpu_cores,
            "gpu_cores": specs.gpu_cores,
            "neural_engine": specs.neural_engine,
            "memory_bandwidth_gbps": specs.memory_bandwidth_gbps,
            "max_power_watts": specs.max_power_watts,
            "optimal_models": specs.optimal_models,
            "max_concurrent_agents": specs.max_concurrent_agents
        }
    }

@app.post("/api/apple-silicon/optimize")
async def optimize_for_apple_silicon(db: Session = Depends(get_db)):
    """Apply Apple Silicon optimizations"""
    try:
        profile = await apple_silicon_optimizer.create_optimization_profile(db)
        
        return {
            "optimized": True,
            "chip_type": profile.chip_type,
            "memory_gb": profile.memory_gb,
            "optimization_level": "balanced",
            "preferred_models": json.loads(profile.preferred_models) if profile.preferred_models else [],
            "max_concurrent_tasks": profile.max_concurrent_tasks,
            "message": "Apple Silicon optimizations applied successfully"
        }
        
    except Exception as e:
        logger.error(f"Apple Silicon optimization failed: {e}")
        return {
            "optimized": False,
            "error": str(e),
            "message": "Optimization failed - check system compatibility"
        }

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
