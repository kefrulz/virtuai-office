# VirtuAI Office - Core Configuration
import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator
from pathlib import Path
import logging

# Get the root directory of the project
ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "VirtuAI Office"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=True, env="RELOAD")
    
    # Database
    database_url: str = Field(
        default=f"sqlite:///{ROOT_DIR}/virtuai_office.db",
        env="DATABASE_URL"
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Ollama Configuration
    ollama_host: str = Field(default="localhost", env="OLLAMA_HOST")
    ollama_port: int = Field(default=11434, env="OLLAMA_PORT")
    ollama_timeout: int = Field(default=300, env="OLLAMA_TIMEOUT")  # 5 minutes
    
    # Default AI Models
    default_model: str = Field(default="llama2:7b", env="DEFAULT_MODEL")
    code_model: str = Field(default="codellama:7b", env="CODE_MODEL")
    
    # Model Configuration
    model_temperature: float = Field(default=0.7, env="MODEL_TEMPERATURE")
    model_max_tokens: int = Field(default=2048, env="MODEL_MAX_TOKENS")
    model_top_p: float = Field(default=0.9, env="MODEL_TOP_P")
    
    # Performance Settings
    max_concurrent_tasks: int = Field(default=5, env="MAX_CONCURRENT_TASKS")
    task_timeout: int = Field(default=600, env="TASK_TIMEOUT")  # 10 minutes
    agent_response_timeout: int = Field(default=180, env="AGENT_RESPONSE_TIMEOUT")  # 3 minutes
    
    # Apple Silicon Optimization
    enable_apple_silicon_optimization: bool = Field(
        default=True,
        env="ENABLE_APPLE_SILICON_OPTIMIZATION"
    )
    auto_model_selection: bool = Field(default=True, env="AUTO_MODEL_SELECTION")
    thermal_monitoring: bool = Field(default=True, env="THERMAL_MONITORING")
    
    # WebSocket Configuration
    websocket_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    websocket_timeout: int = Field(default=60, env="WS_TIMEOUT")
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        env="CORS_ALLOW_HEADERS"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_rotation: str = Field(default="1 week", env="LOG_ROTATION")
    log_retention: str = Field(default="1 month", env="LOG_RETENTION")
    
    # Security Settings
    secret_key: str = Field(
        default="virtuai-office-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    enable_api_key_auth: bool = Field(default=False, env="ENABLE_API_KEY_AUTH")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=False, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    
    # File Storage
    upload_dir: str = Field(
        default=str(ROOT_DIR / "uploads"),
        env="UPLOAD_DIR"
    )
    max_upload_size: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(
        default=[".txt", ".md", ".json", ".csv", ".py", ".js", ".html", ".css"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Monitoring and Analytics
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_endpoint: str = Field(default="/metrics", env="METRICS_ENDPOINT")
    enable_health_check: bool = Field(default=True, env="ENABLE_HEALTH_CHECK")
    health_check_endpoint: str = Field(default="/health", env="HEALTH_CHECK_ENDPOINT")
    
    # Development Settings
    enable_debug_toolbar: bool = Field(default=False, env="ENABLE_DEBUG_TOOLBAR")
    enable_profiler: bool = Field(default=False, env="ENABLE_PROFILER")
    mock_ai_responses: bool = Field(default=False, env="MOCK_AI_RESPONSES")
    
    # Boss AI Configuration
    enable_boss_ai: bool = Field(default=True, env="ENABLE_BOSS_AI")
    boss_ai_model: str = Field(default="llama2:7b", env="BOSS_AI_MODEL")
    intelligent_assignment: bool = Field(default=True, env="INTELLIGENT_ASSIGNMENT")
    auto_collaboration: bool = Field(default=True, env="AUTO_COLLABORATION")
    performance_tracking: bool = Field(default=True, env="PERFORMANCE_TRACKING")
    
    # Agent Configuration
    agent_timeout: int = Field(default=300, env="AGENT_TIMEOUT")  # 5 minutes
    agent_retry_attempts: int = Field(default=3, env="AGENT_RETRY_ATTEMPTS")
    agent_retry_delay: int = Field(default=5, env="AGENT_RETRY_DELAY")  # seconds
    
    # Collaboration Settings
    enable_multi_agent_collaboration: bool = Field(
        default=True,
        env="ENABLE_MULTI_AGENT_COLLABORATION"
    )
    collaboration_timeout: int = Field(default=1800, env="COLLABORATION_TIMEOUT")  # 30 minutes
    max_collaboration_agents: int = Field(default=3, env="MAX_COLLABORATION_AGENTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator("database_url")
    def validate_database_url(cls, v):
        """Ensure database directory exists for SQLite"""
        if v.startswith("sqlite://"):
            db_path = v.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        return v
    
    @validator("upload_dir")
    def validate_upload_dir(cls, v):
        """Ensure upload directory exists"""
        if not os.path.exists(v):
            os.makedirs(v, exist_ok=True)
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("cors_allow_methods", pre=True)
    def parse_cors_methods(cls, v):
        """Parse CORS methods from string or list"""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v
    
    @validator("allowed_file_types", pre=True)
    def parse_allowed_file_types(cls, v):
        """Parse allowed file types from string or list"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @property
    def ollama_base_url(self) -> str:
        """Get the complete Ollama base URL"""
        return f"http://{self.ollama_host}:{self.ollama_port}"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() in ["development", "dev", "local"]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() in ["production", "prod"]
    
    @property
    def database_config(self) -> dict:
        """Get database configuration dictionary"""
        return {
            "url": self.database_url,
            "echo": self.database_echo and self.is_development,
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
    
    @property
    def logging_config(self) -> dict:
        """Get logging configuration dictionary"""
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.log_level,
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "": {
                    "level": self.log_level,
                    "handlers": ["console"],
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": "WARNING",
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
        
        # Add file handler if log file is specified
        if self.log_file:
            config["handlers"]["file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": self.log_level,
                "formatter": "detailed",
                "filename": self.log_file,
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
            }
            config["loggers"][""]["handlers"].append("file")
        
        return config


# Create settings instance
settings = Settings()

# Export commonly used configuration groups
DATABASE_CONFIG = settings.database_config
LOGGING_CONFIG = settings.logging_config
OLLAMA_CONFIG = {
    "base_url": settings.ollama_base_url,
    "timeout": settings.ollama_timeout,
    "default_model": settings.default_model,
    "code_model": settings.code_model,
}

# Model configuration for different use cases
MODEL_CONFIGS = {
    "default": {
        "model": settings.default_model,
        "temperature": settings.model_temperature,
        "max_tokens": settings.model_max_tokens,
        "top_p": settings.model_top_p,
    },
    "code": {
        "model": settings.code_model,
        "temperature": 0.1,  # Lower temperature for code generation
        "max_tokens": settings.model_max_tokens,
        "top_p": 0.95,
    },
    "creative": {
        "model": settings.default_model,
        "temperature": 0.9,  # Higher temperature for creative tasks
        "max_tokens": settings.model_max_tokens,
        "top_p": 0.8,
    },
    "analysis": {
        "model": settings.default_model,
        "temperature": 0.3,  # Lower temperature for analytical tasks
        "max_tokens": settings.model_max_tokens,
        "top_p": 0.9,
    },
}
