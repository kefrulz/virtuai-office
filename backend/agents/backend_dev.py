import asyncio
import logging
from typing import List
from ..models.database import Task, AgentType
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SarahBackendAgent(BaseAgent):
    """Sarah Backend - Senior Backend Developer Agent"""
    
    def __init__(self):
        super().__init__(
            name="Sarah Backend",
            agent_type=AgentType.BACKEND_DEVELOPER,
            description="Senior Backend Developer with expertise in Python, APIs, databases, and system architecture",
            expertise=[
                "python", "fastapi", "django", "flask", "postgresql", "mongodb",
                "rest apis", "graphql", "authentication", "jwt", "oauth",
                "database design", "sqlalchemy", "alembic", "testing", "pytest",
                "docker", "microservices", "redis", "celery", "aws", "security",
                "performance optimization", "caching", "api documentation"
            ]
        )
    
    def get_system_prompt(self) -> str:
        return """You are Sarah Backend, a Senior Backend Developer with 7+ years of experience building scalable backend systems and APIs.

Your expertise includes:
- Python frameworks (FastAPI, Django, Flask)
- RESTful API design and implementation
- Database design and optimization (PostgreSQL, MongoDB, Redis)
- Authentication and authorization (JWT, OAuth, session management)
- Testing frameworks (pytest, unittest, integration testing)
- Docker containerization and deployment
- System architecture and design patterns
- Performance optimization and caching strategies
- Security best practices and vulnerability prevention
- API documentation and OpenAPI specifications

When writing code, you:
- Follow REST API best practices and HTTP standards
- Include comprehensive error handling and validation
- Write secure, well-validated code with proper input sanitization
- Design scalable database schemas with proper relationships
- Provide thorough API documentation
- Consider performance implications and optimization opportunities
- Include proper logging and monitoring
- Write testable code with dependency injection
- Follow Python PEP 8 style guidelines
- Use type hints and docstrings for clarity

Always provide complete, production-ready code with:
- Full implementation with all necessary imports
- Proper error handling and status codes
- Input validation using Pydantic or similar
- Database models with relationships
- Comprehensive docstrings and comments
- Usage examples and testing suggestions
- Security considerations and best practices
- Performance optimization notes where relevant"""

    async def process_task(self, task: Task) -> str:
        """Generate backend code and APIs based on task requirements"""
        
        prompt = f"""{self.get_system_prompt()}

Task: {task.title}
Description: {task.description}
Priority: {task.priority.value}

Please provide a complete backend solution including:

1. **API Endpoints** - FastAPI route implementations with proper HTTP methods
2. **Database Models** - SQLAlchemy models with relationships and constraints
3. **Request/Response Models** - Pydantic schemas for data validation
4. **Authentication** - Security implementation if user management is required
5. **Error Handling** - Comprehensive error responses with proper HTTP status codes
6. **Testing Code** - pytest test examples for the implemented functionality
7. **Database Migration** - Alembic migration script if schema changes are needed
8. **API Documentation** - OpenAPI/Swagger descriptions and examples
9. **Security Considerations** - Input validation, SQL injection prevention, rate limiting
10. **Performance Notes** - Caching strategies, query optimization, scalability considerations

Format your response with clear sections and code blocks. Include:
- Complete working code with all imports
- Detailed comments explaining the implementation
- Usage examples and integration notes
- Testing strategies and example test cases
- Deployment and configuration considerations

Focus on creating robust, scalable, and maintainable backend solutions."""

        try:
            response = await self._call_ollama(prompt)
            return self._enhance_backend_response(response, task)
        except Exception as e:
            logger.error(f"Sarah Backend task processing failed: {e}")
            return self._generate_fallback_response(task, str(e))
    
    def _enhance_backend_response(self, response: str, task: Task) -> str:
        """Enhance the response with additional backend-specific information"""
        
        enhancement = f"""
# 🐍 Sarah Backend's Solution

## Task Overview
**Title:** {task.title}
**Priority:** {task.priority.value.upper()}
**Complexity:** {self._assess_complexity(task.description)}

## Implementation Details
{response}

## 🔧 Additional Recommendations

### Performance Considerations
- Implement database indexing for frequently queried fields
- Use connection pooling for database connections
- Consider implementing Redis for caching frequently accessed data
- Add pagination for list endpoints to handle large datasets
- Implement background tasks with Celery for heavy operations

### Security Best Practices
- Always validate and sanitize user input
- Use parameterized queries to prevent SQL injection
- Implement rate limiting to prevent abuse
- Use HTTPS in production environments
- Store sensitive data (passwords, tokens) securely with proper hashing
- Implement proper CORS policies for frontend integration

### Monitoring & Logging
- Add structured logging with correlation IDs
- Implement health check endpoints for monitoring
- Use application performance monitoring (APM) tools
- Set up alerts for error rates and response times
- Log security events and authentication attempts

### Testing Strategy
- Unit tests for business logic and utilities
- Integration tests for database operations
- API tests for endpoint functionality
- Load testing for performance validation
- Security testing for vulnerability assessment

### Deployment Checklist
- Environment-specific configuration management
- Database migration scripts
- Docker containerization for consistent deployments
- CI/CD pipeline integration
- Database backup and recovery procedures
- Monitoring and alerting setup

## 🚀 Next Steps
1. Review the generated code and adapt to your specific requirements
2. Set up the development environment with the specified dependencies
3. Run the provided tests to validate functionality
4. Configure environment variables for different deployment stages
5. Implement additional business logic as needed
6. Set up monitoring and logging for production deployment

**Generated by Sarah Backend - Senior Backend Developer**
*Specialized in scalable Python APIs and robust database design*
"""
        
        return enhancement
    
    def _assess_complexity(self, description: str) -> str:
        """Assess the complexity of the backend task"""
        description_lower = description.lower()
        
        # High complexity indicators
        high_complexity_keywords = [
            "microservices", "distributed", "scalable", "high-performance",
            "real-time", "websocket", "streaming", "complex business logic",
            "multi-tenant", "enterprise", "integration", "migration"
        ]
        
        # Medium complexity indicators
        medium_complexity_keywords = [
            "authentication", "authorization", "database", "api", "crud",
            "validation", "caching", "background", "notification", "search"
        ]
        
        high_score = sum(1 for keyword in high_complexity_keywords if keyword in description_lower)
        medium_score = sum(1 for keyword in medium_complexity_keywords if keyword in description_lower)
        word_count = len(description.split())
        
        if high_score >= 2 or word_count > 100:
            return "High - Complex system with multiple components"
        elif medium_score >= 2 or word_count > 50:
            return "Medium - Standard backend implementation"
        else:
            return "Low - Simple API or utility"
    
    def _generate_fallback_response(self, task: Task, error: str) -> str:
        """Generate a fallback response when AI processing fails"""
        return f"""# 🐍 Sarah Backend - Task Analysis

## Task: {task.title}

I encountered an issue processing this backend development task: {error}

## Recommended Approach

Based on the task description: "{task.description}"

### Suggested Implementation Steps:

1. **API Design**
   ```python
   from fastapi import FastAPI, HTTPException, Depends
   from pydantic import BaseModel
   from sqlalchemy.orm import Session
   
   app = FastAPI(title="API Service")
   
   class ItemCreate(BaseModel):
       name: str
       description: str
   
   @app.post("/items/")
   async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
       # Implementation here
       pass
   ```

2. **Database Models**
   ```python
   from sqlalchemy import Column, Integer, String, DateTime
   from sqlalchemy.ext.declarative import declarative_base
   
   Base = declarative_base()
   
   class Item(Base):
       __tablename__ = "items"
       
       id = Column(Integer, primary_key=True, index=True)
       name = Column(String, index=True)
       description = Column(String)
   ```

3. **Error Handling**
   ```python
   from fastapi import HTTPException, status
   
   @app.exception_handler(ValueError)
   async def value_error_handler(request, exc):
       return HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail=str(exc)
       )
   ```

### Next Steps:
1. Clarify specific requirements for the backend functionality
2. Define the data models and relationships needed
3. Specify authentication and authorization requirements
4. Determine integration points with other systems
5. Plan testing and deployment strategy

Please provide more specific requirements or try the task again with additional context.

**Sarah Backend - Senior Backend Developer**
*Ready to build robust, scalable backend solutions*
"""
    
    def can_handle_task(self, task_description: str) -> float:
        """Calculate confidence score for handling this task"""
        description_lower = task_description.lower()
        
        # Backend-specific keywords with weights
        backend_indicators = {
            'api': 0.9, 'rest': 0.9, 'fastapi': 1.0, 'django': 1.0, 'flask': 0.9,
            'database': 0.8, 'sql': 0.8, 'postgresql': 0.9, 'mongodb': 0.8,
            'authentication': 0.9, 'jwt': 0.9, 'oauth': 0.8, 'login': 0.7,
            'backend': 1.0, 'server': 0.8, 'endpoint': 0.9, 'microservice': 0.9,
            'python': 0.8, 'pydantic': 0.9, 'sqlalchemy': 0.9, 'alembic': 0.8,
            'testing': 0.7, 'pytest': 0.8, 'security': 0.7, 'validation': 0.8,
            'docker': 0.7, 'deployment': 0.6, 'performance': 0.7, 'caching': 0.8,
            'crud': 0.8, 'model': 0.6, 'schema': 0.7, 'migration': 0.8
        }
        
        # Calculate base confidence
        total_weight = 0
        matched_weight = 0
        
        for keyword, weight in backend_indicators.items():
            total_weight += weight
            if keyword in description_lower:
                matched_weight += weight
        
        base_confidence = matched_weight / total_weight if total_weight > 0 else 0
        
        # Boost for backend-specific task types
        if any(phrase in description_lower for phrase in [
            'build api', 'create endpoint', 'database design', 'backend service',
            'rest api', 'web service', 'authentication system', 'data model'
        ]):
            base_confidence += 0.2
        
        # Reduce confidence for frontend-specific tasks
        if any(phrase in description_lower for phrase in [
            'react component', 'frontend', 'ui component', 'css', 'html',
            'javascript', 'vue', 'angular', 'styling', 'responsive design'
        ]):
            base_confidence *= 0.3
        
        return min(base_confidence, 1.0)
