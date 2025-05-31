# VirtuAI Office - API Dependencies
# Shared dependencies and utilities for API endpoints

from typing import Generator, Optional
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..database import SessionLocal, engine
from ..models import Agent, Task, Project

logger = logging.getLogger(__name__)

# Security (optional - for future authentication)
security = HTTPBearer(auto_error=False)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Get current user (placeholder for future authentication)
    Currently returns None - no authentication required
    """
    # For now, no authentication required
    # In the future, implement JWT token validation here
    return None

def get_agent_by_id(agent_id: str, db: Session = Depends(get_db)) -> Agent:
    """
    Get agent by ID or raise 404
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )
    return agent

def get_task_by_id(task_id: str, db: Session = Depends(get_db)) -> Task:
    """
    Get task by ID or raise 404
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return task

def get_project_by_id(project_id: str, db: Session = Depends(get_db)) -> Project:
    """
    Get project by ID or raise 404
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    return project

def validate_pagination(
    limit: int = 50,
    offset: int = 0
) -> tuple[int, int]:
    """
    Validate pagination parameters
    """
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )
    
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be non-negative"
        )
    
    return limit, offset

def check_system_health() -> dict:
    """
    Check system health status
    """
    try:
        # Check database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    try:
        # Check Ollama connection
        import ollama
        ollama.list()
        ollama_status = "connected"
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        ollama_status = "disconnected"
    
    return {
        "database": db_status,
        "ollama": ollama_status,
        "overall": "healthy" if db_status == "healthy" and ollama_status == "connected" else "degraded"
    }

class RateLimiter:
    """
    Simple in-memory rate limiter (for future use)
    """
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int = 100, window: int = 3600) -> bool:
        """
        Check if request is allowed based on rate limit
        """
        import time
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < window
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(key: str = "global"):
    """
    Dependency to check rate limits
    """
    if not rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return True

def log_api_call(endpoint: str, method: str, user_id: Optional[str] = None):
    """
    Log API calls for monitoring
    """
    logger.info(f"API Call: {method} {endpoint} - User: {user_id or 'anonymous'}")

# Exception handlers
def handle_database_error(error: Exception) -> HTTPException:
    """
    Convert database errors to HTTP exceptions
    """
    logger.error(f"Database error: {error}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database operation failed"
    )

def handle_validation_error(error: Exception) -> HTTPException:
    """
    Convert validation errors to HTTP exceptions
    """
    logger.error(f"Validation error: {error}")
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(error)
    )

def handle_ollama_error(error: Exception) -> HTTPException:
    """
    Convert Ollama errors to HTTP exceptions
    """
    logger.error(f"Ollama error: {error}")
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="AI service temporarily unavailable"
    )
