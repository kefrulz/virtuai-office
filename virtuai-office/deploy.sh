#!/bin/bash

# VirtuAI Office - Production Deployment Script
# One-click deployment for all platforms (Linux, macOS, Windows WSL)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_NAME="virtuai-office"
BACKEND_PORT=8000
FRONTEND_PORT=3000
OLLAMA_PORT=11434

print_header() {
    echo -e "${PURPLE}"
    echo "██╗   ██╗██╗██████╗ ████████╗██╗   ██╗ █████╗ ██╗"
    echo "██║   ██║██║██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██║"
    echo "██║   ██║██║██████╔╝   ██║   ██║   ██║███████║██║"
    echo "╚██╗ ██╔╝██║██╔══██╗   ██║   ██║   ██║██╔══██║██║"
    echo " ╚████╔╝ ██║██║  ██║   ██║   ╚██████╔╝██║  ██║██║"
    echo "  ╚═══╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝"
    echo -e "${NC}"
    echo -e "${CYAN}🤖 VirtuAI Office - Complete AI Development Team${NC}"
    echo -e "${CYAN}================================================${NC}"
    echo -e "${YELLOW}Deploy 5 specialized AI agents in minutes!${NC}"
    echo ""
}

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔄 $1${NC}"; }

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WSL_DISTRO_NAME" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Check system requirements
check_requirements() {
    log_step "Checking system requirements..."
    
    local os=$(detect_os)
    local memory_gb=8
    local disk_space=20
    
    if command -v free >/dev/null 2>&1; then
        memory_gb=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo "8")
    elif command -v sysctl >/dev/null 2>&1; then
        memory_gb=$(( $(sysctl -n hw.memsize 2>/dev/null || echo "8589934592") / 1024 / 1024 / 1024 ))
    fi
    
    if command -v df >/dev/null 2>&1; then
        disk_space=$(df -BG . 2>/dev/null | awk 'NR==2{print $4}' | sed 's/G//' || echo "20")
    fi
    
    echo -e "${CYAN}System Information:${NC}"
    echo -e "  OS: $os"
    echo -e "  RAM: ${memory_gb}GB"
    echo -e "  Disk Space: ${disk_space}GB available"
    echo ""
    
    if [ "$memory_gb" -lt 8 ]; then
        log_warning "8GB+ RAM recommended for optimal AI performance"
    fi
    
    if [ "$disk_space" -lt 10 ]; then
        log_error "At least 10GB free disk space required"
        exit 1
    fi
    
    log_success "System requirements check passed"
}

# Install dependencies based on OS
install_dependencies() {
    log_step "Installing dependencies..."
    
    local os=$(detect_os)
    
    case $os in
        "linux")
            install_linux_deps
            ;;
        "macos")
            install_macos_deps
            ;;
        "windows")
            install_windows_deps
            ;;
        *)
            log_error "Unsupported operating system: $os"
            exit 1
            ;;
    esac
}

install_linux_deps() {
    log_info "Installing dependencies for Linux..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv nodejs npm git curl
    elif command -v yum &> /dev/null; then
        sudo yum update -y
        sudo yum install -y python3 python3-pip nodejs npm git curl
    elif command -v dnf &> /dev/null; then
        sudo dnf update -y
        sudo dnf install -y python3 python3-pip nodejs npm git curl
    elif command -v pacman &> /dev/null; then
        sudo pacman -Syu --noconfirm python nodejs npm git curl
    else
        log_error "Unsupported package manager. Please install Python 3, Node.js, and Git manually."
        exit 1
    fi
    
    log_success "Linux dependencies installed"
}

install_macos_deps() {
    log_info "Installing dependencies for macOS..."
    
    if ! command -v brew &> /dev/null; then
        log_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi
    
    brew update
    brew install python@3.11 node git
    
    log_success "macOS dependencies installed"
}

install_windows_deps() {
    log_info "Installing dependencies for Windows (WSL)..."
    
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv nodejs npm git curl
    
    log_success "Windows WSL dependencies installed"
}

# Install Ollama
install_ollama() {
    log_step "Installing Ollama (Local LLM engine)..."
    
    if command -v ollama &> /dev/null; then
        log_success "Ollama already installed"
        return
    fi
    
    curl -fsSL https://ollama.ai/install.sh | sh
    
    if command -v ollama &> /dev/null; then
        log_success "Ollama installed successfully"
    else
        log_error "Ollama installation failed"
        exit 1
    fi
}

# Start Ollama service
start_ollama() {
    log_step "Starting Ollama service..."
    
    if curl -s http://localhost:$OLLAMA_PORT/api/version &> /dev/null; then
        log_success "Ollama is already running"
        return
    fi
    
    ollama serve > /dev/null 2>&1 &
    local ollama_pid=$!
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:$OLLAMA_PORT/api/version &> /dev/null; then
            log_success "Ollama service started successfully"
            return
        fi
        sleep 2
        ((attempt++))
        if [ $((attempt % 5)) -eq 0 ]; then
            log_info "Waiting for Ollama to start... ($attempt/$max_attempts)"
        fi
    done
    
    log_error "Failed to start Ollama service"
    exit 1
}

# Download AI models
download_models() {
    log_step "Downloading AI models..."
    
    local memory_gb=8
    if command -v free >/dev/null 2>&1; then
        memory_gb=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo "8")
    elif command -v sysctl >/dev/null 2>&1; then
        memory_gb=$(( $(sysctl -n hw.memsize 2>/dev/null || echo "8589934592") / 1024 / 1024 / 1024 ))
    fi
    
    local models=()
    
    if [ "$memory_gb" -ge 16 ]; then
        log_info "16GB+ RAM detected - downloading high-quality models"
        models=("llama2:7b" "codellama:7b" "llama2:13b")
    else
        log_info "8-16GB RAM detected - downloading efficient models"
        models=("llama2:7b" "codellama:7b")
    fi
    
    for model in "${models[@]}"; do
        log_info "Downloading $model..."
        if ! ollama pull "$model"; then
            log_warning "Failed to download $model, continuing with other models"
        else
            log_success "$model downloaded successfully"
        fi
    done
    
    if ! ollama list | grep -q "llama2:7b"; then
        log_warning "No models found, downloading basic model..."
        ollama pull llama2:7b
    fi
    
    log_success "AI models ready"
}

# Setup backend
setup_backend() {
    log_step "Setting up Python backend..."
    
    if [ ! -d "backend" ]; then
        log_error "Backend directory not found. Please run from the project root."
        exit 1
    fi
    
    cd backend
    
    # Create requirements.txt if missing
    if [ ! -f "requirements.txt" ]; then
        log_info "Creating requirements.txt..."
        cat > requirements.txt << 'REQS'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
ollama==0.1.7
python-multipart==0.0.6
python-dateutil==2.8.2
psutil>=5.9.0
aiofiles>=23.0.0
websockets>=11.0.0
REQS
    fi
    
    python3 -m venv venv
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        source venv/Scripts/activate
    fi
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Initialize database if database.py exists
    if [ -f "database.py" ]; then
        python -c "
try:
    from database import init_db
    init_db()
    print('Database initialized successfully!')
except Exception as e:
    print(f'Database initialization skipped: {e}')
"
    fi
    
    cd ..
    log_success "Backend setup complete"
}

# Setup frontend
setup_frontend() {
    log_step "Setting up React frontend..."
    
    if [ ! -d "frontend" ]; then
        log_info "Creating frontend directory..."
        mkdir -p frontend
    fi
    
    cd frontend
    
    # Create package.json if missing
    if [ ! -f "package.json" ]; then
        log_info "Creating package.json..."
        cat > package.json << 'PKG'
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
    "extends": ["react-app", "react-app/jest"]
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}
PKG
    fi
    
    npm install
    
    cd ..
    log_success "Frontend setup complete"
}

# Create management scripts
create_scripts() {
    log_step "Creating management scripts..."
    
    if [ ! -f "start.sh" ]; then
        cat > start.sh << 'STARTSCRIPT'
#!/bin/bash

echo "🚀 Starting VirtuAI Office..."

# Start Ollama
if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "Starting Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Start backend
echo "Starting Python backend..."
cd backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi
python backend.py > ../backend.log 2>&1 &
cd ..

# Start frontend
echo "Starting React frontend..."
cd frontend
PORT=3000 npm start > ../frontend.log 2>&1 &
cd ..

echo ""
echo "✅ VirtuAI Office is starting!"
echo "🌐 Dashboard: http://localhost:3000"
echo "🔧 Backend:   http://localhost:8000"
echo "📚 Docs:      http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  Backend:  tail -f backend.log"
echo "  Frontend: tail -f frontend.log"
STARTSCRIPT

        chmod +x start.sh
    fi
    
    if [ ! -f "stop.sh" ]; then
        cat > stop.sh << 'STOPSCRIPT'
#!/bin/bash

echo "🛑 Stopping VirtuAI Office..."

# Kill Node.js processes
pkill -f "npm start" 2>/dev/null
pkill -f "node.*react-scripts" 2>/dev/null

# Kill Python processes
pkill -f "python backend.py" 2>/dev/null

echo "✅ VirtuAI Office stopped"
STOPSCRIPT

        chmod +x stop.sh
    fi
    
    log_success "Management scripts created"
}

# Start services
start_services() {
    log_step "Starting VirtuAI Office services..."
    
    ./start.sh
    
    sleep 10
    
    local backend_running=false
    local frontend_running=false
    
    for i in {1..30}; do
        if curl -s http://localhost:$BACKEND_PORT/api/status > /dev/null 2>&1; then
            backend_running=true
            break
        fi
        sleep 2
    done
    
    for i in {1..30}; do
        if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            frontend_running=true
            break
        fi
        sleep 2
    done
    
    if [ "$backend_running" = true ] && [ "$frontend_running" = true ]; then
        log_success "All services started successfully"
    else
        log_warning "Some services may still be starting. Check logs if needed."
    fi
}

# Main installation function
main() {
    print_header
    
    check_requirements
    install_dependencies
    install_ollama
    start_ollama
    download_models
    setup_backend
    setup_frontend
    create_scripts
    start_services
    
    echo ""
    echo -e "${GREEN}🎉 VirtuAI Office deployment complete!${NC}"
    echo ""
    echo -e "${CYAN}Access your AI development team:${NC}"
    echo -e "${BLUE}🌐 Dashboard: http://localhost:3000${NC}"
    echo -e "${BLUE}🔧 Backend:   http://localhost:8000${NC}"
    echo -e "${BLUE}📚 API Docs:  http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${CYAN}Management commands:${NC}"
    echo -e "${BLUE}./start.sh   - Start all services${NC}"
    echo -e "${BLUE}./stop.sh    - Stop all services${NC}"
    echo ""
    echo -e "${YELLOW}Your AI team is ready to work! 🤖👩‍💼👨‍💻👩‍💻🎨🔍${NC}"
    echo ""
    echo -e "${CYAN}Getting started:${NC}"
    echo -e "${BLUE}1. Visit http://localhost:3000${NC}"
    echo -e "${BLUE}2. Click 'New Task' to create your first task${NC}"
    echo -e "${BLUE}3. Watch your AI agents work their magic!${NC}"
}

# Error handling
handle_error() {
    echo ""
    log_error "Installation failed on line $1"
    echo ""
    echo -e "${CYAN}Troubleshooting:${NC}"
    echo -e "${BLUE}1. Check system requirements (8GB+ RAM, 10GB+ disk)${NC}"
    echo -e "${BLUE}2. Ensure you have internet connection${NC}"
    echo -e "${BLUE}3. Try running with sudo if permission errors${NC}"
    echo -e "${BLUE}4. Check logs: tail -f backend.log frontend.log${NC}"
    exit 1
}

# Set error trap
trap 'handle_error $LINENO' ERR

# Run main installation
main "$@"
