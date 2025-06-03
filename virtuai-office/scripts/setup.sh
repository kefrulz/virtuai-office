#!/bin/bash

# VirtuAI Office - Complete Setup Script
# Creates all necessary files and directories for a complete installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${PURPLE}🤖 VirtuAI Office - Complete Setup${NC}"
echo -e "${PURPLE}=================================${NC}"
echo ""

# Create directory structure
echo -e "${CYAN}📁 Creating project structure...${NC}"
mkdir -p backend/{models,agents,api,utils,migrations}
mkdir -p frontend/{src/{components,utils,tests},public/{icons,screenshots}}
mkdir -p docs/{images,examples}
mkdir -p tests/{backend,frontend}
mkdir -p scripts
mkdir -p .github/workflows

# Create missing frontend files
echo -e "${CYAN}⚛️ Creating frontend entry files...${NC}"

# frontend/src/index.js
cat > frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import { NotificationProvider } from './components/NotificationSystem';
import { registerServiceWorker } from './utils/pwa';

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

registerServiceWorker();

if (process.env.NODE_ENV === 'production') {
  console.log('🤖 VirtuAI Office running in production mode');
} else {
  console.log('🛠️ VirtuAI Office running in development mode');
}

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
});
EOF

# frontend/src/index.css
cat > frontend/src/index.css << 'EOF'
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

code {
  font-family: 'SFMono-Regular', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
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

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-top: 2px solid var(--primary-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.card-hover {
  transition: all 0.2s ease-in-out;
}

.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
EOF

# frontend/public/index.html
cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#2563eb" />
  <meta name="description" content="Complete AI development team running locally - no cloud dependencies" />
  <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
  <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
  
  <!-- OpenGraph and Twitter Card meta tags -->
  <meta property="og:title" content="VirtuAI Office - Your AI Development Team" />
  <meta property="og:description" content="Deploy 5 specialized AI agents that collaborate like a real development team" />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="%PUBLIC_URL%/og-image.png" />
  
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="VirtuAI Office - Your AI Development Team" />
  <meta name="twitter:description" content="Deploy 5 specialized AI agents that collaborate like a real development team" />
  <meta name="twitter:image" content="%PUBLIC_URL%/twitter-image.png" />
  
  <!-- Preconnect to improve performance -->
  <link rel="preconnect" href="http://localhost:8000" />
  <link rel="preconnect" href="http://localhost:11434" />
  
  <title>VirtuAI Office - Your AI Development Team</title>
</head>
<body>
  <noscript>
    <div style="padding: 2rem; text-align: center; font-family: sans-serif;">
      <h1>🤖 VirtuAI Office</h1>
      <p>You need to enable JavaScript to run this app.</p>
      <p>VirtuAI Office requires JavaScript for the interactive dashboard and real-time updates.</p>
    </div>
  </noscript>
  <div id="root"></div>
  
  <!-- Service Worker Registration -->
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
          .then(registration => console.log('SW registered'))
          .catch(error => console.log('SW registration failed'));
      });
    }
  </script>
</body>
</html>
EOF

# Create backend structure
echo -e "${CYAN}🏗️ Creating backend structure...${NC}"

# backend/__init__.py
cat > backend/__init__.py << 'EOF'
"""
VirtuAI Office - Complete AI Development Team

A local AI-powered development team with 5 specialized agents:
- Alice Chen (Product Manager)
- Marcus Dev (Frontend Developer) 
- Sarah Backend (Backend Developer)
- Luna Design (UI/UX Designer)
- TestBot QA (Quality Assurance)
"""

__version__ = "1.0.0"
__author__ = "VirtuAI Office Contributors"
__license__ = "MIT"
EOF

# backend/database.py
cat > backend/database.py << 'EOF'
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - defaults to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./virtuai_office.db")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Database dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    """Initialize database with all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

if __name__ == "__main__":
    init_db()
EOF

# Create environment files
echo -e "${CYAN}🔧 Creating environment configuration...${NC}"

# .env.example
cat > .env.example << 'EOF'
# VirtuAI Office Environment Configuration

# Database
DATABASE_URL=sqlite:///./virtuai_office.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost/virtuai_office

# API Configuration
API_HOST=localhost
API_PORT=8000
FRONTEND_PORT=3000

# Ollama Configuration
OLLAMA_HOST=localhost:11434
OLLAMA_METAL=1
OLLAMA_NUM_THREADS=6
OLLAMA_MAX_LOADED_MODELS=2

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Logging
LOG_LEVEL=INFO
LOG_FILE=virtuai_office.log

# Apple Silicon Optimization
ENABLE_APPLE_SILICON_OPTIMIZATION=true
AUTO_DETECT_OPTIMAL_MODELS=true

# Development
DEBUG=false
RELOAD=false
EOF

# backend/.env
cat > backend/.env << 'EOF'
# VirtuAI Office Backend Environment
DATABASE_URL=sqlite:///./virtuai_office.db
LOG_LEVEL=INFO
DEBUG=true
RELOAD=true
EOF

# frontend/.env
cat > frontend/.env << 'EOF'
# VirtuAI Office Frontend Environment
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_VERSION=1.0.0
GENERATE_SOURCEMAP=false
EOF

# Create Docker configuration
echo -e "${CYAN}🐳 Creating Docker configuration...${NC}"

# Dockerfile
cat > Dockerfile << 'EOF'
# VirtuAI Office - Multi-stage Docker build

# Backend stage
FROM python:3.11-slim as backend
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# Frontend stage
FROM node:18-alpine as frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build

# Final stage
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy backend
COPY --from=backend /app/backend ./backend

# Copy frontend build
COPY --from=frontend /app/frontend/build ./frontend/build

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose ports
EXPOSE 8000 3000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/status || exit 1

# Start script
COPY scripts/docker-start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
EOF

# docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  virtuai-office:
    build: .
    ports:
      - "3000:3000"
      - "8000:8000"
      - "11434:11434"
    environment:
      - DATABASE_URL=sqlite:///./data/virtuai_office.db
      - OLLAMA_HOST=localhost:11434
    volumes:
      - virtuai_data:/app/data
      - ollama_models:/root/.ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: PostgreSQL database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: virtuai_office
      POSTGRES_USER: virtuai
      POSTGRES_PASSWORD: virtuai_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    profiles:
      - postgres

volumes:
  virtuai_data:
  ollama_models:
  postgres_data:
EOF

# Create test files
echo -e "${CYAN}🧪 Creating test structure...${NC}"

# tests/conftest.py
cat > tests/conftest.py << 'EOF'
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, get_db
from backend.backend import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
EOF

# tests/test_api.py
cat > tests/test_api.py << 'EOF'
import pytest
from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """Test API health check endpoint"""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_get_agents(client: TestClient):
    """Test getting all agents"""
    response = client.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)
    assert len(agents) == 5  # Should have 5 agents

def test_create_task(client: TestClient):
    """Test creating a new task"""
    task_data = {
        "title": "Test task",
        "description": "This is a test task for the AI team",
        "priority": "medium"
    }
    response = client.post("/api/tasks", json=task_data)
    assert response.status_code == 200
    task = response.json()
    assert task["title"] == task_data["title"]
    assert task["status"] == "pending"

def test_get_tasks(client: TestClient):
    """Test getting all tasks"""
    response = client.get("/api/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
EOF

# Create Jest configuration for frontend tests
cat > frontend/jest.config.js << 'EOF'
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/tests/setupTests.js'],
  moduleNameMapping: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/index.js',
    '!src/reportWebVitals.js',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
};
EOF

# Create frontend test setup
cat > frontend/src/tests/setupTests.js << 'EOF'
import '@testing-library/jest-dom';

// Mock WebSocket
global.WebSocket = jest.fn(() => ({
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  })
);

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;
EOF

# Create GitHub Actions workflow
echo -e "${CYAN}🚀 Creating CI/CD configuration...${NC}"

cat > .github/workflows/ci.yml << 'EOF'
name: VirtuAI Office CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
        
    - name: Run backend tests
      run: |
        cd backend
        pytest ../tests/ -v

  test-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Run frontend tests
      run: |
        cd frontend
        npm test -- --coverage --watchAll=false

  build-and-deploy:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t virtuai-office:latest .
        
    - name: Test Docker container
      run: |
        docker run -d --name test-container -p 8000:8000 virtuai-office:latest
        sleep 30
        curl -f http://localhost:8000/api/status || exit 1
        docker stop test-container
        docker rm test-container
EOF

# Create service worker
echo -e "${CYAN}📱 Creating PWA service worker...${NC}"

cat > frontend/public/sw.js << 'EOF'
const CACHE_NAME = 'virtuai-office-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});
EOF

# Create Docker start script
cat > scripts/docker-start.sh << 'EOF'
#!/bin/bash

echo "🤖 Starting VirtuAI Office in Docker..."

# Start Ollama in background
ollama serve &
sleep 5

# Pull default models
ollama pull llama2:7b &
ollama pull codellama:7b &

# Initialize database
cd /app/backend
python database.py

# Start backend
python backend.py &

# Serve frontend (simple HTTP server)
cd /app/frontend/build
python -m http.server 3000 &

# Wait for services
wait
EOF

chmod +x scripts/docker-start.sh

# Create additional documentation
echo -e "${CYAN}📚 Creating additional documentation...${NC}"

cat > CONTRIBUTING.md << 'EOF'
# Contributing to VirtuAI Office

Thank you for your interest in contributing to VirtuAI Office! This document provides guidelines and instructions for contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/virtuai-office.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Test your changes: `npm test` (frontend) and `pytest` (backend)
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature`
8. Create a Pull Request

## Development Setup

```bash
# Install dependencies
cd frontend && npm install
cd ../backend && pip install -r requirements.txt

# Start development servers
./manage.sh start
```

## Code Style

- Frontend: Follow React best practices and use Prettier
- Backend: Follow PEP 8 and use Black formatter
- Add tests for new features
- Update documentation as needed

## Reporting Issues

Please use GitHub Issues to report bugs or request features.
Include as much detail as possible:
- OS and system specs
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
EOF

cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to VirtuAI Office will be documented in this file.

## [1.0.0] - 2024-01-15

### Added
- Initial release of VirtuAI Office
- 5 specialized AI agents (Alice, Marcus, Sarah, Luna, TestBot)
- Boss AI orchestration system
- Apple Silicon optimization
- Real-time dashboard with WebSocket updates
- Complete API with OpenAPI documentation
- PWA support for mobile installation
- Comprehensive documentation and tutorials

### Features
- Local AI processing with Ollama integration
- Smart task assignment based on agent expertise
- Multi-agent collaboration workflows
- Performance monitoring and optimization
- Project management and sprint planning
- Daily standup automation
- One-click deployment scripts

### Supported Platforms
- macOS (Intel and Apple Silicon)
- Linux (Ubuntu, Debian, CentOS)
- Windows (via WSL2)

## [Unreleased]

### Planned
- Custom agent creation
- Advanced analytics dashboard
- External tool integrations
- Enterprise features
EOF

# Create final completion script
echo -e "${CYAN}✨ Creating completion verification...${NC}"

cat > scripts/verify-setup.sh << 'EOF'
#!/bin/bash

echo "🔍 Verifying VirtuAI Office setup..."

# Check required files
REQUIRED_FILES=(
    "frontend/src/index.js"
    "frontend/src/index.css"
    "frontend/public/index.html"
    "backend/__init__.py"
    "backend/database.py"
    "backend/backend.py"
    ".env.example"
    "Dockerfile"
    "docker-compose.yml"
)

echo "📁 Checking required files..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
    fi
done

echo ""
echo "📁 Directory structure:"
find . -type d -name node_modules -prune -o -type d -name __pycache__ -prune -o -type d -print | head -20

echo ""
echo "🎉 Setup verification complete!"
echo "Next steps:"
echo "1. Copy .env.example to .env and configure"
echo "2. Run ./manage.sh start to launch VirtuAI Office"
echo "3. Visit http://localhost:3000 to access dashboard"
EOF

chmod +x scripts/verify-setup.sh

# Final summary
echo ""
echo -e "${GREEN}🎉 VirtuAI Office setup complete!${NC}"
echo ""
echo -e "${BLUE}📁 Created structure:${NC}"
echo "├── frontend/ (React application)"
echo "├── backend/ (FastAPI server)"
echo "├── docs/ (Documentation)"
echo "├── tests/ (Test suites)"
echo "├── scripts/ (Utility scripts)"
echo "├── .github/ (CI/CD workflows)"
echo "└── Docker configuration"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo "1. cp .env.example .env"
echo "2. ./manage.sh start"
echo "3. Visit http://localhost:3000"
echo ""
echo -e "${BLUE}📋 Verify setup:${NC}"
echo "./scripts/verify-setup.sh"
echo ""
echo -e "${GREEN}Your AI development team is ready! 🤖${NC}"
