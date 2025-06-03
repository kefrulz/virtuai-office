# VirtuAI Office - Project Workflow Orchestration Engine
import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

from sqlalchemy.orm import Session
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ProjectPhase(str, Enum):
    ANALYSIS = "analysis"
    BREAKDOWN = "breakdown"
    ASSIGNMENT = "assignment"
    EXECUTION = "execution"
    INTEGRATION = "integration"
    FINALIZATION = "finalization"
    COMPLETED = "completed"

class ProjectType(str, Enum):
    GAME = "game"
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    API = "api"
    LIBRARY = "library"
    GENERAL = "general"

class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class BacklogItem(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    story_points: int
    priority: TaskPriority
    assigned_agent: Optional[str] = None
    dependencies: List[str] = []
    file_outputs: List[str] = []
    status: str = "todo"

class ProjectWorkflow:
    def __init__(self, agent_manager, database_session):
        self.agent_manager = agent_manager
        self.db = database_session
        self.current_projects = {}
    
    async def create_project_from_client_request(self, client_request: str, project_type: str = "general") -> str:
        """
        Main entry point: Client creates a project request
        """
        project_id = str(uuid.uuid4())
        
        project_data = {
            "id": project_id,
            "client_request": client_request,
            "project_type": project_type,
            "phase": ProjectPhase.ANALYSIS,
            "created_at": datetime.utcnow(),
            "backlog": [],
            "assigned_tasks": {},
            "deliverables": [],
            "status": "active"
        }
        
        self.current_projects[project_id] = project_data
        
        # Store in database
        await self._save_project_to_db(project_data)
        
        # Start the workflow
        await self._start_project_workflow(project_id)
        
        return project_id
    
    async def _start_project_workflow(self, project_id: str):
        """
        Start the complete project workflow
        """
        try:
            # Phase 1: Analysis and Breakdown by Product Manager
            await self._phase_analysis_breakdown(project_id)
            
            # Phase 2: Task Assignment
            await self._phase_task_assignment(project_id)
            
            # Phase 3: Task Execution
            await self._phase_task_execution(project_id)
            
            # Phase 4: Integration and Finalization
            await self._phase_integration_finalization(project_id)
            
        except Exception as e:
            logger.error(f"Project workflow failed for {project_id}: {e}")
            await self._mark_project_failed(project_id, str(e))
    
    async def _phase_analysis_breakdown(self, project_id: str):
        """
        Phase 1: Product Manager analyzes request and creates backlog
        """
        project = self.current_projects[project_id]
        project["phase"] = ProjectPhase.BREAKDOWN
        
        # Get Alice Chen (Product Manager)
        alice = self.agent_manager.get_agent_by_type("product_manager")
        
        # Create detailed prompt for project breakdown
        breakdown_prompt = f"""
You are Alice Chen, Senior Product Manager. A client has requested the following project:

CLIENT REQUEST: {project["client_request"]}
PROJECT TYPE: {project["project_type"]}

Your task is to analyze this request and create a comprehensive project backlog. Break down the project into specific, actionable tasks that can be assigned to different team members.

For each backlog item, provide:
1. Title (clear, specific)
2. Description (detailed requirements)
3. Acceptance criteria (3-5 testable criteria)
4. Story points (1, 2, 3, 5, 8, 13)
5. Priority (critical, high, medium, low)
6. Required agent type (frontend_developer, backend_developer, ui_ux_designer, qa_tester)
7. Expected file outputs (list of files this task should create)
8. Dependencies (which other tasks must be completed first)

Respond in the following JSON format:
{{
    "project_analysis": "Brief analysis of the project requirements and approach",
    "estimated_duration": "Estimated completion time in days",
    "backlog_items": [
        {{
            "title": "Task title",
            "description": "Detailed description",
            "acceptance_criteria": ["Criteria 1", "Criteria 2", "Criteria 3"],
            "story_points": 5,
            "priority": "high",
            "required_agent": "frontend_developer",
            "file_outputs": ["index.html", "style.css"],
            "dependencies": []
        }}
    ],
    "project_structure": {{
        "folders": ["src", "assets", "docs"],
        "main_files": ["index.html", "README.md"],
        "technology_stack": ["HTML", "CSS", "JavaScript"]
    }}
}}

Create a complete, professional breakdown that covers all aspects of the project.
        """
        
        # Get breakdown from Alice
        breakdown_response = await alice.process_task_with_prompt(breakdown_prompt)
        
        try:
            breakdown_data = json.loads(breakdown_response)
            
            # Convert to BacklogItem objects
            backlog_items = []
            for item_data in breakdown_data.get("backlog_items", []):
                backlog_item = BacklogItem(
                    id=str(uuid.uuid4()),
                    title=item_data["title"],
                    description=item_data["description"],
                    acceptance_criteria=item_data["acceptance_criteria"],
                    story_points=item_data["story_points"],
                    priority=TaskPriority(item_data["priority"]),
                    file_outputs=item_data.get("file_outputs", []),
                    dependencies=item_data.get("dependencies", [])
                )
                backlog_items.append(backlog_item)
            
            # Store breakdown results
            project["backlog"] = [item.dict() for item in backlog_items]
            project["project_analysis"] = breakdown_data.get("project_analysis", "")
            project["estimated_duration"] = breakdown_data.get("estimated_duration", "")
            project["project_structure"] = breakdown_data.get("project_structure", {})
            project["breakdown_completed"] = True
            
            await self._save_project_to_db(project)
            
            logger.info(f"Project {project_id} breakdown completed: {len(backlog_items)} items created")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse breakdown response: {e}")
            # Fallback: create basic breakdown
            await self._create_fallback_breakdown(project_id)
    
    async def _phase_task_assignment(self, project_id: str):
        """
        Phase 2: Assign backlog items to appropriate agents
        """
        project = self.current_projects[project_id]
        project["phase"] = ProjectPhase.ASSIGNMENT
        
        # Get available agents
        available_agents = self.agent_manager.get_all_agents()
        
        # Assign each backlog item to appropriate agent
        for item in project["backlog"]:
            best_agent = await self._find_best_agent_for_task(item, available_agents)
            item["assigned_agent"] = best_agent.id if best_agent else None
            item["status"] = "assigned"
        
        project["assignment_completed"] = True
        await self._save_project_to_db(project)
        
        logger.info(f"Project {project_id} task assignment completed")
    
    async def _phase_task_execution(self, project_id: str):
        """
        Phase 3: Execute all assigned tasks
        """
        project = self.current_projects[project_id]
        project["phase"] = ProjectPhase.EXECUTION
        
        # Execute tasks in dependency order
        execution_order = self._calculate_execution_order(project["backlog"])
        
        for item_id in execution_order:
            await self._execute_backlog_item(project_id, item_id)
        
        project["execution_completed"] = True
        await self._save_project_to_db(project)
        
        logger.info(f"Project {project_id} execution completed")
    
    async def _phase_integration_finalization(self, project_id: str):
        """
        Phase 4: Integrate all outputs and create final deliverable
        """
        project = self.current_projects[project_id]
        project["phase"] = ProjectPhase.INTEGRATION
        
        # Collect all generated files
        all_files = {}
        for item in project["backlog"]:
            if item.get("output_files"):
                all_files.update(item["output_files"])
        
        # Create project structure
        project_structure = await self._create_project_structure(project)
        
        # Generate additional files (README, package.json, etc.)
        additional_files = await self._generate_project_metadata(project)
        all_files.update(additional_files)
        
        # Create final zip file
        zip_file_path = await self._create_project_zip(project_id, all_files, project_structure)
        
        project["deliverable_path"] = zip_file_path
        project["phase"] = ProjectPhase.COMPLETED
        project["completed_at"] = datetime.utcnow()
        
        await self._save_project_to_db(project)
        
        logger.info(f"Project {project_id} completed successfully")
    
    async def _execute_backlog_item(self, project_id: str, item_id: str):
        """
        Execute a specific backlog item
        """
        project = self.current_projects[project_id]
        
        # Find the backlog item
        item = None
        for backlog_item in project["backlog"]:
            if backlog_item["id"] == item_id:
                item = backlog_item
                break
        
        if not item:
            logger.error(f"Backlog item {item_id} not found")
            return
        
        # Get assigned agent
        agent = self.agent_manager.get_agent_by_id(item["assigned_agent"])
        if not agent:
            logger.error(f"Agent {item['assigned_agent']} not found")
            return
        
        # Mark as in progress
        item["status"] = "in_progress"
        item["started_at"] = datetime.utcnow().isoformat()
        
        # Create detailed task prompt
        task_prompt = self._create_task_prompt(item, project)
        
        # Execute task
        try:
            output = await agent.process_task_with_prompt(task_prompt)
            
            # Parse output to extract files
            files = await self._extract_files_from_output(output, item["file_outputs"])
            
            item["output"] = output
            item["output_files"] = files
            item["status"] = "completed"
            item["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Backlog item {item_id} completed by {agent.name}")
            
        except Exception as e:
            item["status"] = "failed"
            item["error"] = str(e)
            logger.error(f"Backlog item {item_id} failed: {e}")
        
        await self._save_project_to_db(project)
    
    def _create_task_prompt(self, item: Dict, project: Dict) -> str:
        """
        Create a detailed prompt for task execution
        """
        project_context = f"""
PROJECT CONTEXT:
- Client Request: {project['client_request']}
- Project Type: {project['project_type']}
- Project Structure: {json.dumps(project.get('project_structure', {}), indent=2)}

TASK DETAILS:
- Title: {item['title']}
- Description: {item['description']}
- Acceptance Criteria: {json.dumps(item['acceptance_criteria'], indent=2)}
- Expected Files: {json.dumps(item['file_outputs'], indent=2)}
- Priority: {item['priority']}

INSTRUCTIONS:
1. Create complete, working code/content for this task
2. Ensure all acceptance criteria are met
3. Generate all expected output files
4. Include proper comments and documentation
5. Follow best practices for the technology stack
6. Make sure your output integrates well with other project components

For each file you create, use this format:
=== FILENAME: filename.ext ===
[file content here]
=== END FILE ===

Provide complete, production-ready code that fulfills all requirements.
        """
        return project_context
    
    async def _extract_files_from_output(self, output: str, expected_files: List[str]) -> Dict[str, str]:
        """
        Extract individual files from agent output
        """
        files = {}
        
        # Look for file markers in output
        import re
        file_pattern = r'=== FILENAME: (.+?) ===\n(.*?)\n=== END FILE ==='
        matches = re.findall(file_pattern, output, re.DOTALL)
        
        for filename, content in matches:
            files[filename.strip()] = content.strip()
        
        # If no file markers found, try to infer files
        if not files and expected_files:
            # For single file outputs, use the entire output
            if len(expected_files) == 1:
                files[expected_files[0]] = output
            else:
                # Try to split by common delimiters
                parts = output.split('\n\n---\n\n')
                for i, part in enumerate(parts[:len(expected_files)]):
                    if i < len(expected_files):
                        files[expected_files[i]] = part.strip()
        
        return files
    
    def _calculate_execution_order(self, backlog: List[Dict]) -> List[str]:
        """
        Calculate the order to execute tasks based on dependencies
        """
        # Simple topological sort
        item_map = {item["id"]: item for item in backlog}
        in_degree = {item["id"]: 0 for item in backlog}
        
        # Calculate in-degrees
        for item in backlog:
            for dep in item.get("dependencies", []):
                if dep in in_degree:
                    in_degree[item["id"]] += 1
        
        # Queue items with no dependencies
        queue = [item_id for item_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Reduce in-degree for dependent items
            for item in backlog:
                if current in item.get("dependencies", []):
                    in_degree[item["id"]] -= 1
                    if in_degree[item["id"]] == 0:
                        queue.append(item["id"])
        
        return result
    
    async def _find_best_agent_for_task(self, item: Dict, agents: List) -> Any:
        """
        Find the best agent for a specific task
        """
        # Simple assignment based on task requirements
        agent_type_map = {
            "frontend_developer": "frontend_developer",
            "backend_developer": "backend_developer",
            "ui_ux_designer": "ui_ux_designer",
            "qa_tester": "qa_tester",
            "product_manager": "product_manager"
        }
        
        # Determine required agent type from task
        task_desc = item["description"].lower()
        
        if any(keyword in task_desc for keyword in ["react", "html", "css", "frontend", "ui component"]):
            required_type = "frontend_developer"
        elif any(keyword in task_desc for keyword in ["api", "backend", "database", "server"]):
            required_type = "backend_developer"
        elif any(keyword in task_desc for keyword in ["design", "mockup", "wireframe", "style"]):
            required_type = "ui_ux_designer"
        elif any(keyword in task_desc for keyword in ["test", "qa", "quality"]):
            required_type = "qa_tester"
        else:
            required_type = "frontend_developer"  # Default
        
        # Find agent of required type
        for agent in agents:
            if agent.type.value == required_type:
                return agent
        
        return agents[0] if agents else None
    
    async def _create_project_structure(self, project: Dict) -> Dict:
        """
        Create the folder structure for the project
        """
        structure = project.get("project_structure", {})
        
        default_structure = {
            "folders": ["src", "assets", "docs"],
            "main_files": ["README.md", "index.html"]
        }
        
        return {**default_structure, **structure}
    
    async def _generate_project_metadata(self, project: Dict) -> Dict[str, str]:
        """
        Generate additional project files (README, package.json, etc.)
        """
        files = {}
        
        # Generate README.md
        readme_content = f"""# {project.get('client_request', 'Project')}

## Description
{project.get('project_analysis', 'AI-generated project')}

## Setup Instructions
1. Extract the project files
2. Open index.html in a web browser (for web projects)
3. Follow any additional setup instructions below

## Project Structure
```
{self._format_project_structure(project.get('project_structure', {}))}
```

## Technologies Used
{', '.join(project.get('project_structure', {}).get('technology_stack', ['HTML', 'CSS', 'JavaScript']))}

## Generated by VirtuAI Office
This project was created by an AI development team:
- Product Manager: Alice Chen
- Developers: Marcus Dev, Sarah Backend
- Designer: Luna Design  
- QA: TestBot QA

Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
"""
        files["README.md"] = readme_content
        
        # Generate package.json for web projects
        if project.get("project_type") in ["web_app", "game"]:
            package_json = {
                "name": project.get("client_request", "project").lower().replace(" ", "-"),
                "version": "1.0.0",
                "description": project.get("project_analysis", "AI-generated project"),
                "main": "index.html",
                "scripts": {
                    "start": "open index.html"
                },
                "author": "VirtuAI Office",
                "license": "MIT",
                "created": datetime.utcnow().isoformat()
            }
            files["package.json"] = json.dumps(package_json, indent=2)
        
        return files
    
    def _format_project_structure(self, structure: Dict) -> str:
        """
        Format project structure for README
        """
        lines = []
        folders = structure.get("folders", [])
        files = structure.get("main_files", [])
        
        for folder in folders:
            lines.append(f"{folder}/")
        for file in files:
            lines.append(file)
        
        return "\n".join(lines)
    
    async def _create_project_zip(self, project_id: str, files: Dict[str, str], structure: Dict) -> str:
        """
        Create a downloadable zip file with all project files
        """
        import zipfile
        import tempfile
        import os
        
        # Create temporary zip file
        zip_path = f"./deliverables/{project_id}.zip"
        os.makedirs("./deliverables", exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all generated files
            for filename, content in files.items():
                zipf.writestr(filename, content)
            
            # Create empty folders
            for folder in structure.get("folders", []):
                zipf.writestr(f"{folder}/.gitkeep", "")
        
        return zip_path
    
    async def _save_project_to_db(self, project_data: Dict):
        """
        Save project data to database
        """
        # This would save to your database
        # Implementation depends on your database schema
        pass
    
    async def _mark_project_failed(self, project_id: str, error: str):
        """
        Mark project as failed
        """
        if project_id in self.current_projects:
            self.current_projects[project_id]["status"] = "failed"
            self.current_projects[project_id]["error"] = error
            await self._save_project_to_db(self.current_projects[project_id])
    
    async def _create_fallback_breakdown(self, project_id: str):
        """
        Create a basic breakdown if AI parsing fails
        """
        project = self.current_projects[project_id]
        
        # Create basic breakdown based on project type
        basic_items = [
            {
                "id": str(uuid.uuid4()),
                "title": "Project Setup",
                "description": "Set up basic project structure and files",
                "acceptance_criteria": ["Project folder created", "Basic files in place"],
                "story_points": 3,
                "priority": "high",
                "assigned_agent": None,
                "file_outputs": ["index.html", "style.css", "script.js"],
                "dependencies": [],
                "status": "todo"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Core Implementation",
                "description": f"Implement core functionality for: {project['client_request']}",
                "acceptance_criteria": ["Core features working", "Basic styling applied"],
                "story_points": 8,
                "priority": "high",
                "assigned_agent": None,
                "file_outputs": ["script.js"],
                "dependencies": [],
                "status": "todo"
            }
        ]
        
        project["backlog"] = basic_items
        project["breakdown_completed"] = True
    
    # Public API methods
    
    async def get_project_status(self, project_id: str) -> Dict:
        """
        Get current status of a project
        """
        if project_id not in self.current_projects:
            return {"error": "Project not found"}
        
        project = self.current_projects[project_id]
        
        # Calculate progress
        total_items = len(project.get("backlog", []))
        completed_items = len([item for item in project.get("backlog", []) if item.get("status") == "completed"])
        progress = (completed_items / total_items * 100) if total_items > 0 else 0
        
        return {
            "project_id": project_id,
            "phase": project.get("phase"),
            "status": project.get("status"),
            "progress": progress,
            "total_items": total_items,
            "completed_items": completed_items,
            "deliverable_ready": project.get("deliverable_path") is not None,
            "created_at": project.get("created_at"),
            "estimated_duration": project.get("estimated_duration")
        }
    
    async def get_project_backlog(self, project_id: str) -> List[Dict]:
        """
        Get project backlog
        """
        if project_id not in self.current_projects:
            return []
        
        return self.current_projects[project_id].get("backlog", [])
    
    async def get_deliverable_path(self, project_id: str) -> Optional[str]:
        """
        Get path to downloadable zip file
        """
        if project_id not in self.current_projects:
            return None
        
        return self.current_projects[project_id].get("deliverable_path")
