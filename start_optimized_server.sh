#!/bin/bash
# Start optimized server script
# This script kills all existing Python processes and starts the optimized server

echo "Starting optimized server..."

# Kill all existing Python processes
echo "Killing existing Python processes..."
pkill -9 python || true
pkill -9 gunicorn || true

# Wait to ensure all processes are terminated
echo "Waiting for processes to terminate..."
sleep 2

# Start optimized server
echo "Starting optimized Gunicorn server..."
python start_optimized.py

# Exit with the exit code of the Python script
exit $?