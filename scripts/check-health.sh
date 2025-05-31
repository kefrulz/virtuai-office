#!/bin/bash

# VirtuAI Office - Health Check Script
# Comprehensive system health monitoring and diagnostics

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
BACKEND_PORT=8000
FRONTEND_PORT=3000
OLLAMA_PORT=11434
MAX_RESPONSE_TIME=5  # seconds

# Service URLs
BACKEND_URL="http://localhost:$BACKEND_PORT"
FRONTEND_URL="http://localhost:$FRONTEND_PORT"
OLLAMA_URL="http://localhost:$OLLAMA_PORT"

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  VirtuAI Office Health Check             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_section() { echo -e "${CYAN}🔍 $1${NC}"; echo ""; }

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check HTTP endpoint with timeout
check_endpoint() {
    local url="$1"
    local timeout="$2"
    local description="$3"
    
    if curl -s --max-time "$timeout" "$url" >/dev/null 2>&1; then
        log_success "$description is responding"
        return 0
    else
        log_error "$description is not responding"
        return 1
    fi
}

# Check process by name
check_process() {
    local process_name="$1"
    local description="$2"
    
    if pgrep -f "$process_name" >/dev/null 2>&1; then
        local pid=$(pgrep -f "$process_name" | head -1)
        log_success "$description is running (PID: $pid)"
        return 0
    else
        log_error "$description is not running"
        return 1
    fi
}

# Check system resources
check_system_resources() {
    log_section "System Resources"
    
    # Memory check
    local total_memory_gb
    local available_memory_gb
    local memory_usage_percent
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        total_memory_gb=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
        available_memory_gb=$(( $(vm_stat | awk '/Pages free/ {print $3}' | sed 's/\.//' | head -1) * 4096 / 1024 / 1024 / 1024 ))
        memory_usage_percent=$(( (total_memory_gb - available_memory_gb) * 100 / total_memory_gb ))
    else
        # Linux
        total_memory_gb=$(( $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024 / 1024 ))
        available_memory_gb=$(( $(grep MemAvailable /proc/meminfo | awk '{print $2}') / 1024 / 1024 ))
        memory_usage_percent=$(( (total_memory_gb - available_memory_gb) * 100 / total_memory_gb ))
    fi
    
    echo "Memory: ${total_memory_gb}GB total, ${available_memory_gb}GB available (${memory_usage_percent}% used)"
    
    if [ "$memory_usage_percent" -gt 90 ]; then
        log_error "Memory usage is very high (${memory_usage_percent}%)"
    elif [ "$memory_usage_percent" -gt 75 ]; then
        log_warning "Memory usage is high (${memory_usage_percent}%)"
    else
        log_success "Memory usage is normal (${memory_usage_percent}%)"
    fi
    
    # CPU check
    if command_exists "top"; then
        local cpu_usage
        if [[ "$OSTYPE" == "darwin"* ]]; then
            cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
        else
            cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
        fi
        
        if [ -n "$cpu_usage" ]; then
            echo "CPU usage: ${cpu_usage}%"
            if (( $(echo "$cpu_usage > 90" | bc -l) )); then
                log_error "CPU usage is very high (${cpu_usage}%)"
            elif (( $(echo "$cpu_usage > 70" | bc -l) )); then
                log_warning "CPU usage is high (${cpu_usage}%)"
            else
                log_success "CPU usage is normal (${cpu_usage}%)"
            fi
        fi
    fi
    
    # Disk space check
    local disk_usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    echo "Disk usage: ${disk_usage}%"
    
    if [ "$disk_usage" -gt 90 ]; then
        log_error "Disk usage is very high (${disk_usage}%)"
    elif [ "$disk_usage" -gt 80 ]; then
        log_warning "Disk usage is high (${disk_usage}%)"
    else
        log_success "Disk usage is normal (${disk_usage}%)"
    fi
    
    echo ""
}

# Check dependencies
check_dependencies() {
    log_section "Dependencies"
    
    # Python check
    if command_exists python3; then
        local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_success "Python $python_version installed"
    else
        log_error "Python 3 not found"
    fi
    
    # Node.js check
    if command_exists node; then
        local node_version=$(node --version)
        log_success "Node.js $node_version installed"
    else
        log_error "Node.js not found"
    fi
    
    # npm check
    if command_exists npm; then
        local npm_version=$(npm --version)
        log_success "npm $npm_version installed"
    else
        log_error "npm not found"
    fi
    
    # Ollama check
    if command_exists ollama; then
        local ollama_version=$(ollama --version 2>/dev/null || echo "unknown")
        log_success "Ollama $ollama_version installed"
    else
        log_error "Ollama not found"
    fi
    
    # Git check
    if command_exists git; then
        local git_version=$(git --version | cut -d' ' -f3)
        log_success "Git $git_version installed"
    else
        log_warning "Git not found (optional)"
    fi
    
    echo ""
}

# Check processes
check_processes() {
    log_section "Process Status"
    
    check_process "ollama serve" "Ollama service"
    check_process "python.*backend.py" "VirtuAI Backend"
    check_process "node.*react-scripts\|npm.*start" "VirtuAI Frontend"
    
    echo ""
}

# Check services
check_services() {
    log_section "Service Health"
    
    # Ollama API check
    if check_endpoint "$OLLAMA_URL/api/version" "$MAX_RESPONSE_TIME" "Ollama API"; then
        # Check models
        if command_exists ollama; then
            local model_count=$(ollama list 2>/dev/null | grep -c "llama\|codellama" || echo "0")
            if [ "$model_count" -gt 0 ]; then
                log_success "$model_count AI models available"
            else
                log_warning "No AI models found (run 'ollama pull llama2:7b')"
            fi
        fi
    fi
    
    # Backend API check
    if check_endpoint "$BACKEND_URL/api/status" "$MAX_RESPONSE_TIME" "VirtuAI Backend API"; then
        # Test agent endpoint
        if check_endpoint "$BACKEND_URL/api/agents" "$MAX_RESPONSE_TIME" "Agents endpoint"; then
            local agent_count=$(curl -s "$BACKEND_URL/api/agents" | grep -o '"id"' | wc -l)
            log_success "$agent_count AI agents registered"
        fi
    fi
    
    # Frontend check
    check_endpoint "$FRONTEND_URL" "$MAX_RESPONSE_TIME" "VirtuAI Frontend"
    
    echo ""
}

# Check database
check_database() {
    log_section "Database Health"
    
    if [ -f "backend/virtuai_office.db" ]; then
        local db_size=$(du -h backend/virtuai_office.db | cut -f1)
        log_success "Database file exists ($db_size)"
        
        # Check if we can query the database
        if command_exists sqlite3; then
            local table_count=$(sqlite3 backend/virtuai_office.db ".tables" | wc -w)
            log_success "$table_count database tables found"
        fi
    else
        log_error "Database file not found (backend/virtuai_office.db)"
    fi
    
    echo ""
}

# Check network connectivity
check_network() {
    log_section "Network Connectivity"
    
    # Local network check
    if ping -c 1 127.0.0.1 >/dev/null 2>&1; then
        log_success "Local network (127.0.0.1) reachable"
    else
        log_error "Local network connectivity issue"
    fi
    
    # Internet check (optional)
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_success "Internet connectivity available"
    else
        log_warning "No internet connectivity (optional for VirtuAI Office)"
    fi
    
    echo ""
}

# Check Apple Silicon optimization (if applicable)
check_apple_silicon() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        log_section "Apple Silicon Status"
        
        local chip_info=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown")
        echo "Chip: $chip_info"
        
        if [[ "$chip_info" == *"Apple"* ]]; then
            log_success "Apple Silicon detected"
            
            # Check for Metal optimization
            if [ "$OLLAMA_METAL" = "1" ]; then
                log_success "Metal GPU acceleration enabled"
            else
                log_warning "Metal GPU acceleration not enabled (set OLLAMA_METAL=1)"
            fi
            
            # Check memory pressure
            if command_exists memory_pressure; then
                local pressure=$(memory_pressure 2>/dev/null | head -1)
                if [[ "$pressure" == *"normal"* ]]; then
                    log_success "Memory pressure is normal"
                else
                    log_warning "Memory pressure detected: $pressure"
                fi
            fi
        else
            log_info "Intel Mac detected - Apple Silicon optimizations not available"
        fi
        
        echo ""
    fi
}

# Performance test
run_performance_test() {
    log_section "Performance Test"
    
    if check_endpoint "$BACKEND_URL/api/status" 2; then
        echo "Running quick performance test..."
        
        # Time the status endpoint
        local start_time=$(date +%s.%N)
        curl -s "$BACKEND_URL/api/status" >/dev/null
        local end_time=$(date +%s.%N)
        local response_time=$(echo "$end_time - $start_time" | bc)
        
        echo "API response time: ${response_time}s"
        
        if (( $(echo "$response_time < 1.0" | bc -l) )); then
            log_success "API response time is excellent"
        elif (( $(echo "$response_time < 3.0" | bc -l) )); then
            log_success "API response time is good"
        else
            log_warning "API response time is slow"
        fi
    fi
    
    echo ""
}

# Generate health report
generate_report() {
    log_section "Health Summary"
    
    local total_checks=0
    local passed_checks=0
    local warnings=0
    local errors=0
    
    # Count results (simplified for demo)
    if pgrep -f "ollama serve" >/dev/null; then ((passed_checks++)); fi
    if pgrep -f "python.*backend.py" >/dev/null; then ((passed_checks++)); fi
    if pgrep -f "node.*react-scripts\|npm.*start" >/dev/null; then ((passed_checks++)); fi
    if curl -s --max-time 2 "$BACKEND_URL/api/status" >/dev/null; then ((passed_checks++)); fi
    if curl -s --max-time 2 "$FRONTEND_URL" >/dev/null; then ((passed_checks++)); fi
    
    total_checks=5
    
    local health_percentage=$(( passed_checks * 100 / total_checks ))
    
    echo "Health Score: $passed_checks/$total_checks checks passed ($health_percentage%)"
    
    if [ "$health_percentage" -ge 80 ]; then
        log_success "System is healthy and ready for AI development!"
    elif [ "$health_percentage" -ge 60 ]; then
        log_warning "System has minor issues but should work"
    else
        log_error "System has significant issues that need attention"
    fi
    
    echo ""
    echo -e "${CYAN}📋 Quick Actions:${NC}"
    
    if ! pgrep -f "ollama serve" >/dev/null; then
        echo "• Start Ollama: ollama serve"
    fi
    
    if ! pgrep -f "python.*backend.py" >/dev/null; then
        echo "• Start Backend: cd backend && python backend.py"
    fi
    
    if ! pgrep -f "node.*react-scripts\|npm.*start" >/dev/null; then
        echo "• Start Frontend: cd frontend && npm start"
    fi
    
    if ! curl -s --max-time 2 "$OLLAMA_URL/api/version" >/dev/null; then
        echo "• Check Ollama models: ollama list"
        echo "• Download model: ollama pull llama2:7b"
    fi
    
    echo ""
    echo -e "${PURPLE}💡 For detailed troubleshooting, see: docs/TROUBLESHOOTING.md${NC}"
}

# Main execution
main() {
    print_header
    
    check_system_resources
    check_dependencies
    check_processes
    check_services
    check_database
    check_network
    check_apple_silicon
    run_performance_test
    generate_report
    
    echo -e "${CYAN}Health check completed at $(date)${NC}"
}

# Run health check
main "$@"
