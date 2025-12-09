#!/bin/bash

# Subway LED Console - Start Script
# This script starts both the main service and UI in the correct environment
# Usage: ./start_subway_system.sh

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${PROJECT_DIR}/venv"
SERVICE_SCRIPT="${PROJECT_DIR}/network/main_pi_service.py"
UI_SCRIPT="${PROJECT_DIR}/ui/run_ui.py"
LOG_DIR="${PROJECT_DIR}/logs"
SERVICE_LOG="${LOG_DIR}/service.log"
UI_LOG="${LOG_DIR}/ui.log"
PID_FILE="${LOG_DIR}/subway_system.pid"

# Serial port configuration
SERIAL_PORT="${SERIAL_PORT:-/dev/serial0}"
SERIAL_BAUD="${SERIAL_BAUD:-115200}"

# ============================================================================
# FUNCTIONS
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
    exit 1
}

cleanup() {
    log "Shutting down..."
    
    # Kill service process
    if [ -n "$SERVICE_PID" ] && kill -0 "$SERVICE_PID" 2>/dev/null; then
        log "Stopping service (PID: $SERVICE_PID)..."
        kill "$SERVICE_PID" 2>/dev/null || true
        sleep 2
        kill -9 "$SERVICE_PID" 2>/dev/null || true
    fi
    
    # Kill UI process
    if [ -n "$UI_PID" ] && kill -0 "$UI_PID" 2>/dev/null; then
        log "Stopping UI (PID: $UI_PID)..."
        kill "$UI_PID" 2>/dev/null || true
        sleep 2
        kill -9 "$UI_PID" 2>/dev/null || true
    fi
    
    # Clean up PID file
    rm -f "$PID_FILE"
    
    log "Shutdown complete"
    exit 0
}

# ============================================================================
# SETUP
# ============================================================================

log "=========================================="
log "🚇 NYC Subway LED Console Startup"
log "=========================================="
log "Project directory: $PROJECT_DIR"

# Create logs directory
mkdir -p "$LOG_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    error "Virtual environment not found at $VENV_PATH"
fi

log "✅ Virtual environment found"

# Activate virtual environment
source "$VENV_PATH/bin/activate"
log "✅ Virtual environment activated"

# Check required scripts exist
if [ ! -f "$SERVICE_SCRIPT" ]; then
    error "Service script not found: $SERVICE_SCRIPT"
fi

if [ ! -f "$UI_SCRIPT" ]; then
    error "UI script not found: $UI_SCRIPT"
fi

log "✅ All scripts found"

# ============================================================================
# STARTUP
# ============================================================================

log "Starting services..."

# Register signal handlers for graceful shutdown
trap cleanup SIGINT SIGTERM EXIT

# Start the main service in background
log "🔄 Starting main_pi_service.py..."
python3 "$SERVICE_SCRIPT" \
    --port "$SERIAL_PORT" \
    --baud "$SERIAL_BAUD" \
    --db "$PROJECT_DIR/network/subway.db" \
    --lookup "$PROJECT_DIR/network/stop_lookup.json" \
    --update-interval 60 \
    >> "$SERVICE_LOG" 2>&1 &
SERVICE_PID=$!
log "   Service PID: $SERVICE_PID"

# Wait a moment for service to start
sleep 3

# Check if service is still running
if ! kill -0 "$SERVICE_PID" 2>/dev/null; then
    error "Service failed to start! Check logs at $SERVICE_LOG"
fi

log "✅ Service started successfully"

# Start the UI in background with DISPLAY set
log "🔄 Starting run_ui.py..."
export DISPLAY=:0.0
python3 "$UI_SCRIPT" \
    >> "$UI_LOG" 2>&1 &
UI_PID=$!
log "   UI PID: $UI_PID"

# Save PIDs to file for monitoring
echo "$SERVICE_PID" > "$PID_FILE"
echo "$UI_PID" >> "$PID_FILE"

log "✅ UI started successfully"

# ============================================================================
# RUNNING
# ============================================================================

log "=========================================="
log "✅ NYC Subway LED Console Ready"
log "=========================================="
log "Service running with PID: $SERVICE_PID"
log "UI running with PID: $UI_PID"
log "Service log: $SERVICE_LOG"
log "UI log: $UI_LOG"
log "Press Ctrl-C to stop all services"
log "=========================================="

# Monitor processes and keep script running
while true; do
    sleep 1
    
    # Check if service is still running
    if ! kill -0 "$SERVICE_PID" 2>/dev/null; then
        log "⚠️  Service died unexpectedly!"
        tail -20 "$SERVICE_LOG"
        error "Service process not running"
    fi
    
    # Check if UI is still running
    if ! kill -0 "$UI_PID" 2>/dev/null; then
        log "⚠️  UI died unexpectedly!"
        tail -20 "$UI_LOG"
        error "UI process not running"
    fi
done
