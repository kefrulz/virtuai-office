# VirtuAI Office - File Generator System
# Generates complete project files based on agent outputs

import os
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

class FileGenerator:
    def __init__(self):
        self.supported_project_types = {
            'javascript_game': self._generate_js_game_structure,
            'react_app': self._generate_react_app_structure,
            'python_api': self._generate_python_api_structure,
            'html_website': self._generate_html_website_structure,
            'node_api': self._generate_node_api_structure,
            'vue_app': self._generate_vue_app_structure,
            'mobile_app': self._generate_mobile_app_structure
        }
        
        self.file_templates = {
            'package.json': self._generate_package_json,
            'index.html': self._generate_index_html,
            'main.js': self._generate_main_js,
            'style.css': self._generate_style_css,
            'README.md': self._generate_readme,
            'requirements.txt': self._generate_requirements_txt,
            'app.py': self._generate_app_py,
            'server.js': self._generate_server_js
        }

    def generate_project_files(self, project_data: Dict[str, Any], agent_outputs: Dict[str, str]) -> str:
        """Generate complete project file structure based on agent outputs"""
        
        # Create temporary directory for project
        temp_dir = tempfile.mkdtemp(prefix='virtuai_project_')
        project_path = Path(temp_dir)
        
        try:
            # Determine project type from description
            project_type = self._detect_project_type(project_data.get('description', ''))
            
            # Generate base structure
            if project_type in self.supported_project_types:
                self.supported_project_types[project_type](project_path, project_data, agent_outputs)
            else:
                self._generate_generic_structure(project_path, project_data, agent_outputs)
            
            # Process agent outputs and create files
            self._process_agent_outputs(project_path, agent_outputs, project_type)
            
            # Add common files
            self._add_common_files(project_path, project_data)
            
            return str(project_path)
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise Exception(f"File generation failed: {str(e)}")

    def _detect_project_type(self, description: str) -> str:
        """Detect project type from description"""
        description_lower = description.lower()
        
        patterns = {
            'javascript_game': ['game', 'snake', 'tetris', 'pacman', 'puzzle', 'arcade', 'canvas', 'javascript game'],
            'react_app': ['react', 'react app', 'spa', 'single page', 'component'],
            'python_api': ['python api', 'flask', 'django', 'fastapi', 'rest api python'],
            'html_website': ['website', 'html', 'static site', 'landing page'],
            'node_api': ['node', 'express', 'node.js api', 'nodejs'],
            'vue_app': ['vue', 'vue.js', 'vue app'],
            'mobile_app': ['mobile app', 'ionic', 'react native', 'mobile']
        }
        
        for project_type, keywords in patterns.items():
            if any(keyword in description_lower for keyword in keywords):
                return project_type
        
        return 'generic'

    def _generate_js_game_structure(self, project_path: Path, project_data: Dict, agent_outputs: Dict):
        """Generate JavaScript game project structure"""
        
        # Create directories
        (project_path / 'css').mkdir(exist_ok=True)
        (project_path / 'js').mkdir(exist_ok=True)
        (project_path / 'assets').mkdir(exist_ok=True)
        (project_path / 'assets' / 'images').mkdir(exist_ok=True)
        (project_path / 'assets' / 'sounds').mkdir(exist_ok=True)
        
        # Base HTML structure
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div id="game-container">
        <h1>{title}</h1>
        <div id="game-area">
            <canvas id="gameCanvas" width="800" height="600"></canvas>
        </div>
        <div id="game-controls">
            <button id="startBtn">Start Game</button>
            <button id="pauseBtn">Pause</button>
            <button id="resetBtn">Reset</button>
        </div>
        <div id="score-board">
            <span>Score: <span id="score">0</span></span>
        </div>
        <div id="instructions">
            <h3>How to Play:</h3>
            <p>Game instructions will be added here.</p>
        </div>
    </div>
    <script src="js/game.js"></script>
    <script src="js/main.js"></script>
</body>
</html>""".format(title=project_data.get('title', 'Game'))
        
        self._write_file(project_path / 'index.html', html_content)

        # Base CSS structure
        css_content = """/* Game Styles */
body {
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    background-color: #1a1a1a;
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
}

#game-container {
    text-align: center;
    background-color: #2a2a2a;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 0 20px rgba(0,0,0,0.5);
}

#game-area {
    margin: 20px 0;
}

#gameCanvas {
    border: 2px solid #444;
    background-color: #000;
}

#game-controls {
    margin: 20px 0;
}

button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    margin: 0 5px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #45a049;
}

#score-board {
    font-size: 24px;
    font-weight: bold;
    margin: 20px 0;
}

#instructions {
    text-align: left;
    max-width: 400px;
    margin: 20px auto;
}"""
        
        self._write_file(project_path / 'css' / 'style.css', css_content)

        # Base JavaScript structure
        js_content = """// Game Class
class Game {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.running = false;
        this.score = 0;
        this.init();
    }

    init() {
        // Initialize game components
        this.setupEventListeners();
        this.render();
    }

    setupEventListeners() {
        // Add keyboard controls
        document.addEventListener('keydown', (e) => {
            this.handleInput(e.key);
        });
    }

    handleInput(key) {
        // Handle user input
        if (!this.running) return;
        
        switch(key) {
            case 'ArrowUp':
                // Handle up arrow
                break;
            case 'ArrowDown':
                // Handle down arrow
                break;
            case 'ArrowLeft':
                // Handle left arrow
                break;
            case 'ArrowRight':
                // Handle right arrow
                break;
        }
    }

    start() {
        this.running = true;
        this.gameLoop();
    }

    pause() {
        this.running = false;
    }

    reset() {
        this.running = false;
        this.score = 0;
        this.updateScore();
        this.init();
    }

    gameLoop() {
        if (!this.running) return;
        
        this.update();
        this.render();
        
        requestAnimationFrame(() => this.gameLoop());
    }

    update() {
        // Update game logic
    }

    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Render game objects
    }

    updateScore() {
        document.getElementById('score').textContent = this.score;
    }
}"""
        
        self._write_file(project_path / 'js' / 'game.js', js_content)

        # Main.js
        main_js = """// Main game initialization
let game;

document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('gameCanvas');
    game = new Game(canvas);

    // Button event listeners
    document.getElementById('startBtn').addEventListener('click', () => {
        game.start();
    });

    document.getElementById('pauseBtn').addEventListener('click', () => {
        game.pause();
    });

    document.getElementById('resetBtn').addEventListener('click', () => {
        game.reset();
    });
});"""
        
        self._write_file(project_path / 'js' / 'main.js', main_js)

    def _generate_react_app_structure(self, project_path: Path, project_data: Dict, agent_outputs: Dict):
        """Generate React app structure"""
        
        # Create directories
        (project_path / 'src').mkdir(exist_ok=True)
        (project_path / 'src' / 'components').mkdir(exist_ok=True)
        (project_path / 'src' / 'styles').mkdir(exist_ok=True)
        (project_path / 'public').mkdir(exist_ok=True)
        
        # Package.json
        package_json = {
            "name": project_data.get('title', 'react-app').lower().replace(' ', '-'),
            "version": "0.1.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "eslintConfig": {
                "extends": ["react-app", "react-app/jest"]
            },
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
            }
        }
        
        self._write_file(project_path / 'package.json', json.dumps(package_json, indent=2))

        # Public/index.html
        html_content = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{description}" />
    <title>{title}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>""".format(
            title=project_data.get('title', 'React App'),
            description=project_data.get('description', 'React application')
        )
        
        self._write_file(project_path / 'public' / 'index.html', html_content)

        # src/index.js
        index_js = """import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);"""
        
        self._write_file(project_path / 'src' / 'index.js', index_js)

        # src/App.js
        app_js = """import React from 'react';
import './styles/App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>{title}</h1>
        <p>Welcome to your React application!</p>
      </header>
      <main>
        {/* Main content will be added here */}
      </main>
    </div>
  );
}

export default App;""".format(title=project_data.get('title', 'React App'))
        
        self._write_file(project_path / 'src' / 'App.js', app_js)

        # src/styles/index.css
        index_css = """body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}"""
        
        self._write_file(project_path / 'src' / 'styles' / 'index.css', index_css)

        # src/styles/App.css
        app_css = """.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  padding: 40px;
  color: white;
}

.App-header h1 {
  margin: 0;
  font-size: 2.5rem;
}

main {
  padding: 20px;
}"""
        
        self._write_file(project_path / 'src' / 'styles' / 'App.css', app_css)

    def _generate_python_api_structure(self, project_path: Path, project_data: Dict, agent_outputs: Dict):
        """Generate Python API structure"""
        
        # Create directories
        (project_path / 'app').mkdir(exist_ok=True)
        (project_path / 'app' / 'models').mkdir(exist_ok=True)
        (project_path / 'app' / 'routes').mkdir(exist_ok=True)
        (project_path / 'tests').mkdir(exist_ok=True)
        
        # requirements.txt
        requirements = """fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
python-multipart==0.0.6"""
        
        self._write_file(project_path / 'requirements.txt', requirements)

        # main.py
        main_py = """from fastapi import FastAPI
from app.routes import main

app = FastAPI(
    title="{title}",
    description="{description}",
    version="1.0.0"
)

app.include_router(main.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)""".format(
            title=project_data.get('title', 'API'),
            description=project_data.get('description', 'Python API')
        )
        
        self._write_file(project_path / 'main.py', main_py)

        # app/__init__.py
        self._write_file(project_path / 'app' / '__init__.py', '')

        # app/routes/__init__.py
        self._write_file(project_path / 'app' / 'routes' / '__init__.py', '')

        # app/routes/main.py
        routes_main = """from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Welcome to {title}"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}""".format(title=project_data.get('title', 'API'))
        
        self._write_file(project_path / 'app' / 'routes' / 'main.py', routes_main)

    def _generate_html_website_structure(self, project_path: Path, project_data: Dict, agent_outputs: Dict):
        """Generate HTML website structure"""
        
        # Create directories
        (project_path / 'css').mkdir(exist_ok=True)
        (project_path / 'js').mkdir(exist_ok=True)
        (project_path / 'images').mkdir(exist_ok=True)
        
        # index.html
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <nav>
            <h1>{title}</h1>
            <ul>
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#services">Services</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="home">
            <h2>Welcome</h2>
            <p>{description}</p>
        </section>
        
        <section id="about">
            <h2>About</h2>
            <p>About section content goes here.</p>
        </section>
        
        <section id="services">
            <h2>Services</h2>
            <p>Services section content goes here.</p>
        </section>
        
        <section id="contact">
            <h2>Contact</h2>
            <p>Contact information goes here.</p>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 {title}. All rights reserved.</p>
    </footer>
    
    <script src="js/main.js"></script>
</body>
</html>""".format(
            title=project_data.get('title', 'Website'),
            description=project_data.get('description', 'Welcome to our website')
        )
        
        self._write_file(project_path / 'index.html', html_content)

        # css/style.css
        css_content = """/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
}

/* Header styles */
header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem 0;
}

nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}

nav ul {
    display: flex;
    list-style: none;
}

nav ul li {
    margin-left: 2rem;
}

nav ul li a {
    color: white;
    text-decoration: none;
    transition: color 0.3s;
}

nav ul li a:hover {
    color: #3498db;
}

/* Main content */
main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

section {
    margin-bottom: 3rem;
    padding: 2rem;
    background-color: #f8f9fa;
    border-radius: 8px;
}

h1, h2 {
    margin-bottom: 1rem;
}

/* Footer */
footer {
    background-color: #2c3e50;
    color: white;
    text-align: center;
    padding: 1rem;
}

/* Responsive design */
@media (max-width: 768px) {
    nav {
        flex-direction: column;
    }
    
    nav ul {
        margin-top: 1rem;
    }
    
    nav ul li {
        margin: 0 1rem;
    }
}"""
        
        self._write_file(project_path / 'css' / 'style.css', css_content)

        # js/main.js
        js_content = """// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('nav a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add any additional JavaScript functionality here
});"""
        
        self._write_file(project_path / 'js' / 'main.js', js_content)

    def _generate_node_api_structure(self, project_path: Path, project_data: Dict, agent_outputs: Dict):
        """Generate Node.js API structure"""
        
        # Create directories
        (project_path / 'routes').mkdir(exist_ok=True)
        (project_path / 'models').mkdir(exist_ok=True)
        (project_path / 'middleware').mkdir(exist_ok=True)
        
        # package.json
        package_json = {
            "name": project_data.get('title', 'node-api').lower().replace(' ', '-'),
            "version": "1.0.0",
            "description": project_data.get('description', 'Node.js API'),
            "main": "server.js",
            "scripts": {
                "start": "node server.js",
                "dev": "nodemon server.js"
            },
            "dependencies": {
                "express": "^4.18.2",
                "cors": "^2.8.5",
                "dotenv": "^16.3.1"
            },
            "devDependencies": {
                "nodemon": "^3.0.1"
            }
        }
        
        self._write_file(project_path / 'package.json', json.dumps(package_json, indent=2))

        # server.js
        server_js = """const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.get('/', (req, res) => {
    res.json({ message: 'Welcome to {title} API' });
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on port ${{PORT}}`);
});""".format(title=project_data.get('title', 'API'))
        
        self._write_file(project_path / 'server.js', server_js)

        # .env
        env_content = """PORT=3000
NODE_ENV=development"""
        
        self._write_file(project_path / '.env', env_content)

    def _generate_vue_app_structure(self, project_path: Path, project_data: Dict, agent_outputs: Dict):
        """Generate Vue.js app structure"""
        
        # Create directories
        (project_path / 'src').mkdir(exist_ok=True)
        (project_path / 'src' / 'components').mkdir(exist_ok=True)
        (project_path / 'public').mkdir(exist_ok=True)
        
        # package.json
        package_json = {
            "name": project_data.get('title', 'vue-app').lower().replace(' ', '-'),
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "serve": "vue-cli-service serve",
                "build": "vue-cli-service build"
            },
            "dependencies": {
                "core-js": "^3.8.3",
                "vue": "^3.2.13"
            },
            "devDependencies": {
                "@vue/cli-service": "~5.0.0"
            }
        }
        
        self._write_file(project_path / 'package.json', json.dumps(package_json, indent=2))

    def _generate_mobile_app_structure(self, project_path: Path, project_data: Dict, agent_outputs: Dict):
        """Generate mobile app structure"""
        
        # Create directories
        (project_path / 'src').mkdir(exist_ok=True)
        (project_path / 'src' / 'components').mkdir(exist_ok=True)
        (project_path / 'src' / 'pages').mkdir(exist_ok=True)
        
        # Basic mobile app structure
        # This would be expanded based on the specific mobile framework

    def _generate_generic_structure(self, project_path: Path, project_data: Dict, agent_outputs: Dict):
        """Generate generic project structure"""
        
        # Create basic directories
        (project_path / 'src').mkdir(exist_ok=True)
        (project_path / 'docs').mkdir(exist_ok=True)
        (project_path / 'tests').mkdir(exist_ok=True)

    def _process_agent_outputs(self, project_path: Path, agent_outputs: Dict[str, str], project_type: str):
        """Process agent outputs and integrate them into project files"""
        
        for agent_name, output in agent_outputs.items():
            if not output:
                continue
                
            # Extract code blocks from agent output
            code_blocks = self._extract_code_blocks(output)
            
            # Process based on agent type
            if 'marcus' in agent_name.lower() or 'frontend' in agent_name.lower():
                self._process_frontend_output(project_path, output, code_blocks, project_type)
            elif 'sarah' in agent_name.lower() or 'backend' in agent_name.lower():
                self._process_backend_output(project_path, output, code_blocks, project_type)
            elif 'luna' in agent_name.lower() or 'design' in agent_name.lower():
                self._process_design_output(project_path, output, code_blocks, project_type)
            elif 'testbot' in agent_name.lower() or 'qa' in agent_name.lower():
                self._process_qa_output(project_path, output, code_blocks, project_type)
            elif 'alice' in agent_name.lower() or 'product' in agent_name.lower():
                self._process_pm_output(project_path, output, project_type)

    def _extract_code_blocks(self, text: str) -> Dict[str, str]:
        """Extract code blocks from agent output"""
        code_blocks = {}
        
        # Pattern to match code blocks with language specification
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for i, (language, code) in enumerate(matches):
            key = f"{language}_{i}" if language else f"code_{i}"
            code_blocks[key] = code.strip()
        
        return code_blocks

    def _process_frontend_output(self, project_path: Path, output: str, code_blocks: Dict, project_type: str):
        """Process frontend developer output"""
        
        for key, code in code_blocks.items():
            if 'html' in key.lower():
                if project_type == 'javascript_game':
                    # Merge with existing index.html or create new sections
                    self._merge_html_content(project_path / 'index.html', code)
                elif project_type == 'react_app':
                    # Update React components
                    self._update_react_component(project_path / 'src', code)
                else:
                    self._write_file(project_path / 'index.html', code)
                    
            elif 'css' in key.lower():
                if project_type == 'javascript_game':
                    self._merge_css_content(project_path / 'css' / 'style.css', code)
                elif project_type == 'react_app':
                    self._write_file(project_path / 'src' / 'styles' / 'components.css', code)
                else:
                    self._write_file(project_path / 'css' / 'style.css', code)
                    
            elif 'javascript' in key.lower() or 'js' in key.lower():
                if project_type == 'javascript_game':
                    self._merge_js_content(project_path / 'js' / 'game.js', code)
                elif project_type == 'react_app':
                    self._create_react_component(project_path / 'src' / 'components', code)
                else:
                    self._write_file(project_path / 'js' / 'main.js', code)

    def _process_backend_output(self, project_path: Path, output: str, code_blocks: Dict, project_type: str):
        """Process backend developer output"""
        
        for key, code in code_blocks.items():
            if 'python' in key.lower():
                if project_type == 'python_api':
                    # Determine if it's a route, model, or main file
                    if 'route' in code.lower() or '@app.route' in code:
                        self._write_file(project_path / 'app' / 'routes' / 'api.py', code)
                    elif 'class' in code and 'Base' in code:
                        self._write_file(project_path / 'app' / 'models' / 'models.py', code)
                    else:
                        self._write_file(project_path / 'app' / 'main.py', code)
                else:
                    self._write_file(project_path / 'main.py', code)
                    
            elif 'sql' in key.lower():
                self._write_file(project_path / 'database.sql', code)
                
            elif 'json' in key.lower() and 'package' in output.lower():
                self._write_file(project_path / 'package.json', code)

    def _process_design_output(self, project_path: Path, output: str, code_blocks: Dict, project_type: str):
        """Process UI/UX designer output"""
        
        # Create design directory
        design_dir = project_path / 'design'
        design_dir.mkdir(exist_ok=True)
        
        # Save design specifications
        self._write_file(design_dir / 'design_specs.md', output)
        
        # Process any CSS/styling code
        for key, code in code_blocks.items():
            if 'css' in key.lower():
                if project_type == 'javascript_game':
                    self._merge_css_content(project_path / 'css' / 'style.css', code)
                elif project_type == 'react_app':
                    self._write_file(project_path / 'src' / 'styles' / 'design.css', code)
                else:
                    self._write_file(project_path / 'css' / 'design.css', code)

    def _process_qa_output(self, project_path: Path, output: str, code_blocks: Dict, project_type: str):
        """Process QA tester output"""
        
        # Create tests directory
        tests_dir = project_path / 'tests'
        tests_dir.mkdir(exist_ok=True)
        
        # Save test plan
        self._write_file(tests_dir / 'test_plan.md', output)
        
        # Process test code
        for key, code in code_blocks.items():
            if 'javascript' in key.lower() or 'js' in key.lower():
                self._write_file(tests_dir / 'test.js', code)
            elif 'python' in key.lower():
                self._write_file(tests_dir / 'test.py', code)

    def _process_pm_output(self, project_path: Path, output: str, project_type: str):
        """Process product manager output"""
        
        # Create docs directory
        docs_dir = project_path / 'docs'
        docs_dir.mkdir(exist_ok=True)
        
        # Save requirements and user stories
        self._write_file(docs_dir / 'requirements.md', output)

    def _merge_html_content(self, file_path: Path, new_content: str):
        """Merge new HTML content with existing file"""
        if file_path.exists():
            existing_content = file_path.read_text()
            
            # Extract body content from new HTML
            body_match = re.search(r'<body[^>]*>(.*?)</body>', new_content, re.DOTALL)
            if body_match:
                new_body = body_match.group(1).strip()
                
                # Replace the game-area content in existing HTML
                updated_content = re.sub(
                    r'(<div id="game-area">).*?(</div>)',
                    f'\\1\n{new_body}\n\\2',
                    existing_content,
                    flags=re.DOTALL
                )
                self._write_file(file_path, updated_content)
        else:
            self._write_file(file_path, new_content)

    def _merge_css_content(self, file_path: Path, new_content: str):
        """Merge new CSS content with existing file"""
        if file_path.exists():
            existing_content = file_path.read_text()
            merged_content = existing_content + "\n\n/* Generated CSS */\n" + new_content
            self._write_file(file_path, merged_content)
        else:
            self._write_file(file_path, new_content)

    def _merge_js_content(self, file_path: Path, new_content: str):
        """Merge new JavaScript content with existing file"""
        if file_path.exists():
            existing_content = file_path.read_text()
            
            # Try to intelligently merge - replace class methods or add new functions
            if 'class Game' in existing_content and 'class Game' in new_content:
                # Extract methods from new content and merge with existing class
                self._merge_js_class_methods(file_path, existing_content, new_content)
            else:
                merged_content = existing_content + "\n\n// Generated JavaScript\n" + new_content
                self._write_file(file_path, merged_content)
        else:
            self._write_file(file_path, new_content)

    def _merge_js_class_methods(self, file_path: Path, existing_content: str, new_content: str):
        """Merge JavaScript class methods intelligently"""
        
        # Extract methods from new content
        method_pattern = r'(\w+\([^{]*\)\s*{[^}]*})'
        new_methods = re.findall(method_pattern, new_content, re.DOTALL)
        
        updated_content = existing_content
        
        for method in new_methods:
            method_name = re.match(r'(\w+)\(', method).group(1)
            
            # Replace existing method or add new one
            if method_name in existing_content:
                # Replace existing method
                pattern = rf'{method_name}\([^{{]*\)\s*{{[^}}]*}}'
                updated_content = re.sub(pattern, method, updated_content, flags=re.DOTALL)
            else:
                # Add new method before the last closing brace
                updated_content = updated_content.rstrip().rstrip('}')
                updated_content += f"\n\n    {method}\n}}"
        
        self._write_file(file_path, updated_content)

    def _update_react_component(self, src_path: Path, html_content: str):
        """Update React component with new HTML structure"""
        
        # Convert HTML to JSX
        jsx_content = self._html_to_jsx(html_content)
        
        # Update App.js
        app_file = src_path / 'App.js'
        if app_file.exists():
            existing_content = app_file.read_text()
            
            # Replace the main content area
            updated_content = re.sub(
                r'(<main>).*?(</main>)',
                f'\\1\n{jsx_content}\n\\2',
                existing_content,
                flags=re.DOTALL
            )
            self._write_file(app_file, updated_content)

    def _create_react_component(self, components_path: Path, js_content: str):
        """Create a new React component from JavaScript code"""
        
        # Extract component name from code
        component_name = self._extract_component_name(js_content)
        
        # Convert to React component format
        react_component = self._js_to_react_component(js_content, component_name)
        
        self._write_file(components_path / f'{component_name}.js', react_component)

    def _html_to_jsx(self, html_content: str) -> str:
        """Convert HTML to JSX format"""
        
        jsx = html_content
        
        # Convert class to className
        jsx = re.sub(r'\bclass=', 'className=', jsx)
        
        # Convert for to htmlFor
        jsx = re.sub(r'\bfor=', 'htmlFor=', jsx)
        
        # Self-close void elements
        void_elements = ['input', 'img', 'br', 'hr', 'meta', 'link']
        for element in void_elements:
            jsx = re.sub(rf'<{element}([^>]*)(?<!/)>', rf'<{element}\1 />', jsx)
        
        return jsx

    def _js_to_react_component(self, js_content: str, component_name: str) -> str:
        """Convert JavaScript code to React component"""
        
        react_template = f"""import React, {{ useState, useEffect }} from 'react';

const {component_name} = () => {{
    // Component state and logic here
    
    useEffect(() => {{
        // Initialize component
        {js_content}
    }}, []);
    
    return (
        <div className="{component_name.lower()}">
            {{/* Component JSX here */}}
        </div>
    );
}};

export default {component_name};"""
        
        return react_template

    def _extract_component_name(self, js_content: str) -> str:
        """Extract component name from JavaScript code"""
        
        # Look for class definitions
        class_match = re.search(r'class\s+(\w+)', js_content)
        if class_match:
            return class_match.group(1)
        
        # Look for function definitions
        function_match = re.search(r'function\s+(\w+)', js_content)
        if function_match:
            return function_match.group(1)
        
        # Default name
        return 'GeneratedComponent'

    def _add_common_files(self, project_path: Path, project_data: Dict):
        """Add common project files"""
        
        # README.md
        readme_content = f"""# {project_data.get('title', 'Project')}

{project_data.get('description', 'Project description')}

## Generated by VirtuAI Office

This project was automatically generated by VirtuAI Office AI development team.

## Getting Started

### Prerequisites
- Node.js (for JavaScript projects)
- Python 3.8+ (for Python projects)

### Installation
```bash
# For Node.js projects
npm install

# For Python projects
pip install -r requirements.txt
```

### Running the Project
```bash
# For web projects
open index.html in your browser

# For Node.js projects
npm start

# For Python projects
python main.py
```

## Project Structure

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## AI Team Contributors

- 👩‍💼 **Alice Chen** (Product Manager) - Requirements and project planning
- 👨‍💻 **Marcus Dev** (Frontend Developer) - UI components and frontend logic
- 👩‍💻 **Sarah Backend** (Backend Developer) - API and backend systems
- 🎨 **Luna Design** (UI/UX Designer) - Design specifications and styling
- 🔍 **TestBot QA** (QA Tester) - Testing plans and quality assurance

## Support

This project was generated automatically. For modifications, you can:
1. Edit the files directly
2. Use VirtuAI Office to generate additional features
3. Extend the functionality as needed

---
*Generated with ❤️ by VirtuAI Office*
"""
        
        self._write_file(project_path / 'README.md', readme_content)

        # .gitignore
        gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
env/

# Build outputs
dist/
build/
*.egg-info/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Environment variables
.env
.env.local

# Temporary files
*.tmp
*.temp
"""
        
        self._write_file(project_path / '.gitignore', gitignore_content)

    def _write_file(self, file_path: Path, content: str):
        """Write content to file, creating directories if needed"""
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            file_path.write_text(content, encoding='utf-8')
        except Exception as e:
            raise Exception(f"Failed to write file {file_path}: {str(e)}")

    def cleanup_temp_directory(self, temp_path: str):
        """Clean up temporary directory"""
        
        try:
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp directory {temp_path}: {e}")

# Usage example:
# generator = FileGenerator()
# project_path = generator.generate_project_files(project_data, agent_outputs)
# # Use the project_path for zip creation
# generator.cleanup_temp_directory(project_path)
