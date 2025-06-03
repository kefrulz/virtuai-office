"""
VirtuAI Office - Backend API Server
Complete AI development team with 5 specialized agents
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import json
import uuid

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="VirtuAI Office API",
    description="Complete AI development team with 5 specialized agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Task(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    priority: str = "medium"
    status: str = "pending"
    assigned_agent: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None

class Agent(BaseModel):
    id: str
    name: str
    role: str
    description: str
    expertise: List[str]
    status: str = "available"
    tasks_completed: int = 0

# In-memory storage
tasks_db: Dict[str, Task] = {}
agents_db: Dict[str, Agent] = {}

# Initialize AI agents
def initialize_agents():
    agents = [
        Agent(
            id="alice-chen",
            name="Alice Chen",
            role="Product Manager",
            description="Expert in user stories, requirements gathering, and project planning",
            expertise=["user-stories", "requirements", "planning", "stakeholder-analysis"]
        ),
        Agent(
            id="marcus-dev",
            name="Marcus Dev",
            role="Frontend Developer",
            description="Specialized in React, UI components, and responsive design",
            expertise=["react", "javascript", "css", "ui-components", "responsive-design"]
        ),
        Agent(
            id="sarah-backend",
            name="Sarah Backend",
            role="Backend Developer",
            description="Expert in APIs, databases, and server architecture",
            expertise=["python", "fastapi", "databases", "apis", "architecture"]
        ),
        Agent(
            id="luna-design",
            name="Luna Design",
            role="UI/UX Designer",
            description="Specialized in wireframes, design systems, and user experience",
            expertise=["wireframes", "design-systems", "ux", "prototyping", "accessibility"]
        ),
        Agent(
            id="testbot-qa",
            name="TestBot QA",
            role="Quality Assurance",
            description="Expert in test planning, automation, and quality procedures",
            expertise=["testing", "automation", "quality-assurance", "test-plans", "debugging"]
        )
    ]
    
    for agent in agents:
        agents_db[agent.id] = agent
    
    logger.info(f"✅ Initialized {len(agents)} AI agents")

# Boss AI - Task Assignment Logic
def assign_task_to_agent(task: Task) -> str:
    task_lower = task.description.lower()
    title_lower = task.title.lower()
    combined_text = f"{task_lower} {title_lower}"
    
    if any(keyword in combined_text for keyword in ["user story", "requirements", "planning", "stakeholder", "project plan"]):
        return "alice-chen"
    elif any(keyword in combined_text for keyword in ["react", "frontend", "ui", "component", "javascript", "css", "responsive"]):
        return "marcus-dev"
    elif any(keyword in combined_text for keyword in ["api", "backend", "database", "server", "python", "fastapi", "endpoint"]):
        return "sarah-backend"
    elif any(keyword in combined_text for keyword in ["design", "wireframe", "ux", "ui", "mockup", "prototype", "design system"]):
        return "luna-design"
    elif any(keyword in combined_text for keyword in ["test", "testing", "qa", "quality", "automation", "bug", "validation"]):
        return "testbot-qa"
    else:
        return "alice-chen"

# AI Processing simulation
async def process_task_with_agent(task: Task, agent: Agent) -> str:
    await asyncio.sleep(3)  # Simulate AI processing
    
    if agent.id == "alice-chen":
        return f"""# User Story: {task.title}

**As a** user  
**I want** {task.description}  
**So that** I can achieve my goals efficiently

## Acceptance Criteria
- [ ] Feature works as described
- [ ] User interface is intuitive
- [ ] Performance meets requirements
- [ ] Accessibility standards met

## Priority: {task.priority.title()}
## Estimated Effort: 3-5 story points"""

    elif agent.id == "marcus-dev":
        component_name = task.title.replace(' ', '').replace('-', '')
        return f"""```jsx
// {task.title} - React Component
import React, {{ useState }} from 'react';
import './styles.css';

const {component_name}Component = () => {{
  const [isLoading, setIsLoading] = useState(false);

  const handleAction = () => {{
    setIsLoading(true);
    // Implementation for: {task.description}
    setTimeout(() => setIsLoading(false), 1000);
  }};

  return (
    <div className="component-container">
      <h2>{task.title}</h2>
      <p>{task.description}</p>
      <button 
        onClick={{handleAction}}
        disabled={{isLoading}}
        className="primary-button"
      >
        {{isLoading ? 'Processing...' : 'Action'}}
      </button>
    </div>
  );
}};

export default {component_name}Component;
```

**Features:**
✅ Responsive design
✅ Loading states
✅ Accessibility support
✅ Modern React hooks"""

    elif agent.id == "sarah-backend":
        endpoint_name = task.title.lower().replace(' ', '_')
        return f"""```python
# {task.title} - FastAPI Endpoint
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class {task.title.replace(' ', '')}Request(BaseModel):
    name: str
    description: Optional[str] = None

class {task.title.replace(' ', '')}Response(BaseModel):
    id: str
    status: str
    message: str

@router.post("/{endpoint_name}")
async def handle_{endpoint_name}(request: {task.title.replace(' ', '')}Request):
    '''
    {task.description}
    '''
    try:
        # Process the request
        result = {{
            "id": str(uuid.uuid4()),
            "status": "success",
            "message": "Request processed successfully"
        }}
        
        return {task.title.replace(' ', '')}Response(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Database Schema:**
```sql
CREATE TABLE {endpoint_name} (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```"""

    elif agent.id == "luna-design":
        return f"""# {task.title} - Design Specification

## Overview
{task.description}

## Wireframe Structure
```
┌─────────────────────────────────────┐
│             Header/Nav              │
├─────────────────────────────────────┤
│                                     │
│           Main Content              │
│         {task.title}                │
│                                     │
├─────────────────────────────────────┤
│             Actions                 │
└─────────────────────────────────────┘
```

## Design System
- **Primary:** #2563eb (Blue)
- **Secondary:** #7c3aed (Purple) 
- **Success:** #10b981 (Green)
- **Font:** Inter, system fonts
- **Spacing:** 8px grid

## User Experience Flow
1. Clear entry point
2. Intuitive navigation
3. Immediate feedback
4. Success confirmation

## Accessibility (WCAG 2.1 AA)
✅ Color contrast > 4.5:1
✅ Keyboard navigation
✅ Screen reader support
✅ Focus indicators"""

    elif agent.id == "testbot-qa":
        return f"""# Test Plan: {task.title}

## Overview
**Feature:** {task.description}  
**Priority:** {task.priority.title()}

## Test Cases

### ✅ TC001: Basic Functionality
**Steps:**
1. Navigate to feature
2. Perform primary action
3. Verify expected result

**Expected:** Feature works without errors

### ⚠️ TC002: Error Handling
**Steps:**
1. Trigger error condition
2. Verify error message
3. Verify system stability

**Expected:** Graceful error handling

### 📈 TC003: Performance
**Steps:**
1. Measure response time
2. Test concurrent users
3. Monitor resources

**Expected:** < 2 second response

## Automated Tests
```python
import pytest

def test_{task.title.lower().replace(' ', '_')}():
    # Test: {task.description}
    assert True  # Implementation needed

def test_error_handling():
    # Error scenarios
    assert True

def test_performance():
    # Performance validation  
    assert True
```

## Definition of Done
- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Performance acceptable
- [ ] Accessibility verified"""

    return f"Task completed: {task.description}"

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

# API Routes
@app.get("/")
async def root():
    return {"message": "VirtuAI Office API", "version": "1.0.0", "agents": len(agents_db)}

@app.get("/api/status")
async def get_status():
    return {
        "status": "healthy",
        "agents_count": len(agents_db),
        "active_tasks": len([t for t in tasks_db.values() if t.status == "in_progress"]),
        "completed_tasks": len([t for t in tasks_db.values() if t.status == "completed"]),
        "version": "1.0.0"
    }

@app.get("/api/agents", response_model=List[Agent])
async def get_agents():
    return list(agents_db.values())

@app.get("/api/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents_db[agent_id]

@app.post("/api/tasks", response_model=Task)
async def create_task(task: Task):
    task.id = str(uuid.uuid4())
    task.created_at = datetime.now()
    task.status = "pending"
    
    assigned_agent_id = assign_task_to_agent(task)
    task.assigned_agent = assigned_agent_id
    
    tasks_db[task.id] = task
    
    await manager.broadcast({
        "type": "task_created",
        "task_id": task.id,
        "title": task.title,
        "assigned_agent": agents_db[assigned_agent_id].name
    })
    
    asyncio.create_task(process_task_async(task.id))
    
    logger.info(f"Created task {task.id}: {task.title} -> {agents_db[assigned_agent_id].name}")
    return task

async def process_task_async(task_id: str):
    try:
        task = tasks_db[task_id]
        agent = agents_db[task.assigned_agent]
        
        task.status = "in_progress"
        await manager.broadcast({
            "type": "task_update",
            "task_id": task_id,
            "status": "in_progress",
            "agent": agent.name
        })
        
        output = await process_task_with_agent(task, agent)
        
        task.status = "completed"
        task.output = output
        task.completed_at = datetime.now()
        agent.tasks_completed += 1
        
        await manager.broadcast({
            "type": "task_completed",
            "task_id": task_id,
            "agent": agent.name,
            "title": task.title
        })
        
        logger.info(f"Completed task {task_id} with {agent.name}")
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        await manager.broadcast({
            "type": "task_failed",
            "task_id": task_id,
            "error": str(e)
        })
        logger.error(f"Task {task_id} failed: {e}")

@app.get("/api/tasks", response_model=List[Task])
async def get_tasks():
    return list(tasks_db.values())

@app.get("/api/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.on_event("startup")
async def startup_event():
    initialize_agents()
    logger.info("🚀 VirtuAI Office API server started")
    logger.info("👥 AI Development Team Ready:")
    for agent in agents_db.values():
        logger.info(f"   - {agent.name} ({agent.role})")

if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
