# VirtuAI Office - Security Utilities
import os
import secrets
import hashlib
import hmac
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from functools import wraps
import re
import html
import urllib.parse
from pathlib import Path

import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from ..core.logging import get_logger


class SecurityConfig:
    """Security configuration constants"""
    
    # JWT Settings
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30
    
    # Password Settings
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    AUTH_RATE_LIMIT = 10     # auth attempts per minute
    
    # Session Settings
    SESSION_TIMEOUT_MINUTES = 30
    MAX_CONCURRENT_SESSIONS = 5
    
    # File Upload Security
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS = {'.txt', '.json', '.csv', '.md', '.py', '.js', '.html', '.css'}
    DANGEROUS_FILE_EXTENSIONS = {'.exe', '.bat', '.sh', '.ps1', '.cmd', '.scr'}
    
    # Content Security
    MAX_INPUT_LENGTH = 10000
    MAX_TASK_DESCRIPTION_LENGTH = 5000


class PasswordHasher:
    """Secure password hashing utility"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.logger = get_logger('virtuai.security')
    
    def hash_password(self, password: str) -> str:
        """Hash a password securely"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    def is_password_strong(self, password: str) -> tuple[bool, List[str]]:
        """Check if password meets security requirements"""
        issues = []
        
        if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
            issues.append(f"Password must be at least {SecurityConfig.PASSWORD_MIN_LENGTH} characters long")
        
        if SecurityConfig.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if SecurityConfig.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if SecurityConfig.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
            issues.append("Password must contain at least one number")
        
        if SecurityConfig.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        # Check for common weak patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin', 'letmein']:
            issues.append("Password is too common and easily guessed")
        
        return len(issues) == 0, issues


class JWTManager:
    """JWT token management"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or self._generate_secret_key()
        self.logger = get_logger('virtuai.security')
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    def create_access_token(self,
                           subject: str,
                           expires_delta: Optional[timedelta] = None,
                           additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """Create a JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=SecurityConfig.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=SecurityConfig.JWT_ALGORITHM)
    
    def create_refresh_token(self, subject: str) -> str:
        """Create a JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=SecurityConfig.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=SecurityConfig.JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[SecurityConfig.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token"""
        payload = self.verify_token(refresh_token)
        if payload and payload.get("type") == "refresh":
            return self.create_access_token(payload["sub"])
        return None


class DataEncryption:
    """Data encryption utilities"""
    
    def __init__(self, password: Optional[str] = None):
        self.logger = get_logger('virtuai.security')
        if password:
            self.key = self._derive_key_from_password(password)
        else:
            self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key_from_password(self, password: str) -> bytes:
        """Derive encryption key from password"""
        salt = b'virtuai_office_salt'  # In production, use random salt per encryption
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data"""
        if isinstance(data, str):
            data = data.encode()
        
        encrypted = self.cipher.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")
    
    def encrypt_json(self, data: Dict[str, Any]) -> str:
        """Encrypt JSON data"""
        json_str = json.dumps(data, separators=(',', ':'))
        return self.encrypt(json_str)
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt JSON data"""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # HTML escape
        sanitized = html.escape(sanitized)
        
        # Limit length
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_task_input(title: str, description: str) -> tuple[bool, List[str]]:
        """Validate task input"""
        errors = []
        
        # Title validation
        if not title or len(title.strip()) == 0:
            errors.append("Task title is required")
        elif len(title) > 200:
            errors.append("Task title must be less than 200 characters")
        
        # Description validation
        if not description or len(description.strip()) == 0:
            errors.append("Task description is required")
        elif len(description) > SecurityConfig.MAX_TASK_DESCRIPTION_LENGTH:
            errors.append(f"Task description must be less than {SecurityConfig.MAX_TASK_DESCRIPTION_LENGTH} characters")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript URLs
            r'on\w+\s*=',                 # Event handlers
            r'eval\s*\(',                 # eval() calls
            r'exec\s*\(',                 # exec() calls
        ]
        
        combined_text = f"{title} {description}"
        for pattern in suspicious_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                errors.append("Input contains potentially dangerous content")
                break
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_file_upload(filename: str, content_type: str, file_size: int) -> tuple[bool, List[str]]:
        """Validate file upload"""
        errors = []
        
        # File size check
        if file_size > SecurityConfig.MAX_FILE_SIZE:
            errors.append(f"File size exceeds {SecurityConfig.MAX_FILE_SIZE / (1024*1024):.1f}MB limit")
        
        # File extension check
        file_ext = Path(filename).suffix.lower()
        
        if file_ext in SecurityConfig.DANGEROUS_FILE_EXTENSIONS:
            errors.append("File type is not allowed for security reasons")
        elif file_ext not in SecurityConfig.ALLOWED_FILE_EXTENSIONS:
            errors.append(f"File type '{file_ext}' is not supported")
        
        # Filename validation
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
            errors.append("Filename contains invalid characters")
        
        return len(errors) == 0, errors


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}  # {client_id: [(timestamp, endpoint), ...]}
        self.logger = get_logger('virtuai.security')
    
    def is_allowed(self,
                   client_id: str,
                   endpoint: str = "default",
                   limit: int = SecurityConfig.DEFAULT_RATE_LIMIT,
                   window_minutes: int = 1) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        # Clean old entries
        if client_id in self.requests:
            self.requests[client_id] = [
                (timestamp, ep) for timestamp, ep in self.requests[client_id]
                if timestamp > window_start
            ]
        else:
            self.requests[client_id] = []
        
        # Count requests for this endpoint
        endpoint_requests = [
            timestamp for timestamp, ep in self.requests[client_id]
            if ep == endpoint
        ]
        
        if len(endpoint_requests) >= limit:
            self.logger.warning(f"Rate limit exceeded for client {client_id} on endpoint {endpoint}")
            return False
        
        # Add current request
        self.requests[client_id].append((now, endpoint))
        return True
    
    def get_client_id_from_request(self, request: Request) -> str:
        """Extract client ID from request"""
        # Use IP address as default client ID
        client_ip = request.client.host
        
        # If behind proxy, try to get real IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return client_ip


class SessionManager:
    """Session management"""
    
    def __init__(self):
        self.sessions = {}  # {session_id: {user_id, created_at, last_activity, data}}
        self.user_sessions = {}  # {user_id: [session_id, ...]}
        self.logger = get_logger('virtuai.security')
    
    def create_session(self, user_id: str, additional_data: Optional[Dict[str, Any]] = None) -> str:
        """Create a new session"""
        session_id = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        
        # Limit concurrent sessions per user
        if user_id in self.user_sessions:
            user_session_ids = self.user_sessions[user_id]
            if len(user_session_ids) >= SecurityConfig.MAX_CONCURRENT_SESSIONS:
                # Remove oldest session
                oldest_session_id = user_session_ids[0]
                self.destroy_session(oldest_session_id)
        
        # Create session
        session_data = {
            'user_id': user_id,
            'created_at': now,
            'last_activity': now,
            'data': additional_data or {}
        }
        
        self.sessions[session_id] = session_data
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        self.logger.info(f"Created session for user {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session has expired
        if self._is_session_expired(session):
            self.destroy_session(session_id)
            return None
        
        # Update last activity
        session['last_activity'] = datetime.utcnow()
        return session
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        user_id = session['user_id']
        
        # Remove from sessions
        del self.sessions[session_id]
        
        # Remove from user sessions
        if user_id in self.user_sessions:
            self.user_sessions[user_id] = [
                sid for sid in self.user_sessions[user_id] if sid != session_id
            ]
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        self.logger.info(f"Destroyed session {session_id}")
        return True
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.destroy_session(session_id)
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        """Check if session has expired"""
        now = datetime.utcnow()
        timeout = timedelta(minutes=SecurityConfig.SESSION_TIMEOUT_MINUTES)
        return (now - session['last_activity']) > timeout


class SecurityHeaders:
    """Security headers for HTTP responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "frame-ancestors 'none'"
            ),
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': (
                'camera=(), microphone=(), geolocation=(), '
                'payment=(), usb=(), screen-wake-lock=()'
            )
        }


# Security middleware and dependencies

class SecurityMiddleware:
    """Security middleware for FastAPI"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.logger = get_logger('virtuai.security')
    
    async def __call__(self, request: Request, call_next):
        """Process request through security checks"""
        # Rate limiting
        client_id = self.rate_limiter.get_client_id_from_request(request)
        endpoint = str(request.url.path)
        
        # Different limits for different endpoints
        if '/auth' in endpoint:
            limit = SecurityConfig.AUTH_RATE_LIMIT
        else:
            limit = SecurityConfig.DEFAULT_RATE_LIMIT
        
        if not self.rate_limiter.is_allowed(client_id, endpoint, limit):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        security_headers = SecurityHeaders.get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


# Authentication dependencies

security_scheme = HTTPBearer()
jwt_manager = JWTManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = jwt_manager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload.get("sub")


async def get_current_active_user(current_user: str = Depends(get_current_user)) -> str:
    """Get current active user (can be extended to check user status)"""
    # Here you could add additional checks like user.is_active from database
    return current_user


def require_permissions(*required_permissions: str):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs or dependency injection
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permissions (implement based on your user/permission model)
            # For now, we'll assume all authenticated users have all permissions
            # In a real app, you'd check against a database
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure token"""
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    """Generate an API key"""
    return f"vai_{secrets.token_urlsafe(40)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify HMAC signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


def create_signature(payload: str, secret: str) -> str:
    """Create HMAC signature"""
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


# Initialize global instances
password_hasher = PasswordHasher()
input_validator = InputValidator()
session_manager = SessionManager()


# Security audit logging
def log_security_event(event_type: str,
                      user_id: Optional[str] = None,
                      client_ip: Optional[str] = None,
                      additional_data: Optional[Dict[str, Any]] = None):
    """Log security-related events"""
    logger = get_logger('virtuai.security')
    
    log_data = {
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'client_ip': client_ip
    }
    
    if additional_data:
        log_data.update(additional_data)
    
    logger.warning(f"Security Event: {event_type}", extra=log_data)
