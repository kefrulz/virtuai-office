# VirtuAI Office - Backend Utilities Package
"""
Backend utilities package for VirtuAI Office.

This package contains common utility functions, helpers, and shared code
used across the VirtuAI Office backend services.
"""

from .validation import (
    validate_task_input,
    validate_agent_config,
    validate_project_data,
    sanitize_user_input,
    ValidationError
)

from .formatting import (
    format_task_output,
    format_agent_response,
    format_datetime,
    format_file_size,
    truncate_text,
    format_duration
)

from .encryption import (
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    generate_api_key,
    hash_password,
    verify_password
)

from .file_operations import (
    ensure_directory_exists,
    safe_file_write,
    safe_file_read,
    get_file_info,
    cleanup_temp_files,
    compress_file,
    extract_archive
)

from .system_info import (
    get_system_specs,
    get_memory_usage,
    get_cpu_usage,
    get_disk_usage,
    get_network_info,
    is_apple_silicon,
    get_python_version,
    get_platform_info
)

from .api_helpers import (
    create_response,
    create_error_response,
    paginate_results,
    extract_client_ip,
    rate_limit_key,
    validate_api_key
)

from .database_helpers import (
    get_or_create,
    bulk_insert,
    safe_delete,
    backup_table,
    optimize_database,
    get_table_stats
)

from .task_helpers import (
    generate_task_id,
    estimate_task_complexity,
    extract_task_keywords,
    classify_task_type,
    calculate_task_priority_score,
    merge_task_outputs
)

from .agent_helpers import (
    get_agent_by_expertise,
    calculate_agent_workload,
    get_agent_performance_score,
    select_optimal_agent,
    balance_agent_assignments
)

from .performance_utils import (
    measure_execution_time,
    memory_profiler,
    cpu_profiler,
    benchmark_function,
    performance_monitor,
    cache_result
)

from .apple_silicon_utils import (
    detect_apple_chip,
    get_unified_memory_size,
    optimize_for_apple_silicon,
    get_metal_support,
    get_neural_engine_info,
    recommend_model_for_hardware
)

from .websocket_utils import (
    broadcast_message,
    send_to_user,
    create_room,
    join_room,
    leave_room,
    get_room_members
)

from .ai_model_utils import (
    get_available_models,
    download_model,
    get_model_info,
    estimate_model_memory,
    select_optimal_model,
    manage_model_cache
)


# Version information
__version__ = "1.0.0"
__author__ = "VirtuAI Office Team"
__email__ = "support@virtuai-office.com"

# Package metadata
__all__ = [
    # Validation
    'validate_task_input',
    'validate_agent_config',
    'validate_project_data',
    'sanitize_user_input',
    'ValidationError',
    
    # Formatting
    'format_task_output',
    'format_agent_response',
    'format_datetime',
    'format_file_size',
    'truncate_text',
    'format_duration',
    
    # Encryption
    'encrypt_sensitive_data',
    'decrypt_sensitive_data',
    'generate_api_key',
    'hash_password',
    'verify_password',
    
    # File Operations
    'ensure_directory_exists',
    'safe_file_write',
    'safe_file_read',
    'get_file_info',
    'cleanup_temp_files',
    'compress_file',
    'extract_archive',
    
    # System Info
    'get_system_specs',
    'get_memory_usage',
    'get_cpu_usage',
    'get_disk_usage',
    'get_network_info',
    'is_apple_silicon',
    'get_python_version',
    'get_platform_info',
    
    # API Helpers
    'create_response',
    'create_error_response',
    'paginate_results',
    'extract_client_ip',
    'rate_limit_key',
    'validate_api_key',
    
    # Database Helpers
    'get_or_create',
    'bulk_insert',
    'safe_delete',
    'backup_table',
    'optimize_database',
    'get_table_stats',
    
    # Task Helpers
    'generate_task_id',
    'estimate_task_complexity',
    'extract_task_keywords',
    'classify_task_type',
    'calculate_task_priority_score',
    'merge_task_outputs',
    
    # Agent Helpers
    'get_agent_by_expertise',
    'calculate_agent_workload',
    'get_agent_performance_score',
    'select_optimal_agent',
    'balance_agent_assignments',
    
    # Performance Utils
    'measure_execution_time',
    'memory_profiler',
    'cpu_profiler',
    'benchmark_function',
    'performance_monitor',
    'cache_result',
    
    # Apple Silicon Utils
    'detect_apple_chip',
    'get_unified_memory_size',
    'optimize_for_apple_silicon',
    'get_metal_support',
    'get_neural_engine_info',
    'recommend_model_for_hardware',
    
    # WebSocket Utils
    'broadcast_message',
    'send_to_user',
    'create_room',
    'join_room',
    'leave_room',
    'get_room_members',
    
    # AI Model Utils
    'get_available_models',
    'download_model',
    'get_model_info',
    'estimate_model_memory',
    'select_optimal_model',
    'manage_model_cache'
]

# Utility constants
DEFAULT_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Apple Silicon specific constants
APPLE_SILICON_CHIPS = ['M1', 'M2', 'M3', 'M1 Pro', 'M1 Max', 'M1 Ultra', 'M2 Pro', 'M2 Max', 'M2 Ultra', 'M3 Pro', 'M3 Max']
RECOMMENDED_MODELS_BY_MEMORY = {
    8: ['llama2:7b', 'codellama:7b'],
    16: ['llama2:13b', 'codellama:13b'],
    32: ['llama2:13b', 'codellama:13b', 'llama2:70b'],
    64: ['llama2:70b', 'codellama:34b']
}

# Task complexity thresholds
COMPLEXITY_THRESHOLDS = {
    'simple': 0.3,
    'medium': 0.6,
    'complex': 0.8,
    'epic': 1.0
}

# Agent performance thresholds
PERFORMANCE_THRESHOLDS = {
    'excellent': 0.9,
    'good': 0.7,
    'average': 0.5,
    'poor': 0.3
}

# Error codes
ERROR_CODES = {
    'VALIDATION_ERROR': 'VALIDATION_001',
    'AGENT_NOT_FOUND': 'AGENT_001',
    'TASK_NOT_FOUND': 'TASK_001',
    'MODEL_NOT_AVAILABLE': 'MODEL_001',
    'INSUFFICIENT_MEMORY': 'SYSTEM_001',
    'APPLE_SILICON_NOT_DETECTED': 'APPLE_001',
    'WEBSOCKET_CONNECTION_FAILED': 'WS_001',
    'DATABASE_CONNECTION_FAILED': 'DB_001',
    'API_RATE_LIMIT_EXCEEDED': 'API_001'
}

# Success messages
SUCCESS_MESSAGES = {
    'TASK_CREATED': 'Task created successfully',
    'TASK_COMPLETED': 'Task completed successfully',
    'AGENT_ASSIGNED': 'Agent assigned successfully',
    'MODEL_DOWNLOADED': 'Model downloaded successfully',
    'SYSTEM_OPTIMIZED': 'System optimized for Apple Silicon',
    'COLLABORATION_STARTED': 'Agent collaboration initiated',
    'PERFORMANCE_IMPROVED': 'System performance optimized'
}

# Configuration defaults
DEFAULT_CONFIG = {
    'max_concurrent_tasks': 5,
    'task_timeout_seconds': 300,
    'agent_response_timeout': 60,
    'websocket_ping_interval': 30,
    'database_pool_size': 10,
    'cache_ttl_seconds': 3600,
    'log_level': 'INFO',
    'enable_performance_monitoring': True,
    'enable_apple_silicon_optimization': True
}

def get_version():
    """Get the current version of the utilities package."""
    return __version__

def get_default_config():
    """Get the default configuration dictionary."""
    return DEFAULT_CONFIG.copy()

def get_error_code(error_type: str) -> str:
    """Get error code for a specific error type."""
    return ERROR_CODES.get(error_type, 'UNKNOWN_ERROR')

def get_success_message(message_type: str) -> str:
    """Get success message for a specific message type."""
    return SUCCESS_MESSAGES.get(message_type, 'Operation completed successfully')

def initialize_utilities(config: dict = None):
    """Initialize utilities with custom configuration."""
    if config:
        DEFAULT_CONFIG.update(config)
    
    # Initialize logging
    from ..core.logging import setup_logging
    setup_logging(log_level=DEFAULT_CONFIG['log_level'])
    
    # Initialize performance monitoring if enabled
    if DEFAULT_CONFIG['enable_performance_monitoring']:
        from .performance_utils import initialize_monitoring
        initialize_monitoring()
    
    # Initialize Apple Silicon optimization if enabled and available
    if DEFAULT_CONFIG['enable_apple_silicon_optimization'] and is_apple_silicon():
        from .apple_silicon_utils import initialize_apple_silicon_optimization
        initialize_apple_silicon_optimization()

# Auto-initialize with default settings
# This will be called when the package is imported
