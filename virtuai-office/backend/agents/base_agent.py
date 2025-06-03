import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

import ollama
from ..models.database import Task, AgentType

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, name: str, agent_type: AgentType, description: str, expertise: List[str]):
        self.name = name
        self.type = agent_type
        self.description = description
        self.expertise = expertise
        self.model = "llama2:7b"  # Default model
        self.created_at = datetime.utcnow()
        self.task_count = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def process_task(self, task: Task) -> str:
        """Process a task and return the generated output. Must be implemented by subclasses."""
        pass
    
    def can_handle_task(self, task_description: str) -> float:
        """
        Calculate confidence score (0.0-1.0) for handling this task.
        Default implementation uses keyword matching against expertise.
        Subclasses can override for more sophisticated matching.
        """
        if not task_description or not self.expertise:
            return 0.0
        
        description_lower = task_description.lower()
        expertise_lower = [skill.lower() for skill in self.expertise]
        
        # Count matches
        matches = sum(1 for skill in expertise_lower if skill in description_lower)
        
        # Calculate confidence based on match ratio
        if len(expertise_lower) == 0:
            return 0.0
        
        confidence = min(matches / len(expertise_lower), 1.0)
        
        # Apply minimum confidence threshold
        return max(confidence, 0.1) if matches > 0 else 0.0
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with the prompt"""
        try:
            logger.debug(f"{self.name} calling Ollama with model {self.model}")
            
            response = await asyncio.to_thread(
                ollama.generate,
                model=self.model,
                prompt=prompt,
                stream=False,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 4000,
                    'stop': ['<end>', '</end>']
                }
            )
            
            generated_text = response.get('response', '').strip()
            
            if not generated_text:
                raise ValueError("Empty response from Ollama")
            
            logger.debug(f"{self.name} generated {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"Ollama API error for {self.name}: {e}")
            raise Exception(f"AI model error: {str(e)}")
    
    def _build_task_prompt(self, task: Task) -> str:
        """Build the complete prompt for the AI model"""
        system_prompt = self.get_system_prompt()
        
        prompt = f"""{system_prompt}

TASK DETAILS:
Title: {task.title}
Description: {task.description}
Priority: {task.priority.value.upper()}
Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}

INSTRUCTIONS:
Please provide a detailed, professional response that addresses this task according to your expertise.
Format your response with clear structure, proper headings, and actionable content.
Include specific examples, code snippets, or implementation details where appropriate.
Ensure your output is production-ready and follows best practices in your domain.

RESPONSE:"""
        
        return prompt
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive information about this agent"""
        return {
            'id': f"{self.type.value}_{id(self)}",
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'expertise': self.expertise,
            'model': self.model,
            'created_at': self.created_at.isoformat(),
            'stats': {
                'total_tasks': self.task_count,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'success_rate': self.completed_tasks / self.task_count if self.task_count > 0 else 0.0
            }
        }
    
    def update_stats(self, success: bool):
        """Update agent statistics after task completion"""
        self.task_count += 1
        if success:
            self.completed_tasks += 1
        else:
            self.failed_tasks += 1
    
    def set_model(self, model_name: str):
        """Set the AI model for this agent"""
        self.model = model_name
        logger.info(f"{self.name} model updated to {model_name}")
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for this agent"""
        if self.task_count == 0:
            return {
                'success_rate': 0.0,
                'failure_rate': 0.0,
                'total_tasks': 0
            }
        
        return {
            'success_rate': self.completed_tasks / self.task_count,
            'failure_rate': self.failed_tasks / self.task_count,
            'total_tasks': self.task_count
        }
    
    async def validate_response(self, response: str) -> bool:
        """
        Validate the generated response.
        Subclasses can override for domain-specific validation.
        """
        if not response or len(response.strip()) < 10:
            return False
        
        # Check for common error indicators
        error_indicators = [
            'error occurred',
            'unable to process',
            'failed to generate',
            'please try again'
        ]
        
        response_lower = response.lower()
        if any(indicator in response_lower for indicator in error_indicators):
            return False
        
        return True
    
    async def post_process_response(self, response: str, task: Task) -> str:
        """
        Post-process the response before returning.
        Subclasses can override for custom post-processing.
        """
        # Add agent signature
        signature = f"\n\n---\n**Generated by {self.name}**\n*{self.description}*"
        return response + signature
    
    def __str__(self) -> str:
        return f"{self.name} ({self.type.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', type='{self.type.value}')>"
