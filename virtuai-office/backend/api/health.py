# backend/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import psutil
import ollama
from ..database import get_db

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "VirtuAI Office API"
    }

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with system information"""
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database check
    try:
        db.execute("SELECT 1")
        database_status = "healthy"
    except Exception as e:
        database_status = f"error: {str(e)}"
    
    # Ollama check
    try:
        models = ollama.list()
        ollama_status = "connected"
        available_models = [model['name'] for model in models.get('models', [])]
    except Exception as e:
        ollama_status = f"error: {str(e)}"
        available_models = []
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_available": memory.available,
            "disk_usage": disk.percent,
            "disk_free": disk.free
        },
        "services": {
            "database": database_status,
            "ollama": ollama_status,
            "available_models": available_models
        },
        "version": "1.0.0"
    }

@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes-style readiness probe"""
    
    checks = []
    overall_status = "ready"
    
    # Database readiness
    try:
        db.execute("SELECT 1")
        checks.append({"name": "database", "status": "ready"})
    except Exception as e:
        checks.append({"name": "database", "status": "not_ready", "error": str(e)})
        overall_status = "not_ready"
    
    # Ollama readiness
    try:
        ollama.list()
        checks.append({"name": "ollama", "status": "ready"})
    except Exception as e:
        checks.append({"name": "ollama", "status": "not_ready", "error": str(e)})
        overall_status = "not_ready"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/liveness")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
