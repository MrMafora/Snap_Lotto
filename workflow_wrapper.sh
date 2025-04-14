#!/bin/bash
# This script is designed to be called by Replit's workflow system
# instead of gunicorn directly.

# Kill any existing processes on ports 5000 and 8080
echo "Preparing ports for use..."
pkill -9 -f "gunicorn" || true
pkill -9 -f "start_direct.py" || true
pkill -9 -f "python" || true
sleep 1

# Run our special workflow starter that will:
# 1. Open port 5000 immediately (for Replit detection)
# 2. Start our dual-port solution behind the scenes
echo "Executing workflow starter..."
exec python workflow_starter.py