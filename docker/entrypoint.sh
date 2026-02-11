#!/bin/bash
set -e

# ========================================
# Entrypoint script for Digitalism FastAPI
# ========================================
# This script handles:
# - Waiting for PostgreSQL to be ready
# - Running Alembic migrations
# - Running the ETL pipeline (optional)
# - Starting the FastAPI application
# ========================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    log_info "Waiting for PostgreSQL to be ready..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if python -c "
import os
import sys
from sqlalchemy import create_engine, text
try:
    engine = create_engine(os.environ.get('DATABASE_URL'))
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
            log_info "PostgreSQL is ready!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_warn "PostgreSQL not ready yet (attempt $attempt/$max_attempts)..."
        sleep 2
    done
    
    log_error "PostgreSQL did not become ready in time"
    return 1
}

# Run Alembic migrations
run_migrations() {
    log_info "Running Alembic migrations..."
    
    if [ ! -d "alembic" ]; then
        log_warn "Alembic directory not found, skipping migrations"
        return 0
    fi
    
    if ! alembic upgrade head; then
        log_error "Failed to run Alembic migrations"
        return 1
    fi
    
    log_info "Migrations completed successfully"
}

# Run ETL pipeline
run_etl() {
    log_info "Running ETL pipeline..."
    
    if [ ! -f "src/etl/scripts/city_etl_pipeline.py" ]; then
        log_warn "ETL pipeline script not found, skipping"
        return 0
    fi
    
    if ! python -m src.etl.scripts.city_etl_pipeline; then
        log_error "ETL pipeline failed"
        return 1
    fi
    
    log_info "ETL pipeline completed successfully"
}

# Start FastAPI application
start_api() {
    log_info "Starting FastAPI application..."
    
    local workers=${UVICORN_WORKERS:-4}
    local host=${UVICORN_HOST:-0.0.0.0}
    local port=${UVICORN_PORT:-8000}
    local log_level=${UVICORN_LOG_LEVEL:-info}
    
    log_info "Configuration:"
    log_info "  - Workers: $workers"
    log_info "  - Host: $host"
    log_info "  - Port: $port"
    log_info "  - Log Level: $log_level"
    
    exec uvicorn src.app:app \
        --host "$host" \
        --port "$port" \
        --workers "$workers" \
        --loop uvloop \
        --http httptools \
        --log-level "$log_level"
}

# Main execution
main() {
    local mode=${1:-all}
    
    log_info "Starting Digitalism FastAPI in mode: $mode"
    log_info "Environment: ${ENVIRONMENT:-development}"
    
    case "$mode" in
        api)
            wait_for_postgres
            run_migrations
            start_api
            ;;
        etl)
            wait_for_postgres
            run_migrations
            run_etl
            ;;
        migrate)
            wait_for_postgres
            run_migrations
            log_info "Migration completed, exiting"
            ;;
        all)
            wait_for_postgres
            run_migrations
            run_etl
            start_api
            ;;
        *)
            log_error "Unknown mode: $mode"
            log_info "Available modes: api, etl, migrate, all"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
