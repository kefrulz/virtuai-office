#!/bin/bash

# VirtuAI Office - Performance Testing Script
# Tests system performance, AI inference speed, and overall health

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
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
OLLAMA_URL="http://localhost:11434"
TEST_DURATION=30
CONCURRENT_USERS=5

print_header() {
    echo -e "${PURPLE}"
    echo "██╗   ██╗██╗██████╗ ████████╗██╗   ██╗ █████╗ ██╗"
    echo "██║   ██║██║██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██║"
    echo "██║   ██║██║██████╔╝   ██║   ██║   ██║███████║██║"
    echo "╚██╗ ██╔╝██║██╔══██╗   ██║   ██║   ██║██╔══██║██║"
    echo " ╚████╔╝ ██║██║  ██║   ██║   ╚██████╔╝██║  ██║██║"
    echo "  ╚═══╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝"
    echo -e "${NC}"
    echo -e "${CYAN}🔬 VirtuAI Office Performance Test Suite${NC}"
    echo -e "${CYAN}=======================================${NC}"
    echo ""
}

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_test() { echo -e "${PURPLE}🧪 $1${NC}"; }

# Test results storage
RESULTS_DIR="./test-results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# System information collection
collect_system_info() {
    log_test "Collecting system information..."
    
    cat > "$RESULTS_DIR/system_info.txt" << EOF
VirtuAI Office Performance Test Report
Generated: $(date)
======================================

SYSTEM INFORMATION:
Operating System: $(uname -s) $(uname -r)
Architecture: $(uname -m)
Hostname: $(hostname)
Uptime: $(uptime)

HARDWARE:
$(if command -v lscpu >/dev/null 2>&1; then
    echo "CPU Information:"
    lscpu | grep -E "(Model name|CPU\(s\)|Thread|Core|Socket)"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "CPU Information:"
    sysctl -n machdep.cpu.brand_string
    echo "CPU Cores: $(sysctl -n hw.ncpu)"
    echo "Memory: $(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))GB"
fi)

MEMORY:
$(if command -v free >/dev/null 2>&1; then
    free -h
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Total Memory: $(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))GB"
    vm_stat | head -6
fi)

STORAGE:
$(df -h | grep -E "(^/dev/|^Filesystem)")

NETWORK:
$(if command -v ip >/dev/null 2>&1; then
    ip addr show | grep -E "(inet |link/)"
elif command -v ifconfig >/dev/null 2>&1; then
    ifconfig | grep -E "(inet |ether )"
fi)

EOF
    
    log_success "System information collected"
}

# Test service availability
test_service_availability() {
    log_test "Testing service availability..."
    
    local backend_status="❌ DOWN"
    local frontend_status="❌ DOWN"
    local ollama_status="❌ DOWN"
    
    # Test backend
    if curl -s --max-time 5 "$BACKEND_URL/api/status" >/dev/null 2>&1; then
        backend_status="✅ UP"
    fi
    
    # Test frontend
    if curl -s --max-time 5 "$FRONTEND_URL" >/dev/null 2>&1; then
        frontend_status="✅ UP"
    fi
    
    # Test Ollama
    if curl -s --max-time 5 "$OLLAMA_URL/api/version" >/dev/null 2>&1; then
        ollama_status="✅ UP"
    fi
    
    cat > "$RESULTS_DIR/service_availability.txt" << EOF
SERVICE AVAILABILITY TEST:
Backend ($BACKEND_URL): $backend_status
Frontend ($FRONTEND_URL): $frontend_status
Ollama ($OLLAMA_URL): $ollama_status
EOF
    
    log_info "Backend: $backend_status"
    log_info "Frontend: $frontend_status"
    log_info "Ollama: $ollama_status"
}

# Test API response times
test_api_performance() {
    log_test "Testing API performance..."
    
    local endpoints=(
        "/api/status"
        "/api/agents"
        "/api/tasks"
        "/api/projects"
        "/api/analytics"
    )
    
    echo "API PERFORMANCE TEST:" > "$RESULTS_DIR/api_performance.txt"
    echo "=====================" >> "$RESULTS_DIR/api_performance.txt"
    echo "" >> "$RESULTS_DIR/api_performance.txt"
    
    for endpoint in "${endpoints[@]}"; do
        log_info "Testing endpoint: $endpoint"
        
        local response_times=()
        local success_count=0
        
        for i in {1..10}; do
            local start_time=$(date +%s.%N)
            if curl -s --max-time 10 "$BACKEND_URL$endpoint" >/dev/null 2>&1; then
                local end_time=$(date +%s.%N)
                local response_time=$(echo "$end_time - $start_time" | bc)
                response_times+=($response_time)
                ((success_count++))
            fi
        done
        
        if [ ${#response_times[@]} -gt 0 ]; then
            local avg_time=$(echo "${response_times[@]}" | tr ' ' '\n' | awk '{sum+=$1} END {print sum/NR}')
            local min_time=$(printf '%s\n' "${response_times[@]}" | sort -n | head -1)
            local max_time=$(printf '%s\n' "${response_times[@]}" | sort -n | tail -1)
            
            echo "Endpoint: $endpoint" >> "$RESULTS_DIR/api_performance.txt"
            echo "  Success Rate: $success_count/10 ($(( success_count * 10 ))%)" >> "$RESULTS_DIR/api_performance.txt"
            echo "  Average Response Time: ${avg_time}s" >> "$RESULTS_DIR/api_performance.txt"
            echo "  Min Response Time: ${min_time}s" >> "$RESULTS_DIR/api_performance.txt"
            echo "  Max Response Time: ${max_time}s" >> "$RESULTS_DIR/api_performance.txt"
            echo "" >> "$RESULTS_DIR/api_performance.txt"
            
            log_success "$endpoint - Avg: ${avg_time}s, Success: $success_count/10"
        else
            echo "Endpoint: $endpoint - FAILED" >> "$RESULTS_DIR/api_performance.txt"
            echo "" >> "$RESULTS_DIR/api_performance.txt"
            log_error "$endpoint - All requests failed"
        fi
    done
}

# Test AI inference performance
test_ai_inference() {
    log_test "Testing AI inference performance..."
    
    local test_prompts=(
        "Hello, how are you?"
        "Write a simple Python function to add two numbers."
        "Explain the concept of variables in programming."
    )
    
    echo "AI INFERENCE PERFORMANCE TEST:" > "$RESULTS_DIR/ai_inference.txt"
    echo "==============================" >> "$RESULTS_DIR/ai_inference.txt"
    echo "" >> "$RESULTS_DIR/ai_inference.txt"
    
    # Get available models
    local models
    if models=$(curl -s "$OLLAMA_URL/api/tags" | grep -o '"name":"[^"]*"' | cut -d'"' -f4); then
        log_info "Available models: $(echo $models | tr '\n' ' ')"
    else
        log_warning "Could not retrieve model list"
        models="llama2:7b"
    fi
    
    for model in $models; do
        log_info "Testing model: $model"
        echo "Model: $model" >> "$RESULTS_DIR/ai_inference.txt"
        
        local total_time=0
        local total_tokens=0
        local success_count=0
        
        for prompt in "${test_prompts[@]}"; do
            log_info "Testing prompt: ${prompt:0:30}..."
            
            local start_time=$(date +%s.%N)
            local response
            
            if response=$(curl -s --max-time 60 -X POST "$OLLAMA_URL/api/generate" \
                -H "Content-Type: application/json" \
                -d "{\"model\":\"$model\",\"prompt\":\"$prompt\",\"stream\":false}"); then
                
                local end_time=$(date +%s.%N)
                local inference_time=$(echo "$end_time - $start_time" | bc)
                
                # Extract response length (approximate token count)
                local response_length=$(echo "$response" | grep -o '"response":"[^"]*"' | wc -c)
                local token_count=$(( response_length / 4 ))  # Rough approximation
                
                total_time=$(echo "$total_time + $inference_time" | bc)
                total_tokens=$(( total_tokens + token_count ))
                ((success_count++))
                
                echo "  Prompt: $prompt" >> "$RESULTS_DIR/ai_inference.txt"
                echo "    Inference Time: ${inference_time}s" >> "$RESULTS_DIR/ai_inference.txt"
                echo "    Tokens: ~$token_count" >> "$RESULTS_DIR/ai_inference.txt"
                echo "    Tokens/Second: $(echo "scale=2; $token_count / $inference_time" | bc)" >> "$RESULTS_DIR/ai_inference.txt"
                echo "" >> "$RESULTS_DIR/ai_inference.txt"
                
                log_success "Inference time: ${inference_time}s, ~$token_count tokens"
            else
                log_error "Failed to generate response for prompt"
                echo "  Prompt: $prompt - FAILED" >> "$RESULTS_DIR/ai_inference.txt"
            fi
        done
        
        if [ $success_count -gt 0 ]; then
            local avg_time=$(echo "scale=3; $total_time / $success_count" | bc)
            local avg_tokens_per_sec=$(echo "scale=2; $total_tokens / $total_time" | bc)
            
            echo "  Summary:" >> "$RESULTS_DIR/ai_inference.txt"
            echo "    Success Rate: $success_count/${#test_prompts[@]}" >> "$RESULTS_DIR/ai_inference.txt"
            echo "    Average Inference Time: ${avg_time}s" >> "$RESULTS_DIR/ai_inference.txt"
            echo "    Average Tokens/Second: $avg_tokens_per_sec" >> "$RESULTS_DIR/ai_inference.txt"
            echo "" >> "$RESULTS_DIR/ai_inference.txt"
            
            log_success "$model - Avg: ${avg_time}s, ${avg_tokens_per_sec} tokens/sec"
        fi
        echo "----------------------------------------" >> "$RESULTS_DIR/ai_inference.txt"
    done
}

# Test concurrent task creation
test_concurrent_tasks() {
    log_test "Testing concurrent task creation..."
    
    echo "CONCURRENT TASK TEST:" > "$RESULTS_DIR/concurrent_tasks.txt"
    echo "=====================" >> "$RESULTS_DIR/concurrent_tasks.txt"
    echo "" >> "$RESULTS_DIR/concurrent_tasks.txt"
    
    local task_data='{
        "title": "Performance Test Task",
        "description": "This is a test task created during performance testing",
        "priority": "medium"
    }'
    
    local pids=()
    local start_time=$(date +%s.%N)
    
    # Create multiple tasks concurrently
    for i in $(seq 1 $CONCURRENT_USERS); do
        {
            local task_start=$(date +%s.%N)
            local response
            if response=$(curl -s --max-time 30 -X POST "$BACKEND_URL/api/tasks" \
                -H "Content-Type: application/json" \
                -d "$task_data"); then
                local task_end=$(date +%s.%N)
                local task_time=$(echo "$task_end - $task_start" | bc)
                echo "Task $i: SUCCESS (${task_time}s)" >> "$RESULTS_DIR/concurrent_tasks.txt"
            else
                echo "Task $i: FAILED" >> "$RESULTS_DIR/concurrent_tasks.txt"
            fi
        } &
        pids+=($!)
    done
    
    # Wait for all tasks to complete
    for pid in "${pids[@]}"; do
        wait $pid
    done
    
    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc)
    
    echo "" >> "$RESULTS_DIR/concurrent_tasks.txt"
    echo "Total Time: ${total_time}s" >> "$RESULTS_DIR/concurrent_tasks.txt"
    echo "Tasks per Second: $(echo "scale=2; $CONCURRENT_USERS / $total_time" | bc)" >> "$RESULTS_DIR/concurrent_tasks.txt"
    
    log_success "Created $CONCURRENT_USERS tasks in ${total_time}s"
}

# Test memory usage
test_memory_usage() {
    log_test "Testing memory usage..."
    
    echo "MEMORY USAGE TEST:" > "$RESULTS_DIR/memory_usage.txt"
    echo "==================" >> "$RESULTS_DIR/memory_usage.txt"
    echo "" >> "$RESULTS_DIR/memory_usage.txt"
    
    # Monitor memory for a short period
    for i in {1..10}; do
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            local memory_info=$(vm_stat | grep -E "(Pages free|Pages active|Pages inactive|Pages wired)")
            echo "Sample $i:" >> "$RESULTS_DIR/memory_usage.txt"
            echo "$memory_info" >> "$RESULTS_DIR/memory_usage.txt"
        else
            # Linux
            local memory_info=$(free -m | grep -E "(Mem:|Swap:)")
            echo "Sample $i:" >> "$RESULTS_DIR/memory_usage.txt"
            echo "$memory_info" >> "$RESULTS_DIR/memory_usage.txt"
        fi
        echo "" >> "$RESULTS_DIR/memory_usage.txt"
        sleep 2
    done
    
    log_success "Memory usage samples collected"
}

# Test load capacity
test_load_capacity() {
    log_test "Testing load capacity..."
    
    echo "LOAD CAPACITY TEST:" > "$RESULTS_DIR/load_capacity.txt"
    echo "===================" >> "$RESULTS_DIR/load_capacity.txt"
    echo "" >> "$RESULTS_DIR/load_capacity.txt"
    
    local request_count=0
    local success_count=0
    local error_count=0
    local start_time=$(date +%s)
    local end_time=$((start_time + TEST_DURATION))
    
    log_info "Running load test for $TEST_DURATION seconds..."
    
    while [ $(date +%s) -lt $end_time ]; do
        if curl -s --max-time 5 "$BACKEND_URL/api/status" >/dev/null 2>&1; then
            ((success_count++))
        else
            ((error_count++))
        fi
        ((request_count++))
        
        # Brief pause to avoid overwhelming
        sleep 0.1
    done
    
    local actual_duration=$(($(date +%s) - start_time))
    local requests_per_second=$(echo "scale=2; $request_count / $actual_duration" | bc)
    local success_rate=$(echo "scale=2; $success_count * 100 / $request_count" | bc)
    
    echo "Test Duration: ${actual_duration}s" >> "$RESULTS_DIR/load_capacity.txt"
    echo "Total Requests: $request_count" >> "$RESULTS_DIR/load_capacity.txt"
    echo "Successful Requests: $success_count" >> "$RESULTS_DIR/load_capacity.txt"
    echo "Failed Requests: $error_count" >> "$RESULTS_DIR/load_capacity.txt"
    echo "Requests per Second: $requests_per_second" >> "$RESULTS_DIR/load_capacity.txt"
    echo "Success Rate: ${success_rate}%" >> "$RESULTS_DIR/load_capacity.txt"
    
    log_success "Load test completed: $requests_per_second req/s, ${success_rate}% success rate"
}

# Generate performance report
generate_report() {
    log_test "Generating performance report..."
    
    cat > "$RESULTS_DIR/performance_report.md" << 'EOF'
# VirtuAI Office Performance Test Report

## Executive Summary

This report contains the results of comprehensive performance testing for VirtuAI Office.

## Test Environment

See `system_info.txt` for detailed system specifications.

## Test Results

### Service Availability
- **Backend API**: See `service_availability.txt`
- **Frontend Application**: See `service_availability.txt`
- **Ollama AI Service**: See `service_availability.txt`

### API Performance
- **Response Times**: See `api_performance.txt`
- **Endpoint Reliability**: Individual endpoint success rates
- **Performance Bottlenecks**: Identified slow endpoints

### AI Inference Performance
- **Model Performance**: See `ai_inference.txt`
- **Tokens per Second**: AI processing speed metrics
- **Inference Latency**: Time to first token and completion

### Concurrent Operations
- **Task Creation**: See `concurrent_tasks.txt`
- **Concurrent User Simulation**: Multi-user performance
- **Resource Contention**: Impact of concurrent operations

### Resource Usage
- **Memory Consumption**: See `memory_usage.txt`
- **CPU Utilization**: System resource usage patterns
- **Storage Requirements**: Disk space utilization

### Load Capacity
- **Request Throughput**: See `load_capacity.txt`
- **Error Rates**: System stability under load
- **Performance Degradation**: Breaking point analysis

## Recommendations

Based on the test results:

### Performance Optimizations
1. **API Response Time**: If any endpoint shows >1s average response time
2. **AI Inference**: Consider model optimization for faster generation
3. **Memory Usage**: Monitor for memory leaks during extended usage
4. **Concurrent Processing**: Optimize for multi-user scenarios

### Capacity Planning
1. **Recommended Hardware**: Based on performance metrics
2. **Scaling Considerations**: For increased load requirements
3. **Resource Allocation**: Optimal CPU/memory configuration

### Monitoring
1. **Key Metrics**: Response time, memory usage, AI inference speed
2. **Alert Thresholds**: Performance degradation indicators
3. **Regular Testing**: Recommended testing frequency

## Conclusion

VirtuAI Office performance characteristics and recommended usage patterns.

---
*Generated on: $(date)*
*Test Duration: Approximately 5-10 minutes*
*Test Version: 1.0*
EOF

    log_success "Performance report generated at $RESULTS_DIR/performance_report.md"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test artifacts..."
    
    # Remove any test tasks created during concurrent testing
    if curl -s "$BACKEND_URL/api/tasks" | grep -q "Performance Test Task"; then
        log_info "Removing test tasks..."
        # Note: This would require additional API endpoints to clean up
    fi
}

# Main execution
main() {
    print_header
    
    log_info "Starting performance test suite..."
    log_info "Results will be saved to: $RESULTS_DIR"
    echo ""
    
    # Check if services are running
    if ! curl -s --max-time 5 "$BACKEND_URL/api/status" >/dev/null 2>&1; then
        log_error "Backend service is not running at $BACKEND_URL"
        log_info "Please start VirtuAI Office before running performance tests"
        exit 1
    fi
    
    # Run test suite
    collect_system_info
    test_service_availability
    test_api_performance
    test_ai_inference
    test_concurrent_tasks
    test_memory_usage
    test_load_capacity
    generate_report
    
    echo ""
    log_success "Performance test suite completed!"
    log_info "Results available at: $RESULTS_DIR"
    log_info "View the report: cat $RESULTS_DIR/performance_report.md"
    
    echo ""
    echo -e "${CYAN}📊 Quick Summary:${NC}"
    echo -e "${BLUE}• System Info: $RESULTS_DIR/system_info.txt${NC}"
    echo -e "${BLUE}• API Performance: $RESULTS_DIR/api_performance.txt${NC}"
    echo -e "${BLUE}• AI Inference: $RESULTS_DIR/ai_inference.txt${NC}"
    echo -e "${BLUE}• Load Capacity: $RESULTS_DIR/load_capacity.txt${NC}"
    echo -e "${BLUE}• Full Report: $RESULTS_DIR/performance_report.md${NC}"
    
    cleanup
}

# Handle script interruption
trap 'log_warning "Performance test interrupted"; cleanup; exit 1' INT TERM

# Check dependencies
if ! command -v curl >/dev/null 2>&1; then
    log_error "curl is required but not installed"
    exit 1
fi

if ! command -v bc >/dev/null 2>&1; then
    log_error "bc is required but not installed"
    exit 1
fi

# Run main function
main "$@"
