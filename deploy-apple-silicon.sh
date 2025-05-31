#!/bin/bash

# VirtuAI Office - Apple Silicon Optimized Deployment Script
# Automatically detects and optimizes performance for M1/M2/M3 Macs

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔄 $1${NC}"; }

print_header() {
    echo -e "${PURPLE}"
    echo "  🍎 Apple Silicon Deployment for VirtuAI Office"
    echo "=================================================="
    echo -e "${NC}"
}

# Detect Apple Silicon chip type and specs
detect_apple_silicon() {
    log_step "Detecting Apple Silicon hardware..."
    
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script is for macOS only"
        exit 1
    fi
    
    local arch=$(uname -m)
    if [[ "$arch" != "arm64" ]]; then
        log_error "Apple Silicon (ARM64) not detected. This Mac appears to be Intel-based."
        log_info "Use the regular deploy.sh script instead."
        exit 1
    fi
    
    local chip_brand=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown")
    local memory_gb=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    local cpu_cores=$(sysctl -n hw.ncpu)
    
    if [[ "$chip_brand" == *"Apple M1"* ]]; then
        if [[ "$chip_brand" == *"Pro"* ]]; then
            CHIP_TYPE="M1 Pro"
        elif [[ "$chip_brand" == *"Max"* ]]; then
            CHIP_TYPE="M1 Max"
        elif [[ "$chip_brand" == *"Ultra"* ]]; then
            CHIP_TYPE="M1 Ultra"
        else
            CHIP_TYPE="M1"
        fi
    elif [[ "$chip_brand" == *"Apple M2"* ]]; then
        if [[ "$chip_brand" == *"Pro"* ]]; then
            CHIP_TYPE="M2 Pro"
        elif [[ "$chip_brand" == *"Max"* ]]; then
            CHIP_TYPE="M2 Max"
        elif [[ "$chip_brand" == *"Ultra"* ]]; then
            CHIP_TYPE="M2 Ultra"
        else
            CHIP_TYPE="M2"
        fi
    elif [[ "$chip_brand" == *"Apple M3"* ]]; then
        if [[ "$chip_brand" == *"Pro"* ]]; then
            CHIP_TYPE="M3 Pro"
        elif [[ "$chip_brand" == *"Max"* ]]; then
            CHIP_TYPE="M3 Max"
        else
            CHIP_TYPE="M3"
        fi
    else
        CHIP_TYPE="Unknown Apple Silicon"
    fi
    
    MEMORY_GB=$memory_gb
    CPU_CORES=$cpu_cores
    
    log_success "Detected: $CHIP_TYPE with ${MEMORY_GB}GB unified memory"
    log_info "CPU Cores: $CPU_CORES"
    
    local available_gb=$(df -g . | awk 'NR==2 {print $4}')
    log_info "Available disk space: ${available_gb}GB"
    
    if [ $available_gb -lt 5 ]; then
        log_warning "Low disk space. At least 10GB recommended for optimal model storage."
    fi
}

# Install dependencies optimized for Apple Silicon
install_dependencies() {
    log_step "Installing dependencies optimized for Apple Silicon..."
    
    if ! command -v brew &> /dev/null; then
        log_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Ensure Homebrew is in PATH for Apple Silicon
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    # Install native ARM64 versions
    arch -arm64 brew update
    arch -arm64 brew install python@3.11 node git ollama
    
    log_success "Apple Silicon dependencies installed"
}

# Configure optimal settings
configure_optimizations() {
    log_step "Configuring Apple Silicon optimizations..."
    
    # Calculate optimal thread count (leave 2 cores for system)
    local optimal_threads=$((CPU_CORES - 2))
    optimal_threads=$((optimal_threads < 1 ? 1 : optimal_threads))
    
    # Set environment variables for optimal performance
    export OLLAMA_NUM_THREADS=$optimal_threads
    export OLLAMA_METAL=1  # Enable Metal GPU acceleration
    
    # Configure memory usage based on available RAM
    if [ $MEMORY_GB -ge 32 ]; then
        export OLLAMA_MAX_LOADED_MODELS=3
        RECOMMENDED_MODELS=("llama2:13b" "codellama:13b" "llama2:7b")
    elif [ $MEMORY_GB -ge 16 ]; then
        export OLLAMA_MAX_LOADED_MODELS=2
        RECOMMENDED_MODELS=("llama2:7b" "codellama:7b" "llama2:13b-q4_0")
    else
        export OLLAMA_MAX_LOADED_MODELS=1
        RECOMMENDED_MODELS=("llama2:7b-q4_0" "codellama:7b-q4_0")
    fi
    
    # Save optimizations to profile
    cat > ~/.virtuai-apple-silicon-profile << EOF
# VirtuAI Office Apple Silicon Optimization Profile
export CHIP_TYPE="$CHIP_TYPE"
export MEMORY_GB=$MEMORY_GB
export CPU_CORES=$CPU_CORES
export OLLAMA_NUM_THREADS=$optimal_threads
export OLLAMA_METAL=1
export OLLAMA_MAX_LOADED_MODELS=${OLLAMA_MAX_LOADED_MODELS}
export MALLOC_ARENA_MAX=2
export MALLOC_MMAP_THRESHOLD_=131072
