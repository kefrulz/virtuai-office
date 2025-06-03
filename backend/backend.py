# VirtuAI Office - Enhanced Backend with Project Workflow System
import asyncio
import json
import uuid
import zipfile
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import ollama
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey, Enum as SQLEnum, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import uuid as uuid_module

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite:///./virtuai_office.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enums
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AgentType(str, Enum):
    PRODUCT_MANAGER = "product_manager"
    FRONTEND_DEVELOPER = "frontend_developer"
    BACKEND_DEVELOPER = "backend_developer"
    UI_UX_DESIGNER = "ui_ux_designer"
    QA_TESTER = "qa_tester"

class ProjectStatus(str, Enum):
    CREATED = "created"
    BACKLOG_CREATED = "backlog_created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELIVERED = "delivered"

class TaskType(str, Enum):
    CLIENT_REQUEST = "client_request"
    BACKLOG_ITEM = "backlog_item"
    SUBTASK = "subtask"

# Database Models
class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(SQLEnum(AgentType), nullable=False)
    description = Column(Text)
    expertise = Column(Text)  # JSON string of expertise areas
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="agent")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    client_request = Column(Text)  # Original client request
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.CREATED)
    deliverable_path = Column(String)  # Path to final zip file
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    tasks = relationship("Task", back_populates="project")
    backlog_items = relationship("BacklogItem", back_populates="project")

class BacklogItem(Base):
    __tablename__ = "backlog_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    story_points = Column(Integer, default=3)
    acceptance_criteria = Column(Text)
    assigned_agent_type = Column(SQLEnum(AgentType))
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="backlog_items")
    tasks = relationship("Task", back_populates="backlog_item")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    task_type = Column(SQLEnum(TaskType), default=TaskType.SUBTASK)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Foreign keys
    agent_id = Column(String, ForeignKey("agents.id"))
    project_id = Column(String, ForeignKey("projects.id"))
    backlog_item_id = Column(String, ForeignKey("backlog_items.id"))
    parent_task_id = Column(String, ForeignKey("tasks.id"))
    
    # Generated content
    output = Column(Text)  # AI-generated output
    file_outputs = Column(Text)  # JSON array of generated files
    estimated_effort = Column(Integer)  # In hours
    actual_effort = Column(Integer)  # In hours
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    agent = relationship("Agent", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    backlog_item = relationship("BacklogItem", back_populates="tasks")
    parent_task = relationship("Task", remote_side="Task.id")

class Deliverable(Base):
    __tablename__ = "deliverables"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    client_request: str = Field(..., min_length=20)

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: Optional[str] = None
    task_type: TaskType = TaskType.SUBTASK

class BacklogItemResponse(BaseModel):
    id: str
    title: str
    description: str
    priority: TaskPriority
    story_points: int
    acceptance_criteria: Optional[str]
    assigned_agent_type: Optional[AgentType]
    order_index: int

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    client_request: str
    status: ProjectStatus
    backlog_items: List[BacklogItemResponse]
    created_at: datetime
    completed_at: Optional[datetime]

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    agent_id: Optional[str]
    agent_name: Optional[str]
    project_id: Optional[str]
    backlog_item_id: Optional[str]
    output: Optional[str]
    file_outputs: Optional[List[str]]
    estimated_effort: Optional[int]
    actual_effort: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class AgentResponse(BaseModel):
    id: str
    name: str
    type: AgentType
    description: str
    expertise: List[str]
    is_active: bool
    task_count: int
    completed_tasks: int

# Enhanced AI Agent Classes
class BaseAgent:
    def __init__(self, name: str, agent_type: AgentType, description: str, expertise: List[str]):
        self.name = name
        self.type = agent_type
        self.description = description
        self.expertise = expertise
        self.model = "llama2:7b"
    
    def get_system_prompt(self) -> str:
        return f"You are {self.name}, a {self.type.value.replace('_', ' ')}."
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        try:
            prompt = self._build_task_prompt(task)
            response = await self._call_ollama(prompt)
            
            # Parse response for file outputs if applicable
            file_outputs = self._extract_file_outputs(response)
            
            return {
                "output": response,
                "file_outputs": file_outputs
            }
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            raise
    
    def _build_task_prompt(self, task: Task) -> str:
        system_prompt = self.get_system_prompt()
        
        prompt = f"""{system_prompt}

Task: {task.title}
Description: {task.description}
Priority: {task.priority.value}

Please provide a detailed response that addresses this task according to your expertise.
If this task requires creating files, format your response with clear file sections using:

```filename: path/to/file.ext
[file content here]
```

Format your response professionally and include specific, actionable outputs.
"""
        return prompt
    
    def _extract_file_outputs(self, response: str) -> List[Dict[str, str]]:
        """Extract file outputs from agent response"""
        import re
        
        file_pattern = r'```filename:\s*([^\n]+)\n(.*?)```'
        matches = re.findall(file_pattern, response, re.DOTALL)
        
        files = []
        for filename, content in matches:
            files.append({
                "filename": filename.strip(),
                "content": content.strip()
            })
        
        return files
    
    async def _call_ollama(self, prompt: str) -> str:
        try:
            response = await asyncio.to_thread(
                ollama.generate,
                model=self.model,
                prompt=prompt,
                stream=False
            )
            return response['response']
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return f"Error generating response: {str(e)}"

class AliceChenAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Alice Chen",
            agent_type=AgentType.PRODUCT_MANAGER,
            description="Senior Product Manager specializing in project breakdown and backlog creation",
            expertise=["user stories", "requirements", "project planning", "backlog creation", "stakeholder analysis"]
        )
    
    def get_system_prompt(self) -> str:
        return """You are Alice Chen, a Senior Product Manager with expertise in breaking down complex projects into manageable tasks.

Your role in the VirtuAI Office workflow:
1. Analyze client requests and understand project requirements
2. Break down projects into logical, manageable backlog items
3. Create detailed user stories with acceptance criteria
4. Assign appropriate agent types to each backlog item
5. Prioritize backlog items based on dependencies and importance

When creating a project backlog, provide your response in this JSON format:
{
  "project_analysis": "Brief analysis of the project",
  "backlog_items": [
    {
      "title": "Backlog item title",
      "description": "Detailed description",
      "acceptance_criteria": "Clear acceptance criteria",
      "assigned_agent_type": "frontend_developer|backend_developer|ui_ux_designer|qa_tester",
      "priority": "low|medium|high|urgent",
      "story_points": 1-13,
      "order_index": 0
    }
  ]
}

Be thorough and consider all aspects: frontend, backend, design, testing, and documentation."""

    async def create_project_backlog(self, client_request: str, project_name: str) -> Dict[str, Any]:
        """Create a project backlog from client request"""
        prompt = f"""
Client Request: {client_request}
Project Name: {project_name}

Analyze this client request and create a comprehensive project backlog. Break down the project into 5-12 manageable backlog items that cover all aspects of development.

Consider:
- Frontend components and UI elements
- Backend APIs and data models
- Design and user experience
- Testing and quality assurance
- Documentation and deployment

Provide your response in the specified JSON format.
"""
        
        response = await self._call_ollama(prompt)
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Alice's response: {response}")
            # Fallback to basic backlog
            return self._create_fallback_backlog(client_request)
    
    def _create_fallback_backlog(self, client_request: str) -> Dict[str, Any]:
        """Create a basic fallback backlog if JSON parsing fails"""
        return {
            "project_analysis": f"Creating basic backlog for: {client_request}",
            "backlog_items": [
                {
                    "title": "Project Setup and Architecture",
                    "description": "Set up basic project structure and choose technology stack",
                    "acceptance_criteria": "Project initialized with proper folder structure",
                    "assigned_agent_type": "backend_developer",
                    "priority": "high",
                    "story_points": 3,
                    "order_index": 0
                },
                {
                    "title": "Core Functionality Implementation",
                    "description": "Implement the main features as requested",
                    "acceptance_criteria": "Core functionality working as specified",
                    "assigned_agent_type": "frontend_developer",
                    "priority": "high",
                    "story_points": 8,
                    "order_index": 1
                },
                {
                    "title": "UI/UX Design and Styling",
                    "description": "Create attractive and user-friendly interface",
                    "acceptance_criteria": "Application has polished, professional appearance",
                    "assigned_agent_type": "ui_ux_designer",
                    "priority": "medium",
                    "story_points": 5,
                    "order_index": 2
                },
                {
                    "title": "Testing and Quality Assurance",
                    "description": "Ensure application works correctly and handle edge cases",
                    "acceptance_criteria": "Application tested and working without critical bugs",
                    "assigned_agent_type": "qa_tester",
                    "priority": "medium",
                    "story_points": 3,
                    "order_index": 3
                }
            ]
        }

class MarcusDevAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Marcus Dev",
            agent_type=AgentType.FRONTEND_DEVELOPER,
            description="Senior Frontend Developer specializing in complete application development",
            expertise=["html", "css", "javascript", "react", "responsive design", "game development", "web applications"]
        )
    
    def get_system_prompt(self) -> str:
        return """You are Marcus Dev, a Senior Frontend Developer who creates complete, working applications.

When given a task, you provide:
1. Complete HTML files with proper structure
2. CSS for styling and animations
3. JavaScript for functionality and interactivity
4. All necessary code to make the application work
5. Clear file organization and comments

Always create working, complete code that can be directly used. Include all necessary HTML, CSS, and JavaScript in separate files or as indicated by the task requirements.

Format your response with clear file sections:
```filename: index.html
[complete HTML content]
```

```filename: style.css  
[complete CSS content]
```

```filename: script.js
[complete JavaScript content]
```

Make sure your code is production-ready, well-commented, and follows best practices."""

class SarahBackendAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Sarah Backend",
            agent_type=AgentType.BACKEND_DEVELOPER,
            description="Senior Backend Developer creating APIs and server-side logic",
            expertise=["python", "fastapi", "nodejs", "databases", "apis", "server architecture", "data models"]
        )

class LunaDesignAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Luna Design",
            agent_type=AgentType.UI_UX_DESIGNER,
            description="Senior UI/UX Designer creating beautiful and functional interfaces",
            expertise=["ui design", "ux design", "css styling", "responsive design", "color theory", "typography"]
        )

class TestBotQAAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="TestBot QA",
            agent_type=AgentType.QA_TESTER,
            description="Senior QA Engineer ensuring quality and testing applications",
            expertise=["testing", "quality assurance", "bug detection", "test automation", "validation"]
        )

# Agent Manager
class AgentManager:
    def __init__(self):
        self.agents = {
            AgentType.PRODUCT_MANAGER: AliceChenAgent(),
            AgentType.FRONTEND_DEVELOPER: MarcusDevAgent(),
            AgentType.BACKEND_DEVELOPER: SarahBackendAgent(),
            AgentType.UI_UX_DESIGNER: LunaDesignAgent(),
            AgentType.QA_TESTER: TestBotQAAgent(),
        }
    
    def get_agent(self, agent_type: AgentType) -> BaseAgent:
        return self.agents.get(agent_type)

# Project Workflow Manager
class ProjectWorkflowManager:
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
    
    async def create_project_workflow(self, project_data: ProjectCreate, db: Session) -> Project:
        """Create project and initiate workflow"""
        
        # Create project
        project = Project(
            name=project_data.name,
            description=project_data.description,
            client_request=project_data.client_request,
            status=ProjectStatus.CREATED
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Get Alice Chen to create backlog
        alice = self.agent_manager.get_agent(AgentType.PRODUCT_MANAGER)
        backlog_data = await alice.create_project_backlog(
            project_data.client_request,
            project_data.name
        )
        
        # Create backlog items
        for item_data in backlog_data.get("backlog_items", []):
            backlog_item = BacklogItem(
                project_id=project.id,
                title=item_data["title"],
                description=item_data["description"],
                acceptance_criteria=item_data.get("acceptance_criteria"),
                assigned_agent_type=AgentType(item_data["assigned_agent_type"]),
                priority=TaskPriority(item_data["priority"]),
                story_points=item_data["story_points"],
                order_index=item_data["order_index"]
            )
            db.add(backlog_item)
        
        project.status = ProjectStatus.BACKLOG_CREATED
        db.commit()
        
        return project
    
    async def execute_project_backlog(self, project_id: str, db: Session):
        """Execute all backlog items in order"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project.status = ProjectStatus.IN_PROGRESS
        db.commit()
        
        # Get backlog items in order
        backlog_items = db.query(BacklogItem).filter(
            BacklogItem.project_id == project_id
        ).order_by(BacklogItem.order_index).all()
        
        project_files = {}
        
        for backlog_item in backlog_items:
            # Create task for backlog item
            task = Task(
                title=backlog_item.title,
                description=backlog_item.description,
                task_type=TaskType.BACKLOG_ITEM,
                priority=backlog_item.priority,
                project_id=project_id,
                backlog_item_id=backlog_item.id,
                agent_id=self._get_agent_id_by_type(backlog_item.assigned_agent_type, db)
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # Process task
            await self._process_backlog_task(task, project_files, db)
        
        # Create final deliverable
        await self._create_project_deliverable(project, project_files, db)
        
        project.status = ProjectStatus.COMPLETED
        project.completed_at = datetime.utcnow()
        db.commit()
    
    def _get_agent_id_by_type(self, agent_type: AgentType, db: Session) -> str:
        """Get agent ID by type"""
        agent = db.query(Agent).filter(Agent.type == agent_type).first()
        return agent.id if agent else None
    
    async def _process_backlog_task(self, task: Task, project_files: Dict, db: Session):
        """Process a single backlog task"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.utcnow()
            db.commit()
            
            # Get agent and process task
            agent = self.agent_manager.get_agent(task.agent.type)
            result = await agent.process_task(task)
            
            # Store output and files
            task.output = result["output"]
            task.file_outputs = json.dumps(result["file_outputs"])
            
            # Add files to project collection
            for file_data in result["file_outputs"]:
                project_files[file_data["filename"]] = file_data["content"]
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.output = f"Error: {str(e)}"
            db.commit()
            raise
    
    async def _create_project_deliverable(self, project: Project, project_files: Dict, db: Session):
        """Create final zip deliverable"""
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                project_dir = os.path.join(temp_dir, project.name.replace(" ", "_"))
                os.makedirs(project_dir, exist_ok=True)
                
                # Write all files
                for filename, content in project_files.items():
                    file_path = os.path.join(project_dir, filename)
                    
                    # Create subdirectories if needed
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                # Create README
                readme_content = f"""# {project.name}

{project.description}

## Client Request
{project.client_request}

## Generated Files
{chr(10).join([f"- {filename}" for filename in project_files.keys()])}

## How to Use
1. Open index.html in a web browser
2. Or follow specific instructions in individual files

Generated by VirtuAI Office on {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}
"""
                
                with open(os.path.join(project_dir, "README.md"), 'w') as f:
                    f.write(readme_content)
                
                # Create zip file
                zip_filename = f"{project.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_path = os.path.join("deliverables", zip_filename)
                
                # Ensure deliverables directory exists
                os.makedirs("deliverables", exist_ok=True)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(project_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                # Store deliverable info
                deliverable = Deliverable(
                    project_id=project.id,
                    file_path=zip_path,
                    file_name=zip_filename,
                    file_size=os.path.getsize(zip_path)
                )
                db.add(deliverable)
                
                project.deliverable_path = zip_path
                project.status = ProjectStatus.DELIVERED
                db.commit()
                
        except Exception as e:
            logger.error(f"Error creating deliverable: {e}")
            raise

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

# Create FastAPI app
app = FastAPI(
    title="VirtuAI Office API",
    description="Complete AI development team with project workflow",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
agent_manager = AgentManager()
workflow_manager = ProjectWorkflowManager(agent_manager)
connection_manager = ConnectionManager()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)

# API Endpoints

@app.get("/api/projects", response_model=List[ProjectResponse])
async def get_all_projects(db: Session = Depends(get_db)):
    """Get all projects"""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    
    result = []
    for project in projects:
        backlog_items = db.query(BacklogItem).filter(
            BacklogItem.project_id == project.id
        ).order_by(BacklogItem.order_index).all()
        
        backlog_response = [
            BacklogItemResponse(
                id=item.id,
                title=item.title,
                description=item.description,
                priority=item.priority,
                story_points=item.story_points,
                acceptance_criteria=item.acceptance_criteria,
                assigned_agent_type=item.assigned_agent_type,
                order_index=item.order_index
            ) for item in backlog_items
        ]
        
        result.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            client_request=project.client_request,
            status=project.status,
            backlog_items=backlog_response,
            created_at=project.created_at,
            completed_at=project.completed_at
        ))
    
    return result

@app.get("/api/projects/{project_id}/deliverable")
async def download_project_deliverable(project_id: str, db: Session = Depends(get_db)):
    """Download project deliverable zip file"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.deliverable_path or not os.path.exists(project.deliverable_path):
        raise HTTPException(status_code=404, detail="Deliverable not ready yet")
    
    deliverable = db.query(Deliverable).filter(Deliverable.project_id == project_id).first()
    
    return FileResponse(
        path=project.deliverable_path,
        filename=deliverable.file_name if deliverable else f"{project.name}.zip",
        media_type='application/zip'
    )

@app.get("/api/projects/{project_id}/status")
async def get_project_status(project_id: str, db: Session = Depends(get_db)):
    """Get detailed project status including task progress"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all tasks for this project
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    task_status_counts = {
        "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
        "in_progress": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
        "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
        "failed": len([t for t in tasks if t.status == TaskStatus.FAILED])
    }
    
    total_tasks = len(tasks)
    completion_percentage = (task_status_counts["completed"] / total_tasks * 100) if total_tasks > 0 else 0
    
    return {
        "project_id": project.id,
        "project_status": project.status,
        "completion_percentage": round(completion_percentage, 2),
        "task_counts": task_status_counts,
        "total_tasks": total_tasks,
        "deliverable_ready": project.deliverable_path is not None and os.path.exists(project.deliverable_path) if project.deliverable_path else False,
        "created_at": project.created_at,
        "completed_at": project.completed_at
    }

@app.get("/api/agents", response_model=List[AgentResponse])
async def get_agents(db: Session = Depends(get_db)):
    """Get all available agents"""
    # Ensure all agents exist in database
    for agent_type, agent in agent_manager.agents.items():
        existing = db.query(Agent).filter(Agent.type == agent_type).first()
        if not existing:
            db_agent = Agent(
                name=agent.name,
                type=agent.type,
                description=agent.description,
                expertise=json.dumps(agent.expertise)
            )
            db.add(db_agent)
    
    db.commit()
    
    # Get agents with task counts
    agents = db.query(Agent).all()
    result = []
    
    for agent in agents:
        task_count = db.query(Task).filter(Task.agent_id == agent.id).count()
        completed_tasks = db.query(Task).filter(
            Task.agent_id == agent.id,
            Task.status == TaskStatus.COMPLETED
        ).count()
        
        result.append(AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type,
            description=agent.description,
            expertise=json.loads(agent.expertise) if agent.expertise else [],
            is_active=agent.is_active,
            task_count=task_count,
            completed_tasks=completed_tasks
        ))
    
    return result

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new task (legacy endpoint for backwards compatibility)"""
    
    # Create task in database
    task = Task(
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type,
        priority=task_data.priority,
        project_id=task_data.project_id
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Add background task to process it
    background_tasks.add_task(process_single_task, task.id, db)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        agent_id=task.agent_id,
        agent_name=None,
        project_id=task.project_id,
        backlog_item_id=task.backlog_item_id,
        output=task.output,
        file_outputs=json.loads(task.file_outputs) if task.file_outputs else None,
        estimated_effort=task.estimated_effort,
        actual_effort=task.actual_effort,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    )

@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    project_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get tasks with optional filtering"""
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
    
    result = []
    for task in tasks:
        agent_name = None
        if task.agent:
            agent_name = task.agent.name
        
        result.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            status=task.status,
            priority=task.priority,
            agent_id=task.agent_id,
            agent_name=agent_name,
            project_id=task.project_id,
            backlog_item_id=task.backlog_item_id,
            output=task.output,
            file_outputs=json.loads(task.file_outputs) if task.file_outputs else None,
            estimated_effort=task.estimated_effort,
            actual_effort=task.actual_effort,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at
        ))
    
    return result

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    agent_name = None
    if task.agent:
        agent_name = task.agent.name
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        agent_id=task.agent_id,
        agent_name=agent_name,
        project_id=task.project_id,
        backlog_item_id=task.backlog_item_id,
        output=task.output,
        file_outputs=json.loads(task.file_outputs) if task.file_outputs else None,
        estimated_effort=task.estimated_effort,
        actual_effort=task.actual_effort,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await connection_manager.send_personal_message(f"Received: {data}", websocket)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

@app.post("/api/demo/create-game-project")
async def create_demo_game_project(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a demo game project for testing"""
    
    demo_project = ProjectCreate(
        name="Snake Game",
        description="A classic Snake game built with HTML5, CSS3, and JavaScript",
        client_request="Create a simple Snake game in JavaScript that runs in the browser. The game should have a snake that moves around the screen, eats food to grow longer, and ends when the snake hits the walls or itself. Include score tracking and basic styling to make it look professional."
    )
    
    try:
        project = await workflow_manager.create_project_workflow(demo_project, db)
        background_tasks.add_task(workflow_manager.execute_project_backlog, project.id, db)
        
        return {
            "message": "Demo Snake game project created successfully!",
            "project_id": project.id,
            "status": "Backlog created, starting development..."
        }
        
    except Exception as e:
        logger.error(f"Demo project creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task processing functions
async def process_single_task(task_id: str, db: Session):
    """Process a single task (legacy function)"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        
        # Auto-assign agent based on task type or description
        if not task.agent_id:
            agent_type = determine_agent_type(task.description)
            agent = db.query(Agent).filter(Agent.type == agent_type).first()
            if agent:
                task.agent_id = agent.id
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Process task with appropriate agent
        if task.agent:
            agent = agent_manager.get_agent(task.agent.type)
            if agent:
                result = await agent.process_task(task)
                
                task.output = result["output"]
                task.file_outputs = json.dumps(result["file_outputs"])
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                
                # Calculate effort
                if task.started_at and task.completed_at:
                    duration_hours = (task.completed_at - task.started_at).total_seconds() / 3600
                    task.actual_effort = max(1, int(duration_hours))
                
                db.commit()
                
                # Broadcast completion
                await connection_manager.broadcast(json.dumps({
                    "type": "task_completed",
                    "task_id": task_id,
                    "agent_name": agent.name
                }))
        
    except Exception as e:
        logger.error(f"Task processing failed: {e}")
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.output = f"Error: {str(e)}"
            db.commit()

def determine_agent_type(description: str) -> AgentType:
    """Determine appropriate agent type based on task description"""
    description_lower = description.lower()
    
    if any(word in description_lower for word in ["frontend", "ui", "interface", "react", "html", "css", "javascript"]):
        return AgentType.FRONTEND_DEVELOPER
    elif any(word in description_lower for word in ["backend", "api", "database", "server", "python"]):
        return AgentType.BACKEND_DEVELOPER
    elif any(word in description_lower for word in ["design", "mockup", "wireframe", "style", "color", "layout"]):
        return AgentType.UI_UX_DESIGNER
    elif any(word in description_lower for word in ["test", "testing", "qa", "quality", "bug", "validation"]):
        return AgentType.QA_TESTER
    elif any(word in description_lower for word in ["requirements", "story", "plan", "project", "backlog"]):
        return AgentType.PRODUCT_MANAGER
    else:
        return AgentType.FRONTEND_DEVELOPER  # Default

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("🚀 VirtuAI Office Enhanced Backend starting up...")
    
    # Test Ollama connection
    try:
        models = ollama.list()
        logger.info(f"✅ Ollama connected, {len(models.get('models', []))} models available")
    except Exception as e:
        logger.warning(f"⚠️ Ollama connection failed: {e}")
        logger.info("Install Ollama and run 'ollama pull llama2:7b' to enable AI features")
    
    # Initialize agents in database
    db = SessionLocal()
    try:
        for agent_type, agent in agent_manager.agents.items():
            existing = db.query(Agent).filter(Agent.type == agent_type).first()
            if not existing:
                db_agent = Agent(
                    name=agent.name,
                    type=agent.type,
                    description=agent.description,
                    expertise=json.dumps(agent.expertise)
                )
                db.add(db_agent)
                logger.info(f"✅ Initialized agent: {agent.name}")
        
        db.commit()
        logger.info(f"✅ {len(agent_manager.agents)} AI agents ready")
        
        # Ensure deliverables directory exists
        os.makedirs("deliverables", exist_ok=True)
        logger.info("✅ Deliverables directory ready")
        
    finally:
        db.close()
    
    logger.info("🎉 VirtuAI Office Enhanced Backend ready!")
    logger.info("Features enabled:")
    logger.info("  • Project workflow with backlog creation")
    logger.info("  • Alice Chen automatic project breakdown")
    logger.info("  • Complete deliverable zip file generation")
    logger.info("  • Real-time project progress tracking")
    logger.info("  • File-based code generation")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )get("/api/status")
async def get_status():
    """Get API status and health check"""
    try:
        models = ollama.list()
        ollama_status = "connected"
        available_models = [model['name'] for model in models.get('models', [])]
    except Exception as e:
        ollama_status = f"error: {str(e)}"
        available_models = []
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ollama_status": ollama_status,
        "available_models": available_models,
        "agents_count": len(agent_manager.agents),
        "workflow_enabled": True
    }

@app.post("/api/projects/create-workflow", response_model=ProjectResponse)
async def create_project_workflow(
    project_data: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create project and generate backlog with Alice Chen"""
    
    try:
        # Create project and backlog
        project = await workflow_manager.create_project_workflow(project_data, db)
        
        # Start execution in background
        background_tasks.add_task(workflow_manager.execute_project_backlog, project.id, db)
        
        # Get backlog items for response
        backlog_items = db.query(BacklogItem).filter(
            BacklogItem.project_id == project.id
        ).order_by(BacklogItem.order_index).all()
        
        backlog_response = [
            BacklogItemResponse(
                id=item.id,
                title=item.title,
                description=item.description,
                priority=item.priority,
                story_points=item.story_points,
                acceptance_criteria=item.acceptance_criteria,
                assigned_agent_type=item.assigned_agent_type,
                order_index=item.order_index
            ) for item in backlog_items
        ]
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            client_request=project.client_request,
            status=project.status,
            backlog_items=backlog_response,
            created_at=project.created_at,
            completed_at=project.completed_at
        )
        
    except Exception as e:
        logger.error(f"Project workflow creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get project details with backlog"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    backlog_items = db.query(BacklogItem).filter(
        BacklogItem.project_id == project_id
    ).order_by(BacklogItem.order_index).all()
    
    backlog_response = [
        BacklogItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            priority=item.priority,
            story_points=item.story_points,
            acceptance_criteria=item.acceptance_criteria,
            assigned_agent_type=item.assigned_agent_type,
            order_index=item.order_index
        ) for item in backlog_items
    ]
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        client_request=project.client_request,
        status=project.status,
        backlog_items=backlog_response,
        created_at=project.created_at,
        completed_at=project.completed_at
    )

@app.
