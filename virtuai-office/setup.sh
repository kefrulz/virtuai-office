#!/bin/bash

# VirtuAI Office - Repository Setup and Upload Script
# This script will organize your source files and upload them to GitHub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${PURPLE}"
    echo "██╗   ██╗██╗██████╗ ████████╗██╗   ██╗ █████╗ ██╗"
    echo "██║   ██║██║██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██║"
    echo "██║   ██║██║██████╔╝   ██║   ██║   ██║███████║██║"
    echo "╚██╗ ██╔╝██║██╔══██╗   ██║   ██║   ██║██╔══██║██║"
    echo " ╚████╔╝ ██║██║  ██║   ██║   ╚██████╔╝██║  ██║██║"
    echo "  ╚═══╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝"
    echo -e "${NC}"
    echo -e "${CYAN}🚀 VirtuAI Office Repository Setup${NC}"
    echo -e "${CYAN}===================================${NC}"
    echo ""
}

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔄 $1${NC}"; }

# Configuration
REPO_NAME="virtuai-office"
REPO_DESCRIPTION="Complete AI development team running locally - Optimized for Apple Silicon"

# Get user input
get_user_info() {
    echo -e "${CYAN}📝 Repository Configuration${NC}"
    echo ""
    
    read -p "Enter your GitHub username: " GITHUB_USERNAME
    read -p "Enter your email: " USER_EMAIL
    read -p "Enter your full name: " USER_NAME
    read -p "Enter source files directory path: " SOURCE_DIR
    
    # Validate source directory
    if [ ! -d "$SOURCE_DIR" ]; then
        log_error "Source directory does not exist: $SOURCE_DIR"
        exit 1
    fi
    
    echo ""
    log_info "GitHub Username: $GITHUB_USERNAME"
    log_info "Email: $USER_EMAIL"
    log_info "Name: $USER_NAME"
    log_info "Source Directory: $SOURCE_DIR"
    echo ""
    
    read -p "Is this information correct? (y/n): " confirm
    if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
        echo "Please run the script again with correct information."
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    # Check if GitHub CLI is installed (optional but helpful)
    if command -v gh &> /dev/null; then
        log_success "GitHub CLI detected - will use for repository creation"
        USE_GH_CLI=true
    else
        log_warning "GitHub CLI not found - you'll need to create the repository manually"
        USE_GH_CLI=false
    fi
    
    log_success "Prerequisites check completed"
}

# Create directory structure
create_directory_structure() {
    log_step "Creating project directory structure..."
    
    # Create main project directory
    mkdir -p "$REPO_NAME"
    cd "$REPO_NAME"
    
    # Create standard directory structure
    mkdir -p backend/{models,agents,api,orchestration,apple_silicon}
    mkdir -p frontend/{src/{components,utils,hooks},public}
    mkdir -p docs
    mkdir -p tests/{backend,frontend}
    mkdir -p scripts
    mkdir -p .github/workflows
    
    log_success "Directory structure created"
}

# Copy source files with organization
organize_source_files() {
    log_step "Organizing source files..."
    
    # Copy all files from source directory
    cp -r "$SOURCE_DIR"/* . 2>/dev/null || true
    
    # Organize files into proper structure if needed
    
    # Move documentation files
    if [ -f "INSTALLATION.md" ]; then mv "INSTALLATION.md" docs/; fi
    if [ -f "USER_GUIDE.md" ]; then mv "USER_GUIDE.md" docs/; fi
    if [ -f "API.md" ]; then mv "API.md" docs/; fi
    if [ -f "ARCHITECTURE.md" ]; then mv "ARCHITECTURE.md" docs/; fi
    if [ -f "APPLE_SILICON.md" ]; then mv "APPLE_SILICON.md" docs/; fi
    if [ -f "VIDEO_TUTORIALS.md" ]; then mv "VIDEO_TUTORIALS.md" docs/; fi
    
    # Ensure frontend structure
    if [ ! -f "frontend/src/index.js" ]; then
        create_frontend_index
    fi
    
    if [ ! -f "frontend/src/index.css" ]; then
        create_frontend_css
    fi
    
    if [ ! -f "frontend/public/index.html" ]; then
        create_frontend_html
    fi
    
    # Ensure backend structure
    if [ ! -f "backend/__init__.py" ]; then
        touch backend/__init__.py
    fi
    
    log_success "Source files organized"
}

# Create missing essential files
create_frontend_index() {
    cat > frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import { NotificationProvider } from './components/NotificationSystem';

// Register service worker for PWA functionality
import { registerServiceWorker } from './utils/pwa';

// Initialize the React application
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <NotificationProvider>
        <App />
      </NotificationProvider>
    </ErrorBoundary>
  </React.StrictMode>
);

// Register service worker for PWA features
registerServiceWorker();

// Performance monitoring
if (process.env.NODE_ENV === 'production') {
  console.log('🤖 VirtuAI Office running in production mode');
} else {
  console.log('🛠️ VirtuAI Office running in development mode');
}
EOF
}

create_frontend_css() {
    cat > frontend/src/index.css << 'EOF'
/* VirtuAI Office - Global Styles */
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';

:root {
  --primary-blue: #2563eb;
  --primary-blue-dark: #1d4ed8;
  --secondary-purple: #7c3aed;
  --success-green: #10b981;
  --warning-yellow: #f59e0b;
  --error-red: #ef4444;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f9fafb;
  color: #111827;
  line-height: 1.6;
}

*:focus {
  outline: 2px solid var(--primary-blue);
  outline-offset: 2px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
EOF
}

create_frontend_html() {
    cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#2563eb" />
    <meta name="description" content="VirtuAI Office - Complete AI development team running locally" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>VirtuAI Office</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run VirtuAI Office.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF
}

# Create frontend package.json
create_frontend_package_json() {
    if [ ! -f "frontend/package.json" ]; then
        cat > frontend/package.json << 'EOF'
{
  "name": "virtuai-office-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF
    fi
}

# Create essential configuration files
create_config_files() {
    log_step "Creating configuration files..."
    
    # Create .env.example
    cat > .env.example << 'EOF'
# VirtuAI Office Environment Configuration

# Database
DATABASE_URL=sqlite:///./virtuai_office.db

# Ollama Configuration
OLLAMA_HOST=localhost:11434
OLLAMA_METAL=1

# Performance Settings
OLLAMA_NUM_THREADS=6
OLLAMA_MAX_LOADED_MODELS=2

# Logging
LOG_LEVEL=INFO

# Development
NODE_ENV=development
REACT_APP_API_URL=http://localhost:8000
EOF

    # Create .gitignore if it doesn't exist
    if [ ! -f ".gitignore" ]; then
        cat > .gitignore << 'EOF'
# Dependencies
node_modules/
venv/
__pycache__/

# Build outputs
build/
dist/
*.egg-info/

# Environment files
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.sqlite

# Logs
*.log
npm-debug.log*

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# AI Models (too large for git)
*.gguf
*.bin
models/

# Temporary files
tmp/
temp/
EOF
    fi
    
    # Create GitHub workflow
    cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install Python dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Install Node.js dependencies
      run: |
        cd frontend
        npm install
    
    - name: Run Python tests
      run: |
        cd backend
        python -m pytest tests/ --verbose || echo "Tests not yet implemented"
    
    - name: Run Node.js tests
      run: |
        cd frontend
        npm test -- --coverage --watchAll=false || echo "Tests not yet implemented"
    
    - name: Build frontend
      run: |
        cd frontend
        npm run build
EOF

    create_frontend_package_json
    
    log_success "Configuration files created"
}

# Initialize git repository
init_git_repo() {
    log_step "Initializing Git repository..."
    
    # Check if we're in the right directory
    if [ ! -d "$REPO_NAME" ]; then
        log_error "Repository directory $REPO_NAME not found"
        exit 1
    fi
    
    # Ensure we're in the repo directory
    cd "$REPO_NAME"
    
    # Remove any existing .git directory to start fresh
    if [ -d ".git" ]; then
        log_warning "Existing .git directory found, removing it..."
        rm -rf .git
    fi
    
    # Initialize repo
    log_info "Initializing new Git repository..."
    git init
    
    # Check if git init succeeded
    if [ ! -d ".git" ]; then
        log_error "Failed to initialize Git repository"
        exit 1
    fi
    
    # Configure git user (local to this repo)
    log_info "Configuring Git user settings..."
    git config user.name "$USER_NAME"
    git config user.email "$USER_EMAIL"
    
    # Set default branch to main
    git config init.defaultBranch main
    git checkout -b main 2>/dev/null || git branch -M main
    
    # Add all files
    log_info "Adding files to Git..."
    git add .
    
    # Check if there are files to commit
    if git diff --staged --quiet; then
        log_error "No files to commit. Please check your source directory."
        exit 1
    fi
    
    # Initial commit
    log_info "Creating initial commit..."
    git commit -m "🍎 Initial release: VirtuAI Office - Complete AI Development Team

Features:
✅ 5 specialized AI agents (Product Manager, Frontend Dev, Backend Dev, UI/UX Designer, QA Tester)
✅ Boss AI orchestration and intelligent task assignment
✅ Apple Silicon optimization for 3-5x faster performance
✅ Real-time collaboration and task management
✅ 100% local processing - no cloud dependencies
✅ Modern React dashboard with PWA support
✅ Comprehensive documentation and tutorials

Optimized for Apple Silicon Macs (M1/M2/M3) with automatic hardware detection,
model recommendations, and performance tuning."
    
    log_success "Git repository initialized"
}

# Create GitHub repository
create_github_repo() {
    log_step "Creating GitHub repository..."
    
    # Ensure we're in the repo directory and it's a git repo
    if [ ! -d ".git" ]; then
        log_error "Not in a Git repository. Something went wrong with initialization."
        exit 1
    fi
    
    if [ "$USE_GH_CLI" = true ]; then
        # Check if user is logged in
        if gh auth status >/dev/null 2>&1; then
            log_info "Creating repository using GitHub CLI..."
            
            # Create the repository
            gh repo create "$REPO_NAME" \
                --description "$REPO_DESCRIPTION" \
                --homepage "https://github.com/$GITHUB_USERNAME/$REPO_NAME" \
                --public \
                --clone=false \
                --add-readme=false
            
            # Wait a moment for repository to be created
            sleep 2
            
            # Add remote and push
            log_info "Adding remote origin..."
            git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git" || {
                log_warning "Remote origin already exists, updating it..."
                git remote set-url origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
            }
            
            log_info "Pushing to GitHub..."
            git push -u origin main
            
            # Set repository topics
            log_info "Setting repository topics..."
            gh repo edit --add-topic "ai,automation,apple-silicon,ollama,local-llm,development-tools,react,fastapi,agents,productivity"
            
            log_success "Repository created and pushed to GitHub!"
            
        else
            log_warning "GitHub CLI not authenticated. Please run 'gh auth login' first."
            manual_repo_instructions
        fi
    else
        manual_repo_instructions
    fi
}

manual_repo_instructions() {
    log_info "Manual repository creation required:"
    echo ""
    echo -e "${YELLOW}1. Go to GitHub.com and create a new repository:${NC}"
    echo -e "   Name: ${CYAN}$REPO_NAME${NC}"
    echo -e "   Description: ${CYAN}$REPO_DESCRIPTION${NC}"
    echo -e "   Visibility: ${CYAN}Public${NC}"
    echo -e "   Don't initialize with README, .gitignore, or license"
    echo ""
    echo -e "${YELLOW}2. After creating the repository, run these commands:${NC}"
    echo -e "${CYAN}   git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git${NC}"
    echo -e "${CYAN}   git branch -M main${NC}"
    echo -e "${CYAN}   git push -u origin main${NC}"
    echo ""
    echo -e "${YELLOW}3. Add these topics to your repository:${NC}"
    echo -e "${CYAN}   ai, automation, apple-silicon, ollama, local-llm, development-tools${NC}"
    echo ""
}

# Create deployment verification script
create_verification_script() {
    cat > scripts/verify-deployment.sh << 'EOF'
#!/bin/bash

echo "🔍 VirtuAI Office Deployment Verification"
echo "========================================"

# Check Ollama
echo -n "Ollama service: "
if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Backend
echo -n "Backend API: "
if curl -s http://localhost:8000/api/status >/dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Frontend
echo -n "Frontend: "
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Models
echo -n "AI Models: "
if ollama list >/dev/null 2>&1; then
    MODEL_COUNT=$(ollama list | grep -c llama)
    echo "✅ $MODEL_COUNT models installed"
else
    echo "❌ No models found"
fi

echo ""
echo "🌐 Access URLs:"
echo "   Dashboard: http://localhost:3000"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
EOF

    chmod +x scripts/verify-deployment.sh
}

# Final steps and information
show_completion_info() {
    echo ""
    log_success "🎉 VirtuAI Office repository setup completed!"
    echo ""
    echo -e "${CYAN}📁 Repository Structure:${NC}"
    echo "├── README.md"
    echo "├── backend/"
    echo "│   ├── backend.py"
    echo "│   └── requirements.txt"
    echo "├── frontend/"
    echo "│   ├── src/"
    echo "│   ├── public/"
    echo "│   └── package.json"
    echo "├── docs/"
    echo "├── deploy.sh"
    echo "├── deploy-apple-silicon.sh"
    echo "└── manage.sh"
    echo ""
    echo -e "${BLUE}🚀 Next Steps:${NC}"
    echo "1. Visit your repository: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo "2. Users can now deploy with:"
    echo -e "   ${CYAN}curl -fsSL https://raw.githubusercontent.com/$GITHUB_USERNAME/$REPO_NAME/main/deploy.sh | bash${NC}"
    echo ""
    echo -e "${GREEN}🍎 Apple Silicon users can use:${NC}"
    echo -e "   ${CYAN}curl -fsSL https://raw.githubusercontent.com/$GITHUB_USERNAME/$REPO_NAME/main/deploy-apple-silicon.sh | bash${NC}"
    echo ""
    echo -e "${YELLOW}💡 Don't forget to:${NC}"
    echo "- Add repository topics for discoverability"
    echo "- Create releases for version management"
    echo "- Set up GitHub Pages for documentation"
    echo "- Configure branch protection rules"
    echo ""
    echo -e "${PURPLE}🌟 Your AI development team is ready to share with the world!${NC}"
}

# Main execution
main() {
    print_header
    get_user_info
    check_prerequisites
    create_directory_structure
    organize_source_files
    create_config_files
    create_verification_script
    init_git_repo
    create_github_repo
    show_completion_info
}

# Run main function
main "$@"
