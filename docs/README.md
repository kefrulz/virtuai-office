# VirtuAI Office - Complete Documentation

## 🤖 Overview

VirtuAI Office is a complete AI-powered development team that runs entirely on your local machine. It deploys 5 specialized AI agents that collaborate like a real team, with special optimization for Apple Silicon Macs.

### Key Features

- **5 Specialized AI Agents**: Product Manager, Frontend Developer, Backend Developer, UI/UX Designer, and QA Tester
- **100% Local Processing**: No cloud dependencies, complete privacy
- **Apple Silicon Optimized**: Native ARM64 support with Metal acceleration
- **Real-time Collaboration**: Agents work together on complex tasks
- **Boss AI Orchestration**: Intelligent task assignment and team coordination
- **Modern UI**: React dashboard with real-time updates
- **PWA Support**: Mobile installation and offline functionality

## 🏗️ Architecture

### Frontend (React)
- **Framework**: React 18 with hooks
- **Styling**: Tailwind CSS with custom components
- **State Management**: Context API with reducers
- **Real-time Updates**: WebSocket integration
- **PWA**: Service worker for offline functionality

### Backend (Python)
- **Framework**: FastAPI for high-performance API
- **Database**: SQLite (default) or PostgreSQL
- **AI Engine**: Ollama for local LLM processing
- **Real-time**: WebSocket for live updates

### AI Models
- **Primary**: Llama 2 (7B, 13B, 70B variants)
- **Code-focused**: Code Llama (7B, 13B, 34B)
- **Optimization**: Apple Silicon Metal acceleration

## 🚀 Quick Start

### Apple Silicon (M1/M2/M3) - Recommended
```bash
curl -fsSL https://raw.githubusercontent.com/kefrulz/virtuai-office/main/deploy-apple-silicon.sh | bash
```

### All Other Platforms
```bash
curl -fsSL https://raw.githubusercontent.com/kefrulz/virtuai-office/main/deploy.sh | bash
```

### Manual Installation

#### Prerequisites
- **macOS**: Big Sur or later (Apple Silicon recommended)
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 10GB free disk space
- **Network**: Internet connection for initial setup

#### Step-by-Step Setup

1. **Install Dependencies**
   ```bash
   # macOS
   brew install python@3.11 node ollama
   
   # Linux
   sudo apt-get install python3 python3-pip nodejs npm
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/kefrulz/virtuai-office.git
   cd virtuai-office
   ```

3. **Setup Backend**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Setup Frontend**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Download AI Models**
   ```bash
   ollama serve &
   ollama pull llama2:7b  # For 8GB+ RAM
   ollama pull llama2:13b  # For 16GB+ RAM
   ```

6. **Start Services**
   ```bash
   ./manage.sh start
   ```

## 👥 The AI Team

### 🧠 Boss AI
- **Role**: AI Orchestrator
- **Responsibilities**: Task analysis, agent coordination, workload balancing
- **Capabilities**: Smart assignment, performance optimization, team insights

### 👩‍💼 Alice Chen - Product Manager
- **Specialties**: User stories, requirements, project planning
- **Expertise**: Agile, Scrum, stakeholder analysis, product roadmap
- **Output**: User stories, acceptance criteria, project specifications

### 👨‍💻 Marcus Dev - Frontend Developer
- **Specialties**: React components, UI implementation, responsive design
- **Expertise**: JavaScript, TypeScript, CSS, HTML, state management
- **Output**: React components, styled interfaces, interactive features

### 👩‍💻 Sarah Backend - Backend Developer
- **Specialties**: APIs, databases, server-side logic
- **Expertise**: Python, FastAPI, PostgreSQL, REST APIs, authentication
- **Output**: API endpoints, database schemas, backend services

### 🎨 Luna Design - UI/UX Designer
- **Specialties**: Design systems, wireframes, user experience
- **Expertise**: UI design, prototyping, accessibility, responsive design
- **Output**: Wireframes, design specifications, style guides

### 🔍 TestBot QA - QA Tester
- **Specialties**: Test planning, automation, quality assurance
- **Expertise**: Testing strategies, pytest, Jest, Selenium, bug reporting
- **Output**: Test plans, automated tests, quality reports

## 📋 Task Management

### Creating Tasks

Tasks can be created through multiple methods:

1. **Smart Assignment** (Recommended)
   - Boss AI analyzes task requirements
   - Automatically assigns optimal agent
   - Plans collaboration if needed

2. **Manual Assignment**
   - Choose specific agent
   - Set priority and project
   - Direct task execution

### Task Lifecycle

```
Pending → In Progress → Completed
    ↓
   Failed → Retry → Pending
```

### Task Priorities
- **🔥 Urgent**: Critical, immediate attention
- **🔼 High**: Important, prioritized
- **➡️ Medium**: Standard priority
- **🔽 Low**: Nice to have

### Task Status
- **⏳ Pending**: Awaiting agent assignment
- **🔄 In Progress**: Currently being processed
- **✅ Completed**: Successfully finished
- **❌ Failed**: Error occurred, can be retried

## 🤝 Agent Collaboration

### Collaboration Types

1. **Sequential**: Agents work one after another
2. **Parallel**: Agents work simultaneously
3. **Review**: One agent reviews another's work
4. **Independent**: Single agent handles complete task

### Workflow Steps
Each collaboration includes:
- Task breakdown
- Agent assignments
- Dependencies
- Progress tracking
- Quality checkpoints

## 🍎 Apple Silicon Optimization

### Performance Benefits
- **3-5x faster** AI inference
- **Unified memory** architecture
- **Cool and quiet** operation
- **Extended battery life**
- **Native ARM64** processing

### Optimization Features
- Automatic chip detection
- Model recommendations based on RAM
- Performance monitoring
- Thermal management
- Power efficiency tuning

### Recommended Models by RAM
- **8GB**: llama2:7b, codellama:7b
- **16GB**: llama2:13b, codellama:13b
- **32GB+**: llama2:70b (when available)

## 🔧 Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=sqlite:///./virtuai_office.db

# API Configuration
API_HOST=localhost
API_PORT=8000
FRONTEND_PORT=3000

# Ollama Configuration
OLLAMA_HOST=localhost:11434
OLLAMA_NUM_THREADS=6
OLLAMA_MAX_LOADED_MODELS=2

# Apple Silicon Optimization
ENABLE_APPLE_SILICON_OPTIMIZATION=true
AUTO_DETECT_OPTIMAL_MODELS=true

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
```

### Model Configuration

Customize AI models in `backend/config.py`:

```python
MODEL_CONFIG = {
    "default_model": "llama2:7b",
    "code_model": "codellama:7b",
    "max_tokens": 2048,
    "temperature": 0.7
}
```

## 📡 API Reference

### Core Endpoints

#### Tasks
- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Create new task
- `POST /api/tasks/smart-assign` - Create with smart assignment
- `PATCH /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `POST /api/tasks/{id}/retry` - Retry failed task

#### Agents
- `GET /api/agents` - List all agents
- `GET /api/agents/{id}` - Get agent details
- `GET /api/agents/{id}/tasks` - Get agent's tasks
- `GET /api/agents/{id}/performance` - Get performance metrics

#### System
- `GET /api/status` - System health check
- `GET /api/analytics` - Performance analytics
- `POST /api/demo/populate` - Create demo data

#### Apple Silicon
- `GET /api/apple-silicon/detect` - Detect Apple Silicon
- `POST /api/apple-silicon/optimize` - Apply optimizations
- `GET /api/apple-silicon/performance` - Performance metrics
- `POST /api/apple-silicon/benchmark` - Run benchmark

### WebSocket Events

Connect to `ws://localhost:8000/ws` for real-time updates:

```javascript
{
  "type": "task_update",
  "task_id": "123",
  "status": "in_progress"
}

{
  "type": "task_completed",
  "task_id": "123",
  "agent_name": "Marcus Dev",
  "output": "Generated code..."
}

{
  "type": "task_failed",
  "task_id": "123",
  "error": "Error message"
}
```

## 🎨 Frontend Architecture

### Component Structure

```
src/
├── components/
│   ├── AgentCards.js          # Agent display components
│   ├── TaskManager.js         # Task management interface
│   ├── BossAIDashboard.js     # Boss AI control center
│   ├── AppleSiliconDashboard.js  # Apple Silicon optimization
│   ├── CollaborationWorkflow.js  # Team collaboration
│   └── NotificationSystem.js  # Real-time notifications
├── contexts/
│   ├── AppContext.js          # Global app state
│   ├── TaskContext.js         # Task management state
│   ├── AgentContext.js        # Agent management state
│   └── ThemeContext.js        # Theme and preferences
├── hooks/
│   ├── useApi.js              # API integration
│   ├── useWebSocket.js        # Real-time updates
│   └── usePerformance.js      # Performance monitoring
└── utils/
    ├── api.js                 # API utilities
    ├── helpers.js             # Utility functions
    └── constants.js           # App constants
```

### State Management

VirtuAI Office uses React Context for state management:

```javascript
// Global app context
const { state, actions } = useAppContext();

// Task-specific context
const { tasks, createTask, updateTask } = useTasks();

// Agent-specific context
const { agents, getAgentPerformance } = useAgents();
```

### Real-time Updates

WebSocket integration provides live updates:

```javascript
const { isConnected, lastMessage } = useWebSocket();

// Handle real-time task updates
useEffect(() => {
  if (lastMessage?.type === 'task_completed') {
    // Update UI, show notification
  }
}, [lastMessage]);
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=backend
```

### Frontend Tests
```bash
cd frontend
npm test -- --coverage --watchAll=false
```

### Integration Tests
```bash
# Full system test
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🚀 Deployment

### Docker Deployment

1. **Build Image**
   ```bash
   docker build -t virtuai-office:latest .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name virtuai-office \
     -p 3000:3000 \
     -p 8000:8000 \
     -p 11434:11434 \
     -v virtuai_data:/app/data \
     virtuai-office:latest
   ```

3. **Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Production Setup

1. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Database Setup**
   ```bash
   # For PostgreSQL
   createdb virtuai_office
   # Update DATABASE_URL in .env
   ```

3. **SSL/HTTPS Setup**
   ```bash
   # Configure reverse proxy (nginx/caddy)
   # Update CORS_ORIGINS for production domain
   ```

## 📊 Monitoring & Analytics

### Performance Metrics

VirtuAI Office tracks:
- Task completion rates
- Agent performance scores
- System resource usage
- AI model inference speed
- Memory and CPU utilization

### Dashboard Analytics

The analytics dashboard provides:
- Real-time performance monitoring
- Agent workload distribution
- Task completion trends
- System health status
- Apple Silicon optimization metrics

### Logging

Log levels:
- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical error conditions

## 🔧 Troubleshooting

### Common Issues

#### 1. Ollama Connection Failed
```bash
# Check if Ollama is running
ollama list

# Start Ollama if not running
ollama serve

# Check port availability
lsof -i :11434
```

#### 2. High Memory Usage
- Switch to smaller models (7B instead of 13B)
- Reduce concurrent agents
- Close unnecessary applications
- Monitor with Apple Silicon dashboard

#### 3. Slow Performance
- Check thermal throttling
- Ensure adequate RAM
- Use Apple Silicon optimizations
- Monitor system resources

#### 4. WebSocket Connection Issues
```bash
# Check backend is running
curl http://localhost:8000/api/status

# Verify WebSocket endpoint
wscat -c ws://localhost:8000/ws
```

### Log Analysis

#### Backend Logs
```bash
tail -f backend.log
```

#### Frontend Logs
```bash
# Browser console
# Service worker logs in DevTools
```

#### System Logs
```bash
# macOS
log show --predicate 'process == "ollama"' --last 1h

# Linux
journalctl -u ollama -f
```

## 🔐 Security

### Local Processing
- All AI processing happens locally
- No data sent to external servers
- Complete privacy and control

### API Security
- CORS protection
- Input validation
- SQL injection prevention
- XSS protection

### Data Storage
- SQLite for development
- PostgreSQL for production
- Encrypted connections
- Secure file handling

## 🌟 Advanced Features

### Custom Agent Creation
```python
# Add custom agent in backend/agents/
class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Custom Agent",
            type="custom_type",
            expertise=["custom", "skills"]
        )
    
    async def process_task(self, task):
        # Custom processing logic
        return result
```

### Plugin System
- Extensible architecture
- Custom tool integration
- Third-party service connections

### Advanced Collaboration
- Multi-step workflows
- Conditional logic
- Dynamic team assembly

## 📚 Best Practices

### Task Creation
- Be specific about requirements
- Include context and constraints
- Mention preferred technologies
- Break complex tasks into smaller pieces

### System Optimization
- Regular model updates
- Monitor performance metrics
- Use appropriate model sizes
- Keep system updated

### Team Management
- Regular standup reports
- Monitor agent workloads
- Balance task distribution
- Track performance trends

## 🤝 Contributing

### Development Setup
```bash
git clone https://github.com/kefrulz/virtuai-office.git
cd virtuai-office

# Install development dependencies
pip install -r backend/requirements-dev.txt
npm install --prefix frontend

# Run tests
npm run test:all
```

### Code Standards
- Follow PEP 8 for Python
- Use ESLint for JavaScript
- Add tests for new features
- Update documentation

### Pull Request Process
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Update documentation
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

### Documentation
- [Installation Guide](docs/installation.md)
- [API Reference](docs/api.md)
- [Troubleshooting](docs/troubleshooting.md)

### Community
- GitHub Issues: Bug reports and feature requests
- Discussions: Community support and ideas
- Discord: Real-time community chat

### Professional Support
Contact for enterprise support, custom development, and consulting services.

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Start VirtuAI Office
./manage.sh start

# Check status
./manage.sh status

# Stop services
./manage.sh stop

# Optimize Apple Silicon
./manage.sh optimize

# Update models
ollama pull llama2:13b

# Check logs
tail -f backend.log frontend.log
```

### Default URLs
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

### System Requirements
- **Minimum**: 8GB RAM, 10GB storage
- **Recommended**: 16GB+ RAM, 20GB+ storage
- **Optimal**: Apple Silicon Mac with 32GB+ RAM

Ready to deploy your AI workforce? 🚀
