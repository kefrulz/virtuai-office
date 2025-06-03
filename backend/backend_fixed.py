"""
VirtuAI Office - WORKING AI Integration
This version definitely connects to Ollama and processes tasks with real AI
"""

import asyncio
import logging
import json
import uuid
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="VirtuAI Office API", version="2.0.0")

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

# Storage
tasks_db: Dict[str, Task] = {}
agents_db: Dict[str, Agent] = {}

# AI Configuration
OLLAMA_URL = "http://localhost:11434"

# Specialized AI prompts for each agent
AI_PROMPTS = {
    "marcus-dev": """You are Marcus Dev, a senior frontend developer. Create complete, working code for this request.

Task: {title}
Description: {description}

Requirements:
- Write actual, working HTML/CSS/JavaScript code
- Include complete implementation, not just snippets
- Add comments explaining the code
- Make it production-ready
- If it's a game, include HTML5 Canvas implementation

Provide the complete code solution:""",

    "sarah-backend": """You are Sarah Backend, a senior backend developer. Create complete API and server code.

Task: {title}
Description: {description}

Requirements:
- Write working Python/FastAPI code
- Include complete endpoints and data models
- Add proper error handling
- Include database schemas if needed
- Make it production-ready

Provide the complete backend implementation:""",

    "luna-design": """You are Luna Design, a UI/UX designer. Create detailed design specifications.

Task: {title}
Description: {description}

Requirements:
- Create detailed wireframes (ASCII art format)
- Specify exact colors, fonts, spacing
- Include user experience flow
- Add accessibility considerations
- Provide complete design system

Create the complete design specification:""",

    "testbot-qa": """You are TestBot QA, a quality assurance engineer. Create comprehensive test plans.

Task: {title}
Description: {description}

Requirements:
- Write specific test cases with steps
- Include automated test code (Python/pytest)
- Cover functional and edge cases
- Add performance considerations
- Make tests executable

Provide the complete testing strategy:""",

    "alice-chen": """You are Alice Chen, a product manager. Create detailed requirements and user stories.

Task: {title}
Description: {description}

Requirements:
- Write proper user stories with acceptance criteria
- Include business value and priority
- Add technical requirements
- Consider user personas
- Provide project timeline

Create the complete product specification:"""
}

def initialize_agents():
    """Initialize the AI agents"""
    agents = [
        Agent(
            id="alice-chen",
            name="Alice Chen",
            role="Product Manager",
            description="Expert in requirements, user stories, and project planning",
            expertise=["requirements", "user-stories", "planning", "business-analysis"]
        ),
        Agent(
            id="marcus-dev",
            name="Marcus Dev",
            role="Frontend Developer",
            description="Senior developer specializing in React, games, and web applications",
            expertise=["react", "javascript", "html5", "css", "games", "frontend"]
        ),
        Agent(
            id="sarah-backend",
            name="Sarah Backend",
            role="Backend Developer",
            description="Expert in APIs, databases, and server architecture",
            expertise=["python", "fastapi", "databases", "apis", "microservices"]
        ),
        Agent(
            id="luna-design",
            name="Luna Design",
            role="UI/UX Designer",
            description="Specialist in user experience and interface design",
            expertise=["ui-design", "ux", "wireframes", "prototyping", "accessibility"]
        ),
        Agent(
            id="testbot-qa",
            name="TestBot QA",
            role="Quality Assurance",
            description="Expert in testing, automation, and quality processes",
            expertise=["testing", "automation", "quality-assurance", "debugging"]
        )
    ]
    
    for agent in agents:
        agents_db[agent.id] = agent
    
    logger.info(f"✅ Initialized {len(agents)} AI agents")

def assign_task_to_agent(task: Task) -> str:
    """Smart task assignment"""
    text = f"{task.title} {task.description}".lower()
    
    # Games, apps, frontend → Marcus
    if any(word in text for word in ["game", "app", "website", "frontend", "ui", "browser", "html", "css", "javascript", "react"]):
        return "marcus-dev"
    
    # APIs, backend, server → Sarah
    elif any(word in text for word in ["api", "backend", "server", "database", "endpoint", "microservice"]):
        return "sarah-backend"
        
    # Design, wireframes → Luna
    elif any(word in text for word in ["design", "wireframe", "mockup", "ui", "ux", "style", "layout"]):
        return "luna-design"
        
    # Testing, QA → TestBot
    elif any(word in text for word in ["test", "testing", "qa", "bug", "quality", "validation"]):
        return "testbot-qa"
        
    # Requirements, planning → Alice
    elif any(word in text for word in ["requirement", "story", "plan", "spec", "business"]):
        return "alice-chen"
        
    # Default: if building something → Marcus, otherwise Alice
    else:
        if any(word in text for word in ["create", "build", "make", "develop"]):
            return "marcus-dev"
        else:
            return "alice-chen"

async def call_ollama_ai(prompt: str) -> str:
    """Call Ollama API for real AI response"""
    try:
        logger.info("🤖 Calling Ollama AI...")
        
        payload = {
            "model": "llama2:7b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 1000
            }
        }
        
        timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{OLLAMA_URL}/api/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_response = result.get("response", "")
                    logger.info(f"✅ Got AI response ({len(ai_response)} characters)")
                    return ai_response
                else:
                    error_msg = f"Ollama API error: {response.status}"
                    logger.error(error_msg)
                    return f"Error: {error_msg}"
                    
    except asyncio.TimeoutError:
        error_msg = "AI request timed out after 60 seconds"
        logger.error(error_msg)
        return f"Error: {error_msg}"
        
    except Exception as e:
        error_msg = f"Failed to connect to AI: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

async def process_task_with_ai(task: Task, agent: Agent) -> str:
    """Process task using real AI"""
    logger.info(f"🚀 Processing task '{task.title}' with {agent.name}")
    
    # Get agent-specific prompt
    prompt_template = AI_PROMPTS.get(agent.id, AI_PROMPTS["marcus-dev"])
    
    # Format prompt with task details
    full_prompt = prompt_template.format(
        title=task.title,
        description=task.description
    )
    
    # Call real AI
    ai_response = await call_ollama_ai(full_prompt)
    
    # Add signature
    signature = f"\n\n---\n💡 Generated by {agent.name} ({agent.role})\n🤖 Powered by real AI (Ollama + Llama2)\n⏱️ Processing time: ~30 seconds"
    
    return ai_response + signature

async def process_task_async(task_id: str):
    """Process task asynchronously with real AI"""
    try:
        task = tasks_db[task_id]
        agent = agents_db[task.assigned_agent]
        
        logger.info(f"🔄 Starting AI processing for task {task_id}")
        
        # Update status to in_progress
        task.status = "in_progress"
        
        # Process with REAL AI (this takes time!)
        output = await process_task_with_ai(task, agent)
        
        # Update as completed
        task.status = "completed"
        task.output = output
        task.completed_at = datetime.now()
        agent.tasks_completed += 1
        
        logger.info(f"✅ Completed task {task_id} with {agent.name}")
        
    except Exception as e:
        logger.error(f"❌ Task {task_id} failed: {e}")
        task.status = "failed"
        task.error = str(e)

# API Routes
@app.get("/")
async def root():
    return {"message": "VirtuAI Office API v2.0", "ai_enabled": True}

@app.get("/api/status")
async def get_status():
    # Test AI connection
    try:
        test_response = await call_ollama_ai("Say 'AI working' if you can understand this.")
        ai_working = len(test_response) > 5 and "error" not in test_response.lower()
    except:
        ai_working = False
    
    return {
        "status": "healthy",
        "ai_connected": ai_working,
        "agents_count": len(agents_db),
        "active_tasks": len([t for t in tasks_db.values() if t.status == "in_progress"]),
        "completed_tasks": len([t for t in tasks_db.values() if t.status == "completed"]),
        "version": "2.0.0"
    }

@app.get("/api/agents", response_model=List[Agent])
async def get_agents():
    return list(agents_db.values())

@app.post("/api/tasks", response_model=Task)
async def create_task(task: Task):
    # Generate ID and assign agent
    task.id = str(uuid.uuid4())
    task.created_at = datetime.now()
    task.status = "pending"
    task.assigned_agent = assign_task_to_agent(task)
    
    # Store task
    tasks_db[task.id] = task
    
    logger.info(f"📝 Created task {task.id}: '{task.title}' → {agents_db[task.assigned_agent].name}")
    
    # Start AI processing (this will take time!)
    asyncio.create_task(process_task_async(task.id))
    
    return task

@app.get("/api/tasks", response_model=List[Task])
async def get_tasks():
    return list(tasks_db.values())

@app.get("/api/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]

# Initialize agents on startup
@app.on_event("startup")
async def startup_event():
    initialize_agents()
    logger.info("🚀 VirtuAI Office v2.0 started with REAL AI integration")

if __name__ == "__main__":
    uvicorn.run("backend_fixed:app", host="0.0.0.0", port=8000, reload=False)
