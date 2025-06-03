# Enhanced Alice Chen Agent - Product Manager with Project Breakdown Capabilities

import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from ..workflow.task_breakdown import TaskBreakdownEngine
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AliceChenAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Alice Chen",
            agent_type="product_manager",
            description="Senior Product Manager with expertise in project breakdown, user stories, and technical planning",
            expertise=[
                "project breakdown", "user stories", "requirements analysis",
                "technical planning", "task decomposition", "project roadmap",
                "acceptance criteria", "stakeholder analysis", "agile methodology",
                "backlog management", "epic creation", "sprint planning"
            ]
        )
        self.task_breakdown_engine = TaskBreakdownEngine()
        self.project_templates = self._load_project_templates()
    
    def _load_project_templates(self) -> Dict[str, Any]:
        """Load project templates for different types of applications"""
        return {
            "game": {
                "common_tasks": [
                    "Set up project structure",
                    "Create main game loop",
                    "Implement game mechanics",
                    "Add user interface",
                    "Implement scoring system",
                    "Add sound effects",
                    "Create game assets",
                    "Implement game over logic",
                    "Add responsive design",
                    "Write game instructions",
                    "Test gameplay",
                    "Optimize performance"
                ],
                "file_structure": ["index.html", "game.js", "styles.css", "assets/", "README.md"],
                "agents": {
                    "frontend_developer": ["HTML structure", "JavaScript game logic", "DOM manipulation"],
                    "ui_ux_designer": ["Game UI design", "Visual styling", "User experience"],
                    "qa_tester": ["Game testing", "Performance testing", "User acceptance testing"]
                }
            },
            "web_app": {
                "common_tasks": [
                    "Set up project architecture",
                    "Create database schema",
                    "Implement authentication",
                    "Build frontend components",
                    "Create API endpoints",
                    "Add form validation",
                    "Implement routing",
                    "Add error handling",
                    "Create responsive design",
                    "Write documentation",
                    "Add unit tests",
                    "Deploy application"
                ],
                "file_structure": ["frontend/", "backend/", "database/", "docs/", "tests/"],
                "agents": {
                    "frontend_developer": ["React components", "UI implementation", "Client-side logic"],
                    "backend_developer": ["API development", "Database design", "Server logic"],
                    "ui_ux_designer": ["Interface design", "User flow", "Visual design"],
                    "qa_tester": ["API testing", "Integration testing", "UI testing"]
                }
            },
            "mobile_app": {
                "common_tasks": [
                    "Set up mobile project",
                    "Create app navigation",
                    "Implement core features",
                    "Add data persistence",
                    "Create user interface",
                    "Implement push notifications",
                    "Add offline functionality",
                    "Optimize for performance",
                    "Add accessibility features",
                    "Write user guide",
                    "Test on devices",
                    "Prepare for app store"
                ],
                "file_structure": ["src/", "assets/", "components/", "screens/", "services/"],
                "agents": {
                    "frontend_developer": ["App components", "Navigation", "State management"],
                    "backend_developer": ["API integration", "Data services", "Authentication"],
                    "ui_ux_designer": ["Mobile UI", "User experience", "Icon design"],
                    "qa_tester": ["Device testing", "Performance testing", "Usability testing"]
                }
            }
        }
    
    def get_system_prompt(self) -> str:
        return """You are Alice Chen, a Senior Product Manager with 10+ years of experience in software development and project management.

Your core responsibilities:
1. ANALYZE client requirements and break them down into manageable tasks
2. CREATE comprehensive project backlogs with proper task prioritization
3. ASSIGN tasks to appropriate team members based on their expertise
4. DEFINE clear acceptance criteria and success metrics for each task
5. ENSURE project deliverables meet client expectations

Your expertise includes:
- Project decomposition and planning
- Writing detailed user stories in proper format
- Creating technical specifications
- Task estimation and prioritization
- Agile/Scrum methodology
- Stakeholder communication
- Risk assessment and mitigation

When given a project request, you must:
1. Understand the full scope and requirements
2. Break it down into logical, sequential tasks
3. Assign each task to the most suitable team member
4. Define clear acceptance criteria
5. Estimate effort and set priorities
6. Create a project roadmap

Always respond in structured JSON format for project breakdowns.
Be thorough, professional, and focus on delivering working, complete solutions."""

    async def create_project_breakdown(self, client_request: str, project_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a comprehensive project breakdown from client request"""
        
        # Analyze the client request
        project_analysis = await self._analyze_project_request(client_request)
        
        # Generate detailed task breakdown
        task_breakdown = await self._generate_task_breakdown(project_analysis)
        
        # Assign tasks to agents
        task_assignments = await self._assign_tasks_to_agents(task_breakdown)
        
        # Create project roadmap
        roadmap = await self._create_project_roadmap(task_assignments)
        
        # Generate final project backlog
        project_backlog = {
            "project_id": f"proj_{int(datetime.now().timestamp())}",
            "project_name": project_analysis.get("project_name", "Untitled Project"),
            "project_description": project_analysis.get("description", client_request),
            "project_type": project_analysis.get("project_type", "web_app"),
            "estimated_duration": project_analysis.get("estimated_duration", "1-2 weeks"),
            "client_request": client_request,
            "analysis": project_analysis,
            "tasks": task_assignments,
            "roadmap": roadmap,
            "file_structure": project_analysis.get("file_structure", []),
            "success_criteria": project_analysis.get("success_criteria", []),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": self.name
        }
        
        return project_backlog
    
    async def _analyze_project_request(self, client_request: str) -> Dict[str, Any]:
        """Analyze the client request to understand project scope and type"""
        
        analysis_prompt = f"""As Alice Chen, analyze this client request and provide a comprehensive project analysis:

CLIENT REQUEST: "{client_request}"

Analyze and provide the following in JSON format:
1. Project name (short, descriptive)
2. Project type (game, web_app, mobile_app, api, website, tool)
3. Core features and functionality needed
4. Technical requirements and constraints
5. Target audience and use cases
6. Success criteria and acceptance criteria
7. Estimated complexity (simple, medium, complex)
8. Estimated duration
9. Required file structure
10. Key deliverables

Focus on understanding EXACTLY what the client wants to build and what would constitute a complete, working solution.

Respond in JSON format:
{{
    "project_name": "...",
    "project_type": "...",
    "description": "...",
    "core_features": [...],
    "technical_requirements": [...],
    "target_audience": "...",
    "success_criteria": [...],
    "complexity": "...",
    "estimated_duration": "...",
    "file_structure": [...],
    "deliverables": [...]
}}"""

        try:
            response = await self._call_ollama(analysis_prompt)
            # Clean and parse JSON response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            else:
                # Fallback analysis
                return self._create_fallback_analysis(client_request)
        except Exception as e:
            logger.warning(f"Analysis parsing failed: {e}")
            return self._create_fallback_analysis(client_request)
    
    def _create_fallback_analysis(self, client_request: str) -> Dict[str, Any]:
        """Create a fallback analysis when AI parsing fails"""
        
        # Detect project type from keywords
        request_lower = client_request.lower()
        if any(word in request_lower for word in ["game", "snake", "tetris", "puzzle", "platformer"]):
            project_type = "game"
        elif any(word in request_lower for word in ["mobile", "app", "ios", "android"]):
            project_type = "mobile_app"
        elif any(word in request_lower for word in ["api", "backend", "server", "database"]):
            project_type = "api"
        else:
            project_type = "web_app"
        
        return {
            "project_name": "Custom Project",
            "project_type": project_type,
            "description": client_request,
            "core_features": ["Main functionality", "User interface", "Basic features"],
            "technical_requirements": ["Modern web technologies", "Responsive design", "Cross-browser compatibility"],
            "target_audience": "General users",
            "success_criteria": ["Working application", "Good user experience", "Complete functionality"],
            "complexity": "medium",
            "estimated_duration": "1-2 weeks",
            "file_structure": self.project_templates.get(project_type, {}).get("file_structure", []),
            "deliverables": ["Complete working application", "Source code", "Documentation"]
        }
    
    async def _generate_task_breakdown(self, project_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed task breakdown based on project analysis"""
        
        project_type = project_analysis.get("project_type", "web_app")
        template = self.project_templates.get(project_type, self.project_templates["web_app"])
        
        breakdown_prompt = f"""As Alice Chen, create a detailed task breakdown for this project:

PROJECT: {project_analysis.get('project_name')}
TYPE: {project_type}
DESCRIPTION: {project_analysis.get('description')}
CORE FEATURES: {', '.join(project_analysis.get('core_features', []))}

Create a comprehensive task list that will result in a COMPLETE, WORKING application.
Each task should be:
- Specific and actionable
- Properly scoped (not too big, not too small)
- Have clear deliverables
- Include acceptance criteria

Template tasks for {project_type}: {', '.join(template.get('common_tasks', []))}

Provide tasks in JSON format:
[
    {{
        "task_id": "task_001",
        "title": "Task title",
        "description": "Detailed description of what needs to be done",
        "deliverables": ["Specific file or feature to be created"],
        "acceptance_criteria": ["Criteria 1", "Criteria 2"],
        "estimated_hours": 2,
        "priority": "high|medium|low",
        "dependencies": ["task_id"],
        "task_type": "setup|development|design|testing|documentation"
    }}
]

Ensure tasks cover the COMPLETE development lifecycle for a working application."""

        try:
            response = await self._call_ollama(breakdown_prompt)
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                tasks = json.loads(json_match.group())
                return tasks
            else:
                return self._create_fallback_task_breakdown(project_analysis)
        except Exception as e:
            logger.warning(f"Task breakdown parsing failed: {e}")
            return self._create_fallback_task_breakdown(project_analysis)
    
    def _create_fallback_task_breakdown(self, project_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create fallback task breakdown when AI generation fails"""
        
        project_type = project_analysis.get("project_type", "web_app")
        template = self.project_templates.get(project_type, self.project_templates["web_app"])
        
        tasks = []
        task_counter = 1
        
        for task_title in template.get("common_tasks", []):
            task = {
                "task_id": f"task_{task_counter:03d}",
                "title": task_title,
                "description": f"Implement {task_title.lower()} for the project",
                "deliverables": [f"Complete {task_title.lower()}"],
                "acceptance_criteria": ["Feature is working", "Code is clean", "Basic testing completed"],
                "estimated_hours": 3,
                "priority": "medium",
                "dependencies": [],
                "task_type": "development"
            }
            tasks.append(task)
            task_counter += 1
        
        return tasks
    
    async def _assign_tasks_to_agents(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assign tasks to appropriate agents based on task type and content"""
        
        assignment_prompt = f"""As Alice Chen, assign each task to the most appropriate team member.

Available team members:
- frontend_developer (Marcus Dev): React, JavaScript, HTML, CSS, UI implementation
- backend_developer (Sarah Backend): Python, APIs, databases, server logic
- ui_ux_designer (Luna Design): UI design, UX, mockups, styling, visual design
- qa_tester (TestBot QA): Testing, quality assurance, test plans

TASKS TO ASSIGN:
{json.dumps(tasks, indent=2)}

For each task, determine the best agent based on:
1. Task content and requirements
2. Agent expertise and capabilities
3. Logical workflow dependencies

Return the tasks with agent assignments in JSON format:
[
    {{
        "task_id": "task_001",
        "title": "...",
        "description": "...",
        "assigned_agent": "frontend_developer",
        "agent_rationale": "This task involves HTML/CSS which matches frontend expertise",
        "deliverables": [...],
        "acceptance_criteria": [...],
        "estimated_hours": 2,
        "priority": "high",
        "dependencies": [],
        "task_type": "development"
    }}
]"""

        try:
            response = await self._call_ollama(assignment_prompt)
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                assigned_tasks = json.loads(json_match.group())
                return assigned_tasks
            else:
                return self._create_fallback_assignments(tasks)
        except Exception as e:
            logger.warning(f"Task assignment parsing failed: {e}")
            return self._create_fallback_assignments(tasks)
    
    def _create_fallback_assignments(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create fallback task assignments using keyword matching"""
        
        assignment_rules = {
            "frontend_developer": [
                "html", "css", "javascript", "react", "component", "ui", "interface",
                "frontend", "client", "browser", "dom", "styling", "layout"
            ],
            "backend_developer": [
                "api", "database", "server", "backend", "python", "endpoint",
                "authentication", "data", "logic", "service", "infrastructure"
            ],
            "ui_ux_designer": [
                "design", "mockup", "wireframe", "style", "visual", "color",
                "typography", "user experience", "interface design", "branding"
            ],
            "qa_tester": [
                "test", "testing", "quality", "validation", "verification",
                "bug", "qa", "acceptance", "performance", "security"
            ]
        }
        
        assigned_tasks = []
        
        for task in tasks:
            # Analyze task content to determine best agent
            task_content = f"{task.get('title', '')} {task.get('description', '')}".lower()
            
            best_agent = "frontend_developer"  # Default
            best_score = 0
            
            for agent, keywords in assignment_rules.items():
                score = sum(1 for keyword in keywords if keyword in task_content)
                if score > best_score:
                    best_score = score
                    best_agent = agent
            
            # Add assignment to task
            task["assigned_agent"] = best_agent
            task["agent_rationale"] = f"Assigned based on task content matching {best_agent} expertise"
            
            assigned_tasks.append(task)
        
        return assigned_tasks
    
    async def _create_project_roadmap(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create project roadmap with phases and timeline"""
        
        # Organize tasks by priority and dependencies
        high_priority = [t for t in tasks if t.get("priority") == "high"]
        medium_priority = [t for t in tasks if t.get("priority") == "medium"]
        low_priority = [t for t in tasks if t.get("priority") == "low"]
        
        # Calculate phases
        phases = [
            {
                "phase": 1,
                "name": "Project Setup & Core Foundation",
                "tasks": high_priority[:len(high_priority)//2] if high_priority else tasks[:3],
                "estimated_duration": "2-3 days"
            },
            {
                "phase": 2,
                "name": "Main Development",
                "tasks": high_priority[len(high_priority)//2:] + medium_priority[:len(medium_priority)//2],
                "estimated_duration": "5-7 days"
            },
            {
                "phase": 3,
                "name": "Refinement & Testing",
                "tasks": medium_priority[len(medium_priority)//2:] + low_priority,
                "estimated_duration": "2-3 days"
            }
        ]
        
        total_hours = sum(task.get("estimated_hours", 3) for task in tasks)
        
        roadmap = {
            "total_tasks": len(tasks),
            "total_estimated_hours": total_hours,
            "estimated_completion": f"{total_hours // 8 + 1} working days",
            "phases": phases,
            "critical_path": [t["task_id"] for t in high_priority],
            "delivery_milestones": [
                "Phase 1: Foundation Complete",
                "Phase 2: Core Features Complete",
                "Phase 3: Final Product Ready"
            ]
        }
        
        return roadmap
    
    async def process_task(self, task) -> str:
        """Process a regular task (non-project breakdown)"""
        
        # For regular PM tasks, use the standard prompt
        prompt = f"""{self.get_system_prompt()}

Task: {task.title}
Description: {task.description}
Priority: {task.priority.value}

As Alice Chen, provide a comprehensive response that includes:

1. **Analysis** - Understanding of the requirements
2. **User Stories** - Written in proper format ("As a [user], I want [goal] so that [benefit]")
3. **Acceptance Criteria** - Clear, testable criteria
4. **Implementation Plan** - Step-by-step approach
5. **Success Metrics** - How to measure success
6. **Risks & Mitigation** - Potential issues and solutions

Format your response professionally with clear headings and actionable content."""

        return await self._call_ollama(prompt)
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with enhanced prompt for project management"""
        try:
            response = await asyncio.to_thread(
                self._ollama_generate,
                prompt
            )
            return response
        except Exception as e:
            logger.error(f"Ollama API error in Alice Chen agent: {e}")
            return f"Error generating response: {str(e)}"
    
    def _ollama_generate(self, prompt: str) -> str:
        """Synchronous Ollama call"""
        import ollama
        response = ollama.generate(
            model=self.model,
            prompt=prompt,
            stream=False
        )
        return response['response']
