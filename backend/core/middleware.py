# VirtuAI Office - FastAPI Middleware Collection
import time
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.base import BaseHTTPMiddleware as StarletteBaseHTTPMiddleware

from .logging import get_logger, get_virtuai_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger('virtuai.api')
        self.virtuai_logger = get_virtuai_logger()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        self.logger.info(
            f"🔌 Request {request_id}: {request.method} {request.url.path}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'query_params': str(request.query_params),
                'client_ip': request.client.host,
                'user_agent': request.headers.get('user-agent', ''),
                'content_type': request.headers.get('content-type', '')
            }
        )
        
        # Add request ID to state for downstream use
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            
            # Log response
            self.virtuai_logger.log_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                response_time=process_time,
                user_agent=request.headers.get('user-agent'),
                client_ip=request.client.host,
                request_id=request_id
            )
            
            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            self.logger.error(
                f"❌ Request {request_id} failed: {str(e)}",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'error': str(e),
                    'process_time': process_time
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent API abuse"""
    
    def __init__(self, app: ASGIApp, 
                 requests_per_minute: int = 60,
                 requests_per_hour: int = 1000,
                 enable_rate_limiting: bool = True):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.enable_rate_limiting = enable_rate_limiting
        self.logger = get_logger('virtuai.api')
        
        # In-memory store for rate limiting (use Redis in production)
        self.request_counts: Dict[str, Dict[str, Any]] = {}
        self.cleanup_interval = 3600  # Clean up old entries every hour
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enable_rate_limiting:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean up old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            await self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        # Check rate limits
        if await self._is_rate_limited(client_ip, current_time):
            self.logger.warning(
                f"🚫 Rate limit exceeded for {client_ip}",
                extra={
                    'client_ip': client_ip,
                    'path': request.url.path,
                    'method': request.method
                }
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Record request
        await self._record_request(client_ip, current_time)
        
        return await call_next(request)
    
    async def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client has exceeded rate limits"""
        if client_ip not in self.request_counts:
            return False
        
        client_data = self.request_counts[client_ip]
        
        # Check per-minute limit
        minute_requests = [
            req_time for req_time in client_data.get('requests', [])
            if current_time - req_time < 60
        ]
        
        if len(minute_requests) >= self.requests_per_minute:
            return True
        
        # Check per-hour limit
        hour_requests = [
            req_time for req_time in client_data.get('requests', [])
            if current_time - req_time < 3600
        ]
        
        if len(hour_requests) >= self.requests_per_hour:
            return True
        
        return False
    
    async def _record_request(self, client_ip: str, current_time: float):
        """Record a request for rate limiting"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {'requests': []}
        
        self.request_counts[client_ip]['requests'].append(current_time)
        
        # Keep only recent requests (last hour)
        self.request_counts[client_ip]['requests'] = [
            req_time for req_time in self.request_counts[client_ip]['requests']
            if current_time - req_time < 3600
        ]
    
    async def _cleanup_old_entries(self, current_time: float):
        """Clean up old rate limiting entries"""
        clients_to_remove = []
        
        for client_ip, client_data in self.request_counts.items():
            # Remove requests older than 1 hour
            recent_requests = [
                req_time for req_time in client_data.get('requests', [])
                if current_time - req_time < 3600
            ]
            
            if recent_requests:
                self.request_counts[client_ip]['requests'] = recent_requests
            else:
                clients_to_remove.append(client_ip)
        
        # Remove clients with no recent requests
        for client_ip in clients_to_remove:
            del self.request_counts[client_ip]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value
        
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring API performance"""
    
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.logger = get_logger('virtuai.performance')
        self.virtuai_logger = get_virtuai_logger()
        
        # Performance metrics
        self.request_metrics = {
            'total_requests': 0,
            'slow_requests': 0,
            'error_requests': 0,
            'average_response_time': 0.0,
            'last_reset': time.time()
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(response_time, response.status_code)
            
            # Log slow requests
            if response_time > self.slow_request_threshold:
                self.logger.warning(
                    f"🐌 Slow request: {request.method} {request.url.path} took {response_time:.3f}s",
                    extra={
                        'method': request.method,
                        'path': request.url.path,
                        'response_time': response_time,
                        'status_code': response.status_code
                    }
                )
            
            # Add performance headers
            response.headers["X-Response-Time"] = str(round(response_time, 4))
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(response_time, 500, error=True)
            raise
    
    def _update_metrics(self, response_time: float, status_code: int, error: bool = False):
        """Update performance metrics"""
        self.request_metrics['total_requests'] += 1
        
        if response_time > self.slow_request_threshold:
            self.request_metrics['slow_requests'] += 1
        
        if error or status_code >= 400:
            self.request_metrics['error_requests'] += 1
        
        # Update average response time (simple moving average)
        total_requests = self.request_metrics['total_requests']
        current_avg = self.request_metrics['average_response_time']
        self.request_metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
        
        # Log performance metrics every 100 requests
        if total_requests % 100 == 0:
            self.virtuai_logger.log_performance_metric(
                'api_requests_processed',
                total_requests,
                'requests',
                slow_requests=self.request_metrics['slow_requests'],
                error_requests=self.request_metrics['error_requests'],
                average_response_time=self.request_metrics['average_response_time']
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.request_metrics,
            'uptime': time.time() - self.request_metrics['last_reset'],
            'requests_per_second': self.request_metrics['total_requests'] / (time.time() - self.request_metrics['last_reset'])
        }


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling"""
    
    def __init__(self, app: ASGIApp, include_error_details: bool = False):
        super().__init__(app)
        self.include_error_details = include_error_details
        self.logger = get_logger('virtuai.api')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
            
        except HTTPException as e:
            # Handle HTTP exceptions (these are expected)
            self.logger.info(
                f"HTTP Exception: {e.status_code} - {e.detail}",
                extra={
                    'status_code': e.status_code,
                    'detail': e.detail,
                    'path': request.url.path,
                    'method': request.method
                }
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail,
                    "status_code": e.status_code,
                    "path": request.url.path,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            # Handle unexpected exceptions
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            self.logger.error(
                f"Unhandled exception in request {request_id}: {str(e)}",
                extra={
                    'request_id': request_id,
                    'path': request.url.path,
                    'method': request.method,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            
            # Prepare error response
            error_content = {
                "error": "Internal server error",
                "status_code": 500,
                "path": request.url.path,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }
            
            # Include error details in development
            if self.include_error_details:
                error_content["detail"] = str(e)
                error_content["type"] = type(e).__name__
            
            return JSONResponse(
                status_code=500,
                content=error_content
            )


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health checks and system monitoring"""
    
    def __init__(self, app: ASGIApp, health_check_path: str = "/health"):
        super().__init__(app)
        self.health_check_path = health_check_path
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Handle health check requests
        if request.url.path == self.health_check_path:
            return await self._handle_health_check(request)
        
        return await call_next(request)
    
    async def _handle_health_check(self, request: Request) -> Response:
        """Handle health check requests"""
        uptime = time.time() - self.start_time
        
        # Basic health check
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": round(uptime, 2),
            "version": "1.0.0",
            "environment": "production"  # Could be set from env var
        }
        
        # Add detailed health information if requested
        if request.query_params.get("detailed") == "true":
            health_status.update({
                "system": {
                    "cpu_usage": 0.0,  # Could integrate with psutil
                    "memory_usage": 0.0,  # Could integrate with psutil
                    "disk_usage": 0.0   # Could integrate with psutil
                },
                "services": {
                    "database": "healthy",
                    "ollama": "healthy",
                    "agents": "healthy"
                }
            })
        
        return JSONResponse(content=health_status)


class WebSocketMiddleware:
    """Middleware for WebSocket connections"""
    
    def __init__(self):
        self.logger = get_logger('virtuai.websocket')
        self.active_connections: List[Any] = []
    
    async def connect(self, websocket):
        """Handle WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                self.logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected WebSockets
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def send_to_client(self, websocket, message: str):
        """Send message to specific WebSocket client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.warning(f"Failed to send message to specific WebSocket: {e}")
            await self.disconnect(websocket)


def setup_cors_middleware(app, origins: List[str] = None):
    """Setup CORS middleware with appropriate origins"""
    if origins is None:
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080"
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-Response-Time"]
    )


def setup_middleware(app, config: Dict[str, Any] = None):
    """Setup all middleware for the FastAPI application"""
    config = config or {}
    
    # Security headers (first)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Error handling
    app.add_middleware(
        ErrorHandlingMiddleware,
        include_error_details=config.get('include_error_details', False)
    )
    
    # Performance monitoring
    app.add_middleware(
        PerformanceMonitoringMiddleware,
        slow_request_threshold=config.get('slow_request_threshold', 1.0)
    )
    
    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=config.get('rate_limit_per_minute', 60),
        requests_per_hour=config.get('rate_limit_per_hour', 1000),
        enable_rate_limiting=config.get('enable_rate_limiting', True)
    )
    
    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Health check
    app.add_middleware(
        HealthCheckMiddleware,
        health_check_path=config.get('health_check_path', '/health')
    )
    
    # CORS (last)
    setup_cors_middleware(app, config.get('cors_origins'))
    
    logger = get_logger('virtuai.app')
    logger.info("🛡️ All middleware configured successfully")


# Middleware configuration class
class MiddlewareConfig:
    """Configuration class for middleware settings"""
    
    def __init__(self,
                 enable_rate_limiting: bool = True,
                 rate_limit_per_minute: int = 60,
                 rate_limit_per_hour: int = 1000,
                 slow_request_threshold: float = 1.0,
                 include_error_details: bool = False,
                 cors_origins: List[str] = None,
                 health_check_path: str = "/health"):
        
        self.enable_rate_limiting = enable_rate_limiting
        self.rate_limit_per_minute = rate_limit_per_minute
        self.rate_limit_per_hour = rate_limit_per_hour
        self.slow_request_threshold = slow_request_threshold
        self.include_error_details = include_error_details
        self.cors_origins = cors_origins or [
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]
        self.health_check_path = health_check_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'enable_rate_limiting': self.enable_rate_limiting,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'rate_limit_per_hour': self.rate_limit_per_hour,
            'slow_request_threshold': self.slow_request_threshold,
            'include_error_details': self.include_error_details,
            'cors_origins': self.cors_origins,
            'health_check_path': self.health_check_path
        }


# Global WebSocket manager instance
websocket_manager = WebSocketMiddleware()
