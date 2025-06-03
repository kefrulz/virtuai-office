#!/bin/bash

# VirtuAI Office - System Cleanup Script
# Cleans up temporary files, old logs, and optimizes system performance

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
TEMP_DIR="$PROJECT_DIR/temp"
CACHE_DIR="$PROJECT_DIR/.cache"
DB_FILE="$PROJECT_DIR/backend/virtuai_office.db"
BACKUP_DIR="$PROJECT_DIR/backups"

# Logging
CLEANUP_LOG="$PROJECT_DIR/cleanup.log"

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; echo "$(date): INFO: $1" >> "$CLEANUP_LOG"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; echo "$(date): SUCCESS: $1" >> "$CLEANUP_LOG"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; echo "$(date): WARNING: $1" >> "$CLEANUP_LOG"; }
log_error() { echo -e "${RED}❌ $1${NC}"; echo "$(date): ERROR: $1" >> "$CLEANUP_LOG"; }

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                VirtuAI Office Cleanup                    ║"
    echo "║              System Maintenance & Optimization          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_help() {
    echo -e "${CYAN}VirtuAI Office Cleanup Script${NC}"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -a, --all           Perform complete cleanup (default)"
    echo "  -l, --logs          Clean log files only"
    echo "  -t, --temp          Clean temporary files only"
    echo "  -c, --cache         Clean cache files only"
    echo "  -m, --models        Clean unused AI models"
    echo "  -d, --database      Optimize database"
    echo "  -b, --backup        Create backup before cleanup"
    echo "  -f, --force         Force cleanup without prompts"
    echo "  -s, --stats         Show disk usage statistics"
    echo "  --dry-run           Show what would be cleaned without doing it"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Complete cleanup with prompts"
    echo "  $0 --logs --force   # Clean logs without prompts"
    echo "  $0 --dry-run        # Preview cleanup actions"
    echo "  $0 --backup --all   # Backup then complete cleanup"
}

get_size() {
    local path="$1"
    if [[ -d "$path" ]]; then
        du -sh "$path" 2>/dev/null | cut -f1 || echo "0B"
    elif [[ -f "$path" ]]; then
        ls -lh "$path" 2>/dev/null | awk '{print $5}' || echo "0B"
    else
        echo "0B"
    fi
}

show_disk_stats() {
    log_info "Disk usage statistics:"
    echo ""
    
    if [[ -d "$PROJECT_DIR" ]]; then
        echo -e "${CYAN}Project Directory:${NC} $(get_size "$PROJECT_DIR")"
    fi
    
    if [[ -d "$LOG_DIR" ]]; then
        echo -e "${YELLOW}Logs:${NC} $(get_size "$LOG_DIR")"
    fi
    
    if [[ -d "$TEMP_DIR" ]]; then
        echo -e "${YELLOW}Temp Files:${NC} $(get_size "$TEMP_DIR")"
    fi
    
    if [[ -d "$CACHE_DIR" ]]; then
        echo -e "${YELLOW}Cache:${NC} $(get_size "$CACHE_DIR")"
    fi
    
    if [[ -f "$DB_FILE" ]]; then
        echo -e "${BLUE}Database:${NC} $(get_size "$DB_FILE")"
    fi
    
    # Node modules
    if [[ -d "$PROJECT_DIR/frontend/node_modules" ]]; then
        echo -e "${PURPLE}Node Modules:${NC} $(get_size "$PROJECT_DIR/frontend/node_modules")"
    fi
    
    # Python cache
    if [[ -d "$PROJECT_DIR/backend/__pycache__" ]]; then
        echo -e "${PURPLE}Python Cache:${NC} $(get_size "$PROJECT_DIR/backend/__pycache__")"
    fi
    
    # Ollama models
    if command -v ollama >/dev/null 2>&1; then
        local ollama_size=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
        echo -e "${GREEN}Ollama Models:${NC} $ollama_size models installed"
    fi
    
    echo ""
}

create_backup() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create backup in $BACKUP_DIR"
        return
    fi
    
    log_info "Creating backup before cleanup..."
    
    mkdir -p "$BACKUP_DIR"
    local backup_name="virtuai-backup-$(date +%Y%m%d-%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup database
    if [[ -f "$DB_FILE" ]]; then
        cp "$DB_FILE" "$backup_path/database.db"
        log_success "Database backed up"
    fi
    
    # Backup configuration files
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        cp "$PROJECT_DIR/.env" "$backup_path/"
    fi
    
    if [[ -f "$PROJECT_DIR/backend/.env" ]]; then
        cp "$PROJECT_DIR/backend/.env" "$backup_path/backend.env"
    fi
    
    # Backup user data
    if [[ -d "$PROJECT_DIR/user_data" ]]; then
        cp -r "$PROJECT_DIR/user_data" "$backup_path/"
    fi
    
    # Create backup info
    cat > "$backup_path/backup_info.txt" << EOF
VirtuAI Office Backup
Created: $(date)
Version: $(git describe --tags 2>/dev/null || echo "unknown")
Branch: $(git branch --show-current 2>/dev/null || echo "unknown")
Commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
EOF
    
    log_success "Backup created: $backup_path"
}

clean_logs() {
    log_info "Cleaning log files..."
    
    local cleaned_size=0
    local file_count=0
    
    # Clean application logs
    if [[ -d "$LOG_DIR" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            file_count=$(find "$LOG_DIR" -name "*.log" -type f | wc -l)
            log_info "[DRY RUN] Would clean $file_count log files in $LOG_DIR"
        else
            find "$LOG_DIR" -name "*.log" -type f -exec rm -f {} \;
            file_count=$(find "$LOG_DIR" -name "*.log" -type f | wc -l)
        fi
    fi
    
    # Clean Python logs
    if [[ -d "$PROJECT_DIR/backend" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            local py_logs=$(find "$PROJECT_DIR/backend" -name "*.log" -type f | wc -l)
            log_info "[DRY RUN] Would clean $py_logs Python log files"
        else
            find "$PROJECT_DIR/backend" -name "*.log" -type f -exec rm -f {} \;
        fi
    fi
    
    # Clean Node.js logs
    if [[ -d "$PROJECT_DIR/frontend" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            local js_logs=$(find "$PROJECT_DIR/frontend" -name "*.log" -type f | wc -l)
            log_info "[DRY RUN] Would clean $js_logs Node.js log files"
        else
            find "$PROJECT_DIR/frontend" -name "*.log" -name "npm-debug.log*" -type f -exec rm -f {} \;
        fi
    fi
    
    # Clean system logs (if writable)
    if [[ -f "$CLEANUP_LOG" && $(stat -c %s "$CLEANUP_LOG" 2>/dev/null || stat -f %z "$CLEANUP_LOG" 2>/dev/null) -gt 1048576 ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would rotate cleanup log (>1MB)"
        else
            tail -n 1000 "$CLEANUP_LOG" > "$CLEANUP_LOG.tmp" && mv "$CLEANUP_LOG.tmp" "$CLEANUP_LOG"
            log_success "Rotated cleanup log"
        fi
    fi
    
    log_success "Log cleanup completed"
}

clean_temp_files() {
    log_info "Cleaning temporary files..."
    
    # Clean temp directory
    if [[ -d "$TEMP_DIR" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            local temp_count=$(find "$TEMP_DIR" -type f | wc -l)
            log_info "[DRY RUN] Would clean $temp_count files in temp directory"
        else
            rm -rf "$TEMP_DIR"/*
            log_success "Cleaned temp directory"
        fi
    fi
    
    # Clean Python temp files
    if [[ "$DRY_RUN" == "true" ]]; then
        local py_temp=$(find "$PROJECT_DIR" -name "*.pyc" -o -name "*.pyo" -o -name "__pycache__" | wc -l)
        log_info "[DRY RUN] Would clean $py_temp Python temp files"
    else
        find "$PROJECT_DIR" -name "*.pyc" -exec rm -f {} \;
        find "$PROJECT_DIR" -name "*.pyo" -exec rm -f {} \;
        find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || true
        log_success "Cleaned Python temporary files"
    fi
    
    # Clean Node.js temp files
    if [[ -d "$PROJECT_DIR/frontend" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would clean Node.js temporary files"
        else
            find "$PROJECT_DIR/frontend" -name ".DS_Store" -exec rm -f {} \; 2>/dev/null || true
            find "$PROJECT_DIR/frontend" -name "Thumbs.db" -exec rm -f {} \; 2>/dev/null || true
            log_success "Cleaned Node.js temporary files"
        fi
    fi
    
    # Clean OS temporary files
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would clean OS temporary files"
    else
        find "$PROJECT_DIR" -name ".DS_Store" -exec rm -f {} \; 2>/dev/null || true
        find "$PROJECT_DIR" -name "Thumbs.db" -exec rm -f {} \; 2>/dev/null || true
        find "$PROJECT_DIR" -name "*.tmp" -exec rm -f {} \; 2>/dev/null || true
        log_success "Cleaned OS temporary files"
    fi
}

clean_cache() {
    log_info "Cleaning cache files..."
    
    # Clean application cache
    if [[ -d "$CACHE_DIR" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            local cache_size=$(get_size "$CACHE_DIR")
            log_info "[DRY RUN] Would clean cache directory ($cache_size)"
        else
            rm -rf "$CACHE_DIR"/*
            log_success "Cleaned application cache"
        fi
    fi
    
    # Clean pip cache
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would clean pip cache"
    else
        pip cache purge >/dev/null 2>&1 || true
        log_success "Cleaned pip cache"
    fi
    
    # Clean npm cache
    if command -v npm >/dev/null 2>&1; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would clean npm cache"
        else
            npm cache clean --force >/dev/null 2>&1 || true
            log_success "Cleaned npm cache"
        fi
    fi
    
    # Clean yarn cache
    if command -v yarn >/dev/null 2>&1; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would clean yarn cache"
        else
            yarn cache clean >/dev/null 2>&1 || true
            log_success "Cleaned yarn cache"
        fi
    fi
}

clean_models() {
    log_info "Cleaning unused AI models..."
    
    if ! command -v ollama >/dev/null 2>&1; then
        log_warning "Ollama not found, skipping model cleanup"
        return
    fi
    
    # Get list of models
    local models=$(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' || true)
    
    if [[ -z "$models" ]]; then
        log_info "No Ollama models found"
        return
    fi
    
    echo -e "${CYAN}Current AI models:${NC}"
    ollama list 2>/dev/null || log_warning "Could not list models"
    
    if [[ "$FORCE" != "true" && "$DRY_RUN" != "true" ]]; then
        echo ""
        echo -e "${YELLOW}Do you want to remove any unused models? (y/N):${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Skipping model cleanup"
            return
        fi
        
        echo -e "${CYAN}Enter model names to remove (space-separated), or 'all' for all models:${NC}"
        read -r models_to_remove
        
        if [[ "$models_to_remove" == "all" ]]; then
            models_to_remove="$models"
        fi
        
        for model in $models_to_remove; do
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "[DRY RUN] Would remove model: $model"
            else
                log_info "Removing model: $model"
                ollama rm "$model" 2>/dev/null || log_warning "Could not remove model: $model"
            fi
        done
    else
        log_info "Use --force with caution. Manual model cleanup recommended."
    fi
}

optimize_database() {
    log_info "Optimizing database..."
    
    if [[ ! -f "$DB_FILE" ]]; then
        log_warning "Database file not found: $DB_FILE"
        return
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would optimize database"
        return
    fi
    
    # Check if database is accessible
    if ! command -v sqlite3 >/dev/null 2>&1; then
        log_warning "sqlite3 not found, skipping database optimization"
        return
    fi
    
    local db_size_before=$(get_size "$DB_FILE")
    
    # Vacuum database
    sqlite3 "$DB_FILE" "VACUUM;" 2>/dev/null || log_warning "Could not vacuum database"
    
    # Analyze database
    sqlite3 "$DB_FILE" "ANALYZE;" 2>/dev/null || log_warning "Could not analyze database"
    
    # Reindex database
    sqlite3 "$DB_FILE" "REINDEX;" 2>/dev/null || log_warning "Could not reindex database"
    
    local db_size_after=$(get_size "$DB_FILE")
    
    log_success "Database optimized: $db_size_before → $db_size_after"
}

cleanup_old_backups() {
    log_info "Cleaning old backups..."
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_info "No backup directory found"
        return
    fi
    
    # Keep last 5 backups
    local backup_count=$(ls -1 "$BACKUP_DIR" | wc -l)
    
    if [[ $backup_count -gt 5 ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            local old_backups=$((backup_count - 5))
            log_info "[DRY RUN] Would remove $old_backups old backups"
        else
            ls -1t "$BACKUP_DIR" | tail -n +6 | while read -r backup; do
                rm -rf "$BACKUP_DIR/$backup"
                log_info "Removed old backup: $backup"
            done
            log_success "Cleaned old backups"
        fi
    else
        log_info "No old backups to clean (keeping last 5)"
    fi
}

system_optimization() {
    log_info "Performing system optimization..."
    
    # macOS specific optimizations
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would optimize macOS system settings"
        else
            # Purge inactive memory
            sudo purge >/dev/null 2>&1 || log_warning "Could not purge inactive memory (requires sudo)"
            
            # Clear font caches
            sudo atsutil databases -remove >/dev/null 2>&1 || true
            
            log_success "macOS optimization completed"
        fi
    fi
    
    # Linux specific optimizations
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would optimize Linux system settings"
        else
            # Clear PageCache, dentries and inodes
            sync
            echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null 2>&1 || log_warning "Could not clear caches (requires sudo)"
            
            log_success "Linux optimization completed"
        fi
    fi
}

main() {
    print_header
    
    # Parse command line arguments
    local clean_all=false
    local clean_logs=false
    local clean_temp=false
    local clean_cache=false
    local clean_models=false
    local optimize_db=false
    local create_backup_flag=false
    local show_stats=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--all)
                clean_all=true
                shift
                ;;
            -l|--logs)
                clean_logs=true
                shift
                ;;
            -t|--temp)
                clean_temp=true
                shift
                ;;
            -c|--cache)
                clean_cache=true
                shift
                ;;
            -m|--models)
                clean_models=true
                shift
                ;;
            -d|--database)
                optimize_db=true
                shift
                ;;
            -b|--backup)
                create_backup_flag=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -s|--stats)
                show_stats=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Default to all if no specific options
    if [[ "$clean_all" == "false" && "$clean_logs" == "false" && "$clean_temp" == "false" && "$clean_cache" == "false" && "$clean_models" == "false" && "$optimize_db" == "false" && "$show_stats" == "false" ]]; then
        clean_all=true
    fi
    
    # Show statistics if requested
    if [[ "$show_stats" == "true" ]]; then
        show_disk_stats
        exit 0
    fi
    
    # Show what will be done
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN MODE - No actual changes will be made"
    fi
    
    log_info "Starting VirtuAI Office cleanup..."
    
    # Create backup if requested
    if [[ "$create_backup_flag" == "true" ]]; then
        create_backup
    fi
    
    # Perform cleanup operations
    if [[ "$clean_all" == "true" || "$clean_logs" == "true" ]]; then
        clean_logs
    fi
    
    if [[ "$clean_all" == "true" || "$clean_temp" == "true" ]]; then
        clean_temp_files
    fi
    
    if [[ "$clean_all" == "true" || "$clean_cache" == "true" ]]; then
        clean_cache
    fi
    
    if [[ "$clean_all" == "true" || "$clean_models" == "true" ]]; then
        clean_models
    fi
    
    if [[ "$clean_all" == "true" || "$optimize_db" == "true" ]]; then
        optimize_database
    fi
    
    if [[ "$clean_all" == "true" ]]; then
        cleanup_old_backups
        system_optimization
    fi
    
    log_success "Cleanup completed!"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        echo ""
        log_info "System status after cleanup:"
        show_disk_stats
        
        echo ""
        log_info "Recommendations:"
        echo "  • Run cleanup weekly for optimal performance"
        echo "  • Create backups before major cleanups"
        echo "  • Monitor disk usage with: $0 --stats"
        echo "  • Use --dry-run to preview cleanup actions"
    fi
}

# Set default values
FORCE=false
DRY_RUN=false

# Run main function
main "$@"
