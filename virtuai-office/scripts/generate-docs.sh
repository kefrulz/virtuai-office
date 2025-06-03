#!/bin/bash

# VirtuAI Office - Documentation Generation Script
# Generates comprehensive documentation from source code and templates

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
OUTPUT_DIR="$PROJECT_ROOT/docs/generated"
TEMP_DIR="/tmp/virtuai-docs-$$"

# Documentation sections
SECTIONS=(
    "api"
    "architecture"
    "deployment"
    "development"
    "user-guide"
    "troubleshooting"
    "examples"
)

print_header() {
    echo -e "${PURPLE}"
    echo "██╗   ██╗██╗██████╗ ████████╗██╗   ██╗ █████╗ ██╗"
    echo "██║   ██║██║██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██║"
    echo "██║   ██║██║██████╔╝   ██║   ██║   ██║███████║██║"
    echo "╚██╗ ██╔╝██║██╔══██╗   ██║   ██║   ██║██╔══██║██║"
    echo " ╚████╔╝ ██║██║  ██║   ██║   ╚██████╔╝██║  ██║██║"
    echo "  ╚═══╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝"
    echo -e "${NC}"
    echo -e "${CYAN}📚 VirtuAI Office Documentation Generator${NC}"
    echo -e "${CYAN}=======================================${NC}"
    echo ""
}

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔄 $1${NC}"; }

# Initialize directories
init_directories() {
    log_step "Initializing documentation directories..."
    
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$TEMP_DIR"
    mkdir -p "$DOCS_DIR/api"
    mkdir -p "$DOCS_DIR/guides"
    mkdir -p "$DOCS_DIR/examples"
    mkdir -p "$DOCS_DIR/images"
    
    log_success "Documentation structure created"
}

# Extract API documentation from FastAPI
generate_api_docs() {
    log_step "Generating API documentation..."
    
    if [ -f "$BACKEND_DIR/backend.py" ]; then
        # Start backend temporarily to extract OpenAPI schema
        cd "$BACKEND_DIR"
        
        # Check if virtual environment exists
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        # Generate OpenAPI JSON schema
        python3 -c "
import sys
sys.path.append('.')
from backend import app
import json

# Get OpenAPI schema
openapi_schema = app.openapi()

# Write to file
with open('$OUTPUT_DIR/openapi.json', 'w') as f:
    json.dump(openapi_schema, f, indent=2)

print('OpenAPI schema generated')
" 2>/dev/null || log_warning "Could not extract OpenAPI schema"

        # Generate markdown API docs
        cat > "$OUTPUT_DIR/API_REFERENCE.md" << 'EOF'
# 🔧 VirtuAI Office API Reference

## Overview

This is the complete API reference for VirtuAI Office. The API follows RESTful conventions and returns JSON responses.

**Base URL**: `http://localhost:8000`

## Authentication

Currently no authentication required for local development.

## Endpoints

### System Status
- `GET /api/status` - Get system health status
- `GET /api/analytics` - Get performance analytics

### Tasks
- `POST /api/tasks` - Create a new task
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/{id}` - Get specific task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `POST /api/tasks/{id}/retry` - Retry failed task

### Agents
- `GET /api/agents` - List all agents
- `GET /api/agents/{id}` - Get agent details
- `GET /api/agents/{id}/tasks` - Get agent's tasks
- `GET /api/agents/{id}/performance` - Get agent performance

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project details

### Boss AI
- `POST /api/standup` - Generate daily standup
- `GET /api/boss/insights` - Get AI insights
- `POST /api/boss/optimize-assignments` - Optimize task assignments

### Apple Silicon
- `GET /api/apple-silicon/detect` - Detect hardware
- `POST /api/apple-silicon/optimize` - Apply optimizations
- `GET /api/apple-silicon/performance` - Get performance metrics

## WebSocket API

Connect to `ws://localhost:8000/ws` for real-time updates.

Message types:
- `task_update` - Task status changed
- `task_completed` - Task finished
- `task_failed` - Task failed

## Error Handling

Standard HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

EOF

        log_success "API documentation generated"
    else
        log_warning "Backend source not found, skipping API docs"
    fi
}

# Generate architecture documentation
generate_architecture_docs() {
    log_step "Generating architecture documentation..."
    
    cat > "$OUTPUT_DIR/ARCHITECTURE.md" << 'EOF'
# 🏗️ VirtuAI Office Architecture

## System Overview

VirtuAI Office is built as a modular, scalable system with clear separation of concerns.

```
┌─────────────────────────────────────────┐
│            VirtuAI Office               │
├─────────────────────────────────────────┤
│  Frontend (React)    │  Backend (FastAPI)│
│  ├── Dashboard      │  ├── API Routes   │
│  ├── Task Mgmt      │  ├── AI Agents    │
│  ├── Agent Views    │  ├── Boss AI      │
│  └── Real-time UI   │  └── Database     │
├─────────────────────────────────────────┤
│         AI Layer (Ollama)               │
│  ├── LLM Models                         │
│  ├── Model Management                   │
│  └── Optimization                       │
├─────────────────────────────────────────┤
│         Data Layer                      │
│  ├── SQLite Database                    │
│  ├── Task Storage                       │
│  └── Performance Metrics               │
└─────────────────────────────────────────┘
```

## Core Components

### Frontend (React)
- Modern React 18 with hooks
- Tailwind CSS for styling
- WebSocket for real-time updates
- PWA capabilities

### Backend (FastAPI)
- Async FastAPI server
- SQLAlchemy ORM
- Pydantic validation
- WebSocket support

### AI Layer (Ollama)
- Local LLM inference
- Model management
- Apple Silicon optimization
- Performance monitoring

### Database (SQLite)
- Task storage
- Agent configurations
- Performance metrics
- User preferences

## Agent Architecture

Each AI agent inherits from `BaseAgent`:

```python
class BaseAgent:
    def __init__(self, name, type, description, expertise):
        self.name = name
        self.type = type
        self.description = description
        self.expertise = expertise
    
    async def process_task(self, task) -> str:
        # Agent-specific processing
        pass
```

### Specialized Agents

1. **Alice Chen (Product Manager)**
   - User stories and requirements
   - Project planning and coordination

2. **Marcus Dev (Frontend Developer)**
   - React components and UI code
   - Responsive design implementation

3. **Sarah Backend (Backend Developer)**
   - API endpoints and services
   - Database design and implementation

4. **Luna Design (UI/UX Designer)**
   - Design specifications and wireframes
   - User experience planning

5. **TestBot QA (Quality Assurance)**
   - Test plans and automation
   - Quality assurance procedures

## Boss AI System

The Boss AI coordinates the team:
- Intelligent task assignment
- Workload balancing
- Performance optimization
- Team collaboration

## Apple Silicon Optimization

Specialized optimizations for M1/M2/M3 Macs:
- Hardware detection
- Optimal model selection
- Performance monitoring
- Thermal management

## Data Flow

1. **Task Creation**: User → Frontend → API → Boss AI → Agent Assignment
2. **Processing**: Agent → Ollama → AI Processing → Output Generation
3. **Updates**: WebSocket → Frontend → Real-time UI Updates

## Security

- Local-first architecture
- No cloud dependencies
- Data privacy by design
- Input validation and sanitization

## Performance

- Async processing
- Background task queue
- Real-time monitoring
- Apple Silicon optimization

EOF

    log_success "Architecture documentation generated"
}

# Generate deployment guide
generate_deployment_docs() {
    log_step "Generating deployment documentation..."
    
    cat > "$OUTPUT_DIR/DEPLOYMENT.md" << 'EOF'
# 🚀 VirtuAI Office Deployment Guide

## Quick Deployment

### One-Click Install
```bash
curl -fsSL https://raw.githubusercontent.com/kefrulz/virtuai-office/main/deploy.sh | bash
```

### Apple Silicon Optimized
```bash
curl -fsSL https://raw.githubusercontent.com/kefrulz/virtuai-office/main/deploy-apple-silicon.sh | bash
```

## Manual Deployment

### Prerequisites
- Python 3.8+
- Node.js 16+
- 8GB+ RAM
- 10GB disk space

### Step-by-Step Installation

1. **Clone Repository**
```bash
git clone https://github.com/kefrulz/virtuai-office.git
cd virtuai-office
```

2. **Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd ../frontend
npm install
```

4. **Install Ollama**
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

5. **Download AI Models**
```bash
ollama pull llama2:7b
ollama pull codellama:7b
```

6. **Start Services**
```bash
# Start Ollama
ollama serve &

# Start Backend
cd backend && python backend.py &

# Start Frontend  
cd frontend && npm start
```

## Docker Deployment

### Using Docker Compose
```yaml
version: '3.8'
services:
  virtuai-backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    depends_on:
      - ollama

  virtuai-frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - virtuai-backend

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

### Start with Docker
```bash
docker-compose up -d
```

## Production Deployment

### System Requirements
- 16GB+ RAM (for production workloads)
- 50GB+ disk space
- PostgreSQL database
- Reverse proxy (nginx)

### Configuration

1. **Environment Variables**
```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost/virtuai
OLLAMA_HOST=localhost:11434
LOG_LEVEL=INFO

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

2. **Database Migration**
```bash
cd backend
alembic upgrade head
```

3. **Process Management**
```bash
# Using systemd
sudo systemctl enable virtuai-backend
sudo systemctl enable virtuai-frontend
sudo systemctl start virtuai-backend virtuai-frontend
```

## Monitoring

### Health Checks
```bash
# Check system status
curl http://localhost:8000/api/status

# Check Ollama
curl http://localhost:11434/api/version
```

### Performance Monitoring
- CPU and memory usage
- AI inference speed
- Task completion rates
- Error rates

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check logs
journalctl -u virtuai-backend
tail -f backend/logs/app.log
```

**AI models not responding:**
```bash
# Restart Ollama
pkill ollama
ollama serve
```

**Performance issues:**
```bash
# Check system resources
htop
./manage.sh status
```

## Backup and Recovery

### Backup Database
```bash
# SQLite
cp backend/virtuai_office.db backup/

# PostgreSQL
pg_dump virtuai > backup/virtuai_$(date +%Y%m%d).sql
```

### Restore Database
```bash
# SQLite
cp backup/virtuai_office.db backend/

# PostgreSQL
psql virtuai < backup/virtuai_20240115.sql
```

## Updates

### Update VirtuAI Office
```bash
git pull origin main
./scripts/update.sh
```

### Update AI Models
```bash
ollama pull llama2:latest
ollama pull codellama:latest
```

EOF

    log_success "Deployment documentation generated"
}

# Generate development guide
generate_development_docs() {
    log_step "Generating development documentation..."
    
    cat > "$OUTPUT_DIR/DEVELOPMENT.md" << 'EOF'
# 👩‍💻 VirtuAI Office Development Guide

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git
- VS Code (recommended)

### Quick Start
```bash
# Clone and setup
git clone https://github.com/kefrulz/virtuai-office.git
cd virtuai-office

# Backend development
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend development
cd ../frontend
npm install
npm install --save-dev @types/react @types/node
```

## Development Workflow

### Backend Development
```bash
# Start development server with hot reload
cd backend
uvicorn backend:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/

# Code formatting
black .
isort .

# Type checking
mypy .
```

### Frontend Development
```bash
# Start development server
cd frontend
npm start

# Run tests
npm test

# Build for production
npm run build

# Code formatting
npm run format
```

## Project Structure

```
virtuai-office/
├── backend/
│   ├── backend.py              # Main FastAPI application
│   ├── models/                 # Database models
│   ├── agents/                 # AI agent implementations
│   ├── api/                    # API route handlers
│   ├── utils/                  # Utility functions
│   └── tests/                  # Backend tests
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks
│   │   ├── utils/              # Utility functions
│   │   └── tests/              # Frontend tests
│   └── public/                 # Static assets
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
└── tests/                      # Integration tests
```

## Adding New Features

### Creating a New AI Agent

1. **Define Agent Class**
```python
# backend/agents/custom_agent.py
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Custom Agent",
            agent_type="custom",
            description="Specialized custom functionality",
            expertise=["custom", "specialized"]
        )
    
    def get_system_prompt(self):
        return "You are a specialized custom agent..."
    
    async def process_task(self, task):
        # Custom processing logic
        return generated_output
```

2. **Register Agent**
```python
# backend/backend.py
from agents.custom_agent import CustomAgent

# In startup event
agent_manager.register_agent("custom", CustomAgent())
```

3. **Add Frontend UI**
```javascript
// frontend/src/components/CustomAgentCard.js
const CustomAgentCard = ({ agent }) => {
  return (
    <div className="agent-card custom-agent">
      <h3>{agent.name}</h3>
      <p>{agent.description}</p>
    </div>
  );
};
```

### Adding New API Endpoints

1. **Define Pydantic Models**
```python
# backend/models/schemas.py
class CustomRequest(BaseModel):
    name: str
    description: str

class CustomResponse(BaseModel):
    id: str
    result: str
```

2. **Create API Route**
```python
# backend/api/custom.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/custom", tags=["custom"])

@router.post("/", response_model=CustomResponse)
async def create_custom(request: CustomRequest):
    # Implementation
    return CustomResponse(id="123", result="success")
```

3. **Include Router**
```python
# backend/backend.py
from api.custom import router as custom_router

app.include_router(custom_router)
```

## Testing

### Backend Tests
```python
# tests/test_agents.py
import pytest
from agents.product_manager import AliceChenAgent

@pytest.mark.asyncio
async def test_alice_agent():
    agent = AliceChenAgent()
    task = create_test_task("Write user story")
    
    output = await agent.process_task(task)
    
    assert "As a" in output
    assert "I want" in output
    assert "So that" in output
```

### Frontend Tests
```javascript
// src/components/__tests__/TaskCard.test.js
import { render, screen } from '@testing-library/react';
import TaskCard from '../TaskCard';

test('renders task card', () => {
  const task = {
    id: '1',
    title: 'Test Task',
    status: 'pending'
  };
  
  render(<TaskCard task={task} />);
  
  expect(screen.getByText('Test Task')).toBeInTheDocument();
});
```

### Integration Tests
```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from backend import app

client = TestClient(app)

def test_create_task_flow():
    # Create task
    response = client.post("/api/tasks", json={
        "title": "Test Task",
        "description": "Test description"
    })
    
    assert response.status_code == 201
    task_id = response.json()["id"]
    
    # Check task status
    response = client.get(f"/api/tasks/{task_id}")
    assert response.json()["status"] == "pending"
```

## Code Style

### Python (Backend)
```python
# Use Black formatter
black --line-length 88 .

# Use isort for imports
isort .

# Type hints required
def process_task(task: Task) -> str:
    return "result"

# Docstrings for public functions
def create_agent(name: str) -> Agent:
    """Create a new AI agent.
    
    Args:
        name: The agent's name
        
    Returns:
        Configured agent instance
    """
    pass
```

### JavaScript (Frontend)
```javascript
// Use Prettier formatter
npm run format

// Use camelCase
const userName = 'alice';
const taskStatus = 'pending';

// Component naming
const TaskCard = ({ task }) => {
  return <div>{task.title}</div>;
};

// Hook naming
const useTaskManager = () => {
  const [tasks, setTasks] = useState([]);
  return { tasks, setTasks };
};
```

## Database Migrations

### Creating Migrations
```bash
# Generate migration
cd backend
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Migration Best Practices
- Always review generated migrations
- Test migrations on sample data
- Include both upgrade and downgrade
- Document breaking changes

## Performance Optimization

### Backend Optimization
- Use async/await for I/O operations
- Implement connection pooling
- Cache frequently accessed data
- Monitor query performance

### Frontend Optimization
- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Lazy load components
- Optimize bundle size

### AI Model Optimization
- Choose appropriate model sizes
- Implement model caching
- Monitor inference performance
- Use quantized models when appropriate

## Debugging

### Backend Debugging
```python
# Add logging
import logging
logger = logging.getLogger(__name__)

logger.info("Processing task %s", task.id)
logger.error("Failed to process task: %s", error)

# Use debugger
import pdb
pdb.set_trace()
```

### Frontend Debugging
```javascript
// Use React DevTools
// Add console logging
console.log('Task updated:', task);

// Use browser debugger
debugger;

// Performance monitoring
console.time('render');
// ... component render
console.timeEnd('render');
```

## Contributing

### Pull Request Process
1. Fork the repository
2. Create feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

### Code Review Guidelines
- Test coverage > 80%
- Documentation updated
- No breaking changes without migration
- Performance impact considered

EOF

    log_success "Development documentation generated"
}

# Generate user guide
generate_user_guide() {
    log_step "Generating user guide..."
    
    cat > "$OUTPUT_DIR/USER_GUIDE.md" << 'EOF'
# 📖 VirtuAI Office User Guide

## Getting Started

### First Steps
1. **Access Dashboard**: Open http://localhost:3000
2. **Check Status**: Verify all services are running
3. **Meet Your Team**: Review the 5 AI agents
4. **Create First Task**: Start with a simple request

### Understanding Your AI Team

#### 👩‍💼 Alice Chen - Product Manager
**Best for:**
- Writing user stories
- Creating requirements documents
- Project planning
- Stakeholder analysis

**Example tasks:**
- "Write user stories for a shopping cart feature"
- "Create project requirements for user authentication"

#### 👨‍💻 Marcus Dev - Frontend Developer
**Best for:**
- React components
- UI implementation
- Responsive design
- Frontend architecture

**Example tasks:**
- "Create a responsive navigation menu"
- "Build a user profile form with validation"

#### 👩‍💻 Sarah Backend - Backend Developer
**Best for:**
- API development
- Database design
- Server architecture
- Authentication systems

**Example tasks:**
- "Create user authentication API"
- "Design database schema for e-commerce"

#### 🎨 Luna Design - UI/UX Designer
**Best for:**
- Wireframes and mockups
- Design systems
- User experience planning
- Accessibility guidelines

**Example tasks:**
- "Design mobile checkout flow"
- "Create design system for fitness app"

#### 🔍 TestBot QA - Quality Assurance
**Best for:**
- Test planning
- Automated testing
- Quality procedures
- Bug reporting

**Example tasks:**
- "Create test plan for user registration"
- "Write automated API tests"

## Creating Effective Tasks

### Writing Good Descriptions
```
✅ Good Example:
Title: "Create user login page"
Description: "Build a responsive login page with email/password fields,
remember me checkbox, forgot password link, form validation, and
integration with JWT authentication API."

❌ Poor Example:
Title: "Make login"
Description: "Need login page"
```

### Task Priorities
- **Urgent**: Critical bugs, security issues
- **High**: Important features, deadlines
- **Medium**: Regular development work
- **Low**: Nice-to-have improvements

### Best Practices
1. **Be Specific**: Include technical requirements
2. **Provide Context**: Explain the use case
3. **Set Constraints**: Mention frameworks, limitations
4. **Break Down**: Split complex work into smaller tasks

## Monitoring Progress

### Task Statuses
- **Pending** 🟡: Waiting for agent assignment
- **In Progress** 🔵: Agent working on task
- **Completed** 🟢: Task finished with output
- **Failed** 🔴: Error occurred (can retry)

### Real-Time Updates
The dashboard automatically updates via WebSocket connection:
- Task status changes
- Agent activity notifications
- Completion alerts
- System status updates

### Using Generated Output

#### Code Output
```javascript
// Example: Marcus generates React component
import React, { useState } from 'react';

const LoginForm = ({ onSubmit }) => {
  // ... implementation
};

export default LoginForm;
```

**To use:**
1. Copy code to your project
2. Install dependencies
3. Import and customize

#### Documentation Output
- Structured with clear headings
- Actionable recommendations
- Professional formatting
- Ready to use

## Advanced Features

### Project Management
- **Create Projects**: Group related tasks
- **Sprint Planning**: Organize work into sprints
- **Daily Standups**: Get AI team reports
- **Progress Tracking**: Monitor completion

### Boss AI Insights
- Task complexity analysis
- Optimal agent assignments
- Workload balancing
- Performance recommendations

### Apple Silicon Optimization
For M1/M2/M3 Mac users:
- Automatic hardware detection
- Performance optimization
- Model recommendations
- Real-time monitoring

## Troubleshooting

### Common Issues

**Tasks stuck in "Pending":**
- Check Ollama service: http://localhost:11434
- Restart services: `./manage.sh restart`
- Download models: `ollama pull llama2:7b`

**Poor AI responses:**
- Provide more detailed descriptions
- Use larger models if you have 16GB+ RAM
- Break complex tasks into smaller parts

**Slow performance:**
- Close unnecessary applications
- Use quantized models for speed
- Limit concurrent tasks
- Optimize for Apple Silicon

### Getting Help
- **Discord**: Join community for real-time help
- **GitHub**: Report bugs or request features
- **Documentation**: Check relevant docs sections

## Tips for Success

### Start Small
Begin with simple tasks to understand each agent's capabilities.

### Iterate and Refine
Use AI output as starting point, then customize for your needs.

### Leverage Collaboration
Let agents work together on complex projects naturally.

### Monitor Performance
Keep eye on system resources and optimize as needed.

### Join Community
Connect with other users for tips and best practices.

EOF

    log_success "User guide generated"
}

# Generate troubleshooting guide
generate_troubleshooting_docs() {
    log_step "Generating troubleshooting documentation..."
    
    cat > "$OUTPUT_DIR/TROUBLESHOOTING.md" << 'EOF'
# 🔧 VirtuAI Office Troubleshooting Guide

## Quick Diagnosis

### System Health Check
```bash
# Check all services
./manage.sh status

# Verify Ollama
curl http://localhost:11434/api/version

# Check backend API
curl http://localhost:8000/api/status

# Test frontend
curl http://localhost:3000
```

## Common Issues

### Installation Problems

#### Ollama Installation Failed
**Symptoms:**
- "ollama: command not found"
- Models not downloading

**Solutions:**
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Manual install
# Download from https://ollama.ai/download
```

#### Python Dependencies Failed
**Symptoms:**
- "ModuleNotFoundError"
- pip install errors

**Solutions:**
```bash
# Update pip
python3 -m pip install --upgrade pip

# Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# macOS specific
xcode-select --install
```

#### Node.js Issues
**Symptoms:**
- "npm: command not found"
- Package installation errors

**Solutions:**
```bash
# Install Node.js
# macOS: brew install node
# Linux: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Runtime Issues

#### Tasks Stuck in "Pending"
**Symptoms:**
- Tasks never start processing
- No agent assignment

**Diagnosis:**
```bash
# Check Ollama status
ps aux | grep ollama
curl http://localhost:11434/api/version

# Check available models
ollama list

# Check backend logs
tail -f backend/logs/app.log
```

**Solutions:**
```bash
# Restart Ollama
pkill ollama
ollama serve &

# Download required models
ollama pull llama2:7b
ollama pull codellama:7b

# Restart backend
cd backend
python backend.py
```

#### AI Responses Are Poor Quality
**Symptoms:**
- Incomplete or nonsensical outputs
- Generic responses

**Solutions:**
1. **Improve Task Descriptions:**
   - Be more specific about requirements
   - Provide context and examples
   - Include technical constraints

2. **Use Better Models:**
   ```bash
   # For 16GB+ RAM
   ollama pull llama2:13b
   ollama pull codellama:13b
   ```

3. **Check System Resources:**
   ```bash
   # Monitor memory usage
   htop
   
   # Check available RAM
   free -h  # Linux
   vm_stat  # macOS
   ```

#### Slow Performance
**Symptoms:**
- Long task processing times
- UI lag and delays
- High CPU/memory usage

**Solutions:**

1. **System Optimization:**
   ```bash
   # Close unnecessary applications
   # Ensure 8GB+ available RAM
   # Use SSD storage
   ```

2. **Model Optimization:**
   ```bash
   # Use quantized models for speed
   ollama pull llama2:7b-q4_0
   ollama pull codellama:7b-q4_0
   ```

3. **Apple Silicon Optimization:**
   ```bash
   # Run optimization script
   ./deploy-apple-silicon.sh
   
   # Check optimization status
   ./manage.sh optimize
   ```

#### WebSocket Connection Issues
**Symptoms:**
- No real-time updates
- "Connection lost" messages

**Solutions:**
```bash
# Check backend WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws

# Restart services
./manage.sh restart

# Check firewall settings
# Ensure ports 3000, 8000, 11434 are open
```

### Platform-Specific Issues

#### macOS Issues

**Permission Denied Errors:**
```bash
# Fix permissions
sudo chown -R $(whoami) /usr/local/bin
sudo chown -R $(whoami) ~/.npm

# Install Xcode command line tools
xcode-select --install
```

**Rosetta Conflicts (Apple Silicon):**
```bash
# Ensure native ARM64 installation
arch -arm64 brew install python node ollama

# Check architecture
uname -m  # Should show "arm64"
```

**Thermal Throttling:**
```bash
# Check thermal state
pmset -g therm

# Enable high-performance mode (when plugged in)
sudo pmset -c powernap 0
sudo pmset -c sleep 0
```

#### Linux Issues

**Permission Denied for Docker:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Restart Docker service
sudo systemctl restart docker
```

**Missing System Dependencies:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential python3-dev nodejs npm

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel nodejs npm
```

#### Windows (WSL) Issues

**WSL Not Enabled:**
```bash
# Enable WSL2
wsl --install
wsl --set-default-version 2

# Install Ubuntu
wsl --install -d Ubuntu
```

**File Permission Issues:**
```bash
# Fix file permissions in WSL
chmod +x manage.sh
chmod +x deploy.sh
```

### Database Issues

#### Database Connection Errors
**Symptoms:**
- "Database connection failed"
- SQLAlchemy errors

**Solutions:**
```bash
# Reset database
rm backend/virtuai_office.db

# Recreate database
cd backend
python -c "
from backend import Base, engine
Base.metadata.create_all(bind=engine)
print('Database recreated')
"

# Run migrations
alembic upgrade head
```

#### Corrupted Database
**Symptoms:**
- "Database is locked"
- Data inconsistencies

**Solutions:**
```bash
# Backup current database
cp backend/virtuai_office.db backup/

# Check database integrity
sqlite3 backend/virtuai_office.db "PRAGMA integrity_check;"

# Repair database
sqlite3 backend/virtuai_office.db ".recover" | sqlite3 repaired.db
mv repaired.db backend/virtuai_office.db
```

### Memory and Performance Issues

#### Out of Memory Errors
**Symptoms:**
- "MemoryError" in logs
- System becomes unresponsive

**Solutions:**
1. **Use Smaller Models:**
   ```bash
   # Switch to 7B models
   ollama pull llama2:7b-q4_0
   ```

2. **Limit Concurrent Tasks:**
   ```bash
   # Edit configuration
   export OLLAMA_MAX_LOADED_MODELS=1
   ```

3. **Increase Virtual Memory:**
   ```bash
   # Linux: Increase swap
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

#### High CPU Usage
**Symptoms:**
- CPU usage > 90%
- System lag

**Solutions:**
```bash
# Limit CPU threads
export OLLAMA_NUM_THREADS=4

# Monitor processes
htop
ps aux | grep -E "(ollama|python|node)"

# Kill unnecessary processes
pkill -f "unnecessary_process"
```

### Network Issues

#### Port Conflicts
**Symptoms:**
- "Address already in use"
- Services won't start

**Solutions:**
```bash
# Check what's using ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :11434 # Ollama

# Kill conflicting processes
kill -9 <PID>

# Use different ports
PORT=3001 npm start
uvicorn backend:app --port 8001
```

#### Firewall Issues
**Symptoms:**
- Cannot access services
- Connection timeout

**Solutions:**
```bash
# macOS: Allow through firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/ollama
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/local/bin/ollama

# Linux: Configure iptables
sudo iptables -I INPUT -p tcp --dport 3000 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 11434 -j ACCEPT
```

## Advanced Troubleshooting

### Debug Mode

#### Enable Debug Logging
```bash
# Backend debug mode
cd backend
LOG_LEVEL=DEBUG python backend.py

# Frontend debug mode
cd frontend
REACT_APP_DEBUG=true npm start
```

#### Ollama Debug Mode
```bash
# Start Ollama with debug logging
OLLAMA_DEBUG=1 ollama serve

# Check Ollama logs
tail -f ~/.ollama/logs/server.log
```

### Performance Profiling

#### Backend Profiling
```python
# Add to backend.py
import cProfile
import pstats

# Profile endpoint
@app.get("/api/profile")
async def profile_endpoint():
    pr = cProfile.Profile()
    pr.enable()
    
    # Your code here
    
    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.dump_stats('profile.stats')
    
    return {"message": "Profile saved"}
```

#### Frontend Profiling
```javascript
// Use React DevTools Profiler
// Enable in browser developer tools

// Performance monitoring
performance.mark('start-task');
// ... task processing
performance.mark('end-task');
performance.measure('task-duration', 'start-task', 'end-task');
```

### Log Analysis

#### Backend Logs
```bash
# View recent logs
tail -f backend/logs/app.log

# Search for errors
grep -i error backend/logs/app.log

# Analyze patterns
awk '/ERROR/ {print $1, $2}' backend/logs/app.log | sort | uniq -c
```

#### System Logs
```bash
# macOS
log show --predicate 'process == "ollama"' --last 1h

# Linux
journalctl -u virtuai-backend -f
journalctl -u virtuai-frontend -f
```

## Recovery Procedures

### Complete Reset
```bash
# Stop all services
./manage.sh stop
pkill -f ollama

# Remove data
rm -rf backend/virtuai_office.db
rm -rf backend/logs/*
rm -rf frontend/node_modules

# Reinstall
npm install
pip install -r requirements.txt

# Restart
./manage.sh start
```

### Backup and Restore
```bash
# Create backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backup-20240115.tar.gz
```

## Getting Help

### Information to Include
When seeking help, provide:
- Operating system and version
- Hardware specifications (CPU, RAM)
- Error messages (full text)
- Steps to reproduce
- Relevant log excerpts

### Community Support
- **Discord**: Real-time help from community
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Check all relevant docs first

### Professional Support
For production deployments:
- Performance optimization consulting
- Custom agent development
- Enterprise integration support

## Prevention Tips

### Regular Maintenance
```bash
# Weekly tasks
./manage.sh status
ollama list
df -h  # Check disk space

# Monthly tasks
./scripts/cleanup.sh
./scripts/update.sh
```

### Monitoring Setup
```bash
# Set up monitoring
./scripts/setup-monitoring.sh

# Check health regularly
curl http://localhost:8000/api/status
```

### Best Practices
1. **Keep Systems Updated**: OS, Python, Node.js
2. **Monitor Resources**: CPU, memory, disk space
3. **Regular Backups**: Database and configurations
4. **Clean Logs**: Rotate and archive log files
5. **Test Changes**: Verify in development first

EOF

    log_success "Troubleshooting documentation generated"
}

# Generate examples
generate_examples() {
    log_step "Generating example documentation..."
    
    mkdir -p "$OUTPUT_DIR/examples"
    
    # API examples
    cat > "$OUTPUT_DIR/examples/API_EXAMPLES.md" << 'EOF'
# 🔌 VirtuAI Office API Examples

## Python SDK Examples

### Basic Task Creation
```python
import requests
import json
import time

class VirtuAIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def create_task(self, title, description, priority="medium"):
        """Create a new task"""
        response = requests.post(f"{self.base_url}/api/tasks", json={
            "title": title,
            "description": description,
            "priority": priority
        })
        return response.json()
    
    def wait_for_completion(self, task_id, timeout=300):
        """Wait for task to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(f"{self.base_url}/api/tasks/{task_id}")
            task = response.json()
            
            if task["status"] == "completed":
                return task["output"]
            elif task["status"] == "failed":
                raise Exception(f"Task failed: {task.get('error', 'Unknown error')}")
            
            time.sleep(5)
        
        raise TimeoutError("Task did not complete within timeout")

# Usage
client = VirtuAIClient()

# Create a React component task
task = client.create_task(
    title="Create user profile component",
    description="Build a React component for displaying user profile information with avatar, name, email, and edit button",
    priority="high"
)

print(f"Task created: {task['id']}")

# Wait for completion
try:
    output = client.wait_for_completion(task['id'])
    print("Generated code:")
    print(output)
except Exception as e:
    print(f"Error: {e}")
```

### Batch Task Processing
```python
def process_multiple_tasks(client, tasks):
    """Process multiple tasks and collect results"""
    task_ids = []
    
    # Create all tasks
    for task_data in tasks:
        task = client.create_task(**task_data)
        task_ids.append(task['id'])
        print(f"Created task: {task['id']}")
    
    # Wait for all completions
    results = {}
    for task_id in task_ids:
        try:
            output = client.wait_for_completion(task_id)
            results[task_id] = output
        except Exception as e:
            results[task_id] = f"Error: {e}"
    
    return results

# Example usage
tasks = [
    {
        "title": "Create login form",
        "description": "Build a responsive login form with email and password fields",
        "priority": "high"
    },
    {
        "title": "Design user dashboard",
        "description": "Create wireframes for a user dashboard with metrics and navigation",
        "priority": "medium"
    },
    {
        "title": "Write API tests",
        "description": "Create comprehensive test suite for user authentication endpoints",
        "priority": "medium"
    }
]

results = process_multiple_tasks(client, tasks)
for task_id, result in results.items():
    print(f"\nTask {task_id}:")
    print(result[:200] + "..." if len(result) > 200 else result)
```

## JavaScript SDK Examples

### React Integration
```javascript
// VirtuAI React Hook
import { useState, useEffect } from 'react';

export const useVirtuAI = (baseUrl = 'http://localhost:8000') => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);

  const createTask = async (taskData) => {
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      });
      
      const task = await response.json();
      setTasks(prev => [...prev, task]);
      return task;
    } catch (error) {
      console.error('Failed to create task:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const getTask = async (taskId) => {
    const response = await fetch(`${baseUrl}/api/tasks/${taskId}`);
    return await response.json();
  };

  const waitForCompletion = async (taskId, onProgress) => {
    const poll = async () => {
      const task = await getTask(taskId);
      
      if (onProgress) {
        onProgress(task);
      }
      
      if (task.status === 'completed') {
        return task.output;
      } else if (task.status === 'failed') {
        throw new Error(`Task failed: ${task.error || 'Unknown error'}`);
      } else {
        // Continue polling
        setTimeout(poll, 2000);
      }
    };
    
    return poll();
  };

  return {
    tasks,
    loading,
    createTask,
    getTask,
    waitForCompletion
  };
};

// Usage in React component
const TaskCreator = () => {
  const { createTask, waitForCompletion } = useVirtuAI();
  const [result, setResult] = useState('');
  const [progress, setProgress] = useState('');

  const handleCreateTask = async () => {
    try {
      const task = await createTask({
        title: 'Create navigation component',
        description: 'Build a responsive navigation bar with dropdown menus',
        priority: 'high'
      });

      setProgress('Task created, waiting for completion...');
      
      const output = await waitForCompletion(task.id, (task) => {
        setProgress(`Status: ${task.status}`);
      });
      
      setResult(output);
      setProgress('Completed!');
    } catch (error) {
      setProgress(`Error: ${error.message}`);
    }
  };

  return (
    <div>
      <button onClick={handleCreateTask}>Create Navigation Component</button>
      <p>Progress: {progress}</p>
      {result && (
        <pre style={{ background: '#f5f5f5', padding: '1rem' }}>
          {result}
        </pre>
      )}
    </div>
  );
};
```

### WebSocket Integration
```javascript
class VirtuAIWebSocket {
  constructor(url = 'ws://localhost:8000/ws') {
    this.url = url;
    this.ws = null;
    this.listeners = new Map();
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('Connected to VirtuAI Office');
      this.emit('connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit(data.type, data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('Disconnected from VirtuAI Office');
      this.emit('disconnected');
      
      // Reconnect after 5 seconds
      setTimeout(() => this.connect(), 5000);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(callback => callback(data));
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const virtuAI = new VirtuAIWebSocket();

virtuAI.on('connected', () => {
  console.log('Real-time updates enabled');
});

virtuAI.on('task_completed', (data) => {
  console.log(`Task ${data.task_id} completed by ${data.agent_name}`);
  // Update UI with completion notification
});

virtuAI.on('task_failed', (data) => {
  console.error(`Task ${data.task_id} failed: ${data.error}`);
  // Show error notification
});

virtuAI.connect();
```

## Integration Examples

### VS Code Extension
```javascript
// VS Code extension for VirtuAI Office integration
const vscode = require('vscode');
const axios = require('axios');

function activate(context) {
  const disposable = vscode.commands.registerCommand(
    'virtuai.createTaskFromSelection',
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
      }

      const selection = editor.document.getText(editor.selection);
      if (!selection) {
        vscode.window.showErrorMessage('No text selected');
        return;
      }

      const taskType = await vscode.window.showQuickPick([
        'Code Review',
        'Documentation',
        'Test Generation',
        'Refactoring'
      ], { placeHolder: 'Select task type' });

      if (!taskType) return;

      try {
        const response = await axios.post('http://localhost:8000/api/tasks', {
          title: `${taskType} for selected code`,
          description: `Please ${taskType.toLowerCase()} the following code:\n\n${selection}`,
          priority: 'medium'
        });

        const task = response.data;
        vscode.window.showInformationMessage(
          `Task created: ${task.id}`,
          'View in Dashboard'
        ).then(selection => {
          if (selection === 'View in Dashboard') {
            vscode.env.openExternal(vscode.Uri.parse('http://localhost:3000'));
          }
        });
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to create task: ${error.message}`);
      }
    }
  );

  context.subscriptions.push(disposable);
}

module.exports = { activate };
```

### GitHub Actions Integration
```yaml
# .github/workflows/virtuai-review.yml
name: VirtuAI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  virtuai-review:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Get changed files
      id: changes
      run: |
        echo "files=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }} | tr '\n' ' ')" >> $GITHUB_OUTPUT
    
    - name: Create VirtuAI review task
      run: |
        curl -X POST http://your-virtuai-server:8000/api/tasks \
          -H "Content-Type: application/json" \
          -d '{
            "title": "Code review for PR #${{ github.event.number }}",
            "description": "Please review the following files for code quality, security, and best practices: ${{ steps.changes.outputs.files }}",
            "priority": "high"
          }'
```

### Slack Bot Integration
```python
# Slack bot for VirtuAI Office
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests

app = App(token="your-slack-bot-token")

@app.command("/virtuai")
def handle_virtuai_command(ack, respond, command):
    ack()
    
    task_description = command['text']
    if not task_description:
        respond("Please provide a task description. Example: `/virtuai create a login form`")
        return
    
    try:
        # Create task in VirtuAI Office
        response = requests.post('http://localhost:8000/api/tasks', json={
            'title': f"Slack request: {task_description[:50]}...",
            'description': task_description,
            'priority': 'medium'
        })
        
        task = response.json()
        
        respond({
            "text": f"✅ Task created successfully!",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Task ID:* {task['id']}\n*Status:* {task['status']}\n*Description:* {task_description}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Dashboard"},
                            "url": "http://localhost:3000"
                        }
                    ]
                }
            ]
        })
    except Exception as e:
        respond(f"❌ Failed to create task: {str(e)}")

if __name__ == "__main__":
    handler = SocketModeHandler(app, "your-app-token")
    handler.start()
```

EOF

    log_success "Example documentation generated"
}

# Generate final index
generate_index() {
    log_step "Generating documentation index..."
    
    cat > "$OUTPUT_DIR/README.md" << EOF
# 📚 VirtuAI Office Documentation

> Auto-generated documentation for VirtuAI Office

## Quick Links

- [🚀 Deployment Guide](DEPLOYMENT.md)
- [📖 User Guide](USER_GUIDE.md)
- [🔧 API Reference](API_REFERENCE.md)
- [🏗️ Architecture](ARCHITECTURE.md)
- [👩‍💻 Development Guide](DEVELOPMENT.md)
- [🔧 Troubleshooting](TROUBLESHOOTING.md)
- [🔌 Examples](examples/API_EXAMPLES.md)

## Documentation Sections

### Getting Started
- **[Deployment Guide](DEPLOYMENT.md)** - How to install and deploy VirtuAI Office
- **[User Guide](USER_GUIDE.md)** - Complete user manual with best practices

### Development
- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Architecture](ARCHITECTURE.md)** - System architecture overview
- **[Development Guide](DEVELOPMENT.md)** - Guide for contributors and developers

### Support
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Examples](examples/)** - Code examples and integrations

## Auto-Generated

This documentation was automatically generated on $(date) from the VirtuAI Office source code and templates.

To regenerate:
\`\`\`bash
./scripts/generate-docs.sh
\`\`\`

## Contributing

Found an error or want to improve the docs? 
- Edit the source templates in \`docs/\`
- Submit a pull request
- Run the generation script to update

---

**🤖 VirtuAI Office - Your AI Development Team**
EOF

    log_success "Documentation index generated"
}

# Cleanup
cleanup() {
    log_step "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
    log_success "Cleanup completed"
}

# Main execution
main() {
    print_header
    
    log_info "Starting documentation generation..."
    log_info "Project root: $PROJECT_ROOT"
    log_info "Output directory: $OUTPUT_DIR"
    
    init_directories
    generate_api_docs
    generate_architecture_docs
    generate_deployment_docs
    generate_development_docs
    generate_user_guide
    generate_troubleshooting_docs
    generate_examples
    generate_index
    cleanup
    
    echo ""
    log_success "Documentation generation completed!"
    echo ""
    echo -e "${BLUE}📚 Generated documentation available in:${NC}"
    echo -e "${CYAN}   $OUTPUT_DIR${NC}"
    echo ""
    echo -e "${BLUE}📖 View the main index:${NC}"
    echo -e "${CYAN}   cat $OUTPUT_DIR/README.md${NC}"
    echo ""
    echo -e "${BLUE}🌐 Serve locally:${NC}"
    echo -e "${CYAN}   cd $OUTPUT_DIR && python3 -m http.server 8080${NC}"
    echo -e "${CYAN}   Open: http://localhost:8080${NC}"
    echo ""
}

# Error handling
trap cleanup EXIT

# Check if running from correct directory
if [ ! -f "$PROJECT_ROOT/package.json" ]; then
    log_error "Please run from the VirtuAI Office project root directory"
    exit 1
fi

# Run main function
main "$@"
