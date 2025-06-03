# VirtuAI Office - Orchestration Module
"""
AI Orchestration & Collaboration System

This module provides intelligent task assignment, multi-agent collaboration,
and Boss AI orchestration for the VirtuAI Office system.

Components:
- BossAI: Central orchestration and decision-making system
- SmartTaskAssignment: Intelligent task routing and agent selection
- AgentCollaborationManager: Multi-agent workflow coordination
- PerformanceAnalytics: Continuous improvement and optimization
"""

from .boss_ai import (
    BossAI,
    TaskAnalysis,
    CollaborationPlan,
    TaskComplexity,
    TaskType,
    CollaborationType
)

from .task_assignment import (
    SmartTaskAssignment,
    AgentCapability,
    AssignmentResult,
    AssignmentStrategy
)

from .collaboration import (
    AgentCollaborationManager,
    CollaborationWorkflow,
    WorkflowStep,
    CollaborationStatus
)

from .performance import (
    PerformanceAnalytics,
    AgentPerformanceMetrics,
    SystemHealthMetrics,
    OptimizationRecommendation
)

from .workload_balancer import (
    WorkloadBalancer,
    AgentWorkload,
    LoadBalancingStrategy,
    WorkloadMetrics
)

from .decision_engine import (
    DecisionEngine,
    Decision,
    DecisionContext,
    DecisionOutcome
)

# Version information
__version__ = "1.0.0"
__author__ = "VirtuAI Office Team"

# Module configuration
DEFAULT_CONFIG = {
    "max_concurrent_agents": 8,
    "task_timeout_minutes": 30,
    "collaboration_threshold": 0.7,
    "performance_tracking_enabled": True,
    "auto_optimization_enabled": True,
    "workload_balancing_interval": 300,  # 5 minutes
    "decision_logging_enabled": True
}

# Export main orchestration classes
__all__ = [
    # Core orchestration
    "BossAI",
    "SmartTaskAssignment",
    "AgentCollaborationManager",
    "PerformanceAnalytics",
    "WorkloadBalancer",
    "DecisionEngine",
    
    # Data models
    "TaskAnalysis",
    "CollaborationPlan",
    "AgentCapability",
    "AssignmentResult",
    "CollaborationWorkflow",
    "WorkflowStep",
    "AgentPerformanceMetrics",
    "SystemHealthMetrics",
    "OptimizationRecommendation",
    "AgentWorkload",
    "WorkloadMetrics",
    "Decision",
    "DecisionContext",
    "DecisionOutcome",
    
    # Enums
    "TaskComplexity",
    "TaskType",
    "CollaborationType",
    "AssignmentStrategy",
    "CollaborationStatus",
    "LoadBalancingStrategy",
    
    # Configuration
    "DEFAULT_CONFIG",
    
    # Utilities
    "create_orchestration_system",
    "initialize_boss_ai",
    "setup_collaboration_workflows"
]

# Factory functions for easy initialization
def create_orchestration_system(agent_manager, config=None):
    """
    Create a complete orchestration system with all components
    
    Args:
        agent_manager: The agent manager instance
        config: Optional configuration overrides
        
    Returns:
        dict: Dictionary containing all orchestration components
    """
    from ..core.logging import get_logger
    
    logger = get_logger('virtuai.orchestration')
    
    # Merge with default config
    final_config = {**DEFAULT_CONFIG, **(config or {})}
    
    logger.info("🧠 Initializing AI orchestration system...")
    
    # Initialize core components
    boss_ai = BossAI(agent_manager, config=final_config)
    task_assignment = SmartTaskAssignment(boss_ai, agent_manager, config=final_config)
    collaboration_manager = AgentCollaborationManager(agent_manager, config=final_config)
    performance_analytics = PerformanceAnalytics(config=final_config)
    workload_balancer = WorkloadBalancer(agent_manager, config=final_config)
    decision_engine = DecisionEngine(boss_ai, config=final_config)
    
    orchestration_system = {
        'boss_ai': boss_ai,
        'task_assignment': task_assignment,
        'collaboration_manager': collaboration_manager,
        'performance_analytics': performance_analytics,
        'workload_balancer': workload_balancer,
        'decision_engine': decision_engine,
        'config': final_config
    }
    
    logger.info("✅ Orchestration system initialized successfully")
    logger.info(f"   • Max concurrent agents: {final_config['max_concurrent_agents']}")
    logger.info(f"   • Task timeout: {final_config['task_timeout_minutes']} minutes")
    logger.info(f"   • Collaboration threshold: {final_config['collaboration_threshold']}")
    logger.info(f"   • Performance tracking: {final_config['performance_tracking_enabled']}")
    logger.info(f"   • Auto optimization: {final_config['auto_optimization_enabled']}")
    
    return orchestration_system


def initialize_boss_ai(agent_manager, model="llama2:7b", config=None):
    """
    Initialize Boss AI with sensible defaults
    
    Args:
        agent_manager: The agent manager instance
        model: LLM model to use for Boss AI decisions
        config: Optional configuration overrides
        
    Returns:
        BossAI: Configured Boss AI instance
    """
    final_config = {**DEFAULT_CONFIG, **(config or {})}
    boss_ai = BossAI(agent_manager, model=model, config=final_config)
    
    return boss_ai


def setup_collaboration_workflows(collaboration_manager, predefined_workflows=None):
    """
    Setup predefined collaboration workflows
    
    Args:
        collaboration_manager: The collaboration manager instance
        predefined_workflows: Optional list of workflow definitions
        
    Returns:
        dict: Dictionary of registered workflows
    """
    workflows = predefined_workflows or [
        {
            'name': 'feature_development',
            'description': 'Full-stack feature development workflow',
            'steps': [
                {'agent_type': 'product_manager', 'task': 'Create user stories and requirements'},
                {'agent_type': 'ui_ux_designer', 'task': 'Design user interface and experience'},
                {'agent_type': 'frontend_developer', 'task': 'Implement frontend components'},
                {'agent_type': 'backend_developer', 'task': 'Build backend APIs and logic'},
                {'agent_type': 'qa_tester', 'task': 'Create comprehensive test plan'}
            ]
        },
        {
            'name': 'bug_fix',
            'description': 'Bug investigation and resolution workflow',
            'steps': [
                {'agent_type': 'qa_tester', 'task': 'Reproduce and analyze the bug'},
                {'agent_type': 'backend_developer', 'task': 'Investigate root cause and fix'},
                {'agent_type': 'qa_tester', 'task': 'Verify fix and create regression tests'}
            ]
        },
        {
            'name': 'code_review',
            'description': 'Comprehensive code review workflow',
            'steps': [
                {'agent_type': 'backend_developer', 'task': 'Review code architecture and logic'},
                {'agent_type': 'frontend_developer', 'task': 'Review UI implementation'},
                {'agent_type': 'qa_tester', 'task': 'Review testability and edge cases'}
            ]
        },
        {
            'name': 'documentation',
            'description': 'Technical documentation creation workflow',
            'steps': [
                {'agent_type': 'product_manager', 'task': 'Define documentation requirements'},
                {'agent_type': 'backend_developer', 'task': 'Document APIs and architecture'},
                {'agent_type': 'frontend_developer', 'task': 'Document UI components and usage'},
                {'agent_type': 'qa_tester', 'task': 'Document testing procedures'}
            ]
        }
    ]
    
    registered_workflows = {}
    for workflow in workflows:
        registered_workflows[workflow['name']] = collaboration_manager.register_workflow(
            name=workflow['name'],
            description=workflow['description'],
            steps=workflow['steps']
        )
    
    return registered_workflows


# Orchestration system health check
def check_orchestration_health(orchestration_system):
    """
    Check the health of the orchestration system
    
    Args:
        orchestration_system: The orchestration system dictionary
        
    Returns:
        dict: Health status report
    """
    health_report = {
        'overall_status': 'healthy',
        'components': {},
        'warnings': [],
        'errors': []
    }
    
    try:
        # Check each component
        for component_name, component in orchestration_system.items():
            if component_name == 'config':
                continue
                
            try:
                if hasattr(component, 'health_check'):
                    component_health = component.health_check()
                    health_report['components'][component_name] = component_health
                else:
                    health_report['components'][component_name] = {'status': 'unknown'}
            except Exception as e:
                health_report['components'][component_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_report['errors'].append(f"{component_name}: {str(e)}")
        
        # Determine overall status
        if health_report['errors']:
            health_report['overall_status'] = 'degraded'
        elif any(comp.get('status') == 'warning' for comp in health_report['components'].values()):
            health_report['overall_status'] = 'warning'
            
    except Exception as e:
        health_report['overall_status'] = 'error'
        health_report['errors'].append(f"Health check failed: {str(e)}")
    
    return health_report


# Module initialization logging
def _log_module_info():
    """Log module initialization information"""
    from ..core.logging import get_logger
    
    logger = get_logger('virtuai.orchestration')
    logger.info(f"🧠 Orchestration module loaded (v{__version__})")
    logger.info("   Available components:")
    logger.info("   • BossAI - Central decision making")
    logger.info("   • SmartTaskAssignment - Intelligent routing")
    logger.info("   • AgentCollaboration - Multi-agent workflows")
    logger.info("   • PerformanceAnalytics - Continuous optimization")
    logger.info("   • WorkloadBalancer - Resource management")
    logger.info("   • DecisionEngine - Decision tracking and learning")


# Initialize module logging when imported
_log_module_info()
