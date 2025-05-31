# VirtuAI Office - Notification Service
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging
from abc import ABC, abstractmethod

from ..core.logging import get_logger, log_error_with_context
from ..services.websocket_manager import WebSocketManager


class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    TASK_UPDATE = "task_update"
    AGENT_STATUS = "agent_status"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE = "performance"
    APPLE_SILICON = "apple_silicon"


class NotificationPriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class Notification:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType = NotificationType.INFO
    title: str = ""
    message: str = ""
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    read: bool = False
    actions: List[Dict[str, Any]] = field(default_factory=list)
    target_users: Optional[List[str]] = None  # None means broadcast to all
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
            'message': self.message,
            'priority': self.priority.value,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'read': self.read,
            'actions': self.actions,
            'tags': self.tags
        }
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""
    
    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send notification through this channel"""
        pass
    
    @abstractmethod
    def supports_priority(self, priority: NotificationPriority) -> bool:
        """Check if channel supports the given priority level"""
        pass


class WebSocketNotificationChannel(NotificationChannel):
    """WebSocket-based notification channel"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.logger = get_logger('virtuai.notifications.websocket')
    
    async def send(self, notification: Notification) -> bool:
        try:
            await self.websocket_manager.broadcast({
                'type': 'notification',
                'notification': notification.to_dict()
            })
            return True
        except Exception as e:
            self.logger.error(f"Failed to send WebSocket notification: {e}")
            return False
    
    def supports_priority(self, priority: NotificationPriority) -> bool:
        return True  # WebSocket supports all priorities


class ConsoleNotificationChannel(NotificationChannel):
    """Console/logging-based notification channel"""
    
    def __init__(self):
        self.logger = get_logger('virtuai.notifications.console')
    
    async def send(self, notification: Notification) -> bool:
        try:
            emoji_map = {
                NotificationType.INFO: "ℹ️",
                NotificationType.SUCCESS: "✅",
                NotificationType.WARNING: "⚠️",
                NotificationType.ERROR: "❌",
                NotificationType.TASK_UPDATE: "📋",
                NotificationType.AGENT_STATUS: "🤖",
                NotificationType.SYSTEM_ALERT: "🚨",
                NotificationType.PERFORMANCE: "📊",
                NotificationType.APPLE_SILICON: "🍎"
            }
            
            emoji = emoji_map.get(notification.type, "📢")
            log_message = f"{emoji} {notification.title}: {notification.message}"
            
            if notification.priority >= NotificationPriority.URGENT:
                self.logger.critical(log_message)
            elif notification.priority >= NotificationPriority.HIGH:
                self.logger.error(log_message)
            elif notification.priority >= NotificationPriority.NORMAL:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to send console notification: {e}")
            return False
    
    def supports_priority(self, priority: NotificationPriority) -> bool:
        return True


class SlackNotificationChannel(NotificationChannel):
    """Slack webhook notification channel"""
    
    def __init__(self, webhook_url: str, min_priority: NotificationPriority = NotificationPriority.HIGH):
        self.webhook_url = webhook_url
        self.min_priority = min_priority
        self.logger = get_logger('virtuai.notifications.slack')
    
    async def send(self, notification: Notification) -> bool:
        if not self.supports_priority(notification.priority):
            return True  # Skip low priority notifications
        
        try:
            import aiohttp
            
            color_map = {
                NotificationType.SUCCESS: "good",
                NotificationType.WARNING: "warning",
                NotificationType.ERROR: "danger",
                NotificationType.SYSTEM_ALERT: "danger"
            }
            
            slack_message = {
                "text": f"VirtuAI Office Notification",
                "attachments": [{
                    "color": color_map.get(notification.type, "#36a64f"),
                    "title": notification.title,
                    "text": notification.message,
                    "footer": "VirtuAI Office",
                    "ts": int(notification.created_at.timestamp())
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=slack_message) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def supports_priority(self, priority: NotificationPriority) -> bool:
        return priority >= self.min_priority


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self,
                 smtp_server: str,
                 smtp_port: int,
                 username: str,
                 password: str,
                 recipients: List[str],
                 min_priority: NotificationPriority = NotificationPriority.HIGH):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = recipients
        self.min_priority = min_priority
        self.logger = get_logger('virtuai.notifications.email')
    
    async def send(self, notification: Notification) -> bool:
        if not self.supports_priority(notification.priority):
            return True
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = f"VirtuAI Office: {notification.title}"
            
            body = f"""
{notification.message}

Time: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Priority: {notification.priority.name}
Type: {notification.type.value}

---
VirtuAI Office Notification System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email in background thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email_sync, msg)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_email_sync(self, msg):
        """Send email synchronously"""
        import smtplib
        
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.username, self.password)
        text = msg.as_string()
        server.sendmail(self.username, self.recipients, text)
        server.quit()
    
    def supports_priority(self, priority: NotificationPriority) -> bool:
        return priority >= self.min_priority


class NotificationTemplate:
    """Template for creating notifications"""
    
    def __init__(self,
                 type: NotificationType,
                 title_template: str,
                 message_template: str,
                 priority: NotificationPriority = NotificationPriority.NORMAL,
                 expire_after_minutes: Optional[int] = None,
                 actions: List[Dict[str, Any]] = None,
                 tags: List[str] = None):
        self.type = type
        self.title_template = title_template
        self.message_template = message_template
        self.priority = priority
        self.expire_after_minutes = expire_after_minutes
        self.actions = actions or []
        self.tags = tags or []
    
    def create_notification(self, **kwargs) -> Notification:
        """Create notification from template with variable substitution"""
        title = self.title_template.format(**kwargs)
        message = self.message_template.format(**kwargs)
        
        expires_at = None
        if self.expire_after_minutes:
            expires_at = datetime.utcnow() + timedelta(minutes=self.expire_after_minutes)
        
        return Notification(
            type=self.type,
            title=title,
            message=message,
            priority=self.priority,
            expires_at=expires_at,
            actions=self.actions.copy(),
            tags=self.tags.copy(),
            data=kwargs
        )


class NotificationService:
    """Central notification service for VirtuAI Office"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.channels: List[NotificationChannel] = []
        self.templates: Dict[str, NotificationTemplate] = {}
        self.notification_history: List[Notification] = []
        self.max_history = 1000
        self.filters: List[Callable[[Notification], bool]] = []
        self.middleware: List[Callable[[Notification], Notification]] = []
        
        self.logger = get_logger('virtuai.notifications')
        
        # Add default channels
        self.add_channel(WebSocketNotificationChannel(websocket_manager))
        self.add_channel(ConsoleNotificationChannel())
        
        # Register default templates
        self._register_default_templates()
    
    def add_channel(self, channel: NotificationChannel):
        """Add a notification channel"""
        self.channels.append(channel)
        self.logger.info(f"Added notification channel: {channel.__class__.__name__}")
    
    def remove_channel(self, channel_type: type):
        """Remove notification channels of specified type"""
        initial_count = len(self.channels)
        self.channels = [ch for ch in self.channels if not isinstance(ch, channel_type)]
        removed_count = initial_count - len(self.channels)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} channels of type {channel_type.__name__}")
    
    def add_slack_channel(self, webhook_url: str, min_priority: NotificationPriority = NotificationPriority.HIGH):
        """Add Slack notification channel"""
        self.add_channel(SlackNotificationChannel(webhook_url, min_priority))
    
    def add_email_channel(self,
                         smtp_server: str,
                         smtp_port: int,
                         username: str,
                         password: str,
                         recipients: List[str],
                         min_priority: NotificationPriority = NotificationPriority.HIGH):
        """Add email notification channel"""
        self.add_channel(EmailNotificationChannel(
            smtp_server, smtp_port, username, password, recipients, min_priority
        ))
    
    def register_template(self, name: str, template: NotificationTemplate):
        """Register a notification template"""
        self.templates[name] = template
        self.logger.info(f"Registered notification template: {name}")
    
    def add_filter(self, filter_func: Callable[[Notification], bool]):
        """Add notification filter (return False to drop notification)"""
        self.filters.append(filter_func)
    
    def add_middleware(self, middleware_func: Callable[[Notification], Notification]):
        """Add notification middleware (can modify notification)"""
        self.middleware.append(middleware_func)
    
    async def send(self, notification: Notification) -> Dict[str, bool]:
        """Send notification through all appropriate channels"""
        # Apply filters
        for filter_func in self.filters:
            try:
                if not filter_func(notification):
                    self.logger.debug(f"Notification filtered out: {notification.id}")
                    return {}
            except Exception as e:
                self.logger.error(f"Error in notification filter: {e}")
        
        # Apply middleware
        for middleware_func in self.middleware:
            try:
                notification = middleware_func(notification)
            except Exception as e:
                self.logger.error(f"Error in notification middleware: {e}")
        
        # Add to history
        self._add_to_history(notification)
        
        # Send through channels
        results = {}
        for channel in self.channels:
            if channel.supports_priority(notification.priority):
                try:
                    success = await channel.send(notification)
                    results[channel.__class__.__name__] = success
                except Exception as e:
                    log_error_with_context(
                        'virtuai.notifications',
                        e,
                        {'channel': channel.__class__.__name__, 'notification_id': notification.id}
                    )
                    results[channel.__class__.__name__] = False
        
        self.logger.info(
            f"Sent notification {notification.id} ({notification.type.value}): "
            f"{notification.title} - Results: {results}"
        )
        
        return results
    
    async def send_from_template(self, template_name: str, **kwargs) -> Dict[str, bool]:
        """Send notification using a registered template"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        notification = template.create_notification(**kwargs)
        return await self.send(notification)
    
    async def send_simple(self,
                         type: NotificationType,
                         title: str,
                         message: str,
                         priority: NotificationPriority = NotificationPriority.NORMAL,
                         data: Dict[str, Any] = None,
                         actions: List[Dict[str, Any]] = None,
                         tags: List[str] = None) -> Dict[str, bool]:
        """Send a simple notification"""
        notification = Notification(
            type=type,
            title=title,
            message=message,
            priority=priority,
            data=data or {},
            actions=actions or [],
            tags=tags or []
        )
        return await self.send(notification)
    
    def get_history(self,
                   limit: int = 100,
                   type_filter: Optional[NotificationType] = None,
                   priority_filter: Optional[NotificationPriority] = None,
                   tag_filter: Optional[str] = None) -> List[Notification]:
        """Get notification history with optional filters"""
        filtered_notifications = self.notification_history
        
        if type_filter:
            filtered_notifications = [n for n in filtered_notifications if n.type == type_filter]
        
        if priority_filter:
            filtered_notifications = [n for n in filtered_notifications if n.priority >= priority_filter]
        
        if tag_filter:
            filtered_notifications = [n for n in filtered_notifications if tag_filter in n.tags]
        
        # Remove expired notifications
        filtered_notifications = [n for n in filtered_notifications if not n.is_expired()]
        
        return filtered_notifications[-limit:]
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        for notification in self.notification_history:
            if notification.id == notification_id:
                notification.read = True
                return True
        return False
    
    def clear_history(self, older_than_hours: Optional[int] = None):
        """Clear notification history"""
        if older_than_hours:
            cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
            initial_count = len(self.notification_history)
            self.notification_history = [
                n for n in self.notification_history
                if n.created_at > cutoff
            ]
            cleared_count = initial_count - len(self.notification_history)
            self.logger.info(f"Cleared {cleared_count} old notifications")
        else:
            cleared_count = len(self.notification_history)
            self.notification_history.clear()
            self.logger.info(f"Cleared all {cleared_count} notifications")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification service statistics"""
        type_counts = {}
        priority_counts = {}
        
        for notification in self.notification_history:
            type_counts[notification.type.value] = type_counts.get(notification.type.value, 0) + 1
            priority_counts[notification.priority.name] = priority_counts.get(notification.priority.name, 0) + 1
        
        return {
            'total_notifications': len(self.notification_history),
            'channels': len(self.channels),
            'templates': len(self.templates),
            'type_distribution': type_counts,
            'priority_distribution': priority_counts,
            'unread_count': len([n for n in self.notification_history if not n.read])
        }
    
    def _add_to_history(self, notification: Notification):
        """Add notification to history with size limit"""
        self.notification_history.append(notification)
        
        # Maintain history size limit
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]
    
    def _register_default_templates(self):
        """Register default notification templates"""
        templates = {
            'task_created': NotificationTemplate(
                type=NotificationType.TASK_UPDATE,
                title_template="Task Created",
                message_template="Task '{title}' has been created and assigned to {agent_name}",
                priority=NotificationPriority.NORMAL,
                tags=['task', 'creation']
            ),
            
            'task_completed': NotificationTemplate(
                type=NotificationType.SUCCESS,
                title_template="Task Completed",
                message_template="🎉 {agent_name} completed task '{title}'",
                priority=NotificationPriority.NORMAL,
                expire_after_minutes=60,
                tags=['task', 'completion'],
                actions=[
                    {'type': 'view', 'label': 'View Output', 'url': '/tasks/{task_id}'}
                ]
            ),
            
            'task_failed': NotificationTemplate(
                type=NotificationType.ERROR,
                title_template="Task Failed",
                message_template="❌ Task '{title}' failed: {error_message}",
                priority=NotificationPriority.HIGH,
                tags=['task', 'error'],
                actions=[
                    {'type': 'retry', 'label': 'Retry Task', 'action': 'retry_task'},
                    {'type': 'view', 'label': 'View Details', 'url': '/tasks/{task_id}'}
                ]
            ),
            
            'agent_busy': NotificationTemplate(
                type=NotificationType.WARNING,
                title_template="Agent Busy",
                message_template="⏳ {agent_name} is currently busy. Task has been queued.",
                priority=NotificationPriority.LOW,
                expire_after_minutes=30,
                tags=['agent', 'workload']
            ),
            
            'system_optimized': NotificationTemplate(
                type=NotificationType.APPLE_SILICON,
                title_template="System Optimized",
                message_template="🍎 Apple Silicon optimizations applied successfully!",
                priority=NotificationPriority.NORMAL,
                expire_after_minutes=30,
                tags=['apple_silicon', 'optimization']
            ),
            
            'performance_warning': NotificationTemplate(
                type=NotificationType.WARNING,
                title_template="Performance Warning",
                message_template="⚠️ {metric_name}: {message}",
                priority=NotificationPriority.HIGH,
                expire_after_minutes=15,
                tags=['performance', 'warning']
            ),
            
            'model_download_complete': NotificationTemplate(
                type=NotificationType.SUCCESS,
                title_template="Model Download Complete",
                message_template="✅ AI model '{model_name}' is now ready for use!",
                priority=NotificationPriority.NORMAL,
                expire_after_minutes=60,
                tags=['model', 'download']
            ),
            
            'connection_lost': NotificationTemplate(
                type=NotificationType.ERROR,
                title_template="Connection Lost",
                message_template="🔌 Connection to VirtuAI Office lost. Attempting to reconnect...",
                priority=NotificationPriority.URGENT,
                tags=['connection', 'error']
            ),
            
            'connection_restored': NotificationTemplate(
                type=NotificationType.SUCCESS,
                title_template="Connection Restored",
                message_template="🔌 Connection to VirtuAI Office restored!",
                priority=NotificationPriority.NORMAL,
                expire_after_minutes=10,
                tags=['connection', 'recovery']
            )
        }
        
        for name, template in templates.items():
            self.register_template(name, template)


# Convenience functions for common notifications

async def notify_task_created(service: NotificationService, task_title: str, agent_name: str, task_id: str):
    """Send task creation notification"""
    await service.send_from_template(
        'task_created',
        title=task_title,
        agent_name=agent_name,
        task_id=task_id
    )


async def notify_task_completed(service: NotificationService, task_title: str, agent_name: str, task_id: str):
    """Send task completion notification"""
    await service.send_from_template(
        'task_completed',
        title=task_title,
        agent_name=agent_name,
        task_id=task_id
    )


async def notify_task_failed(service: NotificationService, task_title: str, error_message: str, task_id: str):
    """Send task failure notification"""
    await service.send_from_template(
        'task_failed',
        title=task_title,
        error_message=error_message,
        task_id=task_id
    )


async def notify_performance_warning(service: NotificationService, metric_name: str, message: str):
    """Send performance warning notification"""
    await service.send_from_template(
        'performance_warning',
        metric_name=metric_name,
        message=message
    )


async def notify_system_optimized(service: NotificationService):
    """Send system optimization notification"""
    await service.send_from_template('system_optimized')


async def notify_model_downloaded(service: NotificationService, model_name: str):
    """Send model download completion notification"""
    await service.send_from_template(
        'model_download_complete',
        model_name=model_name
    )


async def notify_connection_status(service: NotificationService, connected: bool):
    """Send connection status notification"""
    if connected:
        await service.send_from_template('connection_restored')
    else:
        await service.send_from_template('connection_lost')
