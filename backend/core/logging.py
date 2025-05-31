# VirtuAI Office - Centralized Logging Configuration
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import traceback


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, fmt=None, datefmt=None, use_colors=True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors
    
    def format(self, record):
        if self.use_colors and hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        # Add emoji for different components
        if hasattr(record, 'name'):
            if 'agent' in record.name.lower():
                record.name = f"🤖 {record.name}"
            elif 'boss' in record.name.lower():
                record.name = f"🧠 {record.name}"
            elif 'apple_silicon' in record.name.lower():
                record.name = f"🍎 {record.name}"
            elif 'task' in record.name.lower():
                record.name = f"📋 {record.name}"
            elif 'api' in record.name.lower():
                record.name = f"🔌 {record.name}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry['extra'] = log_entry.get('extra', {})
                log_entry['extra'][key] = value
        
        return json.dumps(log_entry)


class VirtuAILogger:
    """Centralized logging configuration for VirtuAI Office"""
    
    def __init__(self,
                 log_level: str = "INFO",
                 log_dir: str = "logs",
                 console_output: bool = True,
                 file_output: bool = True,
                 json_format: bool = False,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir)
        self.console_output = console_output
        self.file_output = file_output
        self.json_format = json_format
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # Create log directory
        if self.file_output:
            self.log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        self._setup_root_logger()
        
        # Create specialized loggers
        self.loggers = self._create_specialized_loggers()
    
    def _setup_root_logger(self):
        """Configure the root logger"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            
            if self.json_format:
                console_formatter = JSONFormatter()
            else:
                console_formatter = ColoredFormatter(
                    fmt='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    use_colors=True
                )
            
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if self.file_output:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_dir / "virtuai_office.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            
            if self.json_format:
                file_formatter = JSONFormatter()
            else:
                file_formatter = logging.Formatter(
                    fmt='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
    
    def _create_specialized_loggers(self) -> Dict[str, logging.Logger]:
        """Create specialized loggers for different components"""
        loggers = {}
        
        # Component-specific loggers
        components = [
            'virtuai.app',
            'virtuai.agents',
            'virtuai.boss_ai',
            'virtuai.tasks',
            'virtuai.api',
            'virtuai.database',
            'virtuai.apple_silicon',
            'virtuai.performance',
            'virtuai.collaboration',
            'virtuai.websocket'
        ]
        
        for component in components:
            logger = logging.getLogger(component)
            logger.setLevel(self.log_level)
            loggers[component] = logger
        
        # Create separate error log file
        if self.file_output:
            error_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_dir / "errors.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            
            error_formatter = logging.Formatter(
                fmt='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s\n%(pathname)s:%(lineno)d in %(funcName)s()\n',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            error_handler.setFormatter(error_formatter)
            
            # Add error handler to all loggers
            for logger in loggers.values():
                logger.addHandler(error_handler)
        
        return loggers
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger by name"""
        if name in self.loggers:
            return self.loggers[name]
        return logging.getLogger(name)
    
    def log_task_event(self, task_id: str, event: str, agent_name: str = None, **kwargs):
        """Log task-related events with structured data"""
        logger = self.get_logger('virtuai.tasks')
        
        extra_data = {
            'task_id': task_id,
            'event': event,
            'agent_name': agent_name,
            **kwargs
        }
        
        message = f"Task {task_id}: {event}"
        if agent_name:
            message += f" (Agent: {agent_name})"
        
        logger.info(message, extra=extra_data)
    
    def log_agent_activity(self, agent_name: str, activity: str, task_id: str = None, **kwargs):
        """Log agent-related activities"""
        logger = self.get_logger('virtuai.agents')
        
        extra_data = {
            'agent_name': agent_name,
            'activity': activity,
            'task_id': task_id,
            **kwargs
        }
        
        message = f"Agent {agent_name}: {activity}"
        if task_id:
            message += f" (Task: {task_id})"
        
        logger.info(message, extra=extra_data)
    
    def log_boss_decision(self, decision_type: str, reasoning: str, **kwargs):
        """Log Boss AI decisions"""
        logger = self.get_logger('virtuai.boss_ai')
        
        extra_data = {
            'decision_type': decision_type,
            'reasoning': reasoning,
            **kwargs
        }
        
        message = f"Boss AI Decision: {decision_type} - {reasoning}"
        logger.info(message, extra=extra_data)
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = None, **kwargs):
        """Log performance metrics"""
        logger = self.get_logger('virtuai.performance')
        
        extra_data = {
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            **kwargs
        }
        
        message = f"Performance: {metric_name} = {value}"
        if unit:
            message += f" {unit}"
        
        logger.info(message, extra=extra_data)
    
    def log_api_request(self, method: str, endpoint: str, status_code: int,
                       response_time: float, user_agent: str = None, **kwargs):
        """Log API requests"""
        logger = self.get_logger('virtuai.api')
        
        extra_data = {
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time': response_time,
            'user_agent': user_agent,
            **kwargs
        }
        
        message = f"API {method} {endpoint} - {status_code} ({response_time:.3f}s)"
        
        if status_code >= 400:
            logger.warning(message, extra=extra_data)
        else:
            logger.info(message, extra=extra_data)
    
    def log_apple_silicon_event(self, event: str, chip_type: str = None, **kwargs):
        """Log Apple Silicon optimization events"""
        logger = self.get_logger('virtuai.apple_silicon')
        
        extra_data = {
            'event': event,
            'chip_type': chip_type,
            **kwargs
        }
        
        message = f"Apple Silicon: {event}"
        if chip_type:
            message += f" (Chip: {chip_type})"
        
        logger.info(message, extra=extra_data)
    
    def setup_request_logging(self, app):
        """Setup request logging middleware for FastAPI"""
        import time
        from fastapi import Request
        
        @app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()
            
            response = await call_next(request)
            
            process_time = time.time() - start_time
            
            self.log_api_request(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                response_time=process_time,
                user_agent=request.headers.get("user-agent"),
                client_ip=request.client.host
            )
            
            return response
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = {
            'log_level': logging.getLevelName(self.log_level),
            'console_output': self.console_output,
            'file_output': self.file_output,
            'json_format': self.json_format,
            'log_files': []
        }
        
        if self.file_output and self.log_dir.exists():
            for log_file in self.log_dir.glob("*.log*"):
                stats['log_files'].append({
                    'name': log_file.name,
                    'size': log_file.stat().st_size,
                    'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
        
        return stats


# Global logger instance
_logger_instance: Optional[VirtuAILogger] = None


def setup_logging(log_level: str = None,
                 log_dir: str = None,
                 console_output: bool = None,
                 file_output: bool = None,
                 json_format: bool = None) -> VirtuAILogger:
    """Setup global logging configuration"""
    global _logger_instance
    
    # Get configuration from environment variables if not provided
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    log_dir = log_dir or os.getenv('LOG_DIR', 'logs')
    console_output = console_output if console_output is not None else os.getenv('LOG_CONSOLE', 'true').lower() == 'true'
    file_output = file_output if file_output is not None else os.getenv('LOG_FILE', 'true').lower() == 'true'
    json_format = json_format if json_format is not None else os.getenv('LOG_JSON', 'false').lower() == 'true'
    
    _logger_instance = VirtuAILogger(
        log_level=log_level,
        log_dir=log_dir,
        console_output=console_output,
        file_output=file_output,
        json_format=json_format
    )
    
    return _logger_instance


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    if _logger_instance is None:
        setup_logging()
    
    if name:
        return _logger_instance.get_logger(name)
    else:
        return logging.getLogger()


def get_virtuai_logger() -> VirtuAILogger:
    """Get the VirtuAI logger instance"""
    if _logger_instance is None:
        setup_logging()
    return _logger_instance


# Convenience functions for common logging patterns
def log_startup(component: str, message: str):
    """Log startup events"""
    logger = get_logger('virtuai.app')
    logger.info(f"🚀 {component}: {message}")


def log_shutdown(component: str, message: str):
    """Log shutdown events"""
    logger = get_logger('virtuai.app')
    logger.info(f"🛑 {component}: {message}")


def log_error_with_context(logger_name: str, error: Exception, context: Dict[str, Any] = None):
    """Log errors with additional context"""
    logger = get_logger(logger_name)
    
    error_message = f"Error: {str(error)}"
    if context:
        error_message += f" | Context: {context}"
    
    logger.error(error_message, exc_info=True, extra=context or {})


def log_performance_warning(component: str, metric: str, value: float, threshold: float):
    """Log performance warnings"""
    logger = get_logger('virtuai.performance')
    logger.warning(
        f"⚠️ Performance Warning: {component} {metric} = {value:.2f} exceeds threshold {threshold:.2f}",
        extra={
            'component': component,
            'metric': metric,
            'value': value,
            'threshold': threshold
        }
    )


# Export commonly used loggers as module-level variables
app_logger = lambda: get_logger('virtuai.app')
agent_logger = lambda: get_logger('virtuai.agents')
boss_logger = lambda: get_logger('virtuai.boss_ai')
task_logger = lambda: get_logger('virtuai.tasks')
api_logger = lambda: get_logger('virtuai.api')
performance_logger = lambda: get_logger('virtuai.performance')
apple_silicon_logger = lambda: get_logger('virtuai.apple_silicon')
