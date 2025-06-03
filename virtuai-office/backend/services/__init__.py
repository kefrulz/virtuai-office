# VirtuAI Office - Services Package
"""
Service layer for VirtuAI Office backend

This package contains all the business logic services that orchestrate
the AI agents, task processing, and system optimization.
"""

from .task_service import TaskService
from .agent_service import AgentService
from .boss_ai_service import BossAIService
from .collaboration_service import CollaborationService
from .apple_silicon_service import AppleSiliconService
from .notification_service import NotificationService
from .performance_service import PerformanceService
from .project_service import ProjectService

__all__ = [
    # Core Services
    'TaskService',
    'AgentService',
    'BossAIService',
    'CollaborationService',
    
    # Platform Services
    'AppleSiliconService',
    'NotificationService',
    'PerformanceService',
    'ProjectService',
]

# Service version information
__version__ = "1.0.0"
__author__ = "VirtuAI Office Team"

# Service registry for dependency injection
_service_registry = {}

def register_service(name: str, service_instance):
    """Register a service instance in the global registry"""
    _service_registry[name] = service_instance

def get_service(name: str):
    """Get a service instance from the registry"""
    return _service_registry.get(name)

def initialize_services(**kwargs):
    """Initialize all services with configuration"""
    from backend.core.database import get_database
    from backend.core.logging import get_logger
    
    logger = get_logger('virtuai.services')
    db = get_database()
    
    # Initialize services in dependency order
    services = [
        ('performance', PerformanceService),
        ('notification', NotificationService),
        ('apple_silicon', AppleSiliconService),
        ('agent', AgentService),
        ('task', TaskService),
        ('collaboration', CollaborationService),
        ('boss_ai', BossAIService),
        ('project', ProjectService),
    ]
    
    initialized_services = {}
    
    for service_name, service_class in services:
        try:
            logger.info(f"Initializing {service_name} service...")
            
            # Pass database and other services as dependencies
            service_kwargs = {
                'db': db,
                'logger': get_logger(f'virtuai.services.{service_name}'),
                **kwargs
            }
            
            # Add already initialized services as dependencies
            for dep_name, dep_service in initialized_services.items():
                service_kwargs[f'{dep_name}_service'] = dep_service
            
            service_instance = service_class(**service_kwargs)
            
            # Register service
            register_service(service_name, service_instance)
            initialized_services[service_name] = service_instance
            
            logger.info(f"✅ {service_name} service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize {service_name} service: {e}")
            raise
    
    logger.info(f"🎉 All {len(services)} services initialized successfully")
    return initialized_services

async def shutdown_services():
    """Gracefully shutdown all services"""
    from backend.core.logging import get_logger
    
    logger = get_logger('virtuai.services')
    logger.info("Shutting down services...")
    
    for service_name, service_instance in _service_registry.items():
        try:
            if hasattr(service_instance, 'shutdown'):
                await service_instance.shutdown()
                logger.info(f"✅ {service_name} service shutdown complete")
        except Exception as e:
            logger.error(f"❌ Error shutting down {service_name} service: {e}")
    
    _service_registry.clear()
    logger.info("🛑 All services shutdown complete")

# Health check for all services
async def health_check():
    """Check health status of all services"""
    health_status = {
        'status': 'healthy',
        'services': {},
        'timestamp': None
    }
    
    from datetime import datetime
    health_status['timestamp'] = datetime.utcnow().isoformat()
    
    overall_healthy = True
    
    for service_name, service_instance in _service_registry.items():
        try:
            if hasattr(service_instance, 'health_check'):
                service_health = await service_instance.health_check()
            else:
                service_health = {'status': 'healthy', 'message': 'No health check implemented'}
            
            health_status['services'][service_name] = service_health
            
            if service_health.get('status') != 'healthy':
                overall_healthy = False
                
        except Exception as e:
            health_status['services'][service_name] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
    
    health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'
    return health_status
