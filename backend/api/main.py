# VirtuAI Office - Main API Entry Point
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# Import routers
from .routers import tasks, agents, projects, boss, apple_silicon, collaboration, analytics
from ..database import engine, SessionLocal, Base
from ..models import Task, Agent, Project
from ..agents.manager import AgentManager
from ..orchestration.boss_ai import BossAI
from ..apple_silicon.detector import AppleSiliconDetector
from ..apple_silicon.optimizer import AppleSiliconOptimizer
from ..apple_silicon.monitor import AppleSiliconMonitor
from ..websocket.manager import ConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize managers
agent_manager = AgentManager()
boss_ai = BossAI(agent_manager)
connection_manager = ConnectionManager()

# Apple Silicon components
apple_silicon_detector = AppleSiliconDetector()
apple_silicon_monitor = AppleSiliconMonitor()
apple_silicon_optimizer = AppleSiliconOptimizer(apple_silicon_detector, apple_silicon_monitor)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup and shutdown events
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
        for agent in agent_manager.get_all_agents():
            existing = db.query(Agent).filter(Agent.type == agent.type).first()
            if not existing:
                db_agent = Agent(
                    name=agent.name,
                    type=agent.type,
                    description=agent.description,
                    expertise=json.dumps(agent.expertise),
                    is_active=True
                )
                db.add(db_agent)
                logger.info(f"✅ Initialized agent: {agent.name}")
        
        db.commit()
        logger.info(f"✅ {len(agent_manager.get_all_agents())} AI agents ready")
        
    except Exception as e:
        logger.error(f"Error initializing agents: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Check Ollama connection
    try:
        import ollama
        models = ollama.list()
        logger.info(f"✅ Ollama connected, {len(models.get('models', []))} models available")
    except Exception as e:
        logger.warning(f"⚠️ Ollama connection failed: {e}")
        logger.info("Install Ollama and run 'ollama pull llama2:7b' to enable AI features")
    
    # Apple Silicon detection
    try:
        chip_type, specs = apple_silicon_detector.detect_apple_silicon()
        if chip_type.value != "intel":
            logger.info(f"🍎 Apple Silicon detected: {chip_type.value}")
            if specs:
                logger.info(f"   Memory: {specs.unified_memory_gb}GB unified memory")
                logger.info(f"   CPU: {specs.cpu_cores} cores")
                logger.info(f"   GPU: {specs.gpu_cores} cores")
                logger.info(f"   Optimal Models: {', '.join(specs.optimal_models[:3])}")
                logger.info(f"   Max Concurrent Agents: {specs.max_concurrent_agents}")
                
                # Apply basic optimizations
                await apple_silicon_optimizer._optimize_ollama_settings(specs)
                logger.info("✅ Basic Apple Silicon optimizations applied")
        else:
            logger.info("ℹ️  Intel/Non-Apple system detected")
    except Exception as e:
        logger.warning(f"⚠️  Apple Silicon detection failed: {e}")
    
    logger.info("🎉 VirtuAI Office ready! Your AI development team is standing by.")
    
    yield
    
    # Shutdown
    logger.info("🔄 VirtuAI Office shutting down...")

# Create FastAPI app
app = FastAPI(
    title="VirtuAI Office API",
    description="Complete AI development team API with 5 specialized agents",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(boss.router, prefix="/api", tags=["boss"])
app.include_router(apple_silicon.router, prefix="/api", tags=["apple-silicon"])
app.include_router(collaboration.router, prefix="/api", tags=["collaboration"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "VirtuAI Office API",
        "version": "1.0.0",
        "description": "Complete AI development team with 5 specialized agents",
        "docs": "/docs",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat()
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Ollama connection
    try:
        import ollama
        models = ollama.list()
        ollama_status = "connected"
        available_models = [model['name'] for model in models.get('models', [])]
    except Exception as e:
        ollama_status = f"disconnected: {str(e)}"
        available_models = []
    
    return {
        "status": "healthy" if db_status == "healthy" and "connected" in ollama_status else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "ollama": ollama_status,
            "agents": len(agent_manager.get_all_agents()),
            "websocket": len(connection_manager.active_connections)
        },
        "available_models": available_models
    }

# System status endpoint
@app.get("/api/status")
async def get_system_status():
    """Get comprehensive system status"""
    try:
        # Database stats
        db = SessionLocal()
        total_tasks = db.query(Task).count()
        active_agents = db.query(Agent).filter(Agent.is_active == True).count()
        total_projects = db.query(Project).count()
        db.close()
        
        # Ollama status
        try:
            import ollama
            models = ollama.list()
            ollama_status = "connected"
            available_models = [model['name'] for model in models.get('models', [])]
        except Exception as e:
            ollama_status = "disconnected"
            available_models = []
        
        # Apple Silicon detection
        chip_type, specs = apple_silicon_detector.detect_apple_silicon()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "platform": chip_type.value if chip_type else "unknown",
                "is_apple_silicon": chip_type.value not in ["intel", "unknown"] if chip_type else False,
                "memory_gb": specs.unified_memory_gb if specs else None,
                "cpu_cores": specs.cpu_cores if specs else None
            },
            "services": {
                "database": "healthy",
                "ollama_status": ollama_status,
                "websocket_connections": len(connection_manager.active_connections)
            },
            "data": {
                "total_tasks": total_tasks,
                "active_agents": active_agents,
                "total_projects": total_projects,
                "available_models": available_models
            }
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# WebSocket endpoint
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

# Demo data endpoint
@app.post("/api/demo/populate")
async def populate_demo_data(db: SessionLocal = Depends(get_db)):
    """Populate database with demo data for testing"""
    
    try:
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
                "priority": "high"
            },
            {
                "title": "Design shopping cart interface",
                "description": "Create a modern shopping cart interface that shows product images, quantities, prices, and total. Include add/remove functionality and proceed to checkout button.",
                "priority": "medium"
            },
            {
                "title": "Build user authentication API",
                "description": "Implement REST API endpoints for user registration, login, logout, and password reset. Include JWT token management and proper error handling.",
                "priority": "high"
            },
            {
                "title": "Write user stories for checkout flow",
                "description": "Create comprehensive user stories for the entire checkout process including payment, shipping selection, order confirmation, and email notifications.",
                "priority": "medium"
            },
            {
                "title": "Create test plan for payment system",
                "description": "Develop comprehensive test plan for payment processing including credit card validation, payment gateway integration, error handling, and security testing.",
                "priority": "high"
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
        
        return {
            "success": True,
            "message": f"Created demo project with {len(demo_tasks)} tasks",
            "project_id": demo_project.id
        }
        
    except Exception as e:
        logger.error(f"Demo data population failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to populate demo data: {str(e)}")

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# Make managers available for import
__all__ = [
    "app",
    "agent_manager",
    "boss_ai",
    "connection_manager",
    "apple_silicon_detector",
    "apple_silicon_optimizer",
    "apple_silicon_monitor"
]
