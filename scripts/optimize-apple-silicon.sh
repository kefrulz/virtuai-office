#!/bin/bash

# VirtuAI Office - Apple Silicon Optimization Script
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

# Configuration
OLLAMA_HOST="localhost:11434"
API_BASE="http://localhost:8000"

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔄 $1${NC}"; }

print_header() {
    echo -e "${PURPLE}"
    echo "  🍎 Apple Silicon Optimization for VirtuAI Office"
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
        exit 1
    fi
    
    # Get chip information
    local chip_brand=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown")
    local memory_gb=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    local cpu_cores=$(sysctl -n hw.ncpu)
    
    # Determine chip type
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
    
    # Check available disk space
    local available_gb=$(df -g . | awk 'NR==2 {print $4}')
    log_info "Available disk space: ${available_gb}GB"
    
    if [ $available_gb -lt 5 ]; then
        log_warning "Low disk space. At least 10GB recommended for optimal model storage."
    fi
}

# Optimize system settings for AI workloads
optimize_system_settings() {
    log_step "Optimizing system settings..."
    
    # Increase file descriptor limits
    ulimit -n 4096 2>/dev/null || log_warning "Could not increase file descriptor limit"
    
    # Set memory allocation preferences
    export MALLOC_ARENA_MAX=2
    export MALLOC_MMAP_THRESHOLD_=131072
    
    # Enable high-performance mode if plugged in
    if pmset -g batt | grep -q "AC Power"; then
        log_info "AC power detected - enabling high-performance mode"
        sudo pmset -c powernap 0 2>/dev/null || log_warning "Could not disable power nap (requires sudo)"
        sudo pmset -c sleep 0 2>/dev/null || log_warning "Could not disable sleep (requires sudo)"
    else
        log_info "Running on battery - using balanced power settings"
    fi
    
    log_success "System settings optimized"
}

# Configure Ollama for optimal Apple Silicon performance
optimize_ollama() {
    log_step "Optimizing Ollama for Apple Silicon..."
    
    # Check if Ollama is running
    if ! curl -s "$OLLAMA_HOST/api/version" >/dev/null 2>&1; then
        log_warning "Ollama is not running. Starting Ollama..."
        ollama serve >/dev/null 2>&1 &
        sleep 3
        
        if ! curl -s "$OLLAMA_HOST/api/version" >/dev/null 2>&1; then
            log_error "Failed to start Ollama. Please install Ollama first."
            exit 1
        fi
    fi
    
    # Set optimal thread count (leave 2 cores for system)
    local optimal_threads=$((CPU_CORES - 2))
    optimal_threads=$((optimal_threads < 1 ? 1 : optimal_threads))
    
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
    
    log_success "Ollama optimized with $optimal_threads threads and Metal acceleration"
    log_info "Max loaded models: $OLLAMA_MAX_LOADED_MODELS"
}

# Download and verify optimal models
setup_optimal_models() {
    log_step "Setting up optimal AI models..."
    
    # Get currently installed models
    local installed_models=$(ollama list | tail -n +2 | awk '{print $1}' | grep -v "^$" || echo "")
    
    log_info "Currently installed models:"
    if [ -n "$installed_models" ]; then
        echo "$installed_models" | while read model; do
            echo "  • $model"
        done
    else
        echo "  None"
    fi
    
    echo ""
    log_info "Recommended models for your ${CHIP_TYPE} (${MEMORY_GB}GB):"
    for model in "${RECOMMENDED_MODELS[@]}"; do
        echo "  • $model"
    done
    
    echo ""
    read -p "$(echo -e ${CYAN})Would you like to download recommended models? [y/N]: $(echo -e ${NC})" -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for model in "${RECOMMENDED_MODELS[@]}"; do
            if echo "$installed_models" | grep -q "^$model$"; then
                log_success "$model already installed"
            else
                log_step "Downloading $model..."
                if ollama pull "$model"; then
                    log_success "$model downloaded successfully"
                else
                    log_warning "Failed to download $model"
                fi
            fi
        done
    else
        log_info "Skipped model downloads"
    fi
}

# Apply VirtuAI Office specific optimizations
optimize_virtuai_office() {
    log_step "Applying VirtuAI Office optimizations..."
    
    # Check if VirtuAI Office API is running
    if curl -s "$API_BASE/api/status" >/dev/null 2>&1; then
        log_info "VirtuAI Office API detected - applying optimizations"
        
        # Apply Apple Silicon optimizations via API
        local optimize_response=$(curl -s -X POST "$API_BASE/api/apple-silicon/optimize" -H "Content-Type: application/json" 2>/dev/null || echo '{"optimized": false}')
        
        if echo "$optimize_response" | grep -q '"optimized": true'; then
            log_success "VirtuAI Office Apple Silicon optimizations applied"
        else
            log_warning "Could not apply VirtuAI Office optimizations via API"
        fi
    else
        log_info "VirtuAI Office API not running - manual optimization applied"
    fi
    
    # Create optimization profile file
    cat > ~/.virtuai-apple-silicon-profile << EOF
# VirtuAI Office Apple Silicon Optimization Profile
# Generated: $(date)

export CHIP_TYPE="$CHIP_TYPE"
export MEMORY_GB=$MEMORY_GB
export CPU_CORES=$CPU_CORES
export OLLAMA_NUM_THREADS=$optimal_threads
export OLLAMA_METAL=1
export OLLAMA_MAX_LOADED_MODELS=${OLLAMA_MAX_LOADED_MODELS:-2}
export MALLOC_ARENA_MAX=2
export MALLOC_MMAP_THRESHOLD_=131072

# Recommended models for this system:
$(printf '# %s\n' "${RECOMMENDED_MODELS[@]}")
EOF
    
    log_success "Optimization profile saved to ~/.virtuai-apple-silicon-profile"
}

# Performance benchmark
run_performance_benchmark() {
    echo ""
    read -p "$(echo -e ${CYAN})Would you like to run a performance benchmark? [y/N]: $(echo -e ${NC})" -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_step "Running performance benchmark..."
        
        # Check if a model is available
        local available_model=$(ollama list | tail -n +2 | head -1 | awk '{print $1}')
        
        if [ -z "$available_model" ]; then
            log_warning "No models available for benchmarking"
            return
        fi
        
        log_info "Testing model: $available_model"
        
        # Simple benchmark
        local start_time=$(date +%s.%N)
        
        local test_response=$(ollama generate "$available_model" "Write a simple Python function to calculate fibonacci numbers." --format json 2>/dev/null || echo '{"response": "benchmark failed"}')
        
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "unknown")
        
        if echo "$test_response" | grep -q "fibonacci"; then
            log_success "Benchmark completed in ${duration}s"
            
            # Estimate tokens per second (rough approximation)
            local response_text=$(echo "$test_response" | jq -r '.response' 2>/dev/null || echo "$test_response")
            local word_count=$(echo "$response_text" | wc -w | tr -d ' ')
            local tokens_per_second=$(echo "scale=2; $word_count / $duration" | bc 2>/dev/null || echo "unknown")
            
            log_info "Estimated performance: ${tokens_per_second} tokens/second"
            
            # Performance assessment
            if [ "$tokens_per_second" != "unknown" ] && [ $(echo "$tokens_per_second > 10" | bc 2>/dev/null || echo 0) -eq 1 ]; then
                log_success "Excellent performance for Apple Silicon!"
            elif [ "$tokens_per_second" != "unknown" ] && [ $(echo "$tokens_per_second > 5" | bc 2>/dev/null || echo 0) -eq 1 ]; then
                log_info "Good performance - consider using larger models if you have more RAM"
            else
                log_warning "Lower performance detected - ensure system is optimized and not under load"
            fi
        else
            log_warning "Benchmark test failed or returned unexpected results"
        fi
    fi
}

# System health check
system_health_check() {
    log_step "Running system health check..."
    
    # Check memory pressure
    local memory_pressure=$(memory_pressure 2>/dev/null | grep -i "system" | head -1 || echo "unknown")
    if echo "$memory_pressure" | grep -qi "normal"; then
        log_success "Memory pressure: Normal"
    elif echo "$memory_pressure" | grep -qi "warn"; then
        log_warning "Memory pressure: Warning - consider closing unnecessary applications"
    elif echo "$memory_pressure" | grep -qi "critical"; then
        log_error "Memory pressure: Critical - close applications or use smaller models"
    else
        log_info "Memory pressure: Unable to determine"
    fi
    
    # Check thermal state
    local thermal_state=$(pmset -g therm 2>/dev/null | grep -i "thermal" || echo "unknown")
    if [ "$thermal_state" = "unknown" ] || echo "$thermal_state" | grep -q "thermal state 0"; then
        log_success "Thermal state: Normal"
    else
        log_warning "Thermal state: Elevated - ensure good ventilation"
    fi
    
    # Check CPU usage
    local cpu_usage=$(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' 2>/dev/null || echo "unknown")
    if [ "$cpu_usage" != "unknown" ]; then
        if [ $(echo "$cpu_usage < 50" | bc 2>/dev/null || echo 1) -eq 1 ]; then
            log_success "CPU usage: ${cpu_usage}% - Good"
        elif [ $(echo "$cpu_usage < 80" | bc 2>/dev/null || echo 1) -eq 1 ]; then
            log_info "CPU usage: ${cpu_usage}% - Moderate"
        else
            log_warning "CPU usage: ${cpu_usage}% - High"
        fi
    fi
}

# Display optimization summary
show_summary() {
    echo ""
    echo -e "${PURPLE}🎉 Apple Silicon Optimization Complete!${NC}"
    echo ""
    echo -e "${CYAN}System Configuration:${NC}"
    echo "  Chip: $CHIP_TYPE"
    echo "  Memory: ${MEMORY_GB}GB unified memory"
    echo "  CPU Cores: $CPU_CORES"
    echo "  Optimized Threads: ${OLLAMA_NUM_THREADS:-$(($CPU_CORES - 2))}"
    echo "  Metal Acceleration: Enabled"
    echo ""
    echo -e "${CYAN}Recommendations:${NC}"
    echo "  • Keep your Mac plugged in during heavy AI processing"
    echo "  • Monitor memory pressure in Activity Monitor"
    echo "  • Use the VirtuAI Office Apple Silicon dashboard for real-time monitoring"
    echo "  • Run this script periodically to maintain optimal performance"
    echo ""
    echo -e "${CYAN}Quick Commands:${NC}"
    echo "  • Check status: curl http://localhost:8000/api/apple-silicon/performance"
    echo "  • View dashboard: http://localhost:3000 (Apple Silicon tab)"
    echo "  • Reload optimizations: source ~/.virtuai-apple-silicon-profile"
    echo ""
    echo -e "${GREEN}Your Apple Silicon Mac is now optimized for VirtuAI Office! 🚀${NC}"
}

# Main execution
main() {
    print_header
    
    detect_apple_silicon
    echo ""
    
    optimize_system_settings
    echo ""
    
    optimize_ollama
    echo ""
    
    setup_optimal_models
    echo ""
    
    optimize_virtuai_office
    echo ""
    
    run_performance_benchmark
    echo ""
    
    system_health_check
    echo ""
    
    show_summary
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
