"""
VirtuAI Office Backend - ASGI Application

ASGI (Asynchronous Server Gateway Interface) configuration for the VirtuAI Office backend.
This module provides the main ASGI application entry point for production deployment
with uvicorn, gunicorn, or other ASGI servers.

Features:
- FastAPI application with async/await support
- WebSocket support for real-time updates
- Middleware configuration for production
- Health checks and monitoring endpoints
- Apple Silicon optimization integration
- Comprehensive error handling and logging
"""

import logging
import os
import sys
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from pathlib import Path

# Add backend package to Python path
backend_path = Path(__file__).parent.absolute()
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Core FastAPI imports
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

# Application imports
try:
    from backend import ENV_CONFIG, logger, health_check, __version__
    from backend.database import engine, Base, get_db
    from backend.api import router as api_router
    from backend.websocket import websocket_router
    from backend.middleware import (
        SecurityHeadersMiddleware,
        RequestLoggingMiddleware,
        PerformanceMiddleware,
        RateLimitMiddleware
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all backend modules are properly installed")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=getattr(logging, ENV_CONFIG.get("LOG_LEVEL", "INFO")),
    format=ENV_CONFIG.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

logger = logging.getLogger(__name__)

# Global application state
app_state = {
    "startup_time": None,
    "ollama_connected": False,
    "agents_initialized": False,
    "apple_silicon_optimized": False,
}

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Handles:
    - Database initialization
    - AI agent setup
    - Ollama connection verification
    - Apple Silicon optimization
    - Resource cleanup on shutdown
    """
    from datetime import datetime
    
    logger.info("🚀 VirtuAI Office Backend starting up...")
    
    try:
        # Record startup time
        app_state["startup_time"] = datetime.utcnow()
        
        # Initialize database
        logger.info("📊 Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized")
        
        # Check Ollama connection
        logger.info("🤖 Checking Ollama connection...")
        from backend import check_ollama_connection
        app_state["ollama_connected"] = check_ollama_connection()
        
        if app_state["ollama_connected"]:
            logger.info("✅ Ollama service connected")
        else:
            logger.warning("⚠️ Ollama service not available - AI features may be limited")
        
        # Initialize AI agents
        logger.info("🤖 Initializing AI agents...")
        try:
            from backend.agents import initialize_agents
            await initialize_agents()
            app_state["agents_initialized"] = True
            logger.info("✅ AI agents initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI agents: {e}")
        
        # Apple Silicon optimization
        try:
            from backend.apple_silicon import initialize_apple_silicon
            optimized = await initialize_apple_silicon()
            app_state["apple_silicon_optimized"] = optimized
            if optimized:
                logger.info("🍎 Apple Silicon optimizations applied")
        except ImportError:
            logger.info("🍎 Apple Silicon optimization not available")
        except Exception as e:
            logger.warning(f"🍎 Apple Silicon optimization failed: {e}")
        
        # Initialize Boss AI
        try:
            from backend.orchestration import initialize_boss_ai
            await initialize_boss_ai()
            logger.info("🧠 Boss AI orchestration initialized")
        except Exception as e:
            logger.warning(f"🧠 Boss AI initialization failed: {e}")
        
        # Start background tasks
        logger.info("⚙️ Starting background tasks...")
        try:
            from backend.tasks import start_background_tasks
            await start_background_tasks()
            logger.info("✅ Background tasks started")
        except Exception as e:
            logger.warning(f"⚙️ Background tasks failed to start: {e}")
        
        # Populate demo data if enabled
        if ENV_CONFIG.get("AUTO_POPULATE_DEMO_DATA", False):
            logger.info("📝 Populating demo data...")
            try:
                from backend.demo import populate_demo_data
                await populate_demo_data()
                logger.info("✅ Demo data populated")
            except Exception as e:
                logger.warning(f"📝 Demo data population failed: {e}")
        
        logger.info("🎉 VirtuAI Office Backend startup complete!")
        
        # Yield control to the application
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    finally:
        # Shutdown procedures
        logger.info("🛑 VirtuAI Office Backend shutting down...")
        
        try:
            # Stop background tasks
            from backend.tasks import stop_background_tasks
            await stop_background_tasks()
            logger.info("✅ Background tasks stopped")
        except Exception as e:
            logger.warning(f"⚙️ Background task cleanup failed: {e}")
        
        try:
            # Close database connections
            engine.dispose()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.warning(f"📊 Database cleanup failed: {e}")
        
        logger.info("👋 VirtuAI Office Backend shutdown complete")

# Create FastAPI application
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Application metadata
    app_config = {
        "title": ENV_CONFIG.get("API_TITLE", "VirtuAI Office API"),
        "description": ENV_CONFIG.get("API_DESCRIPTION", "Complete AI development team API"),
        "version": __version__,
        "lifespan": lifespan,
        "docs_url": "/docs" if ENV_CONFIG.get("ENABLE_API_DOCS", True) else None,
        "redoc_url": "/redoc" if ENV_CONFIG.get("ENABLE_REDOC", True) else None,
        "openapi_url": "/openapi.json",
    }
    
    # Create FastAPI app
    app = FastAPI(**app_config)
    
    # Add middleware in reverse order (last added, first executed)
    
    # Security headers (outermost)
    if ENV_CONFIG.get("ENABLE_SECURITY_HEADERS", True):
        app.add_middleware(SecurityHeadersMiddleware)
    
    # Trusted hosts
    trusted_hosts = ENV_CONFIG.get("TRUSTED_HOSTS", ["localhost", "127.0.0.1"])
    if isinstance(trusted_hosts, str):
        trusted_hosts = [host.strip() for host in trusted_hosts.split(",")]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
    
    # GZip compression
    if ENV_CONFIG.get("ENABLE_GZIP_COMPRESSION", True):
        app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Performance monitoring
    if ENV_CONFIG.get("ENABLE_PERFORMANCE_MONITORING", True):
        app.add_middleware(PerformanceMiddleware)
    
    # Rate limiting
    if ENV_CONFIG.get("ENABLE_RATE_LIMITING", False):
        app.add_middleware(
            RateLimitMiddleware,
            calls=ENV_CONFIG.get("RATE_LIMIT_PER_MINUTE", 60),
            period=60
        )
    
    # Request logging
    if ENV_CONFIG.get("ENABLE_REQUEST_LOGGING", True):
        app.add_middleware(RequestLoggingMiddleware)
    
    # CORS (innermost, closest to the application)
    cors_origins = ENV_CONFIG.get("CORS_ORIGINS", "http://localhost:3000")
    if isinstance(cors_origins, str):
        cors_origins = [origin.strip() for origin in cors_origins.split(",")]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=ENV_CONFIG.get("CORS_ALLOW_CREDENTIALS", True),
        allow_methods=ENV_CONFIG.get("CORS_ALLOW_METHODS", ["*"]),
        allow_headers=ENV_CONFIG.get("CORS_ALLOW_HEADERS", ["*"]),
        max_age=ENV_CONFIG.get("CORS_MAX_AGE", 86400),
    )
    
    return app

# Create the main application instance
app = create_app()

# Include API routers
app.include_router(api_router, prefix="/api")
app.include_router(websocket_router)

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_endpoint():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": app_state.get("startup_time")}

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_endpoint():
    """Detailed health check with system information."""
    health_data = health_check()
    health_data.update(app_state)
    return health_data

@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}

@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    if not app_state.get("agents_initialized", False):
        raise HTTPException(status_code=503, detail="Agents not initialized")
    
    return {
        "status": "ready",
        "ollama_connected": app_state.get("ollama_connected", False),
        "agents_initialized": app_state.get("agents_initialized", False),
    }

# Metrics endpoint (if enabled)
if ENV_CONFIG.get("ENABLE_METRICS", False):
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics_endpoint():
        """Prometheus-compatible metrics endpoint."""
        try:
            from backend.monitoring import get_metrics
            return Response(
                content=get_metrics(),
                media_type="text/plain",
                headers={"Content-Type": "text/plain; version=0.0.4"}
            )
        except ImportError:
            raise HTTPException(status_code=404, detail="Metrics not available")

# Static file serving (if enabled)
if ENV_CONFIG.get("SERVE_STATIC_FILES", False):
    static_dir = ENV_CONFIG.get("STATIC_FILES_DIRECTORY", "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema with additional metadata."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom metadata
    openapi_schema["info"]["x-logo"] = {
        "url": "https://virtuai-office.com/logo.png",
        "altText": "VirtuAI Office Logo"
    }
    
    openapi_schema["info"]["contact"] = {
        "name": "VirtuAI Office Support",
        "url": "https://github.com/kefrulz/virtuai-office",
        "email": "support@virtuai-office.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Add security schemes if authentication is enabled
    if ENV_CONFIG.get("ENABLE_AUTHENTICATION", False):
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if ENV_CONFIG.get("DEBUG_MODE", False):
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "traceback": traceback.format_exc() if ENV_CONFIG.get("SHOW_TRACEBACKS", False) else None
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Development endpoints (only in debug mode)
if ENV_CONFIG.get("DEBUG_MODE", False):
    
    @app.get("/debug/state", tags=["Debug"])
    async def debug_app_state():
        """Get current application state (debug only)."""
        return app_state
    
    @app.get("/debug/config", tags=["Debug"])
    async def debug_config():
        """Get current configuration (debug only)."""
        # Filter out sensitive information
        safe_config = {
            k: v for k, v in ENV_CONFIG.items()
            if not any(sensitive in k.lower() for sensitive in ["password", "secret", "key", "token"])
        }
        return safe_config
    
    @app.post("/debug/reset", tags=["Debug"])
    async def debug_reset():
        """Reset application state (debug only)."""
        global app_state
        app_state = {
            "startup_time": app_state.get("startup_time"),
            "ollama_connected": False,
            "agents_initialized": False,
            "apple_silicon_optimized": False,
        }
        return {"message": "Application state reset"}

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "🤖 VirtuAI Office Backend API",
        "version": __version__,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "startup_time": app_state.get("startup_time"),
    }

# Startup logging
@app.on_event("startup")
async def log_startup_info():
    """Log startup information."""
    logger.info(f"🤖 VirtuAI Office Backend v{__version__}")
    logger.info(f"🌐 Server: {ENV_CONFIG.get('FASTAPI_HOST')}:{ENV_CONFIG.get('FASTAPI_PORT')}")
    logger.info(f"🔧 Environment: {ENV_CONFIG.get('NODE_ENV', 'development')}")
    logger.info(f"📊 Database: {ENV_CONFIG.get('DATABASE_URL', 'not configured')}")
    logger.info(f"🤖 Ollama: {ENV_CONFIG.get('OLLAMA_BASE_URL', 'not configured')}")
    logger.info(f"📚 API Docs: {'/docs' if app.docs_url else 'disabled'}")

# Export the ASGI application
__all__ = ["app"]

# For uvicorn/gunicorn deployment
if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn_config = {
        "app": "asgi:app",
        "host": ENV_CONFIG.get("FASTAPI_HOST", "0.0.0.0"),
        "port": ENV_CONFIG.get("FASTAPI_PORT", 8000),
        "reload": ENV_CONFIG.get("FASTAPI_RELOAD", False),
        "log_level": ENV_CONFIG.get("UVICORN_LOG_LEVEL", "info"),
        "access_log": ENV_CONFIG.get("ENABLE_ACCESS_LOG", True),
    }
    
    logger.info("🚀 Starting VirtuAI Office Backend with uvicorn...")
    uvicorn.run(**uvicorn_config)
