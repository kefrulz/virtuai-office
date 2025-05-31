# VirtuAI Office - Database Configuration and Models
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Float, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, scoped_session
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
import enum

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./virtuai_office.db")

# Create engine with optimized settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30
        },
        pool_pre_ping=True,
        echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
    )
else:
    # PostgreSQL settings
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
    )

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(SessionLocal)

# Base class for all models
Base = declarative_base()

# Enums
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskComplexity(str, enum.Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EPIC = "epic"

class TaskType(str, enum.Enum):
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    RESEARCH = "research"
    DESIGN = "design"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"

class AgentType(str, enum.Enum):
    PRODUCT_MANAGER = "product_manager"
    FRONTEND_DEVELOPER = "frontend_developer"
    BACKEND_DEVELOPER = "backend_developer"
    UI_UX_DESIGNER = "ui_ux_designer"
    QA_TESTER = "qa_tester"
    BOSS_AI = "boss_ai"

class CollaborationType(str, enum.Enum):
    INDEPENDENT = "independent"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    REVIEW = "review"

class OptimizationLevel(str, enum.Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

class ChipType(str, enum.Enum):
    M1 = "m1"
    M2 = "m2"
    M3 = "m3"
    M1_PRO = "m1_pro"
    M1_MAX = "m1_max"
    M1_ULTRA = "m1_ultra"
    M2_PRO = "m2_pro"
    M2_MAX = "m2_max"
    M2_ULTRA = "m2_ultra"
    M3_PRO = "m3_pro"
    M3_MAX = "m3_max"
    INTEL = "intel"
    UNKNOWN = "unknown"

# Utility functions for JSON fields
def generate_uuid():
    return str(uuid.uuid4())

def json_field_default():
    return "{}"

# Core Models
class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, index=True)
    type = Column(SQLEnum(AgentType), nullable=False, index=True)
    description = Column(Text)
    expertise = Column(Text, default=json_field_default)  # JSON string of expertise areas
    is_active = Column(Boolean, default=True, index=True)
    model_preference = Column(String(50), default="llama2:7b")
    max_concurrent_tasks = Column(Integer, default=3)
    
    # Performance tracking
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    avg_processing_time = Column(Float, default=0.0)
    quality_score = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="agent")
    workload_metrics = relationship("AgentWorkload", back_populates="agent")
    performance_metrics = relationship("PerformanceMetric", back_populates="agent")
    
    def __repr__(self):
        return f"<Agent(id='{self.id}', name='{self.name}', type='{self.type}')>"
    
    @property
    def expertise_list(self) -> List[str]:
        """Get expertise as a Python list"""
        try:
            return json.loads(self.expertise) if self.expertise else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    @expertise_list.setter
    def expertise_list(self, value: List[str]):
        """Set expertise from a Python list"""
        self.expertise = json.dumps(value) if value else "[]"
    
    @property
    def completion_rate(self) -> float:
        """Calculate task completion rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(20), default="active", index=True)
    
    # Project metadata
    tags = Column(Text, default="[]")  # JSON array of tags
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    estimated_hours = Column(Float)
    actual_hours = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    tasks = relationship("Task", back_populates="project")
    sprints = relationship("Sprint", back_populates="project")
    
    def __repr__(self):
        return f"<Project(id='{self.id}', name='{self.name}')>"
    
    @property
    def tag_list(self) -> List[str]:
        """Get tags as a Python list"""
        try:
            return json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            return []

class Sprint(Base):
    __tablename__ = "sprints"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    
    # Sprint details
    goal = Column(Text)
    status = Column(String(20), default="planned", index=True)  # planned, active, completed
    capacity_hours = Column(Float, default=40.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    project = relationship("Project", back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint")
    
    def __repr__(self):
        return f"<Sprint(id='{self.id}', name='{self.name}')>"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, index=True)
    
    # Task classification
    task_type = Column(SQLEnum(TaskType), default=TaskType.FEATURE)
    complexity = Column(SQLEnum(TaskComplexity), default=TaskComplexity.MEDIUM)
    
    # Assignment
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    project_id = Column(String, ForeignKey("projects.id"), index=True)
    sprint_id = Column(String, ForeignKey("sprints.id"), index=True)
    parent_task_id = Column(String, ForeignKey("tasks.id"), index=True)
    
    # AI-generated content
    output = Column(Text)
    quality_score = Column(Float)
    confidence_score = Column(Float)
    
    # Effort tracking
    estimated_effort = Column(Integer)  # Story points
    estimated_hours = Column(Float)
    actual_effort = Column(Integer)
    actual_hours = Column(Float)
    
    # AI analysis metadata
    keywords = Column(Text, default="[]")  # JSON array
    skill_requirements = Column(Text, default="[]")  # JSON array
    requires_collaboration = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    due_date = Column(DateTime)
    
    # Relationships
    agent = relationship("Agent", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    sprint = relationship("Sprint", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id])
    subtasks = relationship("Task")
    dependencies = relationship("TaskDependency", foreign_keys="TaskDependency.task_id")
    collaborations = relationship("TaskCollaboration", foreign_keys="TaskCollaboration.primary_task_id")
    performance_metrics = relationship("PerformanceMetric", back_populates="task")
    
    def __repr__(self):
        return f"<Task(id='{self.id}', title='{self.title[:50]}', status='{self.status}')>"
    
    @property
    def keywords_list(self) -> List[str]:
        """Get keywords as a Python list"""
        try:
            return json.loads(self.keywords) if self.keywords else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    @property
    def skill_requirements_list(self) -> List[str]:
        """Get skill requirements as a Python list"""
        try:
            return json.loads(self.skill_requirements) if self.skill_requirements else []
        except (json.JSONDecodeError, TypeError):
            return []

# Collaboration and Dependencies
class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    depends_on_task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    dependency_type = Column(String(20), default="blocks")  # blocks, informs, enhances
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TaskDependency(task='{self.task_id}', depends_on='{self.depends_on_task_id}')>"

class TaskCollaboration(Base):
    __tablename__ = "task_collaborations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    primary_task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    secondary_task_id = Column(String, ForeignKey("tasks.id"), index=True)
    collaboration_type = Column(SQLEnum(CollaborationType), nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending, active, completed
    
    # Collaboration metadata
    workflow_data = Column(Text, default=json_field_default)  # JSON workflow steps
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<TaskCollaboration(primary='{self.primary_task_id}', type='{self.collaboration_type}')>"

# Performance and Analytics
class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    
    # System metrics
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    memory_pressure = Column(String(20))
    thermal_state = Column(String(20))
    power_mode = Column(String(20))
    
    # AI performance
    model_name = Column(String(50))
    inference_speed = Column(Float)  # tokens/second
    model_load_time = Column(Float)
    context_length = Column(Integer)
    
    # Task performance
    processing_time = Column(Float)  # seconds
    quality_score = Column(Float)
    user_rating = Column(Integer)  # 1-5 stars
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="performance_metrics")
    task = relationship("Task", back_populates="performance_metrics")
    
    def __repr__(self):
        return f"<PerformanceMetric(agent='{self.agent_id}', task='{self.task_id}')>"

class AgentWorkload(Base):
    __tablename__ = "agent_workload"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    
    # Workload metrics
    current_tasks = Column(Integer, default=0)
    estimated_hours = Column(Float, default=0.0)
    actual_hours = Column(Float, default=0.0)
    performance_score = Column(Float, default=1.0)  # 0.0 to 2.0
    
    # Capacity planning
    max_concurrent_tasks = Column(Integer, default=3)
    preferred_task_types = Column(Text, default="[]")  # JSON array
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="workload_metrics")
    
    def __repr__(self):
        return f"<AgentWorkload(agent='{self.agent_id}', current_tasks={self.current_tasks})>"

# Boss AI and Decision Tracking
class BossDecision(Base):
    __tablename__ = "boss_decisions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    decision_type = Column(String(50), nullable=False, index=True)  # assignment, prioritization, collaboration
    
    # Decision context and reasoning
    context = Column(Text)  # JSON with decision context
    reasoning = Column(Text)  # AI reasoning for the decision
    outcome = Column(Text)   # JSON with decision outcome
    confidence = Column(Float)  # 0.0 to 1.0
    
    # Reference data
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    
    # Validation and feedback
    was_successful = Column(Boolean)
    user_feedback = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    validated_at = Column(DateTime)
    
    def __repr__(self):
        return f"<BossDecision(type='{self.decision_type}', confidence={self.confidence})>"

# Apple Silicon Optimization
class AppleSiliconProfile(Base):
    __tablename__ = "apple_silicon_profiles"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    chip_type = Column(SQLEnum(ChipType), nullable=False, index=True)
    memory_gb = Column(Integer, nullable=False)
    cpu_cores = Column(Integer, nullable=False)
    gpu_cores = Column(Integer)
    
    # Optimization settings
    optimization_level = Column(SQLEnum(OptimizationLevel), default=OptimizationLevel.BALANCED)
    preferred_models = Column(Text, default="[]")  # JSON array
    max_concurrent_tasks = Column(Integer, default=3)
    
    # Performance metrics
    avg_inference_speed = Column(Float, default=0.0)
    peak_memory_usage = Column(Float, default=0.0)
    thermal_throttling_events = Column(Integer, default=0)
    
    # Hardware specifications
    memory_bandwidth_gbps = Column(Float)
    max_power_watts = Column(Float)
    neural_engine = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_optimized = Column(DateTime, default=datetime.utcnow)
    last_benchmarked = Column(DateTime)
    
    def __repr__(self):
        return f"<AppleSiliconProfile(chip='{self.chip_type}', memory={self.memory_gb}GB)>"
    
    @property
    def preferred_models_list(self) -> List[str]:
        """Get preferred models as a Python list"""
        try:
            return json.loads(self.preferred_models) if self.preferred_models else []
        except (json.JSONDecodeError, TypeError):
            return []

# System Configuration and Settings
class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text)
    description = Column(Text)
    
    # Metadata
    config_type = Column(String(20), default="string")  # string, integer, float, boolean, json
    is_sensitive = Column(Boolean, default=False)
    requires_restart = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.key}')>"

# User Preferences and Sessions
class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_data = Column(Text, default=json_field_default)  # JSON session data
    
    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    
    def __repr__(self):
        return f"<UserSession(id='{self.id}', active={self.is_active})>"

# Database utility functions
def get_db() -> Session:
    """Get database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        return False

def seed_default_data():
    """Seed database with default data"""
    with get_db_session() as db:
        # Check if agents already exist
        if db.query(Agent).count() > 0:
            print("ℹ️ Database already contains data, skipping seeding")
            return
        
        # Create default agents
        agents_data = [
            {
                "name": "Alice Chen",
                "type": AgentType.PRODUCT_MANAGER,
                "description": "Senior Product Manager with expertise in user stories, requirements, and project planning",
                "expertise": json.dumps(["user stories", "requirements", "product roadmap", "stakeholder analysis", "project planning", "agile", "scrum"])
            },
            {
                "name": "Marcus Dev",
                "type": AgentType.FRONTEND_DEVELOPER,
                "description": "Senior Frontend Developer specializing in React, modern UI frameworks, and responsive design",
                "expertise": json.dumps(["react", "javascript", "typescript", "css", "html", "responsive design", "ui components", "state management", "testing"])
            },
            {
                "name": "Sarah Backend",
                "type": AgentType.BACKEND_DEVELOPER,
                "description": "Senior Backend Developer with expertise in Python, FastAPI, databases, and system architecture",
                "expertise": json.dumps(["python", "fastapi", "django", "postgresql", "mongodb", "rest apis", "authentication", "database design", "testing", "docker"])
            },
            {
                "name": "Luna Design",
                "type": AgentType.UI_UX_DESIGNER,
                "description": "Senior UI/UX Designer with expertise in user-centered design, wireframing, and design systems",
                "expertise": json.dumps(["ui design", "ux design", "wireframing", "prototyping", "design systems", "accessibility", "user research", "figma", "responsive design"])
            },
            {
                "name": "TestBot QA",
                "type": AgentType.QA_TESTER,
                "description": "Senior QA Engineer with expertise in test planning, automation, and quality assurance",
                "expertise": json.dumps(["test planning", "test automation", "manual testing", "pytest", "jest", "selenium", "api testing", "performance testing", "bug reporting"])
            }
        ]
        
        for agent_data in agents_data:
            agent = Agent(**agent_data)
            db.add(agent)
        
        # Create default system configurations
        default_configs = [
            {"key": "ollama_host", "value": "localhost:11434", "description": "Ollama service host"},
            {"key": "max_concurrent_tasks", "value": "3", "config_type": "integer", "description": "Maximum concurrent tasks per agent"},
            {"key": "default_model", "value": "llama2:7b", "description": "Default LLM model"},
            {"key": "enable_apple_silicon_optimization", "value": "true", "config_type": "boolean", "description": "Enable Apple Silicon optimizations"},
            {"key": "performance_monitoring", "value": "true", "config_type": "boolean", "description": "Enable performance monitoring"},
        ]
        
        for config_data in default_configs:
            config = SystemConfig(**config_data)
            db.add(config)
        
        print("✅ Default data seeded successfully")

def cleanup_old_data(days: int = 90):
    """Clean up old performance metrics and sessions"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    with get_db_session() as db:
        # Clean old performance metrics
        old_metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.timestamp < cutoff_date
        ).count()
        
        if old_metrics > 0:
            db.query(PerformanceMetric).filter(
                PerformanceMetric.timestamp < cutoff_date
            ).delete()
            print(f"🧹 Cleaned up {old_metrics} old performance metrics")
        
        # Clean expired sessions
        expired_sessions = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).count()
        
        if expired_sessions > 0:
            db.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow()
            ).delete()
            print(f"🧹 Cleaned up {expired_sessions} expired sessions")

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics"""
    with get_db_session() as db:
        stats = {
            "agents": db.query(Agent).count(),
            "projects": db.query(Project).count(),
            "tasks": db.query(Task).count(),
            "sprints": db.query(Sprint).count(),
            "performance_metrics": db.query(PerformanceMetric).count(),
            "boss_decisions": db.query(BossDecision).count(),
            "collaborations": db.query(TaskCollaboration).count(),
            "apple_silicon_profiles": db.query(AppleSiliconProfile).count(),
            "active_sessions": db.query(UserSession).filter(UserSession.is_active == True).count(),
        }
        
        # Task status breakdown
        for status in TaskStatus:
            stats[f"tasks_{status.value}"] = db.query(Task).filter(Task.status == status).count()
        
        # Agent performance summary
        agents = db.query(Agent).all()
        stats["agent_performance"] = [
            {
                "name": agent.name,
                "type": agent.type.value,
                "total_tasks": agent.total_tasks,
                "completion_rate": agent.completion_rate,
                "quality_score": agent.quality_score
            } for agent in agents
        ]
        
        return stats

# Migration utilities
def check_database_version() -> str:
    """Check current database schema version"""
    with get_db_session() as db:
        try:
            # Try to query a recently added column to determine version
            db.execute("SELECT chip_type FROM apple_silicon_profiles LIMIT 1")
            return "v1.0.0"
        except Exception:
            return "unknown"

def migrate_database():
    """Run database migrations"""
    current_version = check_database_version()
    print(f"Current database version: {current_version}")
    
    # Add migration logic here as needed
    # For now, just ensure all tables exist
    init_database()

if __name__ == "__main__":
    print("🗄️ VirtuAI Office Database Setup")
    print("=" * 40)
    
    # Initialize database
    if init_database():
        print("✅ Database initialized successfully")
        
        # Seed default data
        seed_default_data()
        
        # Show database stats
        stats = get_database_stats()
        print(f"\n📊 Database Statistics:")
        print(f"  Agents: {stats['agents']}")
        print(f"  Projects: {stats['projects']}")
        print(f"  Tasks: {stats['tasks']}")
        print(f"  Performance Metrics: {stats['performance_metrics']}")
        
        print(f"\n🎉 VirtuAI Office database is ready!")
    else:
        print("❌ Database setup failed!")
        exit(1)
