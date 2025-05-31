# VirtuAI Office - WebSocket Manager Service
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Callable
from enum import Enum
import logging
import weakref
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from starlette.websockets import WebSocketState
import jwt
from pydantic import BaseModel, ValidationError

from ..core.logging import get_logger, log_error_with_context


class MessageType(str, Enum):
    # System messages
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    
    # Task-related messages
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_update"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_ASSIGNED = "task_assigned"
    
    # Agent-related messages
    AGENT_STATUS_CHANGED = "agent_status_changed"
    AGENT_PERFORMANCE_UPDATE = "agent_performance_update"
    
    # Boss AI messages
    BOSS_DECISION = "boss_decision"
    STANDUP_GENERATED = "standup_generated"
    OPTIMIZATION_APPLIED = "optimization_applied"
    
    # Collaboration messages
    COLLABORATION_STARTED = "collaboration_started"
    COLLABORATION_COMPLETED = "collaboration_completed"
    
    # System messages
    SYSTEM_OPTIMIZED = "system_optimized"
    MODEL_DOWNLOADED = "model_downloaded"
    BENCHMARK_COMPLETED = "benchmark_completed"
    PERFORMANCE_WARNING = "performance_warning"
    
    # Notification messages
    NOTIFICATION = "notification"
    ALERT = "alert"


class ClientType(str, Enum):
    DASHBOARD = "dashboard"
    API_CLIENT = "api_client"
    MOBILE = "mobile"
    ADMIN = "admin"


@dataclass
class WebSocketMessage:
    type: MessageType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    client_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "client_id": self.client_id,
            "correlation_id": self.correlation_id
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class WebSocketClient:
    id: str
    websocket: WebSocket
    client_type: ClientType = ClientType.DASHBOARD
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_connected(self) -> bool:
        return (self.websocket.client_state == WebSocketState.CONNECTED and
                self.websocket.application_state == WebSocketState.CONNECTED)
    
    @property
    def connection_duration(self) -> timedelta:
        return datetime.utcnow() - self.connected_at
    
    def is_heartbeat_expired(self, timeout_seconds: int = 60) -> bool:
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() > timeout_seconds


class WebSocketManager:
    """Manages WebSocket connections and real-time communication"""
    
    def __init__(self,
                 heartbeat_interval: int = 30,
                 heartbeat_timeout: int = 60,
                 max_connections: int = 100,
                 enable_authentication: bool = False,
                 jwt_secret: Optional[str] = None):
        
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.max_connections = max_connections
        self.enable_authentication = enable_authentication
        self.jwt_secret = jwt_secret
        
        # Active connections
        self.connections: Dict[str, WebSocketClient] = {}
        self.connection_lock = asyncio.Lock()
        
        # Message handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "broadcasts_sent": 0,
            "errors": 0
        }
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        self.running = False
        
        self.logger = get_logger('virtuai.websocket')
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.ERROR, self._handle_error)
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler for a specific message type"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        self.logger.info(f"Registered handler for message type: {message_type.value}")
    
    async def start(self):
        """Start the WebSocket manager"""
        if self.running:
            self.logger.warning("WebSocket manager is already running")
            return
        
        self.running = True
        self.logger.info("Starting WebSocket manager...")
        
        # Start background tasks
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.background_tasks.add(heartbeat_task)
        self.background_tasks.add(cleanup_task)
        
        # Add cleanup callbacks
        heartbeat_task.add_done_callback(self.background_tasks.discard)
        cleanup_task.add_done_callback(self.background_tasks.discard)
        
        self.logger.info("WebSocket manager started successfully")
    
    async def stop(self):
        """Stop the WebSocket manager"""
        if not self.running:
            return
        
        self.logger.info("Stopping WebSocket manager...")
        self.running = False
        
        # Disconnect all clients
        await self.disconnect_all()
        
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
        self.logger.info("WebSocket manager stopped")
    
    async def connect(self,
                     websocket: WebSocket,
                     client_type: ClientType = ClientType.DASHBOARD,
                     client_id: Optional[str] = None,
                     token: Optional[str] = None) -> str:
        """Connect a new WebSocket client"""
        
        # Check connection limit
        if len(self.connections) >= self.max_connections:
            raise HTTPException(status_code=429, detail="Maximum connections exceeded")
        
        # Authenticate if required
        if self.enable_authentication and not await self._authenticate_client(token):
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # Accept the WebSocket connection
        await websocket.accept()
        
        # Create client object
        client = WebSocketClient(
            id=client_id,
            websocket=websocket,
            client_type=client_type,
            metadata={"token": token} if token else {}
        )
        
        async with self.connection_lock:
            self.connections[client_id] = client
        
        self.stats["total_connections"] += 1
        
        # Send connection confirmation
        await self._send_to_client(client, WebSocketMessage(
            type=MessageType.CONNECTED,
            data={
                "client_id": client_id,
                "server_time": datetime.utcnow().isoformat(),
                "heartbeat_interval": self.heartbeat_interval
            },
            client_id=client_id
        ))
        
        self.logger.info(f"Client connected: {client_id} (type: {client_type.value})")
        return client_id
    
    async def disconnect(self, client_id: str, reason: str = "Normal closure"):
        """Disconnect a specific client"""
        async with self.connection_lock:
            client = self.connections.get(client_id)
            if client:
                try:
                    if client.is_connected:
                        await client.websocket.close(code=1000, reason=reason)
                except Exception as e:
                    self.logger.warning(f"Error closing WebSocket for client {client_id}: {e}")
                
                del self.connections[client_id]
                self.logger.info(f"Client disconnected: {client_id} (reason: {reason})")
    
    async def disconnect_all(self, reason: str = "Server shutdown"):
        """Disconnect all clients"""
        client_ids = list(self.connections.keys())
        for client_id in client_ids:
            await self.disconnect(client_id, reason)
    
    async def send_to_client(self,
                           client_id: str,
                           message_type: MessageType,
                           data: Dict[str, Any] = None,
                           correlation_id: Optional[str] = None) -> bool:
        """Send a message to a specific client"""
        client = self.connections.get(client_id)
        if not client:
            self.logger.warning(f"Client not found: {client_id}")
            return False
        
        message = WebSocketMessage(
            type=message_type,
            data=data or {},
            client_id=client_id,
            correlation_id=correlation_id
        )
        
        return await self._send_to_client(client, message)
    
    async def broadcast(self,
                       message_type: MessageType,
                       data: Dict[str, Any] = None,
                       client_types: Optional[List[ClientType]] = None,
                       exclude_clients: Optional[List[str]] = None) -> int:
        """Broadcast a message to all or filtered clients"""
        message = WebSocketMessage(
            type=message_type,
            data=data or {}
        )
        
        sent_count = 0
        failed_clients = []
        
        async with self.connection_lock:
            clients_to_send = []
            
            for client_id, client in self.connections.items():
                # Apply filters
                if exclude_clients and client_id in exclude_clients:
                    continue
                
                if client_types and client.client_type not in client_types:
                    continue
                
                clients_to_send.append(client)
        
        # Send messages outside the lock to avoid blocking
        for client in clients_to_send:
            try:
                if await self._send_to_client(client, message):
                    sent_count += 1
                else:
                    failed_clients.append(client.id)
            except Exception as e:
                self.logger.error(f"Failed to send message to client {client.id}: {e}")
                failed_clients.append(client.id)
        
        # Clean up failed clients
        for client_id in failed_clients:
            await self.disconnect(client_id, "Send failed")
        
        self.stats["broadcasts_sent"] += 1
        self.logger.debug(f"Broadcast sent to {sent_count} clients (type: {message_type.value})")
        
        return sent_count
    
    async def subscribe_client(self, client_id: str, subscription: str) -> bool:
        """Subscribe a client to specific message types or topics"""
        client = self.connections.get(client_id)
        if not client:
            return False
        
        client.subscriptions.add(subscription)
        self.logger.debug(f"Client {client_id} subscribed to: {subscription}")
        return True
    
    async def unsubscribe_client(self, client_id: str, subscription: str) -> bool:
        """Unsubscribe a client from specific message types or topics"""
        client = self.connections.get(client_id)
        if not client:
            return False
        
        client.subscriptions.discard(subscription)
        self.logger.debug(f"Client {client_id} unsubscribed from: {subscription}")
        return True
    
    async def handle_client_message(self, client_id: str, message: str):
        """Handle incoming message from a client"""
        try:
            self.stats["messages_received"] += 1
            
            # Parse message
            try:
                message_data = json.loads(message)
            except json.JSONDecodeError as e:
                await self._send_error_to_client(client_id, f"Invalid JSON: {str(e)}")
                return
            
            # Validate message structure
            message_type = message_data.get("type")
            if not message_type:
                await self._send_error_to_client(client_id, "Missing message type")
                return
            
            try:
                msg_type = MessageType(message_type)
            except ValueError:
                await self._send_error_to_client(client_id, f"Invalid message type: {message_type}")
                return
            
            # Create message object
            ws_message = WebSocketMessage(
                type=msg_type,
                data=message_data.get("data", {}),
                client_id=client_id,
                correlation_id=message_data.get("correlation_id")
            )
            
            # Call registered handlers
            if msg_type in self.message_handlers:
                for handler in self.message_handlers[msg_type]:
                    try:
                        await handler(client_id, ws_message)
                    except Exception as e:
                        log_error_with_context(
                            'virtuai.websocket',
                            e,
                            {'client_id': client_id, 'message_type': msg_type.value}
                        )
            
        except Exception as e:
            self.stats["errors"] += 1
            log_error_with_context(
                'virtuai.websocket',
                e,
                {'client_id': client_id, 'message': message[:100]}
            )
            await self._send_error_to_client(client_id, "Internal server error")
    
    async def _send_to_client(self, client: WebSocketClient, message: WebSocketMessage) -> bool:
        """Send a message to a specific client"""
        if not client.is_connected:
            return False
        
        try:
            await client.websocket.send_text(message.to_json())
            self.stats["messages_sent"] += 1
            return True
        except Exception as e:
            self.logger.warning(f"Failed to send message to client {client.id}: {e}")
            return False
    
    async def _send_error_to_client(self, client_id: str, error_message: str):
        """Send an error message to a client"""
        await self.send_to_client(
            client_id,
            MessageType.ERROR,
            {"message": error_message}
        )
    
    async def _authenticate_client(self, token: Optional[str]) -> bool:
        """Authenticate a client using JWT token"""
        if not token or not self.jwt_secret:
            return not self.enable_authentication
        
        try:
            jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return True
        except jwt.InvalidTokenError:
            return False
    
    async def _heartbeat_loop(self):
        """Background task to send heartbeats and check client health"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                expired_clients = []
                
                async with self.connection_lock:
                    for client_id, client in self.connections.items():
                        # Check if client is still responsive
                        if client.is_heartbeat_expired(self.heartbeat_timeout):
                            expired_clients.append(client_id)
                        elif client.is_connected:
                            # Send heartbeat
                            try:
                                await client.websocket.ping()
                            except Exception:
                                expired_clients.append(client_id)
                
                # Disconnect expired clients
                for client_id in expired_clients:
                    await self.disconnect(client_id, "Heartbeat timeout")
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                log_error_with_context('virtuai.websocket', e, {'component': 'heartbeat'})
                await asyncio.sleep(5)
    
    async def _cleanup_loop(self):
        """Background task to clean up disconnected clients"""
        while self.running:
            try:
                disconnected_clients = []
                
                async with self.connection_lock:
                    for client_id, client in self.connections.items():
                        if not client.is_connected:
                            disconnected_clients.append(client_id)
                
                # Remove disconnected clients
                for client_id in disconnected_clients:
                    await self.disconnect(client_id, "Connection closed")
                
                await asyncio.sleep(30)  # Run every 30 seconds
                
            except Exception as e:
                log_error_with_context('virtuai.websocket', e, {'component': 'cleanup'})
                await asyncio.sleep(30)
    
    # Default message handlers
    
    async def _handle_heartbeat(self, client_id: str, message: WebSocketMessage):
        """Handle heartbeat message from client"""
        client = self.connections.get(client_id)
        if client:
            client.last_heartbeat = datetime.utcnow()
            
            # Send heartbeat response
            await self.send_to_client(
                client_id,
                MessageType.HEARTBEAT,
                {"server_time": datetime.utcnow().isoformat()}
            )
    
    async def _handle_error(self, client_id: str, message: WebSocketMessage):
        """Handle error message from client"""
        error_data = message.data
        self.logger.warning(f"Client {client_id} reported error: {error_data}")
        self.stats["errors"] += 1
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        active_connections = len(self.connections)
        
        # Connection breakdown by type
        type_breakdown = {}
        connection_durations = []
        
        for client in self.connections.values():
            client_type = client.client_type.value
            type_breakdown[client_type] = type_breakdown.get(client_type, 0) + 1
            connection_durations.append(client.connection_duration.total_seconds())
        
        avg_duration = sum(connection_durations) / len(connection_durations) if connection_durations else 0
        
        return {
            "active_connections": active_connections,
            "max_connections": self.max_connections,
            "connection_types": type_breakdown,
            "average_connection_duration": avg_duration,
            "total_connections": self.stats["total_connections"],
            "messages_sent": self.stats["messages_sent"],
            "messages_received": self.stats["messages_received"],
            "broadcasts_sent": self.stats["broadcasts_sent"],
            "errors": self.stats["errors"],
            "running": self.running
        }
    
    def get_connected_clients(self) -> List[Dict[str, Any]]:
        """Get information about connected clients"""
        clients = []
        
        for client in self.connections.values():
            clients.append({
                "id": client.id,
                "type": client.client_type.value,
                "connected_at": client.connected_at.isoformat(),
                "last_heartbeat": client.last_heartbeat.isoformat(),
                "connection_duration": client.connection_duration.total_seconds(),
                "subscriptions": list(client.subscriptions),
                "is_connected": client.is_connected
            })
        
        return clients


# Convenience functions for common WebSocket operations

async def notify_task_created(ws_manager: WebSocketManager, task_id: str, title: str, agent_name: str = None):
    """Notify clients about a new task"""
    await ws_manager.broadcast(
        MessageType.TASK_CREATED,
        {
            "task_id": task_id,
            "title": title,
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def notify_task_completed(ws_manager: WebSocketManager, task_id: str, agent_name: str, output_preview: str = None):
    """Notify clients about task completion"""
    await ws_manager.broadcast(
        MessageType.TASK_COMPLETED,
        {
            "task_id": task_id,
            "agent_name": agent_name,
            "output_preview": output_preview,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def notify_task_failed(ws_manager: WebSocketManager, task_id: str, error: str, agent_name: str = None):
    """Notify clients about task failure"""
    await ws_manager.broadcast(
        MessageType.TASK_FAILED,
        {
            "task_id": task_id,
            "error": error,
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def notify_agent_status_change(ws_manager: WebSocketManager, agent_id: str, agent_name: str, status: str, details: Dict[str, Any] = None):
    """Notify clients about agent status changes"""
    await ws_manager.broadcast(
        MessageType.AGENT_STATUS_CHANGED,
        {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": status,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def notify_boss_decision(ws_manager: WebSocketManager, decision_type: str, reasoning: str, outcome: Dict[str, Any] = None):
    """Notify clients about Boss AI decisions"""
    await ws_manager.broadcast(
        MessageType.BOSS_DECISION,
        {
            "decision_type": decision_type,
            "reasoning": reasoning,
            "outcome": outcome or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def send_notification(ws_manager: WebSocketManager, title: str, message: str, notification_type: str = "info", client_id: str = None):
    """Send a notification to clients"""
    notification_data = {
        "title": title,
        "message": message,
        "type": notification_type,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if client_id:
        await ws_manager.send_to_client(client_id, MessageType.NOTIFICATION, notification_data)
    else:
        await ws_manager.broadcast(MessageType.NOTIFICATION, notification_data)


async def send_performance_warning(ws_manager: WebSocketManager, component: str, metric: str, value: float, threshold: float):
    """Send a performance warning to clients"""
    await ws_manager.broadcast(
        MessageType.PERFORMANCE_WARNING,
        {
            "component": component,
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "message": f"{component} {metric} ({value:.2f}) exceeds threshold ({threshold:.2f})",
            "timestamp": datetime.utcnow().isoformat()
        },
        client_types=[ClientType.DASHBOARD, ClientType.ADMIN]
    )
