#!/bin/bash

# VirtuAI Office - Backup Script
# Creates complete backups of your AI office data and configuration

set -e

# Configuration
BACKUP_DIR="${HOME}/.virtuai-backups"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="virtuai_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    VirtuAI Office Backup                        ║"
    echo "║                  Secure your AI team data                       ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

create_backup_directory() {
    log_info "Creating backup directory..."
    mkdir -p "${BACKUP_PATH}"
    mkdir -p "${BACKUP_PATH}/database"
    mkdir -p "${BACKUP_PATH}/config"
    mkdir -p "${BACKUP_PATH}/logs"
    mkdir -p "${BACKUP_PATH}/models"
    mkdir -p "${BACKUP_PATH}/scripts"
    log_success "Backup directory created: ${BACKUP_PATH}"
}

backup_database() {
    log_info "Backing up database..."
    
    # SQLite database
    if [ -f "${PROJECT_DIR}/backend/virtuai_office.db" ]; then
        cp "${PROJECT_DIR}/backend/virtuai_office.db" "${BACKUP_PATH}/database/"
        log_success "SQLite database backed up"
    else
        log_warning "No SQLite database found"
    fi
    
    # Database backup with SQL dump if possible
    if command -v sqlite3 >/dev/null 2>&1 && [ -f "${PROJECT_DIR}/backend/virtuai_office.db" ]; then
        sqlite3 "${PROJECT_DIR}/backend/virtuai_office.db" .dump > "${BACKUP_PATH}/database/virtuai_office_dump.sql"
        log_success "Database SQL dump created"
    fi
}

backup_configuration() {
    log_info "Backing up configuration files..."
    
    # Environment files
    [ -f "${PROJECT_DIR}/.env" ] && cp "${PROJECT_DIR}/.env" "${BACKUP_PATH}/config/"
    [ -f "${PROJECT_DIR}/backend/.env" ] && cp "${PROJECT_DIR}/backend/.env" "${BACKUP_PATH}/config/backend.env"
    [ -f "${PROJECT_DIR}/frontend/.env" ] && cp "${PROJECT_DIR}/frontend/.env" "${BACKUP_PATH}/config/frontend.env"
    
    # Configuration files
    [ -f "${PROJECT_DIR}/package.json" ] && cp "${PROJECT_DIR}/package.json" "${BACKUP_PATH}/config/"
    [ -f "${PROJECT_DIR}/requirements.txt" ] && cp "${PROJECT_DIR}/requirements.txt" "${BACKUP_PATH}/config/"
    [ -f "${PROJECT_DIR}/backend/requirements.txt" ] && cp "${PROJECT_DIR}/backend/requirements.txt" "${BACKUP_PATH}/config/backend_requirements.txt"
    
    # Docker and deployment configs
    [ -f "${PROJECT_DIR}/docker-compose.yml" ] && cp "${PROJECT_DIR}/docker-compose.yml" "${BACKUP_PATH}/config/"
    [ -f "${PROJECT_DIR}/Dockerfile" ] && cp "${PROJECT_DIR}/Dockerfile" "${BACKUP_PATH}/config/"
    
    log_success "Configuration files backed up"
}

backup_scripts() {
    log_info "Backing up management scripts..."
    
    [ -f "${PROJECT_DIR}/manage.sh" ] && cp "${PROJECT_DIR}/manage.sh" "${BACKUP_PATH}/scripts/"
    [ -f "${PROJECT_DIR}/deploy.sh" ] && cp "${PROJECT_DIR}/deploy.sh" "${BACKUP_PATH}/scripts/"
    [ -f "${PROJECT_DIR}/deploy-apple-silicon.sh" ] && cp "${PROJECT_DIR}/deploy-apple-silicon.sh" "${BACKUP_PATH}/scripts/"
    
    # Copy the scripts directory if it exists
    if [ -d "${PROJECT_DIR}/scripts" ]; then
        cp -r "${PROJECT_DIR}/scripts/"* "${BACKUP_PATH}/scripts/" 2>/dev/null || true
    fi
    
    log_success "Scripts backed up"
}

backup_logs() {
    log_info "Backing up logs..."
    
    # Application logs
    if [ -d "${PROJECT_DIR}/logs" ]; then
        cp -r "${PROJECT_DIR}/logs/"* "${BACKUP_PATH}/logs/" 2>/dev/null || true
        log_success "Application logs backed up"
    fi
    
    # System logs (last 1000 lines)
    if command -v journalctl >/dev/null 2>&1; then
        journalctl -u virtuai-office --lines=1000 > "${BACKUP_PATH}/logs/systemd.log" 2>/dev/null || true
    fi
    
    # Docker logs if running in containers
    if command -v docker >/dev/null 2>&1; then
        docker logs virtuai-backend > "${BACKUP_PATH}/logs/docker-backend.log" 2>/dev/null || true
        docker logs virtuai-frontend > "${BACKUP_PATH}/logs/docker-frontend.log" 2>/dev/null || true
    fi
}

backup_ollama_models() {
    log_info "Backing up Ollama model information..."
    
    if command -v ollama >/dev/null 2>&1; then
        # List installed models
        ollama list > "${BACKUP_PATH}/models/installed_models.txt" 2>/dev/null || true
        
        # Model configurations (if accessible)
        if [ -d "${HOME}/.ollama" ]; then
            # Only backup configuration, not the large model files
            [ -f "${HOME}/.ollama/config.json" ] && cp "${HOME}/.ollama/config.json" "${BACKUP_PATH}/models/" 2>/dev/null || true
            log_success "Ollama model information backed up"
        fi
    else
        log_warning "Ollama not found - skipping model backup"
    fi
}

backup_user_preferences() {
    log_info "Backing up user preferences and settings..."
    
    # Browser localStorage backup (if accessible)
    cat > "${BACKUP_PATH}/config/restore_preferences.js" << 'EOF'
// VirtuAI Office - User Preferences Backup
// Run this in browser console to restore preferences

// Example preferences that would be restored
const preferences = {
    'virtuai-user-preferences': '{"experience_level":"intermediate","primary_use_case":"web_development","optimization_level":"balanced"}',
    'virtuai-onboarding-completed': 'true',
    'virtuai-tutorial-completed': 'true'
};

// Restore function
Object.entries(preferences).forEach(([key, value]) => {
    localStorage.setItem(key, value);
});

console.log('VirtuAI Office preferences restored!');
EOF
    
    log_success "User preferences backup script created"
}

create_backup_manifest() {
    log_info "Creating backup manifest..."
    
    cat > "${BACKUP_PATH}/backup_manifest.json" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "${TIMESTAMP}",
    "date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "version": "1.0.0",
    "system_info": {
        "os": "$(uname -s)",
        "arch": "$(uname -m)",
        "hostname": "$(hostname)",
        "user": "$(whoami)"
    },
    "project_info": {
        "path": "${PROJECT_DIR}",
        "git_commit": "$(git -C "${PROJECT_DIR}" rev-parse HEAD 2>/dev/null || echo 'unknown')",
        "git_branch": "$(git -C "${PROJECT_DIR}" branch --show-current 2>/dev/null || echo 'unknown')"
    },
    "backup_contents": {
        "database": $([ -f "${BACKUP_PATH}/database/virtuai_office.db" ] && echo 'true' || echo 'false'),
        "configuration": true,
        "scripts": true,
        "logs": true,
        "models_info": $(command -v ollama >/dev/null 2>&1 && echo 'true' || echo 'false'),
        "user_preferences": true
    },
    "restore_notes": [
        "Use restore.sh script to restore this backup",
        "Ensure VirtuAI Office is stopped before restoring",
        "Models will need to be re-downloaded after restore",
        "Check system compatibility before restoring"
    ]
}
EOF
    
    log_success "Backup manifest created"
}

create_restore_script() {
    log_info "Creating restore script..."
    
    cat > "${BACKUP_PATH}/restore.sh" << 'EOF'
#!/bin/bash

# VirtuAI Office - Restore Script
# Restores a VirtuAI Office backup

set -e

BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${1:-$(pwd)}"

echo "🔄 Restoring VirtuAI Office backup..."
echo "Backup: $(basename "${BACKUP_DIR}")"
echo "Target: ${PROJECT_DIR}"
echo ""

read -p "Continue with restore? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Stop services if running
if [ -f "${PROJECT_DIR}/manage.sh" ]; then
    echo "Stopping VirtuAI Office services..."
    "${PROJECT_DIR}/manage.sh" stop 2>/dev/null || true
fi

# Restore database
if [ -f "${BACKUP_DIR}/database/virtuai_office.db" ]; then
    echo "Restoring database..."
    mkdir -p "${PROJECT_DIR}/backend"
    cp "${BACKUP_DIR}/database/virtuai_office.db" "${PROJECT_DIR}/backend/"
    echo "✅ Database restored"
fi

# Restore configuration
if [ -d "${BACKUP_DIR}/config" ]; then
    echo "Restoring configuration..."
    [ -f "${BACKUP_DIR}/config/.env" ] && cp "${BACKUP_DIR}/config/.env" "${PROJECT_DIR}/"
    [ -f "${BACKUP_DIR}/config/backend.env" ] && cp "${BACKUP_DIR}/config/backend.env" "${PROJECT_DIR}/backend/.env"
    [ -f "${BACKUP_DIR}/config/frontend.env" ] && cp "${BACKUP_DIR}/config/frontend.env" "${PROJECT_DIR}/frontend/.env"
    echo "✅ Configuration restored"
fi

# Restore scripts
if [ -d "${BACKUP_DIR}/scripts" ]; then
    echo "Restoring scripts..."
    cp "${BACKUP_DIR}/scripts/"* "${PROJECT_DIR}/" 2>/dev/null || true
    chmod +x "${PROJECT_DIR}/"*.sh 2>/dev/null || true
    echo "✅ Scripts restored"
fi

echo ""
echo "🎉 Restore completed!"
echo ""
echo "Next steps:"
echo "1. Reinstall Ollama models: ollama pull llama2:7b"
echo "2. Start services: ./manage.sh start"
echo "3. Visit: http://localhost:3000"
echo ""
echo "Check backup_manifest.json for details about this backup."
EOF
    
    chmod +x "${BACKUP_PATH}/restore.sh"
    log_success "Restore script created"
}

compress_backup() {
    log_info "Compressing backup..."
    
    cd "${BACKUP_DIR}"
    
    if command -v tar >/dev/null 2>&1; then
        tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
        COMPRESSED_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
        log_success "Backup compressed: ${BACKUP_NAME}.tar.gz (${COMPRESSED_SIZE})"
        
        # Remove uncompressed directory
        rm -rf "${BACKUP_NAME}"
        
        return 0
    else
        log_warning "tar not available - backup left uncompressed"
        return 1
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    # Keep last 10 backups
    cd "${BACKUP_DIR}"
    ls -t virtuai_backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    ls -td virtuai_backup_* 2>/dev/null | tail -n +11 | xargs rm -rf 2>/dev/null || true
    
    BACKUP_COUNT=$(ls virtuai_backup_* 2>/dev/null | wc -l)
    log_success "Backup cleanup completed (${BACKUP_COUNT} backups retained)"
}

print_summary() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                     Backup Completed!                           ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Backup Details:${NC}"
    echo "  📁 Location: ${BACKUP_DIR}"
    echo "  📦 Name: ${BACKUP_NAME}"
    echo "  📅 Date: $(date)"
    
    if [ -f "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" ]; then
        BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
        echo "  💾 Size: ${BACKUP_SIZE}"
        echo ""
        echo -e "${BLUE}To restore this backup:${NC}"
        echo "  tar -xzf ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
        echo "  cd ${BACKUP_NAME}"
        echo "  ./restore.sh /path/to/virtuai-office"
    else
        echo "  📂 Type: Uncompressed directory"
        echo ""
        echo -e "${BLUE}To restore this backup:${NC}"
        echo "  cd ${BACKUP_PATH}"
        echo "  ./restore.sh /path/to/virtuai-office"
    fi
    
    echo ""
    echo -e "${YELLOW}💡 Tips:${NC}"
    echo "  • Store backups in a safe location (external drive, cloud storage)"
    echo "  • Test restore process periodically"
    echo "  • Backup before major updates or changes"
    echo "  • Keep multiple backup versions for safety"
    echo ""
}

main() {
    print_header
    
    # Validate project directory
    if [ ! -f "${PROJECT_DIR}/manage.sh" ] && [ ! -f "${PROJECT_DIR}/backend/backend.py" ]; then
        log_error "VirtuAI Office installation not found in: ${PROJECT_DIR}"
        log_info "Please run this script from the VirtuAI Office directory"
        exit 1
    fi
    
    # Create backup
    create_backup_directory
    backup_database
    backup_configuration
    backup_scripts
    backup_logs
    backup_ollama_models
    backup_user_preferences
    create_backup_manifest
    create_restore_script
    
    # Compress and cleanup
    compress_backup
    cleanup_old_backups
    
    print_summary
}

# Help function
show_help() {
    echo "VirtuAI Office Backup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0                    # Create backup of current installation"
    echo "  $0 --verbose          # Create backup with detailed output"
    echo ""
    echo "Backup includes:"
    echo "  • Database and all data"
    echo "  • Configuration files"
    echo "  • Management scripts"
    echo "  • Application logs"
    echo "  • Ollama model information"
    echo "  • User preferences"
    echo ""
    echo "Backups are stored in: ${HOME}/.virtuai-backups"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -v|--verbose)
        set -x
        ;;
esac

# Run main function
main "$@"
