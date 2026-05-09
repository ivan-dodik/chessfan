#!/bin/bash
# ============================================
# Chessfan Database Deployment Script
# ============================================
# This script:
# 1. Starts PostgreSQL container using Docker Compose
# 2. Waits for PostgreSQL to be ready
# 3. Creates database structure (tables, views, triggers)
# 4. Verifies everything is ready to accept data
# ============================================

set -e  # Exit on any error

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
SQL_INIT_FILE="$PROJECT_DIR/docs/db/sql/create.sql"
LOG_FILE="$PROJECT_DIR/deploy.log"

# Database connection settings (from docker-compose.yml)
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="chessfan"
DB_USER="chessfan"
DB_PASSWORD="chessfan123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Logging Functions ---
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# --- Helper Functions ---

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    for cmd in docker docker-compose psql; do
        if ! command_exists "$cmd"; then
            missing_tools+=("$cmd")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install: docker, docker-compose, postgresql-client"
        exit 1
    fi
    
    log_success "All prerequisites are installed"
}

# Check if docker-compose file exists
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    log_success "Docker Compose file found"
}

# Start PostgreSQL container
start_postgres() {
    log_info "Starting PostgreSQL container..."
    
    cd "$PROJECT_DIR"
    
    # Check if container already exists
    if docker-compose ps | grep -q "chessfan-postgres"; then
        log_warning "Container 'chessfan-postgres' already exists"
        log_info "Stopping existing container..."
        docker-compose stop postgres
    fi
    
    # Start the container
    docker-compose up -d postgres
    
    log_success "PostgreSQL container started"
}

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    log_info "Waiting for PostgreSQL to be ready..."
    
    local max_attempts=30
    local attempt=1
    local sleep_interval=2
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T postgres pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
            log_success "PostgreSQL is ready to accept connections"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - Waiting for PostgreSQL..."
        sleep $sleep_interval
        attempt=$((attempt + 1))
    done
    
    log_error "PostgreSQL failed to start within $((max_attempts * sleep_interval)) seconds"
    log_info "Check logs: docker-compose logs postgres"
    exit 1
}

# Create database structure
create_database_structure() {
    log_info "Creating database structure..."
    
    # Check if SQL file exists
    if [ ! -f "$SQL_INIT_FILE" ]; then
        log_error "SQL initialization file not found: $SQL_INIT_FILE"
        exit 1
    fi
    
    # Run the SQL script
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -f "$SQL_INIT_FILE" \
        -v ON_ERROR_STOP=1 \
        --set=ON_ERROR_STOP=1
    
    log_success "Database structure created successfully"
}

# Verify database structure
verify_database() {
    log_info "Verifying database structure..."
    
    local errors=0
    
    # Check tables
    log_info "Checking tables..."
    local tables=("players" "tournaments" "tournament_players" "games" "player_ratings" "tournament_standings")
    for table in "${tables[@]}"; do
        if PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            -t \
            -c "SELECT 1 FROM information_schema.tables WHERE table_name = '$table';" 2>/dev/null | grep -q "1"; then
            log_success "Table '$table' exists"
        else
            log_error "Table '$table' not found"
            errors=$((errors + 1))
        fi
    done
    
    # Check views
    log_info "Checking views..."
    local views=("v_active_tournament_table" "v_player_profile" "v_player_rating_history")
    for view in "${views[@]}"; do
        if PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            -t \
            -c "SELECT 1 FROM information_schema.views WHERE table_name = '$view';" 2>/dev/null | grep -q "1"; then
            log_success "View '$view' exists"
        else
            log_error "View '$view' not found"
            errors=$((errors + 1))
        fi
    done
    
    # Check trigger exists
    log_info "Checking trigger..."
    if PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -t \
        -c "SELECT 1 FROM information_schema.triggers WHERE trigger_name = 'trg_notify_game_result_change';" 2>/dev/null | grep -q "1"; then
        log_success "Trigger 'trg_notify_game_result_change' exists"
    else
        log_error "Trigger 'trg_notify_game_result_change' not found"
        errors=$((errors + 1))
    fi
    
    # Check pg_notify channel
    log_info "Checking pg_notify function..."
    if PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -t \
        -c "SELECT 1 FROM pg_proc WHERE proname = 'notify_game_result_change';" 2>/dev/null | grep -q "1"; then
        log_success "Function 'notify_game_result_change' exists"
    else
        log_error "Function 'notify_game_result_change' not found"
        errors=$((errors + 1))
    fi
    
    # Summary
    if [ $errors -eq 0 ]; then
        log_success "All database structures verified successfully!"
        return 0
    else
        log_error "Verification failed with $errors error(s)"
        return 1
    fi
}

# Test database connection with sample query
test_database_connection() {
    log_info "Testing database connection with sample query..."
    
    local result
    result=$(PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -t \
        -c "SELECT COUNT(*) FROM players;" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        log_success "Database connection test passed (players table accessible)"
    else
        log_error "Database connection test failed"
        exit 1
    fi
}

# Display connection information
show_connection_info() {
    echo ""
    log_info "============================================"
    log_info "PostgreSQL Deployment Complete!"
    log_info "============================================"
    echo ""
    log_info "Connection Details:"
    echo "  Host:     $DB_HOST"
    echo "  Port:     $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User:     $DB_USER"
    echo ""
    log_info "Quick Commands:"
    echo "  # Connect to database"
    echo "  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
    echo ""
    echo "  # Using docker-compose"
    echo "  docker-compose exec postgres psql -U $DB_USER -d $DB_NAME"
    echo ""
    log_info "View logs:"
    echo "  docker-compose logs -f postgres"
    echo ""
    log_info "Stop database:"
    echo "  docker-compose down"
    echo ""
}

# --- Main Execution ---
main() {
    echo ""
    echo "============================================"
    echo "  Chessfan Database Deployment Script"
    echo "============================================"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    check_compose_file
    
    # Start PostgreSQL
    start_postgres
    
    # Wait for PostgreSQL to be ready
    wait_for_postgres
    
    # Create database structure
    create_database_structure
    
    # Verify database structure
    verify_database
    
    # Test database connection
    test_database_connection
    
    # Show connection information
    show_connection_info
    
    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"