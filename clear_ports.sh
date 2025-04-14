#!/bin/bash
# Aggressively clear ports 4999, 5000, and 8080 for use

echo "Aggressively clearing ports 4999, 5000, and 8080..."

echo "1. Using fuser (if available)..."
if command -v fuser >/dev/null 2>&1; then
  fuser -k 4999/tcp 2>/dev/null || echo "No processes on port 4999"
  fuser -k 5000/tcp 2>/dev/null || echo "No processes on port 5000"
  fuser -k 8080/tcp 2>/dev/null || echo "No processes on port 8080"
fi

echo "2. Using pkill..."
pkill -9 -f "gunicorn" || echo "No gunicorn processes found"
pkill -9 -f "port_opener.py" || echo "No port_opener.py processes found"
pkill -9 -f "workflow_starter.py" || echo "No workflow_starter.py processes found" 
pkill -9 -f "python.*workflow" || echo "No python workflow processes found"
pkill -9 -f "python.*0.0.0.0" || echo "No python web server processes found"

echo "3. Final process cleanup..."
# Use ps and grep to find any remaining python processes related to web servers
ps aux | grep -E 'gunicorn|flask|python.*port' | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || echo "No remaining processes found"

echo "4. Waiting for processes to terminate..."
sleep 2

echo "All ports should now be clear for use!"