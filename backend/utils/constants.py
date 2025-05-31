# VirtuAI Office - Application Constants
from enum import Enum
from typing import Dict, List, Tuple, Any
import os


# Application Information
APP_NAME = "VirtuAI Office"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Complete AI development team running locally"
APP_AUTHOR = "VirtuAI Office Contributors"
APP_LICENSE = "MIT"
APP_URL = "https://github.com/kefrulz/virtuai-office"


# API Configuration
API_VERSION = "v1"
API_PREFIX = "/api"
API_TITLE = "VirtuAI Office API"
API_DESCRIPTION = "Complete AI development team API with 5 specialized agents"


# Default Ports
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 3000
DEFAULT_OLLAMA_PORT = 11434
DEFAULT_WEBSOCKET_PORT = 8001


# Database Configuration
DEFAULT_DATABASE_URL = "sqlite:///./virtuai_office.db"
DEFAULT_DATABASE_POOL_SIZE = 5
DEFAULT_DATABASE_MAX_OVERFLOW = 10
DATABASE_ECHO = False


# Agent Types
class AgentType(str, Enum):
    PRODUCT_MANAGER = "product_manager"
    FRONTEND_DEVELOPER = "frontend_developer"
    BACKEND_DEVELOPER = "backend_developer"
    UI_UX_DESIGNER = "ui_ux_designer"
    QA_TESTER = "qa_tester"
    BOSS_AI = "boss_ai"


# Task Configuration
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EPIC = "epic"


class TaskType(str, Enum):
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    RESEARCH = "research"
    DESIGN = "design"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"
    DEPLOYMENT = "deployment"


# Agent Definitions
AGENT_DEFINITIONS = {
    AgentType.PRODUCT_MANAGER: {
        "name": "Alice Chen",
        "description": "Senior Product Manager with expertise in user stories, requirements, and project planning",
        "expertise": [
            "user stories", "requirements", "product roadmap", "stakeholder analysis",
            "project planning", "agile", "scrum", "acceptance criteria",
            "sprint planning", "backlog management", "user research"
        ],
        "emoji": "👩‍💼",
        "color": "#7c3aed",
        "default_model": "llama2:7b"
    },
    AgentType.FRONTEND_DEVELOPER: {
        "name": "Marcus Dev",
        "description": "Senior Frontend Developer specializing in React, modern UI frameworks, and responsive design",
        "expertise": [
            "react", "javascript", "typescript", "css", "html",
            "responsive design", "ui components", "state management",
            "testing", "webpack", "next.js", "tailwind", "styled-components"
        ],
        "emoji": "👨‍💻",
        "color": "#2563eb",
        "default_model": "codellama:7b"
    },
    AgentType.BACKEND_DEVELOPER: {
        "name": "Sarah Backend",
        "description": "Senior Backend Developer with expertise in Python, APIs, databases, and system architecture",
        "expertise": [
            "python", "fastapi", "django", "flask", "postgresql", "mongodb",
            "rest apis", "graphql", "authentication", "database design",
            "testing", "docker", "microservices", "redis", "celery"
        ],
        "emoji": "👩‍💻",
        "color": "#10b981",
        "default_model": "codellama:7b"
    },
    AgentType.UI_UX_DESIGNER: {
        "name": "Luna Design",
        "description": "Senior UI/UX Designer with expertise in user-centered design, wireframing, and design systems",
        "expertise": [
            "ui design", "ux design", "wireframing", "prototyping",
            "design systems", "accessibility", "user research", "figma",
            "responsive design", "interaction design", "usability testing"
        ],
        "emoji": "🎨",
        "color": "#ec4899",
        "default_model": "llama2:7b"
    },
    AgentType.QA_TESTER: {
        "name": "TestBot QA",
        "description": "Senior QA Engineer with expertise in test planning, automation, and quality assurance",
        "expertise": [
            "test planning", "test automation", "manual testing", "pytest",
            "jest", "selenium", "api testing", "performance testing",
            "bug reporting", "test data management", "ci/cd testing"
        ],
        "emoji": "🔍",
        "color": "#f59e0b",
        "default_model": "llama2:7b"
    }
}


# Apple Silicon Configuration
class AppleSiliconChip(str, Enum):
    M1 = "m1"
    M1_PRO = "m1_pro"
    M1_MAX = "m1_max"
    M1_ULTRA = "m1_ultra"
    M2 = "m2"
    M2_PRO = "m2_pro"
    M2_MAX = "m2_max"
    M2_ULTRA = "m2_ultra"
    M3 = "m3"
    M3_PRO = "m3_pro"
    M3_MAX = "m3_max"
    INTEL = "intel"
    UNKNOWN = "unknown"


APPLE_SILICON_SPECS = {
    AppleSiliconChip.M1: {
        "cpu_cores": 8,
        "gpu_cores": 7,
        "neural_engine": True,
        "memory_bandwidth_gbps": 68.25,
        "max_power_watts": 20,
        "optimal_models": ["llama2:7b", "codellama:7b"],
        "max_concurrent_agents": 3
    },
    AppleSiliconChip.M1_PRO: {
        "cpu_cores": 10,
        "gpu_cores": 16,
        "neural_engine": True,
        "memory_bandwidth_gbps": 200,
        "max_power_watts": 30,
        "optimal_models": ["llama2:13b", "codellama:13b"],
        "max_concurrent_agents": 5
    },
    AppleSiliconChip.M1_MAX: {
        "cpu_cores": 10,
        "gpu_cores": 32,
        "neural_engine": True,
        "memory_bandwidth_gbps": 400,
        "max_power_watts": 60,
        "optimal_models": ["llama2:13b", "codellama:13b"],
        "max_concurrent_agents": 8
    },
    AppleSiliconChip.M2: {
        "cpu_cores": 8,
        "gpu_cores": 10,
        "neural_engine": True,
        "memory_bandwidth_gbps": 100,
        "max_power_watts": 20,
        "optimal_models": ["llama2:7b", "codellama:7b"],
        "max_concurrent_agents": 4
    },
    AppleSiliconChip.M2_PRO: {
        "cpu_cores": 12,
        "gpu_cores": 19,
        "neural_engine": True,
        "memory_bandwidth_gbps": 200,
        "max_power_watts": 30,
        "optimal_models": ["llama2:13b", "codellama:13b"],
        "max_concurrent_agents": 6
    },
    AppleSiliconChip.M2_MAX: {
        "cpu_cores": 12,
        "gpu_cores": 38,
        "neural_engine": True,
        "memory_bandwidth_gbps": 400,
        "max_power_watts": 60,
        "optimal_models": ["llama2:13b", "codellama:13b"],
        "max_concurrent_agents": 10
    },
    AppleSiliconChip.M3: {
        "cpu_cores": 8,
        "gpu_cores": 10,
        "neural_engine": True,
        "memory_bandwidth_gbps": 100,
        "max_power_watts": 22,
        "optimal_models": ["llama2:7b", "codellama:7b"],
        "max_concurrent_agents": 5
    },
    AppleSiliconChip.M3_PRO: {
        "cpu_cores": 12,
        "gpu_cores": 18,
        "neural_engine": True,
        "memory_bandwidth_gbps": 150,
        "max_power_watts": 30,
        "optimal_models": ["llama2:13b", "codellama:13b"],
        "max_concurrent_agents": 7
    },
    AppleSiliconChip.M3_MAX: {
        "cpu_cores": 16,
        "gpu_cores": 40,
        "neural_engine": True,
        "memory_bandwidth_gbps": 300,
        "max_power_watts": 60,
        "optimal_models": ["llama2:13b", "codellama:13b"],
        "max_concurrent_agents": 12
    }
}


# AI Model Configuration
DEFAULT_AI_MODELS = {
    "llama2:7b": {
        "size_gb": 3.8,
        "complexity": "medium",
        "speed": "fast",
        "min_memory_gb": 8,
        "use_cases": ["general", "conversation", "analysis"]
    },
    "llama2:13b": {
        "size_gb": 7.3,
        "complexity": "high",
        "speed": "medium",
        "min_memory_gb": 16,
        "use_cases": ["complex_reasoning", "detailed_analysis", "professional"]
    },
    "llama2:70b": {
        "size_gb": 39.0,
        "complexity": "very_high",
        "speed": "slow",
        "min_memory_gb": 64,
        "use_cases": ["research", "expert_analysis", "complex_projects"]
    },
    "codellama:7b": {
        "size_gb": 3.8,
        "complexity": "medium",
        "speed": "fast",
        "min_memory_gb": 8,
        "use_cases": ["coding", "debugging", "code_review"]
    },
    "codellama:13b": {
        "size_gb": 7.3,
        "complexity": "high",
        "speed": "medium",
        "min_memory_gb": 16,
        "use_cases": ["complex_coding", "architecture", "system_design"]
    },
    "codellama:34b": {
        "size_gb": 19.0,
        "complexity": "very_high",
        "speed": "slow",
        "min_memory_gb": 32,
        "use_cases": ["advanced_coding", "optimization", "enterprise_development"]
    }
}


# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    "cpu_usage_warning": 80.0,
    "cpu_usage_critical": 95.0,
    "memory_usage_warning": 85.0,
    "memory_usage_critical": 95.0,
    "inference_speed_minimum": 1.0,  # tokens per second
    "inference_speed_good": 10.0,
    "inference_speed_excellent": 20.0,
    "model_load_time_warning": 30.0,  # seconds
    "model_load_time_critical": 60.0,
    "task_timeout_default": 300,  # seconds
    "task_timeout_complex": 900,  # 15 minutes
    "max_concurrent_tasks_default": 3,
    "max_queue_size": 100
}


# WebSocket Message Types
class WebSocketMessageType(str, Enum):
    TASK_UPDATE = "task_update"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_STATUS = "agent_status"
    SYSTEM_STATUS = "system_status"
    PERFORMANCE_UPDATE = "performance_update"
    NOTIFICATION = "notification"
    STANDUP_GENERATED = "standup_generated"
    MODEL_DOWNLOADED = "model_downloaded"
    OPTIMIZATION_COMPLETE = "optimization_complete"
    COLLABORATION_UPDATE = "collaboration_update"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


# File and Directory Paths
DEFAULT_LOG_DIR = "logs"
DEFAULT_BACKUP_DIR = "backups"
DEFAULT_MODELS_DIR = "models"
DEFAULT_UPLOADS_DIR = "uploads"
DEFAULT_EXPORTS_DIR = "exports"


# Logging Configuration
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5


# Security Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001"
]

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]


# Rate Limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_STORAGE = "memory"


# Background Task Configuration
MAX_BACKGROUND_WORKERS = 4
MAX_CONCURRENT_AI_TASKS = 2
TASK_RETRY_ATTEMPTS = 3
TASK_RETRY_DELAY_BASE = 2  # seconds (exponential backoff)
TASK_RETRY_DELAY_MAX = 300  # 5 minutes


# Cleanup Configuration
CLEANUP_COMPLETED_TASKS_DAYS = 30
CLEANUP_FAILED_TASKS_DAYS = 7
CLEANUP_LOG_FILES_DAYS = 14
CLEANUP_BACKUP_FILES_DAYS = 90


# API Response Messages
API_MESSAGES = {
    "task_created": "Task created successfully",
    "task_not_found": "Task not found",
    "agent_not_found": "Agent not found",
    "project_created": "Project created successfully",
    "project_not_found": "Project not found",
    "optimization_applied": "Apple Silicon optimizations applied successfully",
    "optimization_failed": "Optimization failed - check system compatibility",
    "model_download_started": "Model download started in background",
    "model_download_failed": "Model download failed",
    "invalid_input": "Invalid input provided",
    "system_healthy": "System is healthy",
    "system_issues": "System issues detected",
    "unauthorized": "Unauthorized access",
    "internal_error": "Internal server error occurred"
}


# Environment Variable Names
ENV_VARS = {
    "DATABASE_URL": "DATABASE_URL",
    "LOG_LEVEL": "LOG_LEVEL",
    "LOG_DIR": "LOG_DIR",
    "OLLAMA_HOST": "OLLAMA_HOST",
    "OLLAMA_PORT": "OLLAMA_PORT",
    "FRONTEND_URL": "FRONTEND_URL",
    "BACKEND_PORT": "BACKEND_PORT",
    "ENVIRONMENT": "ENVIRONMENT",
    "DEBUG": "DEBUG",
    "MAX_WORKERS": "MAX_WORKERS",
    "MAX_AI_TASKS": "MAX_AI_TASKS",
    "APPLE_SILICON_OPTIMIZE": "APPLE_SILICON_OPTIMIZE"
}


# Development vs Production Settings
DEVELOPMENT_SETTINGS = {
    "debug": True,
    "reload": True,
    "log_level": "DEBUG",
    "cors_origins": ["*"],
    "database_echo": True
}

PRODUCTION_SETTINGS = {
    "debug": False,
    "reload": False,
    "log_level": "INFO",
    "cors_origins": CORS_ORIGINS,
    "database_echo": False
}


# Feature Flags
FEATURE_FLAGS = {
    "apple_silicon_optimization": True,
    "collaboration_workflows": True,
    "performance_monitoring": True,
    "background_tasks": True,
    "websocket_updates": True,
    "model_auto_download": True,
    "system_benchmarking": True,
    "advanced_logging": True,
    "api_rate_limiting": False,  # Disabled for local use
    "user_authentication": False  # Not implemented yet
}


# Status Codes
HTTP_STATUS_CODES = {
    "OK": 200,
    "CREATED": 201,
    "ACCEPTED": 202,
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503
}


# System Requirements
MINIMUM_SYSTEM_REQUIREMENTS = {
    "memory_gb": 8,
    "disk_space_gb": 10,
    "cpu_cores": 2,
    "python_version": "3.8",
    "node_version": "16.0"
}

RECOMMENDED_SYSTEM_REQUIREMENTS = {
    "memory_gb": 16,
    "disk_space_gb": 50,
    "cpu_cores": 8,
    "python_version": "3.11",
    "node_version": "18.0"
}


# Default Task Templates
TASK_TEMPLATES = {
    "create_react_component": {
        "title": "Create React Component",
        "description": "Create a reusable React component with props, state management, and proper styling",
        "priority": TaskPriority.MEDIUM,
        "complexity": TaskComplexity.MEDIUM,
        "estimated_effort": 2
    },
    "api_endpoint": {
        "title": "Create API Endpoint",
        "description": "Implement a REST API endpoint with proper validation, error handling, and documentation",
        "priority": TaskPriority.MEDIUM,
        "complexity": TaskComplexity.MEDIUM,
        "estimated_effort": 3
    },
    "ui_design": {
        "title": "UI Design",
        "description": "Create UI design specifications including wireframes, mockups, and style guidelines",
        "priority": TaskPriority.MEDIUM,
        "complexity": TaskComplexity.SIMPLE,
        "estimated_effort": 2
    },
    "test_plan": {
        "title": "Test Plan",
        "description": "Create comprehensive test plan with test cases, scenarios, and automation strategy",
        "priority": TaskPriority.HIGH,
        "complexity": TaskComplexity.MEDIUM,
        "estimated_effort": 2
    },
    "user_story": {
        "title": "User Story",
        "description": "Write detailed user stories with acceptance criteria and success metrics",
        "priority": TaskPriority.MEDIUM,
        "complexity": TaskComplexity.SIMPLE,
        "estimated_effort": 1
    }
}


# Collaboration Types
class CollaborationType(str, Enum):
    INDEPENDENT = "independent"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    REVIEW = "review"
    BRAINSTORM = "brainstorm"


# Performance Metrics
PERFORMANCE_METRICS = [
    "cpu_usage_percent",
    "memory_usage_percent",
    "memory_pressure_state",
    "thermal_state",
    "inference_speed_tokens_per_second",
    "model_load_time_seconds",
    "task_completion_rate",
    "agent_utilization_percent",
    "queue_size",
    "average_response_time_ms"
]


# Export commonly used constants
__all__ = [
    "APP_NAME", "APP_VERSION", "API_VERSION", "API_PREFIX",
    "AgentType", "TaskStatus", "TaskPriority", "TaskComplexity", "TaskType",
    "AGENT_DEFINITIONS", "AppleSiliconChip", "APPLE_SILICON_SPECS",
    "DEFAULT_AI_MODELS", "PERFORMANCE_THRESHOLDS", "WebSocketMessageType",
    "CORS_ORIGINS", "FEATURE_FLAGS", "HTTP_STATUS_CODES",
    "MINIMUM_SYSTEM_REQUIREMENTS", "RECOMMENDED_SYSTEM_REQUIREMENTS",
    "TASK_TEMPLATES", "CollaborationType", "PERFORMANCE_METRICS"
]
