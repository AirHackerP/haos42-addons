#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# RGB Status LED Add-on - Startup Script
# ==============================================================================

bashio::log.info "Starting RGB Status LED add-on..."

# Activate virtual environment
source /opt/venv/bin/activate

# Run the main application
exec python3 /app/main.py
