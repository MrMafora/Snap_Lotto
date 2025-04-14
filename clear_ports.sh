#!/bin/bash
# This script aggressively clears port 5000 and 8080 for fresh starts

# Notify user
echo "Aggressively clearing ports 5000 and 8080..."

# Try to kill using various methods
echo "1. Using pkill..."
pkill -9 -f "gunicorn" || echo "No gunicorn processes found"
pkill -9 -f "start_direct.py" || echo "No start_direct.py processes found"
pkill -9 -f "python" || echo "No python processes found"

# List all processes just to be sure
echo "2. Checking for any remaining processes..."
ps aux | grep -E "(gunicorn|python|5000|8080)" | grep -v grep

# Wait a bit
echo "3. Waiting for processes to terminate..."
sleep 3

# Final check
echo "4. Final status of ports:"
netstat -tuln | grep -E "(5000|8080)" || echo "Ports 5000 and 8080 are free!"

echo "Ports should now be clear for use"