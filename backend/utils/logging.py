# VirtuAI Office - Logging Utilities
import logging
import sys
import os
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
from functools import wraps
import asyncio
from contextlib import contextmanager

# ANSI color codes for console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class VirtuAIFormatter(logging.Formatter):
    """Custom formatter for VirtuAI Office logs"""
    
    def __init__(self, use_colors: bool = True, include_emoji: bool = True):
        self.use_colors = use_colors
        self.include_emoji = include_emoji
        
        # Color mapping for log levels
        self.colors = {
            logging.DEBUG: Colors.OKCYAN,
            logging.INFO: Colors.OKGREEN,
            logging.WARNING: Colors.WARNING,
            logging.ERROR: Colors.FAIL,
            logging.CRITICAL: Colors.FAIL + Colors.BOLD
        }
        
        # Emoji mapping for different components
        self.component_emojis = {
            'agent': '🤖',
            'boss': '🧠',
            'task': '📋',
            'api': '🔌',
            'websocket': '🔗',
            'database': '💾',
            'apple_silicon': '🍎',
            'performance': '📊',
            'background': '⚡',
            'startup': '🚀',
            'shutdown': '🛑',
            'error': '❌',
            'warning': '⚠️',
            'success': '✅',
            'info': 'ℹ️',
            'debug': '🔍'
        }
        
        super().__init__()
    
    def format(self, record):
        # Get the original message
        message = record.getMessage()
        
        # Add emoji based on logger name or record level
        emoji = self._get_emoji(record)
        
        # Color the log level
        level_name = record.levelname
        if self.use_colors:
            color = self.colors.get(record.levelno, '')
            level_name = f"{color}{level_name}{Colors.ENDC}"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Create formatted message
        formatted_message = f"{timestamp} | {emoji} {record.name:<20} | {level_name:<8} | {message}"
        
        # Add exception info if present
        if record.exc_info:
            formatted_message += "\n" + self.formatException(record.exc_info)
        
        return formatted_message
    
    def _get_emoji(self, record):
        """Get appropriate emoji for the log record"""
        if not self.include_emoji:
            return ""
        
        # Check logger name for component-specific emojis
        logger_name = record.name.lower()
        for component, emoji in self.component_emojis.items():
            if component in logger_name:
                return emoji
        
        # Default to level-based emoji
        level_emojis = {
            logging.DEBUG: self.component_emojis['debug'],
            logging.INFO: self.component_emojis['info'],
            logging.WARNING: self.component_emojis['warning'],
            logging.ERROR: self.component_emojis['error'],
            logging.CRITICAL: self.component_emojis['error']
        }
        
        return level_emojis.get(record.levelno, self.component_emojis['info'])


class JSONLogFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields from LoggerAdapter or custom fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


def setup_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    console_output: bool = True,
    file_output: bool = True,
    json_format: bool = False,
    use_colors: bool = True,
    include_emoji: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """Setup logging configuration for VirtuAI Office"""
    
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory if needed
    if file_output:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        if json_format:
            console_formatter = JSONLogFormatter()
        else:
            console_formatter = VirtuAIFormatter(
                use_colors=use_colors and sys.stdout.isatty(),
                include_emoji=include_emoji
            )
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            filename=Path(log_dir) / "virtuai_office.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        
        if json_format:
            file_formatter = JSONLogFormatter()
        else:
            file_formatter = VirtuAIFormatter(use_colors=False, include_emoji=False)
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Separate error log file
        error_handler = RotatingFileHandler(
            filename=Path(log_dir) / "errors.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)


def get_component_logger(component: str) -> logging.Logger:
    """Get a logger for a specific VirtuAI component"""
    return logging.getLogger(f"virtuai.{component}")


class LoggingMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        return self._logger


def log_execution_time(logger: Optional[logging.Logger] = None):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_logger = logger or logging.getLogger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                func_logger.info(f"Function {func.__name__} executed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                func_logger.error(f"Function {func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_logger = logger or logging.getLogger(func.__module__)
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                func_logger.info(f"Async function {func.__name__} executed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                func_logger.error(f"Async function {func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    return decorator


def log_function_call(logger: Optional[logging.Logger] = None, log_args: bool = False, log_result: bool = False):
    """Decorator to log function calls with optional arguments and results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or logging.getLogger(func.__module__)
            
            # Log function call
            call_info = f"Calling {func.__name__}"
            if log_args:
                call_info += f" with args={args}, kwargs={kwargs}"
            func_logger.debug(call_info)
            
            try:
                result = func(*args, **kwargs)
                
                # Log result if requested
                if log_result:
                    func_logger.debug(f"{func.__name__} returned: {result}")
                
                return result
            except Exception as e:
                func_logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_logger = logger or logging.getLogger(func.__module__)
            
            # Log function call
            call_info = f"Calling async {func.__name__}"
            if log_args:
                call_info += f" with args={args}, kwargs={kwargs}"
            func_logger.debug(call_info)
            
            try:
                result = await func(*args, **kwargs)
                
                # Log result if requested
                if log_result:
                    func_logger.debug(f"{func.__name__} returned: {result}")
                
                return result
            except Exception as e:
                func_logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    return decorator


@contextmanager
def log_context(logger: logging.Logger, message: str, level: int = logging.INFO):
    """Context manager for logging entry and exit of code blocks"""
    logger.log(level, f"Entering: {message}")
    start_time = time.time()
    
    try:
        yield
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Exception in {message} after {duration:.3f}s: {e}")
        raise
    else:
        duration = time.time() - start_time
        logger.log(level, f"Completed: {message} in {duration:.3f}s")


def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    """Log a message with additional context information"""
    if context:
        # Create a LoggerAdapter to include context
        adapter = logging.LoggerAdapter(logger, context)
        adapter.log(level, message)
    else:
        logger.log(level, message)


def log_startup_message(component: str, version: str = None, port: int = None):
    """Log a standardized startup message"""
    logger = get_component_logger(component)
    
    message = f"🚀 {component} starting up"
    if version:
        message += f" (v{version})"
    if port:
        message += f" on port {port}"
    
    logger.info(message)


def log_shutdown_message(component: str):
    """Log a standardized shutdown message"""
    logger = get_component_logger(component)
    logger.info(f"🛑 {component} shutting down")


def log_error_with_traceback(logger: logging.Logger, message: str, error: Exception):
    """Log an error with full traceback information"""
    logger.error(f"{message}: {error}")
    logger.debug(f"Traceback for {message}:", exc_info=True)


def log_performance_metric(logger: logging.Logger, metric_name: str, value: Union[int, float], unit: str = ""):
    """Log a performance metric"""
    unit_str = f" {unit}" if unit else ""
    logger.info(f"📊 Performance: {metric_name} = {value}{unit_str}")


def log_user_action(logger: logging.Logger, user_id: str, action: str, details: Dict[str, Any] = None):
    """Log user actions for audit purposes"""
    message = f"👤 User {user_id}: {action}"
    if details:
        message += f" | Details: {details}"
    logger.info(message)


def log_api_request(logger: logging.Logger, method: str, path: str, status_code: int, response_time: float):
    """Log API requests"""
    status_emoji = "✅" if status_code < 400 else "❌"
    logger.info(f"{status_emoji} {method} {path} - {status_code} ({response_time:.3f}s)")


def log_task_event(logger: logging.Logger, task_id: str, event: str, agent_name: str = None, **kwargs):
    """Log task-related events"""
    message = f"📋 Task {task_id}: {event}"
    if agent_name:
        message += f" (Agent: {agent_name})"
    
    if kwargs:
        message += f" | {kwargs}"
    
    logger.info(message)


def log_agent_activity(logger: logging.Logger, agent_name: str, activity: str, **kwargs):
    """Log agent activities"""
    message = f"🤖 Agent {agent_name}: {activity}"
    
    if kwargs:
        message += f" | {kwargs}"
    
    logger.info(message)


def log_boss_decision(logger: logging.Logger, decision_type: str, reasoning: str, **kwargs):
    """Log Boss AI decisions"""
    message = f"🧠 Boss AI: {decision_type} - {reasoning}"
    
    if kwargs:
        message += f" | {kwargs}"
    
    logger.info(message)


def log_apple_silicon_event(logger: logging.Logger, event: str, chip_type: str = None, **kwargs):
    """Log Apple Silicon optimization events"""
    message = f"🍎 Apple Silicon: {event}"
    if chip_type:
        message += f" ({chip_type})"
    
    if kwargs:
        message += f" | {kwargs}"
    
    logger.info(message)


def log_system_resource(logger: logging.Logger, resource_type: str, value: float, threshold: float = None):
    """Log system resource usage"""
    emoji = "📊"
    if threshold and value > threshold:
        emoji = "⚠️"
    
    message = f"{emoji} System: {resource_type} = {value:.2f}"
    if threshold:
        message += f" (threshold: {threshold:.2f})"
    
    logger.info(message)


def suppress_logging(logger_names: list, level: int = logging.WARNING):
    """Suppress logging for specified loggers below the given level"""
    for logger_name in logger_names:
        logging.getLogger(logger_name).setLevel(level)


def configure_third_party_logging():
    """Configure logging for third-party libraries"""
    # Suppress verbose logging from third-party libraries
    suppress_logging([
        'urllib3.connectionpool',
        'httpx',
        'asyncio',
    ], logging.WARNING)
    
    # Set specific levels for important libraries
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('ollama').setLevel(logging.INFO)


# Default logger for this module
_module_logger = get_logger(__name__)

# Common logger instances
app_logger = get_component_logger('app')
agent_logger = get_component_logger('agents')
boss_logger = get_component_logger('boss_ai')
task_logger = get_component_logger('tasks')
api_logger = get_component_logger('api')
websocket_logger = get_component_logger('websocket')
database_logger = get_component_logger('database')
apple_silicon_logger = get_component_logger('apple_silicon')
performance_logger = get_component_logger('performance')
background_logger = get_component_logger('background_tasks')


# Initialize logging configuration
def init_logging():
    """Initialize logging with default configuration"""
    # Get configuration from environment variables
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_dir = os.getenv('LOG_DIR', 'logs')
    console_output = os.getenv('LOG_CONSOLE', 'true').lower() == 'true'
    file_output = os.getenv('LOG_FILE', 'true').lower() == 'true'
    json_format = os.getenv('LOG_JSON', 'false').lower() == 'true'
    use_colors = os.getenv('LOG_COLORS', 'true').lower() == 'true'
    include_emoji = os.getenv('LOG_EMOJI', 'true').lower() == 'true'
    
    setup_logging(
        level=log_level,
        log_dir=log_dir,
        console_output=console_output,
        file_output=file_output,
        json_format=json_format,
        use_colors=use_colors,
        include_emoji=include_emoji
    )
    
    # Configure third-party library logging
    configure_third_party_logging()
    
    app_logger.info("Logging system initialized")


# Auto-initialize logging when module is imported
if not logging.getLogger().handlers:
    init_logging()
