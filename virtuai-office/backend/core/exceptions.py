# VirtuAI Office - Custom Exception Classes
from typing import Optional, Dict, Any
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class VirtuAIException(Exception):
    """Base exception class for VirtuAI Office"""
    def __init__(self, message: str, code: str = "VIRTUAI_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.code}] {self.message}"

    def to_dict(self):
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details
        }

# Agent-related exceptions
class AgentException(VirtuAIException):
    """Base exception for agent-related errors"""
    pass

class AgentNotFoundError(AgentException):
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent with ID '{agent_id}' not found",
            code="AGENT_NOT_FOUND",
            details={"agent_id": agent_id}
        )

class AgentBusyError(AgentException):
    def __init__(self, agent_id: str, current_task_count: int):
        super().__init__(
            message=f"Agent '{agent_id}' is busy with {current_task_count} tasks",
            code="AGENT_BUSY",
            details={"agent_id": agent_id, "current_task_count": current_task_count}
        )

class AgentCapabilityError(AgentException):
    def __init__(self, agent_id: str, required_skills: list):
        super().__init__(
            message=f"Agent '{agent_id}' lacks required skills: {', '.join(required_skills)}",
            code="AGENT_CAPABILITY_MISMATCH",
            details={"agent_id": agent_id, "required_skills": required_skills}
        )

class AgentInitializationError(AgentException):
    def __init__(self, agent_type: str, error_details: str):
        super().__init__(
            message=f"Failed to initialize agent of type '{agent_type}': {error_details}",
            code="AGENT_INIT_ERROR",
            details={"agent_type": agent_type, "error_details": error_details}
        )

# Task-related exceptions
class TaskException(VirtuAIException):
    """Base exception for task-related errors"""
    pass

class TaskNotFoundError(TaskException):
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task with ID '{task_id}' not found",
            code="TASK_NOT_FOUND",
            details={"task_id": task_id}
        )

class TaskValidationError(TaskException):
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Task validation failed for field '{field}': {message}",
            code="TASK_VALIDATION_ERROR",
            details={"field": field, "validation_error": message}
        )

class TaskProcessingError(TaskException):
    def __init__(self, task_id: str, error_details: str):
        super().__init__(
            message=f"Failed to process task '{task_id}': {error_details}",
            code="TASK_PROCESSING_ERROR",
            details={"task_id": task_id, "error_details": error_details}
        )

class TaskAssignmentError(TaskException):
    def __init__(self, task_id: str, reason: str):
        super().__init__(
            message=f"Failed to assign task '{task_id}': {reason}",
            code="TASK_ASSIGNMENT_ERROR",
            details={"task_id": task_id, "reason": reason}
        )

class TaskStatusError(TaskException):
    def __init__(self, task_id: str, current_status: str, attempted_status: str):
        super().__init__(
            message=f"Cannot change task '{task_id}' from '{current_status}' to '{attempted_status}'",
            code="TASK_STATUS_ERROR",
            details={
                "task_id": task_id,
                "current_status": current_status,
                "attempted_status": attempted_status
            }
        )

# AI Model exceptions
class ModelException(VirtuAIException):
    """Base exception for AI model-related errors"""
    pass

class ModelNotFoundError(ModelException):
    def __init__(self, model_name: str):
        super().__init__(
            message=f"AI model '{model_name}' not found or not available",
            code="MODEL_NOT_FOUND",
            details={"model_name": model_name}
        )

class ModelLoadError(ModelException):
    def __init__(self, model_name: str, error_details: str):
        super().__init__(
            message=f"Failed to load model '{model_name}': {error_details}",
            code="MODEL_LOAD_ERROR",
            details={"model_name": model_name, "error_details": error_details}
        )

class ModelInferenceError(ModelException):
    def __init__(self, model_name: str, prompt_length: int, error_details: str):
        super().__init__(
            message=f"Inference failed for model '{model_name}': {error_details}",
            code="MODEL_INFERENCE_ERROR",
            details={
                "model_name": model_name,
                "prompt_length": prompt_length,
                "error_details": error_details
            }
        )

class ModelCompatibilityError(ModelException):
    def __init__(self, model_name: str, system_requirements: dict):
        super().__init__(
            message=f"Model '{model_name}' is not compatible with current system",
            code="MODEL_COMPATIBILITY_ERROR",
            details={"model_name": model_name, "requirements": system_requirements}
        )

# Ollama-specific exceptions
class OllamaException(VirtuAIException):
    """Base exception for Ollama-related errors"""
    pass

class OllamaConnectionError(OllamaException):
    def __init__(self, host: str, port: int):
        super().__init__(
            message=f"Cannot connect to Ollama server at {host}:{port}",
            code="OLLAMA_CONNECTION_ERROR",
            details={"host": host, "port": port}
        )

class OllamaServiceError(OllamaException):
    def __init__(self, error_details: str):
        super().__init__(
            message=f"Ollama service error: {error_details}",
            code="OLLAMA_SERVICE_ERROR",
            details={"error_details": error_details}
        )

# Boss AI exceptions
class BossAIException(VirtuAIException):
    """Base exception for Boss AI orchestration errors"""
    pass

class TaskAnalysisError(BossAIException):
    def __init__(self, task_description: str, error_details: str):
        super().__init__(
            message=f"Failed to analyze task: {error_details}",
            code="TASK_ANALYSIS_ERROR",
            details={"task_description": task_description[:100], "error_details": error_details}
        )

class OptimalAssignmentError(BossAIException):
    def __init__(self, task_id: str, available_agents: int):
        super().__init__(
            message=f"Cannot find optimal assignment for task '{task_id}' among {available_agents} agents",
            code="OPTIMAL_ASSIGNMENT_ERROR",
            details={"task_id": task_id, "available_agents": available_agents}
        )

class CollaborationPlanningError(BossAIException):
    def __init__(self, task_id: str, required_agents: list):
        super().__init__(
            message=f"Failed to create collaboration plan for task '{task_id}'",
            code="COLLABORATION_PLANNING_ERROR",
            details={"task_id": task_id, "required_agents": required_agents}
        )

# Apple Silicon exceptions
class AppleSiliconException(VirtuAIException):
    """Base exception for Apple Silicon optimization errors"""
    pass

class AppleSiliconDetectionError(AppleSiliconException):
    def __init__(self, error_details: str):
        super().__init__(
            message=f"Failed to detect Apple Silicon capabilities: {error_details}",
            code="APPLE_SILICON_DETECTION_ERROR",
            details={"error_details": error_details}
        )

class AppleSiliconOptimizationError(AppleSiliconException):
    def __init__(self, chip_type: str, error_details: str):
        super().__init__(
            message=f"Failed to apply optimizations for {chip_type}: {error_details}",
            code="APPLE_SILICON_OPTIMIZATION_ERROR",
            details={"chip_type": chip_type, "error_details": error_details}
        )

class PerformanceMonitoringError(AppleSiliconException):
    def __init__(self, metric_type: str, error_details: str):
        super().__init__(
            message=f"Failed to monitor {metric_type} performance: {error_details}",
            code="PERFORMANCE_MONITORING_ERROR",
            details={"metric_type": metric_type, "error_details": error_details}
        )

# Database exceptions
class DatabaseException(VirtuAIException):
    """Base exception for database-related errors"""
    pass

class DatabaseConnectionError(DatabaseException):
    def __init__(self, database_url: str):
        super().__init__(
            message=f"Failed to connect to database: {database_url}",
            code="DATABASE_CONNECTION_ERROR",
            details={"database_url": database_url}
        )

class DatabaseMigrationError(DatabaseException):
    def __init__(self, migration_name: str, error_details: str):
        super().__init__(
            message=f"Database migration '{migration_name}' failed: {error_details}",
            code="DATABASE_MIGRATION_ERROR",
            details={"migration_name": migration_name, "error_details": error_details}
        )

# Project management exceptions
class ProjectException(VirtuAIException):
    """Base exception for project-related errors"""
    pass

class ProjectNotFoundError(ProjectException):
    def __init__(self, project_id: str):
        super().__init__(
            message=f"Project with ID '{project_id}' not found",
            code="PROJECT_NOT_FOUND",
            details={"project_id": project_id}
        )

class ProjectValidationError(ProjectException):
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Project validation failed for field '{field}': {message}",
            code="PROJECT_VALIDATION_ERROR",
            details={"field": field, "validation_error": message}
        )

# System resource exceptions
class ResourceException(VirtuAIException):
    """Base exception for system resource errors"""
    pass

class InsufficientMemoryError(ResourceException):
    def __init__(self, required_mb: int, available_mb: int):
        super().__init__(
            message=f"Insufficient memory: required {required_mb}MB, available {available_mb}MB",
            code="INSUFFICIENT_MEMORY",
            details={"required_mb": required_mb, "available_mb": available_mb}
        )

class InsufficientDiskSpaceError(ResourceException):
    def __init__(self, required_gb: float, available_gb: float):
        super().__init__(
            message=f"Insufficient disk space: required {required_gb}GB, available {available_gb}GB",
            code="INSUFFICIENT_DISK_SPACE",
            details={"required_gb": required_gb, "available_gb": available_gb}
        )

class ThermalThrottlingError(ResourceException):
    def __init__(self, current_temp: float, max_temp: float):
        super().__init__(
            message=f"System thermal throttling detected: {current_temp}°C (max: {max_temp}°C)",
            code="THERMAL_THROTTLING",
            details={"current_temp": current_temp, "max_temp": max_temp}
        )

# Utility functions for exception handling
def handle_virtuai_exception(exc: VirtuAIException) -> HTTPException:
    """Convert VirtuAI exception to FastAPI HTTPException"""
    
    # Log the exception
    logger.error(f"VirtuAI Exception: {exc}")
    
    # Map exception codes to HTTP status codes
    status_code_map = {
        "AGENT_NOT_FOUND": 404,
        "TASK_NOT_FOUND": 404,
        "PROJECT_NOT_FOUND": 404,
        "MODEL_NOT_FOUND": 404,
        "AGENT_BUSY": 429,
        "TASK_VALIDATION_ERROR": 422,
        "PROJECT_VALIDATION_ERROR": 422,
        "AGENT_CAPABILITY_MISMATCH": 400,
        "TASK_STATUS_ERROR": 400,
        "MODEL_COMPATIBILITY_ERROR": 400,
        "OLLAMA_CONNECTION_ERROR": 503,
        "OLLAMA_SERVICE_ERROR": 503,
        "DATABASE_CONNECTION_ERROR": 503,
        "INSUFFICIENT_MEMORY": 507,
        "INSUFFICIENT_DISK_SPACE": 507,
        "THERMAL_THROTTLING": 503
    }
    
    status_code = status_code_map.get(exc.code, 500)
    
    return HTTPException(
        status_code=status_code,
        detail=exc.to_dict()
    )

def log_and_raise(exception_class, *args, **kwargs):
    """Helper function to log and raise exceptions"""
    exc = exception_class(*args, **kwargs)
    logger.error(f"Raising exception: {exc}")
    raise exc

def safe_execute(func, *args, exception_class=VirtuAIException, error_message="Operation failed", **kwargs):
    """Safely execute a function and convert exceptions to VirtuAI exceptions"""
    try:
        return func(*args, **kwargs)
    except VirtuAIException:
        # Re-raise VirtuAI exceptions as-is
        raise
    except Exception as e:
        # Convert other exceptions to VirtuAI exceptions
        logger.error(f"Unexpected error in {func.__name__}: {e}")
        raise exception_class(f"{error_message}: {str(e)}")

# Exception middleware for FastAPI
async def virtuai_exception_handler(request, exc: VirtuAIException):
    """FastAPI exception handler for VirtuAI exceptions"""
    http_exc = handle_virtuai_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail
    )

# Context manager for exception handling
class ExceptionContext:
    """Context manager for handling exceptions in specific contexts"""
    
    def __init__(self, context_name: str, suppress_errors: bool = False):
        self.context_name = context_name
        self.suppress_errors = suppress_errors
        self.exceptions = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, VirtuAIException):
            self.exceptions.append(exc_val)
            logger.error(f"Exception in context '{self.context_name}': {exc_val}")
            
            if self.suppress_errors:
                return True  # Suppress the exception
        
        return False  # Let other exceptions propagate
    
    def has_errors(self) -> bool:
        return len(self.exceptions) > 0
    
    def get_errors(self) -> list:
        return self.exceptions.copy()

# Decorator for automatic exception handling
def handle_exceptions(exception_class=VirtuAIException, error_message="Operation failed"):
    """Decorator to automatically handle exceptions in functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return safe_execute(func, *args, exception_class=exception_class,
                              error_message=error_message, **kwargs)
        return wrapper
    return decorator
