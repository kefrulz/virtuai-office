# VirtuAI Office - Security and Safety Module
import os
import re
import hashlib
import secrets
import hmac
import time
from typing import Dict, List, Optional, Set, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import json

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


# Security Configuration
@dataclass
class SecurityConfig:
    """Security configuration settings"""
    # API Security
    api_key_required: bool = False
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Input Validation
    max_input_length: int = 10000
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: Set[str] = None
    
    # Content Filtering
    content_filtering_enabled: bool = True
    blocked_patterns: List[str] = None
    
    # Local-First Security
    disable_network_access: bool = False
    sandbox_mode: bool = True
    
    def __post_init__(self):
        if self.allowed_file_types is None:
            self.allowed_file_types = {'.txt', '.md', '.json', '.py', '.js', '.css', '.html'}
        
        if self.blocked_patterns is None:
            self.blocked_patterns = [
                r'<script[^>]*>.*?</script>',  # Script tags
                r'javascript:',  # JavaScript URLs
                r'on\w+\s*=',  # Event handlers
                r'eval\s*\(',  # Eval function
                r'exec\s*\(',  # Exec function
            ]


class SecurityLevel(str, Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats"""
    XSS = "xss"
    SQL_INJECTION = "sql_injection"
    CODE_INJECTION = "code_injection"
    PATH_TRAVERSAL = "path_traversal"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MALICIOUS_INPUT = "malicious_input"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: ThreatType
    severity: SecurityLevel
    source_ip: str
    user_agent: str
    request_path: str
    payload: str
    timestamp: datetime
    blocked: bool
    additional_info: Dict[str, Any] = None


class SecurityLogger:
    """Centralized security logging"""
    
    def __init__(self, log_file: str = "logs/security.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger("virtuai.security")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter(
                '%(asctime)s | SECURITY | %(levelname)s | %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_security_event(self, event: SecurityEvent):
        """Log a security event"""
        log_data = {
            'type': event.event_type.value,
            'severity': event.severity.value,
            'source_ip': event.source_ip,
            'user_agent': event.user_agent,
            'request_path': event.request_path,
            'blocked': event.blocked,
            'timestamp': event.timestamp.isoformat()
        }
        
        if event.additional_info:
            log_data.update(event.additional_info)
        
        self.logger.warning(f"Security Event: {json.dumps(log_data)}")
    
    def log_access_attempt(self, ip: str, endpoint: str, success: bool):
        """Log access attempts"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Access {status}: {ip} -> {endpoint}")


class InputValidator:
    """Input validation and sanitization"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.blocked_patterns = [re.compile(pattern, re.IGNORECASE)
                                for pattern in config.blocked_patterns]
    
    def validate_input(self, input_data: str, max_length: int = None) -> tuple[bool, str]:
        """Validate and sanitize input data"""
        if not input_data:
            return True, ""
        
        # Length check
        max_len = max_length or self.config.max_input_length
        if len(input_data) > max_len:
            return False, f"Input exceeds maximum length of {max_len} characters"
        
        # Pattern matching for malicious content
        for pattern in self.blocked_patterns:
            if pattern.search(input_data):
                return False, f"Input contains blocked pattern: {pattern.pattern}"
        
        # SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(--|#|\/\*|\*\/)",
            r"(\b(CHAR|NCHAR|VARCHAR|NVARCHAR)\s*\()",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return False, "Input contains potential SQL injection pattern"
        
        # XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return False, "Input contains potential XSS pattern"
        
        return True, input_data
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path separators and special characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        sanitized = re.sub(r'\.{2,}', '.', sanitized)  # Remove multiple dots
        sanitized = sanitized.strip('. ')  # Remove leading/trailing dots and spaces
        
        # Prevent reserved names on Windows
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        
        if sanitized.upper() in reserved_names:
            sanitized = f"_{sanitized}"
        
        return sanitized or "unnamed_file"
    
    def validate_file_upload(self, filename: str, content: bytes) -> tuple[bool, str]:
        """Validate file uploads"""
        # Check filename
        if not filename:
            return False, "Filename is required"
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.config.allowed_file_types:
            return False, f"File type {file_ext} not allowed"
        
        # Check file size
        if len(content) > self.config.max_file_size:
            return False, f"File size exceeds maximum of {self.config.max_file_size} bytes"
        
        # Check for executable content
        executable_signatures = [
            b'\x4D\x5A',  # PE executable
            b'\x7F\x45\x4C\x46',  # ELF executable
            b'\xCA\xFE\xBA\xBE',  # Mach-O executable
            b'\xFE\xED\xFA\xCE',  # Mach-O executable (reverse)
        ]
        
        for signature in executable_signatures:
            if content.startswith(signature):
                return False, "Executable files are not allowed"
        
        return True, "File validation passed"


class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.requests: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, float] = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed based on rate limiting"""
        if not self.config.rate_limit_enabled:
            return True
        
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if client_ip in self.blocked_ips:
            if current_time < self.blocked_ips[client_ip]:
                return False
            else:
                del self.blocked_ips[client_ip]
        
        # Initialize or clean up request history
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Remove old requests outside the window
        window_start = current_time - self.config.rate_limit_window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > window_start
        ]
        
        # Check if rate limit is exceeded
        if len(self.requests[client_ip]) >= self.config.rate_limit_requests:
            # Block IP for the window duration
            self.blocked_ips[client_ip] = current_time + self.config.rate_limit_window
            return False
        
        # Add current request
        self.requests[client_ip].append(current_time)
        return True
    
    def cleanup_old_entries(self):
        """Clean up old entries to prevent memory leaks"""
        current_time = time.time()
        window_start = current_time - self.config.rate_limit_window
        
        # Clean up request history
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                req_time for req_time in self.requests[ip]
                if req_time > window_start
            ]
            if not self.requests[ip]:
                del self.requests[ip]
        
        # Clean up expired blocks
        for ip in list(self.blocked_ips.keys()):
            if current_time >= self.blocked_ips[ip]:
                del self.blocked_ips[ip]


class ContentFilter:
    """Content filtering for AI-generated outputs"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        
        # Patterns for potentially harmful content
        self.harmful_patterns = [
            # Personal information patterns
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            
            # Sensitive instructions
            r'(password|secret|token|key)\s*[:=]\s*[\'"][^\'"]+[\'"]',
            r'rm\s+-rf\s+/',  # Destructive commands
            r'sudo\s+rm',
            r'format\s+c:',
            
            # Malicious code patterns
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
            r'os\.system\s*\(',
            r'subprocess\.',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE)
                                 for pattern in self.harmful_patterns]
    
    def filter_content(self, content: str) -> tuple[bool, str, List[str]]:
        """Filter content for harmful patterns"""
        if not self.config.content_filtering_enabled:
            return True, content, []
        
        issues = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(content)
            if matches:
                issues.append(f"Pattern {i+1}: {self.harmful_patterns[i]}")
        
        if issues:
            return False, content, issues
        
        return True, content, []
    
    def sanitize_ai_output(self, content: str) -> str:
        """Sanitize AI-generated content"""
        # Remove potentially harmful patterns
        sanitized = content
        
        # Remove script tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove eval/exec functions
        sanitized = re.sub(r'\beval\s*\([^)]*\)', '[REMOVED: eval function]', sanitized)
        sanitized = re.sub(r'\bexec\s*\([^)]*\)', '[REMOVED: exec function]', sanitized)
        
        # Remove system commands
        sanitized = re.sub(r'\bos\.system\s*\([^)]*\)', '[REMOVED: system command]', sanitized)
        
        return sanitized


class APIKeyManager:
    """API Key management for authentication"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from secure storage"""
        # In a real implementation, this would load from a secure database
        # For local-first approach, we'll use a simple file-based storage
        api_keys_file = Path("config/api_keys.json")
        
        if api_keys_file.exists():
            try:
                with open(api_keys_file, 'r') as f:
                    self.api_keys = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load API keys: {e}")
    
    def generate_api_key(self, user_id: str, description: str = "") -> str:
        """Generate a new API key"""
        api_key = secrets.token_urlsafe(32)
        
        self.api_keys[api_key] = {
            'user_id': user_id,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'last_used': None,
            'is_active': True
        }
        
        self.save_api_keys()
        return api_key
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate an API key"""
        if not self.config.api_key_required:
            return True
        
        if api_key not in self.api_keys:
            return False
        
        key_data = self.api_keys[api_key]
        if not key_data.get('is_active', False):
            return False
        
        # Update last used timestamp
        key_data['last_used'] = datetime.utcnow().isoformat()
        self.save_api_keys()
        
        return True
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        if api_key in self.api_keys:
            self.api_keys[api_key]['is_active'] = False
            self.save_api_keys()
            return True
        return False
    
    def save_api_keys(self):
        """Save API keys to secure storage"""
        api_keys_file = Path("config/api_keys.json")
        api_keys_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(api_keys_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save API keys: {e}")


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for FastAPI"""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.security_logger = SecurityLogger()
        self.input_validator = InputValidator(config)
        self.rate_limiter = RateLimiter(config)
        self.content_filter = ContentFilter(config)
        self.api_key_manager = APIKeyManager(config)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks"""
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        request_path = request.url.path
        
        # Rate limiting check
        if not self.rate_limiter.is_allowed(client_ip):
            security_event = SecurityEvent(
                event_type=ThreatType.RATE_LIMIT_EXCEEDED,
                severity=SecurityLevel.MEDIUM,
                source_ip=client_ip,
                user_agent=user_agent,
                request_path=request_path,
                payload="",
                timestamp=datetime.utcnow(),
                blocked=True
            )
            self.security_logger.log_security_event(security_event)
            
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
        
        # API key validation
        if self.config.api_key_required:
            api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
            
            if not self.api_key_manager.validate_api_key(api_key):
                security_event = SecurityEvent(
                    event_type=ThreatType.UNAUTHORIZED_ACCESS,
                    severity=SecurityLevel.HIGH,
                    source_ip=client_ip,
                    user_agent=user_agent,
                    request_path=request_path,
                    payload="Invalid API key",
                    timestamp=datetime.utcnow(),
                    blocked=True
                )
                self.security_logger.log_security_event(security_event)
                
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid API key"}
                )
        
        # Input validation for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8')
                    is_valid, error_msg = self.input_validator.validate_input(body_str)
                    
                    if not is_valid:
                        security_event = SecurityEvent(
                            event_type=ThreatType.MALICIOUS_INPUT,
                            severity=SecurityLevel.HIGH,
                            source_ip=client_ip,
                            user_agent=user_agent,
                            request_path=request_path,
                            payload=body_str[:500],  # Truncate for logging
                            timestamp=datetime.utcnow(),
                            blocked=True,
                            additional_info={"validation_error": error_msg}
                        )
                        self.security_logger.log_security_event(security_event)
                        
                        return JSONResponse(
                            status_code=400,
                            content={"detail": f"Invalid input: {error_msg}"}
                        )
                
                # Recreate request with validated body
                request._body = body
            except Exception as e:
                logging.error(f"Error validating request body: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Log successful access
        self.security_logger.log_access_attempt(client_ip, request_path, True)
        
        return response


class SecurityManager:
    """Main security manager class"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.security_logger = SecurityLogger()
        self.input_validator = InputValidator(self.config)
        self.rate_limiter = RateLimiter(self.config)
        self.content_filter = ContentFilter(self.config)
        self.api_key_manager = APIKeyManager(self.config)
    
    def setup_security_middleware(self, app):
        """Setup security middleware for FastAPI app"""
        return SecurityMiddleware(app, self.config)
    
    def validate_task_input(self, title: str, description: str) -> tuple[bool, str]:
        """Validate task creation input"""
        # Validate title
        is_valid, error = self.input_validator.validate_input(title, max_length=200)
        if not is_valid:
            return False, f"Invalid title: {error}"
        
        # Validate description
        is_valid, error = self.input_validator.validate_input(description, max_length=5000)
        if not is_valid:
            return False, f"Invalid description: {error}"
        
        return True, "Validation passed"
    
    def filter_ai_output(self, content: str) -> str:
        """Filter and sanitize AI-generated content"""
        is_safe, filtered_content, issues = self.content_filter.filter_content(content)
        
        if not is_safe:
            logging.warning(f"Content filtering issues: {issues}")
            filtered_content = self.content_filter.sanitize_ai_output(content)
        
        return filtered_content
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, stored_token: str) -> bool:
        """Validate CSRF token"""
        return hmac.compare_digest(token, stored_token)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    def cleanup_security_data(self):
        """Clean up old security data"""
        self.rate_limiter.cleanup_old_entries()
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        return {
            "api_key_required": self.config.api_key_required,
            "rate_limiting_enabled": self.config.rate_limit_enabled,
            "content_filtering_enabled": self.config.content_filtering_enabled,
            "sandbox_mode": self.config.sandbox_mode,
            "active_api_keys": len([k for k, v in self.api_key_manager.api_keys.items() if v.get('is_active', False)]),
            "blocked_ips_count": len(self.rate_limiter.blocked_ips)
        }


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def setup_security(app, config: SecurityConfig = None):
    """Setup security for FastAPI application"""
    security_manager = SecurityManager(config)
    
    # Add security middleware
    app.add_middleware(SecurityMiddleware, config=config or SecurityConfig())
    
    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        headers = security_manager.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
        return response
    
    return security_manager


# Utility functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def safe_file_path(base_path: str, user_path: str) -> str:
    """Create a safe file path preventing directory traversal"""
    base = Path(base_path).resolve()
    user_file = (base / user_path).resolve()
    
    # Ensure the resolved path is within the base directory
    if not str(user_file).startswith(str(base)):
        raise ValueError("Path traversal attempt detected")
    
    return str(user_file)
