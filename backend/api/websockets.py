# VirtuAI Office - WebSocket API for Real-time Updates

import asyncio
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.database import Task, Agent

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = "anonymous"):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "subscriptions": set()
        }
        
        logger.info(f"WebSocket connection established for user: {user_id}")
        
        # Send welcome message
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "message": "Connected to VirtuAI Office",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        try:
            self.active_connections.remove(websocket)
            
            # Remove from user connections
            metadata = self.connection_metadata.get(websocket, {})
            user_id = metadata.get("user_id", "anonymous")
            
            if user_id in self.user_connections:
                if websocket in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(websocket)
                
                # Clean up empty user connection lists
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove metadata
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket connection closed for user: {user_id}")
            
        except ValueError:
            # Connection already removed
            pass
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections for a specific user"""
        if user_id in self.user_connections:
            disconnected = []
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn)
    
    async def broadcast(self, message: Dict[str, Any], exclude: List[WebSocket] = None):
        """Broadcast message to all active connections"""
        if exclude is None:
            exclude = []
        
        disconnected = []
        for connection in self.active_connections:
            if connection not in exclude:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_subscribers(self, event_type: str, message: Dict[str, Any]):
        """Broadcast to connections subscribed to specific event type"""
        disconnected = []
        for connection, metadata in self.connection_metadata.items():
            if event_type in metadata.get("subscriptions", set()):
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending to subscriber: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    def subscribe(self, websocket: WebSocket, event_type: str):
        """Subscribe connection to specific event type"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].add(event_type)
    
    def unsubscribe(self, websocket: WebSocket, event_type: str):
        """Unsubscribe connection from specific event type"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].discard(event_type)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_user_count(self) -> int:
        """Get number of unique users connected"""
        return len(self.user_connections)

# Global connection manager instance
manager = ConnectionManager()

class WebSocketEvents:
    """WebSocket event handlers and message types"""
    
    @staticmethod
    async def task_created(task_id: str, task_title: str, agent_name: str = None):
        """Broadcast task creation event"""
        message = {
            "type": "task_created",
            "task_id": task_id,
            "task_title": task_title,
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(message)
    
    @staticmethod
    async def task_updated(task_id: str, status: str, agent_name: str = None):
        """Broadcast task status update"""
        message = {
            "type": "task_updated",
            "task_id": task_id,
            "status": status,
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(message)
    
    @staticmethod
    async def task_completed(task_id: str, task_title: str, agent_name: str,
                           output_preview: str = None):
        """Broadcast task completion event"""
        message = {
            "type": "task_completed",
            "task_id": task_id,
            "task_title": task_title,
            "agent_name": agent_name,
            "output_preview": output_preview,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(message)
    
    @staticmethod
    async def task_failed(task_id: str, task_title: str, error: str, agent_name: str = None):
        """Broadcast task failure event"""
        message = {
            "type": "task_failed",
            "task_id": task_id,
            "task_title": task_title,
            "error": error,
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(message)
    
    @staticmethod
    async def agent_status_changed(agent_id: str, agent_name: str, status: str,
                                 current_task: str = None):
        """Broadcast agent status change"""
        message = {
            "type": "agent_status_changed",
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": status,
            "current_task": current_task,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(message)
    
    @staticmethod
    async def collaboration_started(task_id: str, agents: List[str]):
        """Broadcast collaboration start event"""
        message = {
            "type": "collaboration_started",
            "task_id": task_id,
            "agents": agents,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(message)
    
    @staticmethod
    async def system_notification(message_text: str, notification_type: str = "info"):
        """Broadcast system notification"""
        message = {
            "type": "system_notification",
            "message": message_text,
            "notification_type": notification_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast(message)
    
    @staticmethod
    async def performance_update(cpu_usage: float, memory_usage: float,
                               active_tasks: int, queue_size: int):
        """Broadcast system performance update"""
        message = {
            "type": "performance_update",
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "active_tasks": active_tasks,
            "queue_size": queue_size,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast_to_subscribers("performance", message)

async def handle_websocket_message(websocket: WebSocket, data: Dict[str, Any], db: Session):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")
    
    try:
        if message_type == "ping":
            # Heartbeat/keepalive
            await manager.send_personal_message(websocket, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == "subscribe":
            # Subscribe to event type
            event_type = data.get("event_type")
            if event_type:
                manager.subscribe(websocket, event_type)
                await manager.send_personal_message(websocket, {
                    "type": "subscribed",
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        elif message_type == "unsubscribe":
            # Unsubscribe from event type
            event_type = data.get("event_type")
            if event_type:
                manager.unsubscribe(websocket, event_type)
                await manager.send_personal_message(websocket, {
                    "type": "unsubscribed",
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        elif message_type == "get_status":
            # Send current system status
            active_tasks = db.query(Task).filter(Task.status == "in_progress").count()
            pending_tasks = db.query(Task).filter(Task.status == "pending").count()
            agents_count = db.query(Agent).filter(Agent.is_active == True).count()
            
            await manager.send_personal_message(websocket, {
                "type": "status_response",
                "active_tasks": active_tasks,
                "pending_tasks": pending_tasks,
                "agents_count": agents_count,
                "connections": manager.get_connection_count(),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == "request_task_updates":
            # Send recent task updates
            recent_tasks = db.query(Task).order_by(Task.created_at.desc()).limit(10).all()
            tasks_data = []
            
            for task in recent_tasks:
                tasks_data.append({
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "agent_name": task.agent.name if task.agent else None,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                })
            
            await manager.send_personal_message(websocket, {
                "type": "task_updates_response",
                "tasks": tasks_data,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        else:
            # Unknown message type
            await manager.send_personal_message(websocket, {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await manager.send_personal_message(websocket, {
            "type": "error",
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        })

async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """Main WebSocket endpoint"""
    user_id = websocket.query_params.get("user_id", "anonymous")
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON message
                message_data = json.loads(data)
                await handle_websocket_message(websocket, message_data, db)
                
            except json.JSONDecodeError:
                # Handle non-JSON messages
                await manager.send_personal_message(websocket, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message(websocket, {
                    "type": "error",
                    "message": "Error processing message",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        manager.disconnect(websocket)

# Background task for periodic updates
async def periodic_updates():
    """Send periodic system updates to connected clients"""
    while True:
        try:
            if manager.get_connection_count() > 0:
                # Send heartbeat every 30 seconds
                await manager.broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "connections": manager.get_connection_count(),
                    "users": manager.get_user_count()
                })
            
            await asyncio.sleep(30)  # Wait 30 seconds
            
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(5)  # Short wait before retrying

# Utility functions for other modules
def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    return manager

def get_websocket_events() -> WebSocketEvents:
    """Get WebSocket events handler"""
    return WebSocketEvents
