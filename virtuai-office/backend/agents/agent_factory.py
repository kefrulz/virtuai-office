from typing import Dict, Type
from .base_agent import BaseAgent
from .product_manager import AliceChenAgent
from .frontend_dev import MarcusDevAgent
from .backend_dev import SarahBackendAgent
from .ui_designer import LunaDesignAgent
from .qa_tester import TestBotQAAgent

class AgentFactory:
    """Factory class for creating AI agents"""
    
    _agent_registry: Dict[str, Type[BaseAgent]] = {
        'product_manager': AliceChenAgent,
        'frontend_developer': MarcusDevAgent,
        'backend_developer': SarahBackendAgent,
        'ui_ux_designer': LunaDesignAgent,
        'qa_tester': TestBotQAAgent
    }
    
    @classmethod
    def create_agent(cls, agent_type: str) -> BaseAgent:
        """Create an agent instance by type"""
        if agent_type not in cls._agent_registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = cls._agent_registry[agent_type]
        return agent_class()
    
    @classmethod
    def get_available_agents(cls) -> Dict[str, Type[BaseAgent]]:
        """Get all available agent types"""
        return cls._agent_registry.copy()
    
    @classmethod
    def register_agent(cls, agent_type: str, agent_class: Type[BaseAgent]):
        """Register a new agent type"""
        cls._agent_registry[agent_type] = agent_class
    
    @classmethod
    def get_agent_info(cls, agent_type: str) -> Dict[str, str]:
        """Get basic info about an agent type"""
        if agent_type not in cls._agent_registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent = cls.create_agent(agent_type)
        return {
            'name': agent.name,
            'type': agent.type.value,
            'description': agent.description,
            'expertise': agent.expertise
        }
    
    @classmethod
    def create_all_agents(cls) -> Dict[str, BaseAgent]:
        """Create instances of all available agents"""
        return {
            agent_type: cls.create_agent(agent_type)
            for agent_type in cls._agent_registry.keys()
        }
