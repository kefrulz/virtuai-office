# VirtuAI Office - API Package Initialization
"""
API Package for VirtuAI Office

This package contains all API endpoint modules for the VirtuAI Office system.
Each module handles specific functionality areas:

- agents.py: Agent management and status endpoints
- tasks.py: Task creation, management, and processing endpoints  
- projects.py: Project organization and tracking endpoints
- boss.py: Boss AI orchestration and insights endpoints
- apple_silicon.py: Apple Silicon optimization endpoints
- collaboration.py: Multi-agent collaboration endpoints
- analytics.py: Performance analytics and reporting endpoints
"""

__version__ = "1.0.0"
__author__ = "VirtuAI Office Team"

# Import all API modules to make them available at package level
from . import agents
from . import tasks
from . import projects
from . import boss
from . import apple_silicon
from . import collaboration
from . import analytics

# Define API routes that should be included in the main FastAPI app
API_ROUTES = [
    "agents",
    "tasks",
    "projects",
    "boss",
    "apple_silicon",
    "collaboration",
    "analytics"
]

# API versioning
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Common response models and utilities
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool = True
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

class PaginatedResponse(BaseModel):
    """Paginated API response format"""
    items: List[Dict[str, Any]]
    total: int
    page: int = 1
    per_page: int = 50
    has_next: bool = False
    has_prev: bool = False

class ErrorResponse(BaseModel):
    """Error response format"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

# Common HTTP status codes
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "INTERNAL_ERROR": 500
}

# API configuration
API_CONFIG = {
    "title": "VirtuAI Office API",
    "description": "Complete AI development team API with 5 specialized agents",
    "version": __version__,
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json"
}

# Rate limiting configuration (if implemented)
RATE_LIMITS = {
    "default": "100/minute",
    "heavy": "20/minute",
    "auth": "5/minute"
}

# CORS configuration
CORS_CONFIG = {
    "allow_origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"]
}

def get_api_info() -> Dict[str, Any]:
    """Get API information and health status"""
    return {
        "name": "VirtuAI Office API",
        "version": __version__,
        "status": "healthy",
        "available_routes": API_ROUTES,
        "docs_url": "/docs",
        "api_prefix": API_PREFIX
    }
