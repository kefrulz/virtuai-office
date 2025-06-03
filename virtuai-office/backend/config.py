# VirtuAI Office - Backend Configuration Management
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
from enum import Enum

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class DatabaseType(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"

class Settings(BaseSettings):
    """
    VirtuAI Office Configuration Settings
    """
    
    # Application Settings
    APP_NAME: str = "VirtuAI Office"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    RELOAD: bool = Field(default=True, env="RELOAD")
    
    # Database Configuration
    DATABASE_TYPE: DatabaseType = Field(default=DatabaseType.SQLITE, env="DATABASE_TYPE")
    DATABASE_URL: str = Field(default="sqlite:///./virtuai_office.db", env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # PostgreSQL specific settings (if used)
    POSTGRES_USER: Optional[str] = Field(default=None, env="POSTGRES_USER")
    POSTGRES_PASSWORD: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")
    POSTGRES_HOST: Optional[str] = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: Optional[int] = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DB: Optional[str] = Field(default="virtuai_office", env="POSTGRES_DB")
    
    # Ollama Configuration
    OLLAMA_HOST: str = Field(default="localhost", env="OLLAMA_HOST")
    OLLAMA_PORT: int = Field(default=11434, env="OLLAMA_PORT")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_TIMEOUT: int = Field(default=120, env="OLLAMA_TIMEOUT")  # seconds
    OLLAMA_MAX_RETRIES: int = Field(default=3, env="OLLAMA_MAX_RETRIES")
    
    # Default AI Models
    DEFAULT_MODEL: str = Field(default="llama2:7b", env="DEFAULT_MODEL")
    CODING_MODEL: str = Field(default="codellama:7b", env="CODING_MODEL")
    FALLBACK_MODEL: str = Field(default="llama2:7b", env="FALLBACK_MODEL")
    
    # Apple Silicon Optimization
    OLLAMA_NUM_THREADS: Optional[int] = Field(default=None, env="OLLAMA_NUM_THREADS")
    OLLAMA_METAL: bool = Field(default=True, env="OLLAMA_METAL")  # GPU acceleration
    OLLAMA_MAX_LOADED_MODELS: int = Field(default=2, env="OLLAMA_MAX_LOADED_MODELS")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # WebSocket Configuration
    WEBSOCKET_PATH: str = Field(default="/ws", env="WEBSOCKET_PATH")
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    
    # Task Processing Configuration
    MAX_CONCURRENT_TASKS: int = Field(default=5, env="MAX_CONCURRENT_TASKS")
    TASK_TIMEOUT: int = Field(default=300, env="TASK_TIMEOUT")  # seconds
    BACKGROUND_TASK_QUEUE_SIZE: int = Field(default=100, env="BACKGROUND_TASK_QUEUE_SIZE")
    
    # Agent Configuration
    AGENT_RESPONSE_TIMEOUT: int = Field(default=120, env="AGENT_RESPONSE_TIMEOUT")
    AGENT_MAX_OUTPUT_LENGTH: int = Field(default=50000, env="AGENT_MAX_OUTPUT_LENGTH")
    AGENT_DEFAULT_TEMPERATURE: float = Field(default=0.7, env="AGENT_DEFAULT_TEMPERATURE")
    
    # Performance Configuration
    PERFORMANCE_MONITORING_ENABLED: bool = Field(default=True, env="PERFORMANCE_MONITORING_ENABLED")
    PERFORMANCE_METRICS_RETENTION_DAYS: int = Field(default=30, env="PERFORMANCE_METRICS_RETENTION_DAYS")
    
    # Apple Silicon Detection
    AUTO_DETECT_APPLE_SILICON: bool = Field(default=True, env="AUTO_DETECT_APPLE_SILICON")
    APPLE_SILICON_OPTIMIZATION: bool = Field(default=True, env="APPLE_SILICON_OPTIMIZATION")
    
    # Security Configuration
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    API_KEY_ENABLED: bool = Field(default=False, env="API_KEY_ENABLED")
    API_KEY: Optional[str] = Field(default=None, env="API_KEY")
    
    # Logging Configuration
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    LOG_FILE_MAX_SIZE: int = Field(default=10485760, env="LOG_FILE_MAX_SIZE")  # 10MB
    LOG_FILE_BACKUP_COUNT: int = Field(default=5, env="LOG_FILE_BACKUP_COUNT")
    
    # File Storage Configuration
    UPLOAD_DIR: str = Field(default="uploads/", env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE: int = Field(default=10485760, env="MAX_UPLOAD_SIZE")  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = Field(
        default=[".txt", ".md", ".json", ".csv", ".py", ".js", ".html", ".css"],
        env="ALLOWED_UPLOAD_EXTENSIONS"
    )
    
    # Cache Configuration
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # seconds
    CACHE_MAX_SIZE: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=False, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Development Features
    ENABLE_DEBUG_ENDPOINTS: bool = Field(default=False, env="ENABLE_DEBUG_ENDPOINTS")
    ENABLE_DEMO_DATA: bool = Field(default=True, env="ENABLE_DEMO_DATA")
    AUTO_RELOAD_MODELS: bool = Field(default=False, env="AUTO_RELOAD_MODELS")
    
    # Monitoring and Health Checks
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    SYSTEM_METRICS_ENABLED: bool = Field(default=True, env="SYSTEM_METRICS_ENABLED")
    
    # Boss AI Configuration
    BOSS_AI_ENABLED: bool = Field(default=True, env="BOSS_AI_ENABLED")
    BOSS_AI_MODEL: str = Field(default="llama2:7b", env="BOSS_AI_MODEL")
    BOSS_AI_DECISION_CONFIDENCE_THRESHOLD: float = Field(default=0.7, env="BOSS_AI_DECISION_CONFIDENCE_THRESHOLD")
    
    # Collaboration Features
    COLLABORATION_ENABLED: bool = Field(default=True, env="COLLABORATION_ENABLED")
    MAX_COLLABORATION_AGENTS: int = Field(default=3, env="MAX_COLLABORATION_AGENTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @validator("DATABASE_URL", pre=True)
    def build_database_url(cls, v, values):
        """Build database URL based on database type and credentials"""
        if "DATABASE_TYPE" in values:
            db_type = values["DATABASE_TYPE"]
            
            if db_type == DatabaseType.POSTGRESQL:
                if all(key in values for key in ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB"]):
                    return f"postgresql://{values['POSTGRES_USER']}:{values['POSTGRES_PASSWORD']}@{values['POSTGRES_HOST']}:{values['POSTGRES_PORT']}/{values['POSTGRES_DB']}"
            elif db_type == DatabaseType.SQLITE:
                return v or "sqlite:///./virtuai_office.db"
        
        return v
    
    @validator("OLLAMA_BASE_URL", pre=True)
    def build_ollama_url(cls, v, values):
        """Build Ollama base URL from host and port"""
        if v:
            return v
        
        host = values.get("OLLAMA_HOST", "localhost")
        port = values.get("OLLAMA_PORT", 11434)
        return f"http://{host}:{port}"
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_UPLOAD_EXTENSIONS", pre=True)
    def parse_upload_extensions(cls, v):
        """Parse allowed upload extensions from string or list"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    def get_database_url(self) -> str:
        """Get the database URL for SQLAlchemy"""
        return self.DATABASE_URL
    
    def get_ollama_url(self) -> str:
        """Get the Ollama base URL"""
        return self.OLLAMA_BASE_URL
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.ENVIRONMENT == Environment.TESTING

# Create global settings instance
settings = Settings()

# Apple Silicon Configuration
class AppleSiliconConfig:
    """Apple Silicon specific configuration"""
    
    @staticmethod
    def get_optimal_settings(memory_gb: int, cpu_cores: int) -> Dict[str, Any]:
        """Get optimal settings based on Apple Silicon specs"""
        config = {}
        
        # Thread optimization
        config["OLLAMA_NUM_THREADS"] = max(1, cpu_cores - 2)
        
        # Model recommendations based on memory
        if memory_gb >= 32:
            config["DEFAULT_MODEL"] = "llama2:13b"
            config["CODING_MODEL"] = "codellama:13b"
            config["OLLAMA_MAX_LOADED_MODELS"] = 3
            config["MAX_CONCURRENT_TASKS"] = 8
        elif memory_gb >= 16:
            config["DEFAULT_MODEL"] = "llama2:7b"
            config["CODING_MODEL"] = "codellama:7b"
            config["OLLAMA_MAX_LOADED_MODELS"] = 2
            config["MAX_CONCURRENT_TASKS"] = 5
        else:
            config["DEFAULT_MODEL"] = "llama2:7b"
            config["CODING_MODEL"] = "codellama:7b"
            config["OLLAMA_MAX_LOADED_MODELS"] = 1
            config["MAX_CONCURRENT_TASKS"] = 3
        
        # Enable Metal GPU acceleration
        config["OLLAMA_METAL"] = True
        
        return config

# Logging Configuration
def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if settings.LOG_FILE:
        from logging.handlers import RotatingFileHandler
        
        # Ensure log directory exists
        log_file_path = Path(settings.LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=settings.LOG_FILE_MAX_SIZE,
            backupCount=settings.LOG_FILE_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Silence noisy loggers in production
    if settings.is_production():
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

# Environment Configuration Validation
def validate_configuration():
    """Validate configuration settings"""
    errors = []
    
    # Check required settings in production
    if settings.is_production():
        if settings.SECRET_KEY == "your-secret-key-change-in-production":
            errors.append("SECRET_KEY must be changed in production")
        
        if settings.DEBUG:
            errors.append("DEBUG should be False in production")
    
    # Validate database configuration
    if settings.DATABASE_TYPE == DatabaseType.POSTGRESQL:
        required_postgres_fields = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_DB"]
        for field in required_postgres_fields:
            if not getattr(settings, field):
                errors.append(f"{field} is required for PostgreSQL")
    
    # Validate upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create upload directory: {e}")
    
    if errors:
        error_msg = "Configuration validation errors:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_msg)

# Configuration Factory
class ConfigurationFactory:
    """Factory for creating different configuration profiles"""
    
    @staticmethod
    def create_development_config() -> Dict[str, Any]:
        """Create development configuration"""
        return {
            "DEBUG": True,
            "ENVIRONMENT": Environment.DEVELOPMENT,
            "DATABASE_URL": "sqlite:///./virtuai_office_dev.db",
            "LOG_LEVEL": LogLevel.DEBUG,
            "ENABLE_DEBUG_ENDPOINTS": True,
            "ENABLE_DEMO_DATA": True,
            "AUTO_RELOAD_MODELS": True,
        }
    
    @staticmethod
    def create_production_config() -> Dict[str, Any]:
        """Create production configuration"""
        return {
            "DEBUG": False,
            "ENVIRONMENT": Environment.PRODUCTION,
            "LOG_LEVEL": LogLevel.INFO,
            "ENABLE_DEBUG_ENDPOINTS": False,
            "ENABLE_DEMO_DATA": False,
            "AUTO_RELOAD_MODELS": False,
            "RATE_LIMIT_ENABLED": True,
        }
    
    @staticmethod
    def create_testing_config() -> Dict[str, Any]:
        """Create testing configuration"""
        return {
            "DEBUG": True,
            "ENVIRONMENT": Environment.TESTING,
            "DATABASE_URL": "sqlite:///:memory:",
            "LOG_LEVEL": LogLevel.WARNING,
            "ENABLE_DEMO_DATA": False,
        }

# Export commonly used objects
__all__ = [
    "settings",
    "Settings",
    "Environment",
    "LogLevel",
    "DatabaseType",
    "AppleSiliconConfig",
    "setup_logging",
    "validate_configuration",
    "ConfigurationFactory",
]

# Initialize logging on import
setup_logging()

# Validate configuration
try:
    validate_configuration()
except ValueError as e:
    logging.warning(f"Configuration validation warning: {e}")
