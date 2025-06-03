# VirtuAI Office - Input Validation Utilities
import re
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
import bleach
from pydantic import BaseModel, validator, ValidationError
from email_validator import validate_email, EmailNotValidError

from ..models.database import TaskStatus, TaskPriority, AgentType


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    STRICT = "strict"


class TaskValidator:
    """Validator for task-related inputs"""
    
    @staticmethod
    def validate_title(title: str, max_length: int = 200) -> str:
        """Validate task title"""
        if not title or not title.strip():
            raise ValidationError("Task title is required", "title", "REQUIRED")
        
        title = title.strip()
        
        if len(title) < 3:
            raise ValidationError("Task title must be at least 3 characters", "title", "MIN_LENGTH")
        
        if len(title) > max_length:
            raise ValidationError(f"Task title must be less than {max_length} characters", "title", "MAX_LENGTH")
        
        # Check for malicious content
        if SecurityValidator.contains_malicious_content(title):
            raise ValidationError("Task title contains prohibited content", "title", "MALICIOUS_CONTENT")
        
        return title
    
    @staticmethod
    def validate_description(description: str, min_length: int = 10, max_length: int = 10000) -> str:
        """Validate task description"""
        if not description or not description.strip():
            raise ValidationError("Task description is required", "description", "REQUIRED")
        
        description = description.strip()
        
        if len(description) < min_length:
            raise ValidationError(f"Task description must be at least {min_length} characters", "description", "MIN_LENGTH")
        
        if len(description) > max_length:
            raise ValidationError(f"Task description must be less than {max_length} characters", "description", "MAX_LENGTH")
        
        # Sanitize HTML content
        description = SecurityValidator.sanitize_html(description)
        
        # Check for reasonable content
        if not TaskValidator._has_meaningful_content(description):
            raise ValidationError("Task description must contain meaningful content", "description", "INVALID_CONTENT")
        
        return description
    
    @staticmethod
    def validate_priority(priority: Union[str, TaskPriority]) -> TaskPriority:
        """Validate task priority"""
        if isinstance(priority, str):
            try:
                return TaskPriority(priority.lower())
            except ValueError:
                valid_priorities = [p.value for p in TaskPriority]
                raise ValidationError(
                    f"Invalid priority. Must be one of: {', '.join(valid_priorities)}",
                    "priority",
                    "INVALID_ENUM"
                )
        
        if isinstance(priority, TaskPriority):
            return priority
        
        raise ValidationError("Priority must be a string or TaskPriority enum", "priority", "INVALID_TYPE")
    
    @staticmethod
    def validate_agent_assignment(agent_id: Optional[str], available_agents: List[str] = None) -> Optional[str]:
        """Validate agent assignment"""
        if agent_id is None:
            return None
        
        if not UUIDValidator.is_valid_uuid(agent_id):
            raise ValidationError("Invalid agent ID format", "agent_id", "INVALID_UUID")
        
        if available_agents and agent_id not in available_agents:
            raise ValidationError("Agent not found or not available", "agent_id", "AGENT_NOT_FOUND")
        
        return agent_id
    
    @staticmethod
    def validate_effort_estimate(effort: Optional[int]) -> Optional[int]:
        """Validate effort estimate"""
        if effort is None:
            return None
        
        if not isinstance(effort, int):
            raise ValidationError("Effort must be an integer", "effort", "INVALID_TYPE")
        
        if effort < 1:
            raise ValidationError("Effort must be at least 1 hour", "effort", "MIN_VALUE")
        
        if effort > 1000:
            raise ValidationError("Effort cannot exceed 1000 hours", "effort", "MAX_VALUE")
        
        return effort
    
    @staticmethod
    def _has_meaningful_content(text: str) -> bool:
        """Check if text has meaningful content"""
        # Remove common filler words and check remaining content
        words = text.lower().split()
        meaningful_words = [w for w in words if len(w) > 2 and w not in [
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'
        ]]
        
        return len(meaningful_words) >= 3


class AgentValidator:
    """Validator for agent-related inputs"""
    
    @staticmethod
    def validate_agent_type(agent_type: Union[str, AgentType]) -> AgentType:
        """Validate agent type"""
        if isinstance(agent_type, str):
            try:
                return AgentType(agent_type.lower())
            except ValueError:
                valid_types = [t.value for t in AgentType]
                raise ValidationError(
                    f"Invalid agent type. Must be one of: {', '.join(valid_types)}",
                    "agent_type",
                    "INVALID_ENUM"
                )
        
        if isinstance(agent_type, AgentType):
            return agent_type
        
        raise ValidationError("Agent type must be a string or AgentType enum", "agent_type", "INVALID_TYPE")
    
    @staticmethod
    def validate_agent_name(name: str) -> str:
        """Validate agent name"""
        if not name or not name.strip():
            raise ValidationError("Agent name is required", "name", "REQUIRED")
        
        name = name.strip()
        
        if len(name) < 2:
            raise ValidationError("Agent name must be at least 2 characters", "name", "MIN_LENGTH")
        
        if len(name) > 100:
            raise ValidationError("Agent name must be less than 100 characters", "name", "MAX_LENGTH")
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValidationError("Agent name can only contain letters, spaces, hyphens, and apostrophes", "name", "INVALID_CHARACTERS")
        
        return name
    
    @staticmethod
    def validate_expertise(expertise: Union[str, List[str]]) -> List[str]:
        """Validate agent expertise"""
        if isinstance(expertise, str):
            # Try to parse as JSON array
            try:
                expertise = json.loads(expertise)
            except json.JSONDecodeError:
                # Treat as comma-separated string
                expertise = [e.strip() for e in expertise.split(',') if e.strip()]
        
        if not isinstance(expertise, list):
            raise ValidationError("Expertise must be a list or comma-separated string", "expertise", "INVALID_TYPE")
        
        if not expertise:
            raise ValidationError("At least one expertise area is required", "expertise", "REQUIRED")
        
        validated_expertise = []
        for skill in expertise:
            if not isinstance(skill, str):
                raise ValidationError("Each expertise item must be a string", "expertise", "INVALID_TYPE")
            
            skill = skill.strip().lower()
            if len(skill) < 2:
                continue  # Skip very short skills
            
            if len(skill) > 50:
                raise ValidationError("Each expertise item must be less than 50 characters", "expertise", "MAX_LENGTH")
            
            # Check for reasonable skill names
            if re.match(r'^[a-zA-Z0-9\s\-+#.]+$', skill):
                validated_expertise.append(skill)
        
        if not validated_expertise:
            raise ValidationError("No valid expertise areas found", "expertise", "INVALID_CONTENT")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_expertise = []
        for skill in validated_expertise:
            if skill not in seen:
                seen.add(skill)
                unique_expertise.append(skill)
        
        return unique_expertise[:10]  # Limit to 10 skills


class ProjectValidator:
    """Validator for project-related inputs"""
    
    @staticmethod
    def validate_project_name(name: str) -> str:
        """Validate project name"""
        if not name or not name.strip():
            raise ValidationError("Project name is required", "name", "REQUIRED")
        
        name = name.strip()
        
        if len(name) < 2:
            raise ValidationError("Project name must be at least 2 characters", "name", "MIN_LENGTH")
        
        if len(name) > 100:
            raise ValidationError("Project name must be less than 100 characters", "name", "MAX_LENGTH")
        
        # Check for malicious content
        if SecurityValidator.contains_malicious_content(name):
            raise ValidationError("Project name contains prohibited content", "name", "MALICIOUS_CONTENT")
        
        return name
    
    @staticmethod
    def validate_project_description(description: str) -> str:
        """Validate project description"""
        if not description:
            return ""
        
        description = description.strip()
        
        if len(description) > 2000:
            raise ValidationError("Project description must be less than 2000 characters", "description", "MAX_LENGTH")
        
        # Sanitize HTML content
        description = SecurityValidator.sanitize_html(description)
        
        return description


class SecurityValidator:
    """Security-focused validators"""
    
    # Common malicious patterns
    MALICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'vbscript:',   # VBScript protocol
        r'on\w+\s*=',   # Event handlers
        r'<iframe[^>]*>',  # Iframes
        r'<embed[^>]*>',   # Embeds
        r'<object[^>]*>',  # Objects
        r'eval\s*\(',      # eval() calls
        r'exec\s*\(',      # exec() calls
        r'import\s+os',    # OS imports
        r'__import__',     # Dynamic imports
        r'subprocess',     # Subprocess calls
        r'system\s*\(',    # System calls
    ]
    
    @staticmethod
    def sanitize_html(content: str, level: SecurityLevel = SecurityLevel.MEDIUM) -> str:
        """Sanitize HTML content"""
        if level == SecurityLevel.STRICT:
            # Strip all HTML
            return bleach.clean(content, tags=[], strip=True)
        elif level == SecurityLevel.HIGH:
            # Allow only very basic formatting
            allowed_tags = ['p', 'br', 'strong', 'em', 'u']
            allowed_attributes = {}
        elif level == SecurityLevel.MEDIUM:
            # Allow basic formatting and lists
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'code', 'pre']
            allowed_attributes = {}
        else:  # LOW
            # Allow most safe tags
            allowed_tags = bleach.ALLOWED_TAGS + ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'code', 'span', 'div']
            allowed_attributes = bleach.ALLOWED_ATTRIBUTES
        
        return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)
    
    @staticmethod
    def contains_malicious_content(content: str) -> bool:
        """Check if content contains malicious patterns"""
        content_lower = content.lower()
        
        for pattern in SecurityValidator.MALICIOUS_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE | re.DOTALL):
                return True
        
        return False
    
    @staticmethod
    def validate_file_upload(file_content: bytes, allowed_extensions: List[str], max_size: int = 10 * 1024 * 1024) -> bool:
        """Validate file upload"""
        if len(file_content) > max_size:
            raise ValidationError(f"File size exceeds maximum of {max_size} bytes", "file", "FILE_TOO_LARGE")
        
        # Check for malicious file signatures
        malicious_signatures = [
            b'\x4d\x5a',  # PE executable
            b'\x7f\x45\x4c\x46',  # ELF executable
            b'\xca\xfe\xba\xbe',  # Java class file
            b'\xfe\xed\xfa\xce',  # Mach-O executable
        ]
        
        for signature in malicious_signatures:
            if file_content.startswith(signature):
                raise ValidationError("File type not allowed", "file", "MALICIOUS_FILE")
        
        return True
    
    @staticmethod
    def validate_sql_injection(query_params: Dict[str, Any]) -> bool:
        """Check for SQL injection patterns"""
        sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+.*set',
            r'exec\s*\(',
            r'sp_executesql',
            r'xp_cmdshell',
            r'--\s*$',
            r'/\*.*\*/',
        ]
        
        for key, value in query_params.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for pattern in sql_patterns:
                    if re.search(pattern, value_lower):
                        raise ValidationError(f"Potentially malicious content in {key}", key, "SQL_INJECTION")
        
        return True


class UUIDValidator:
    """UUID validation utilities"""
    
    @staticmethod
    def is_valid_uuid(uuid_string: str, version: int = 4) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid_obj = uuid.UUID(uuid_string, version=version)
            return str(uuid_obj) == uuid_string
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_uuid(uuid_string: str, field_name: str = "id") -> str:
        """Validate UUID and raise error if invalid"""
        if not uuid_string:
            raise ValidationError(f"{field_name} is required", field_name, "REQUIRED")
        
        if not UUIDValidator.is_valid_uuid(uuid_string):
            raise ValidationError(f"Invalid {field_name} format", field_name, "INVALID_UUID")
        
        return uuid_string


class DateTimeValidator:
    """DateTime validation utilities"""
    
    @staticmethod
    def validate_datetime(dt_string: str, field_name: str = "datetime") -> datetime:
        """Validate datetime string"""
        if not dt_string:
            raise ValidationError(f"{field_name} is required", field_name, "REQUIRED")
        
        # Try different datetime formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with microseconds
            '%Y-%m-%dT%H:%M:%SZ',     # ISO format
            '%Y-%m-%dT%H:%M:%S',      # ISO format without Z
            '%Y-%m-%d %H:%M:%S',      # Standard format
            '%Y-%m-%d',               # Date only
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_string, fmt)
            except ValueError:
                continue
        
        raise ValidationError(f"Invalid {field_name} format", field_name, "INVALID_DATETIME")
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime,
                          max_range_days: int = 365) -> bool:
        """Validate date range"""
        if start_date >= end_date:
            raise ValidationError("Start date must be before end date", "date_range", "INVALID_RANGE")
        
        if (end_date - start_date).days > max_range_days:
            raise ValidationError(f"Date range cannot exceed {max_range_days} days", "date_range", "RANGE_TOO_LARGE")
        
        return True


class EmailValidator:
    """Email validation utilities"""
    
    @staticmethod
    def validate_email_address(email: str) -> str:
        """Validate email address"""
        if not email:
            raise ValidationError("Email is required", "email", "REQUIRED")
        
        try:
            # Validate and get normalized result
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email address: {str(e)}", "email", "INVALID_EMAIL")


class PaginationValidator:
    """Pagination parameter validators"""
    
    @staticmethod
    def validate_limit(limit: int, max_limit: int = 100) -> int:
        """Validate pagination limit"""
        if limit < 1:
            raise ValidationError("Limit must be at least 1", "limit", "MIN_VALUE")
        
        if limit > max_limit:
            raise ValidationError(f"Limit cannot exceed {max_limit}", "limit", "MAX_VALUE")
        
        return limit
    
    @staticmethod
    def validate_offset(offset: int) -> int:
        """Validate pagination offset"""
        if offset < 0:
            raise ValidationError("Offset must be non-negative", "offset", "MIN_VALUE")
        
        return offset


class PerformanceValidator:
    """Performance and resource validators"""
    
    @staticmethod
    def validate_memory_usage(memory_gb: float) -> float:
        """Validate memory usage value"""
        if memory_gb < 0:
            raise ValidationError("Memory usage cannot be negative", "memory", "MIN_VALUE")
        
        if memory_gb > 1024:  # 1TB should be more than enough
            raise ValidationError("Memory usage value seems unrealistic", "memory", "MAX_VALUE")
        
        return memory_gb
    
    @staticmethod
    def validate_cpu_usage(cpu_percent: float) -> float:
        """Validate CPU usage percentage"""
        if cpu_percent < 0:
            raise ValidationError("CPU usage cannot be negative", "cpu_usage", "MIN_VALUE")
        
        if cpu_percent > 100:
            raise ValidationError("CPU usage cannot exceed 100%", "cpu_usage", "MAX_VALUE")
        
        return cpu_percent
    
    @staticmethod
    def validate_inference_speed(tokens_per_second: float) -> float:
        """Validate AI inference speed"""
        if tokens_per_second < 0:
            raise ValidationError("Inference speed cannot be negative", "inference_speed", "MIN_VALUE")
        
        if tokens_per_second > 10000:  # Unrealistically high
            raise ValidationError("Inference speed value seems unrealistic", "inference_speed", "MAX_VALUE")
        
        return tokens_per_second


# Composite validators for complex objects

def validate_task_creation_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate complete task creation data"""
    validated = {}
    
    # Required fields
    validated['title'] = TaskValidator.validate_title(data.get('title', ''))
    validated['description'] = TaskValidator.validate_description(data.get('description', ''))
    
    # Optional fields
    if 'priority' in data:
        validated['priority'] = TaskValidator.validate_priority(data['priority'])
    
    if 'agent_id' in data:
        validated['agent_id'] = TaskValidator.validate_agent_assignment(data['agent_id'])
    
    if 'project_id' in data:
        validated['project_id'] = UUIDValidator.validate_uuid(data['project_id'], 'project_id') if data['project_id'] else None
    
    if 'estimated_effort' in data:
        validated['estimated_effort'] = TaskValidator.validate_effort_estimate(data['estimated_effort'])
    
    # Check for SQL injection in all string fields
    SecurityValidator.validate_sql_injection(validated)
    
    return validated


def validate_agent_creation_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate complete agent creation data"""
    validated = {}
    
    # Required fields
    validated['name'] = AgentValidator.validate_agent_name(data.get('name', ''))
    validated['type'] = AgentValidator.validate_agent_type(data.get('type', ''))
    validated['expertise'] = AgentValidator.validate_expertise(data.get('expertise', []))
    
    # Optional fields
    if 'description' in data:
        description = data['description'].strip() if data['description'] else ''
        if description:
            validated['description'] = SecurityValidator.sanitize_html(description)
    
    # Check for SQL injection
    SecurityValidator.validate_sql_injection(validated)
    
    return validated


def validate_project_creation_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate complete project creation data"""
    validated = {}
    
    # Required fields
    validated['name'] = ProjectValidator.validate_project_name(data.get('name', ''))
    
    # Optional fields
    if 'description' in data:
        validated['description'] = ProjectValidator.validate_project_description(data.get('description', ''))
    
    # Check for SQL injection
    SecurityValidator.validate_sql_injection(validated)
    
    return validated


# Decorator for automatic validation
def validate_input(validation_func: Callable):
    """Decorator to automatically validate input data"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Find data parameter (usually the first dict parameter)
            for i, arg in enumerate(args):
                if isinstance(arg, dict):
                    args = list(args)
                    args[i] = validation_func(arg)
                    break
            
            # Check kwargs for data
            for key, value in kwargs.items():
                if isinstance(value, dict) and key in ['data', 'payload', 'request_data']:
                    kwargs[key] = validation_func(value)
                    break
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
