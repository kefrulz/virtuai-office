# VirtuAI Office - Zip Creator for Complete Project Deliverables
import os
import zipfile
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ProjectZipCreator:
    def __init__(self):
        self.temp_dir = None
        self.project_structure = {}
        
    def create_project_zip(self, project_data: Dict[str, Any], tasks_output: List[Dict], project_type: str = "web") -> str:
        """
        Create a complete project zip file from agent outputs
        
        Args:
            project_data: Project metadata and configuration
            tasks_output: List of completed tasks with their outputs
            project_type: Type of project (web, game, mobile, etc.)
            
        Returns:
            Path to the created zip file
        """
        try:
            # Create temporary directory for project files
            self.temp_dir = tempfile.mkdtemp(prefix="virtuai_project_")
            project_name = self._sanitize_filename(project_data.get('name', 'VirtuAI_Project'))
            project_path = os.path.join(self.temp_dir, project_name)
            os.makedirs(project_path, exist_ok=True)
            
            # Generate project structure based on type
            self._create_project_structure(project_path, project_type)
            
            # Process and organize task outputs
            self._process_task_outputs(project_path, tasks_output, project_type)
            
            # Generate project documentation
            self._generate_documentation(project_path, project_data, tasks_output)
            
            # Create package.json or equivalent project files
            self._create_project_config(project_path, project_data, project_type)
            
            # Create README and setup instructions
            self._create_readme(project_path, project_data, project_type)
            
            # Create the zip file
            zip_path = self._create_zip_archive(project_path, project_name)
            
            logger.info(f"Project zip created successfully: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Error creating project zip: {e}")
            raise
        finally:
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_project_structure(self, project_path: str, project_type: str):
        """Create the basic project directory structure"""
        
        structures = {
            "web": {
                "src": ["js", "css", "components"],
                "public": ["images", "assets"],
                "tests": [],
                "docs": []
            },
            "game": {
                "src": ["js", "css", "assets"],
                "assets": ["images", "sounds", "sprites"],
                "levels": [],
                "docs": []
            },
            "react": {
                "src": ["components", "hooks", "utils", "styles"],
                "public": ["images", "icons"],
                "tests": [],
                "docs": []
            },
            "node": {
                "src": ["routes", "models", "controllers", "middleware"],
                "tests": [],
                "config": [],
                "docs": []
            },
            "python": {
                "src": ["modules", "utils", "tests"],
                "data": [],
                "config": [],
                "docs": []
            }
        }
        
        structure = structures.get(project_type, structures["web"])
        
        for main_dir, subdirs in structure.items():
            main_path = os.path.join(project_path, main_dir)
            os.makedirs(main_path, exist_ok=True)
            
            for subdir in subdirs:
                sub_path = os.path.join(main_path, subdir)
                os.makedirs(sub_path, exist_ok=True)
    
    def _process_task_outputs(self, project_path: str, tasks_output: List[Dict], project_type: str):
        """Process agent outputs and place files in correct locations"""
        
        for task in tasks_output:
            agent_type = task.get('agent_type', '')
            output = task.get('output', '')
            task_title = task.get('title', '')
            
            # Determine file placement based on agent type and content
            if agent_type == 'frontend_developer':
                self._process_frontend_output(project_path, output, task_title, project_type)
            elif agent_type == 'backend_developer':
                self._process_backend_output(project_path, output, task_title, project_type)
            elif agent_type == 'ui_ux_designer':
                self._process_design_output(project_path, output, task_title)
            elif agent_type == 'qa_tester':
                self._process_testing_output(project_path, output, task_title)
            elif agent_type == 'product_manager':
                self._process_documentation_output(project_path, output, task_title)
    
    def _process_frontend_output(self, project_path: str, output: str, task_title: str, project_type: str):
        """Process frontend developer output"""
        
        # Extract code blocks from output
        code_blocks = self._extract_code_blocks(output)
        
        for block in code_blocks:
            language = block.get('language', '').lower()
            code = block.get('code', '')
            
            if not code.strip():
                continue
                
            if language in ['javascript', 'js']:
                if 'component' in task_title.lower() or 'react' in output.lower():
                    # React component
                    filename = self._generate_filename(task_title, 'jsx')
                    filepath = os.path.join(project_path, 'src', 'components', filename)
                else:
                    # Regular JavaScript
                    filename = self._generate_filename(task_title, 'js')
                    filepath = os.path.join(project_path, 'src', 'js', filename)
                    
            elif language in ['css', 'scss']:
                filename = self._generate_filename(task_title, 'css')
                filepath = os.path.join(project_path, 'src', 'css', filename)
                
            elif language in ['html']:
                filename = self._generate_filename(task_title, 'html')
                if project_type == 'game':
                    filepath = os.path.join(project_path, filename)
                else:
                    filepath = os.path.join(project_path, 'public', filename)
                    
            else:
                # Default to JavaScript if no language specified but contains code
                if self._contains_code_patterns(code):
                    filename = self._generate_filename(task_title, 'js')
                    filepath = os.path.join(project_path, 'src', 'js', filename)
                else:
                    continue
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Write the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
                
        # If no code blocks found, create a documentation file
        if not code_blocks and output.strip():
            filename = self._generate_filename(task_title, 'md')
            filepath = os.path.join(project_path, 'docs', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {task_title}\n\n{output}")
    
    def _process_backend_output(self, project_path: str, output: str, task_title: str, project_type: str):
        """Process backend developer output"""
        
        code_blocks = self._extract_code_blocks(output)
        
        for block in code_blocks:
            language = block.get('language', '').lower()
            code = block.get('code', '')
            
            if not code.strip():
                continue
                
            if language in ['python', 'py']:
                if 'model' in task_title.lower():
                    filename = self._generate_filename(task_title, 'py')
                    filepath = os.path.join(project_path, 'src', 'models', filename)
                elif 'api' in task_title.lower() or 'route' in task_title.lower():
                    filename = self._generate_filename(task_title, 'py')
                    filepath = os.path.join(project_path, 'src', 'routes', filename)
                else:
                    filename = self._generate_filename(task_title, 'py')
                    filepath = os.path.join(project_path, 'src', filename)
                    
            elif language in ['javascript', 'js', 'node']:
                if 'route' in task_title.lower() or 'api' in task_title.lower():
                    filename = self._generate_filename(task_title, 'js')
                    filepath = os.path.join(project_path, 'src', 'routes', filename)
                else:
                    filename = self._generate_filename(task_title, 'js')
                    filepath = os.path.join(project_path, 'src', filename)
                    
            elif language in ['sql']:
                filename = self._generate_filename(task_title, 'sql')
                filepath = os.path.join(project_path, 'src', 'database', filename)
                
            else:
                # Default handling
                filename = self._generate_filename(task_title, 'txt')
                filepath = os.path.join(project_path, 'src', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Write the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
    
    def _process_design_output(self, project_path: str, output: str, task_title: str):
        """Process UI/UX designer output"""
        
        # Design output is typically documentation, specifications, or CSS
        code_blocks = self._extract_code_blocks(output)
        
        css_written = False
        for block in code_blocks:
            language = block.get('language', '').lower()
            code = block.get('code', '')
            
            if language in ['css', 'scss'] and not css_written:
                filename = self._generate_filename(task_title, 'css')
                filepath = os.path.join(project_path, 'src', 'css', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(code)
                css_written = True
        
        # Always create a design document
        filename = self._generate_filename(task_title, 'md')
        filepath = os.path.join(project_path, 'docs', 'design', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Design: {task_title}\n\n{output}")
    
    def _process_testing_output(self, project_path: str, output: str, task_title: str):
        """Process QA tester output"""
        
        code_blocks = self._extract_code_blocks(output)
        
        for block in code_blocks:
            language = block.get('language', '').lower()
            code = block.get('code', '')
            
            if language in ['javascript', 'js']:
                filename = self._generate_filename(task_title, 'test.js')
                filepath = os.path.join(project_path, 'tests', filename)
            elif language in ['python', 'py']:
                filename = self._generate_filename(task_title, 'test.py')
                filepath = os.path.join(project_path, 'tests', filename)
            else:
                continue
                
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
        
        # Create test documentation
        filename = self._generate_filename(task_title, 'md')
        filepath = os.path.join(project_path, 'docs', 'testing', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Test Plan: {task_title}\n\n{output}")
    
    def _process_documentation_output(self, project_path: str, output: str, task_title: str):
        """Process product manager documentation output"""
        
        filename = self._generate_filename(task_title, 'md')
        filepath = os.path.join(project_path, 'docs', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {task_title}\n\n{output}")
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown-style text"""
        import re
        
        # Pattern to match code blocks with language specification
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        code_blocks = []
        for language, code in matches:
            code_blocks.append({
                'language': language or 'text',
                'code': code.strip()
            })
        
        # Also look for single-line code blocks
        single_line_pattern = r'`([^`]+)`'
        single_matches = re.findall(single_line_pattern, text)
        
        for code in single_matches:
            if len(code) > 50:  # Only consider longer code snippets
                code_blocks.append({
                    'language': 'text',
                    'code': code.strip()
                })
        
        return code_blocks
    
    def _contains_code_patterns(self, text: str) -> bool:
        """Check if text contains code-like patterns"""
        code_patterns = [
            r'function\s+\w+\s*\(',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'class\s+\w+',
            r'def\s+\w+\s*\(',
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            r'<\w+[^>]*>',
            r'\{\s*\w+\s*:',
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _generate_filename(self, task_title: str, extension: str) -> str:
        """Generate a filename from task title"""
        # Remove special characters and convert to snake_case
        filename = re.sub(r'[^a-zA-Z0-9\s]', '', task_title)
        filename = re.sub(r'\s+', '_', filename.strip())
        filename = filename.lower()
        
        # Ensure it's not too long
        if len(filename) > 40:
            filename = filename[:40]
        
        # Ensure it doesn't start with a number
        if filename and filename[0].isdigit():
            filename = f"task_{filename}"
        
        return f"{filename}.{extension}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        return filename[:50]  # Limit length
    
    def _create_project_config(self, project_path: str, project_data: Dict, project_type: str):
        """Create project configuration files"""
        
        if project_type in ['web', 'react', 'game']:
            # Create package.json
            package_json = {
                "name": self._sanitize_filename(project_data.get('name', 'virtuai-project')).lower(),
                "version": "1.0.0",
                "description": project_data.get('description', 'Generated by VirtuAI Office'),
                "main": "src/js/main.js" if project_type == 'game' else "src/index.js",
                "scripts": {
                    "start": "python -m http.server 8000" if project_type == 'game' else "npm start",
                    "test": "echo \"Error: no test specified\" && exit 1"
                },
                "keywords": ["virtuai", "generated", project_type],
                "author": "VirtuAI Office",
                "license": "MIT"
            }
            
            if project_type == 'react':
                package_json["dependencies"] = {
                    "react": "^18.0.0",
                    "react-dom": "^18.0.0"
                }
                package_json["scripts"]["start"] = "react-scripts start"
                package_json["scripts"]["build"] = "react-scripts build"
            
            with open(os.path.join(project_path, 'package.json'), 'w') as f:
                json.dump(package_json, f, indent=2)
        
        elif project_type == 'python':
            # Create requirements.txt
            requirements = [
                "# Generated by VirtuAI Office",
                "# Add your Python dependencies here",
                ""
            ]
            
            with open(os.path.join(project_path, 'requirements.txt'), 'w') as f:
                f.write('\n'.join(requirements))
            
            # Create setup.py
            setup_py = f'''from setuptools import setup, find_packages

setup(
    name="{self._sanitize_filename(project_data.get('name', 'virtuai-project')).lower()}",
    version="1.0.0",
    description="{project_data.get('description', 'Generated by VirtuAI Office')}",
    packages=find_packages(),
    python_requires=">=3.7",
)
'''
            with open(os.path.join(project_path, 'setup.py'), 'w') as f:
                f.write(setup_py)
    
    def _create_readme(self, project_path: str, project_data: Dict, project_type: str):
        """Create README.md file"""
        
        project_name = project_data.get('name', 'VirtuAI Project')
        description = project_data.get('description', 'A project generated by VirtuAI Office')
        
        readme_content = f"""# {project_name}

{description}

## Generated by VirtuAI Office 🤖

This project was automatically generated by VirtuAI Office - your local AI development team.

## Project Structure

```
{self._get_structure_tree(project_path)}
```

## Getting Started

"""
        
        if project_type == 'game':
            readme_content += """### Running the Game

1. Open `index.html` in your web browser, or
2. Start a local server:
   ```bash
   python -m http.server 8000
   ```
   Then visit http://localhost:8000

### Game Controls

[Add game-specific controls here]

"""
        elif project_type == 'react':
            readme_content += """### Installation and Running

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Open http://localhost:3000 in your browser

### Building for Production

```bash
npm run build
```

"""
        elif project_type == 'web':
            readme_content += """### Running the Application

1. Open `public/index.html` in your web browser, or
2. Start a local server:
   ```bash
   python -m http.server 8000
   ```
   Then visit http://localhost:8000

"""
        elif project_type == 'python':
            readme_content += """### Installation and Running

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python src/main.py
   ```

"""
        
        readme_content += """## Features

- [List the main features of your project]
- Generated with AI assistance
- Clean, organized code structure
- Comprehensive documentation

## Documentation

Check the `docs/` folder for detailed documentation including:
- Design specifications
- Technical documentation
- Test plans
- User guides

## Contributing

This project was generated by AI, but you can continue developing it:

1. Make your changes
2. Test thoroughly
3. Update documentation as needed

## Generated with ❤️ by VirtuAI Office

VirtuAI Office is a complete AI development team that runs locally on your machine.
Learn more at: https://github.com/kefrulz/virtuai-office

---

*This README was automatically generated. Feel free to customize it for your project!*
"""
        
        with open(os.path.join(project_path, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _get_structure_tree(self, project_path: str) -> str:
        """Generate a simple directory tree structure"""
        def _build_tree(path, prefix="", max_depth=3, current_depth=0):
            if current_depth >= max_depth:
                return ""
                
            items = []
            try:
                entries = sorted(os.listdir(path))
                for i, entry in enumerate(entries):
                    if entry.startswith('.'):
                        continue
                        
                    entry_path = os.path.join(path, entry)
                    is_last = i == len(entries) - 1
                    
                    if os.path.isdir(entry_path):
                        items.append(f"{prefix}{'└── ' if is_last else '├── '}{entry}/")
                        if current_depth < max_depth - 1:
                            extension = "    " if is_last else "│   "
                            items.append(_build_tree(entry_path, prefix + extension, max_depth, current_depth + 1))
                    else:
                        items.append(f"{prefix}{'└── ' if is_last else '├── '}{entry}")
            except PermissionError:
                pass
                
            return "\n".join(filter(None, items))
        
        return _build_tree(project_path)
    
    def _generate_documentation(self, project_path: str, project_data: Dict, tasks_output: List[Dict]):
        """Generate comprehensive project documentation"""
        
        docs_path = os.path.join(project_path, 'docs')
        os.makedirs(docs_path, exist_ok=True)
        
        # Create project overview
        overview = f"""# Project Overview

## {project_data.get('name', 'VirtuAI Project')}

**Description:** {project_data.get('description', 'Generated by VirtuAI Office')}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Team:** VirtuAI Office AI Agents

## Tasks Completed

"""
        
        for task in tasks_output:
            overview += f"- **{task.get('title', 'Untitled Task')}** (by {task.get('agent_name', 'Unknown Agent')})\n"
        
        overview += f"""
## Project Statistics

- Total Tasks: {len(tasks_output)}
- Agents Involved: {len(set(task.get('agent_type', 'unknown') for task in tasks_output))}
- Files Generated: [Will be updated after file creation]

## Next Steps

1. Review the generated code
2. Test the application
3. Customize as needed
4. Deploy to your preferred platform

## Support

This project was generated by VirtuAI Office. For support:
- Check the documentation in this folder
- Review the code comments
- Visit the VirtuAI Office repository for updates
"""
        
        with open(os.path.join(docs_path, 'PROJECT_OVERVIEW.md'), 'w', encoding='utf-8') as f:
            f.write(overview)
    
    def _create_zip_archive(self, project_path: str, project_name: str) -> str:
        """Create the final zip archive"""
        
        zip_filename = f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(os.path.dirname(project_path), zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, os.path.dirname(project_path))
                    zipf.write(file_path, arc_path)
        
        return zip_path

class GameZipCreator(ProjectZipCreator):
    """Specialized zip creator for game projects"""
    
    def _create_project_structure(self, project_path: str, project_type: str):
        """Create game-specific structure"""
        structure = {
            "assets": ["images", "sounds", "fonts"],
            "src": ["js", "css"],
            "levels": [],
            "docs": []
        }
        
        for main_dir, subdirs in structure.items():
            main_path = os.path.join(project_path, main_dir)
            os.makedirs(main_path, exist_ok=True)
            
            for subdir in subdirs:
                sub_path = os.path.join(main_path, subdir)
                os.makedirs(sub_path, exist_ok=True)
    
    def _create_game_index_html(self, project_path: str, project_data: Dict):
        """Create a basic index.html for the game"""
        
        game_name = project_data.get('name', 'VirtuAI Game')
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{game_name}</title>
    <link rel="stylesheet" href="src/css/style.css">
</head>
<body>
    <div id="gameContainer">
        <h1>{game_name}</h1>
        <canvas id="gameCanvas" width="800" height="600"></canvas>
        <div id="gameControls">
            <button id="startButton">Start Game</button>
            <button id="pauseButton">Pause</button>
            <button id="resetButton">Reset</button>
        </div>
        <div id="gameInfo">
            <p>Score: <span id="score">0</span></p>
            <p>Level: <span id="level">1</span></p>
        </div>
    </div>
    
    <!-- Load game scripts -->
    <script src="src/js/main.js"></script>
</body>
</html>"""
        
        with open(os.path.join(project_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
