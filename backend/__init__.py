"""
VirtuAI Office Backend Package

Complete AI-powered development team backend system with 5 specialized AI agents,
Boss AI orchestration, and Apple Silicon optimization.

Features:
- 5 Specialized AI Agents (Product Manager, Frontend Dev, Backend Dev, Designer, QA)
- Boss AI for intelligent task assignment and team orchestration
- Apple Silicon optimization for M1/M2/M3 Macs
- Real-time WebSocket updates
- Comprehensive API with FastAPI
- Local AI processing with Ollama
- Advanced collaboration workflows
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Version information
__version__ = "1.0.0"
__author__ = "VirtuAI Office Team"
__email__ = "support@virtuai-office.com"
__license__ = "MIT"

# Package metadata
__title__ = "VirtuAI Office Backend"
__description__ = "AI-powered development team backend system"
__url__ = "https://github.com/kefrulz/virtuai-office"

# Supported Python versions
__python_requires__ = ">=3.8"

# Package root directory
PACKAGE_ROOT = Path(__file__).parent.absolute()
PROJECT_ROOT = PACKAGE_ROOT.parent.absolute()

# Configure logging for the package
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "backend.log", mode="a")
    ] if (PROJECT_ROOT / "logs").exists() else [logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Environment configuration
def load_environment() -> Dict[str, Any]:
    """Load and validate environment configuration."""
    from dotenv import load_dotenv
    
    # Load environment variables
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded environment from {env_file}")
    else:
        logger.warning("No .env file found, using system environment variables")
    
    # Validate required environment variables
    required_vars = [
        "DATABASE_URL",
        "OLLAMA_HOST",
        "OLLAMA_PORT"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
    
    return {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./virtuai_office.db"),
        "ollama_host": os.getenv("OLLAMA_HOST", "localhost"),
        "ollama_port": int(os.getenv("OLLAMA_PORT", 11434)),
        "api_host": os.getenv("FASTAPI_HOST", "0.0.0.0"),
        "api_port": int(os.getenv("FASTAPI_PORT", 8000)),
        "debug": os.getenv("FASTAPI_DEBUG", "true").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
    }

# Initialize environment
try:
    ENV_CONFIG = load_environment()
    logger.info("Environment configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load environment configuration: {e}")
    ENV_CONFIG = {}

# Import order for proper initialization
def initialize_backend():
    """Initialize the backend package components in proper order."""
    try:
        # Core imports
        from . import database
        from . import models
        from . import agents
        from . import api
        
        # Optional imports (may not be available in all environments)
        try:
            from . import apple_silicon
            logger.info("Apple Silicon optimization module loaded")
        except ImportError:
            logger.info("Apple Silicon optimization not available")
        
        try:
            from . import orchestration
            logger.info("AI orchestration module loaded")
        except ImportError:
            logger.info("AI orchestration module not available")
        
        logger.info("Backend package initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize backend package: {e}")
        return False

# System information
def get_system_info() -> Dict[str, Any]:
    """Get system information for diagnostics."""
    import platform
    import psutil
    
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "package_version": __version__,
        "package_root": str(PACKAGE_ROOT),
        "project_root": str(PROJECT_ROOT),
    }

# Utility functions
def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are available."""
    dependencies = {
        "fastapi": False,
        "sqlalchemy": False,
        "ollama": False,
        "pydantic": False,
        "uvicorn": False,
        "psutil": False,
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
        except ImportError:
            logger.warning(f"Dependency {dep} not available")
    
    return dependencies

def check_ollama_connection() -> bool:
    """Check if Ollama service is accessible."""
    try:
        import requests
        ollama_url = f"http://{ENV_CONFIG.get('ollama_host', 'localhost')}:{ENV_CONFIG.get('ollama_port', 11434)}"
        response = requests.get(f"{ollama_url}/api/version", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Ollama connection check failed: {e}")
        return False

# Health check function
def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": str(logger.handlers[0].formatter.converter()),
        "environment": ENV_CONFIG,
        "system_info": get_system_info(),
        "dependencies": check_dependencies(),
        "ollama_connected": check_ollama_connection(),
    }

# Exception classes
class VirtuAIError(Exception):
    """Base exception for VirtuAI Office backend."""
    pass

class ConfigurationError(VirtuAIError):
    """Configuration related errors."""
    pass

class AgentError(VirtuAIError):
    """AI agent related errors."""
    pass

class DatabaseError(VirtuAIError):
    """Database related errors."""
    pass

class OllamaError(VirtuAIError):
    """Ollama service related errors."""
    pass

# Export main components
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__title__",
    "__description__",
    "__url__",
    
    # Configuration
    "ENV_CONFIG",
    "PACKAGE_ROOT",
    "PROJECT_ROOT",
    
    # Functions
    "initialize_backend",
    "load_environment",
    "get_system_info",
    "check_dependencies",
    "check_ollama_connection",
    "health_check",
    
    # Exceptions
    "VirtuAIError",
    "ConfigurationError",
    "AgentError",
    "DatabaseError",
    "OllamaError",
]

# Initialize the package
if __name__ != "__main__":
    # Only initialize when imported, not when run directly
    initialization_success = initialize_backend()
    if initialization_success:
        logger.info(f"VirtuAI Office Backend v{__version__} ready")
    else:
        logger.error("VirtuAI Office Backend initialization failed")

# Development and debugging utilities
def enable_debug_mode():
    """Enable debug mode with verbose logging."""
    logging.getLogger().setLevel(logging.DEBUG)
    logger.debug("Debug mode enabled")

def get_package_info():
    """Get detailed package information for debugging."""
    return {
        "package": __title__,
        "version": __version__,
        "author": __author__,
        "python_requires": __python_requires__,
        "package_root": str(PACKAGE_ROOT),
        "project_root": str(PROJECT_ROOT),
        "environment": ENV_CONFIG,
        "initialization_status": "ready" if check_dependencies()["fastapi"] else "incomplete"
    }

# Startup message
logger.info(f"🤖 VirtuAI Office Backend Package v{__version__} loaded")
logger.info(f"📁 Package root: {PACKAGE_ROOT}")
logger.info(f"🐍 Python version: {sys.version.split()[0]}")

# Environment validation on import
if ENV_CONFIG:
    logger.info(f"🔧 Environment: {ENV_CONFIG.get('database_url', 'not configured')}")
    logger.info(f"🤖 Ollama: {ENV_CONFIG.get('ollama_host')}:{ENV_CONFIG.get('ollama_port')}")
else:
    logger.warning("⚠️ Environment configuration incomplete")

# Final initialization check
try:
    deps = check_dependencies()
    missing_deps = [dep for dep, available in deps.items() if not available]
    if missing_deps:
        logger.warning(f"⚠️ Missing dependencies: {missing_deps}")
    else:
        logger.info("✅ All dependencies available")
except Exception as e:
    logger.error(f"❌ Dependency check failed: {e}")
