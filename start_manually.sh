#!/bin/bash
# OPTIMIZED MANUAL STARTUP SCRIPT FOR REPLIT
# This is the most reliable solution for running the application
# It completely bypasses Replit's workflow system and timeout limitations
# IMPORTANT: Uses both ports 5000 and 8080 as required by Replit

# --- PORT CLEANUP SECTION ---
echo "Performing comprehensive port cleanup..."
pkill -9 -f "python" 2>/dev/null || true
pkill -9 -f "gunicorn" 2>/dev/null || true
pkill -9 -f "node" 2>/dev/null || true
pkill -9 -f ":8080" 2>/dev/null || true
pkill -9 -f ":5000" 2>/dev/null || true

# Clean up port 8080
if which netstat > /dev/null && netstat -tln | grep :8080 > /dev/null; then
    echo "Port 8080 still in use! Performing deep cleanup..."
    # Find and kill ANY process using port 8080 with multiple methods
    if which lsof > /dev/null; then
        pids=$(lsof -i:8080 -t)
        if [ ! -z "$pids" ]; then
            echo "Killing processes: $pids"
            for pid in $pids; do
                kill -9 $pid 2>/dev/null || true
            done
        fi
    fi
    sleep 0.5
fi

# Clean up port 5000
if which netstat > /dev/null && netstat -tln | grep :5000 > /dev/null; then
    echo "Port 5000 still in use! Performing deep cleanup..."
    # Find and kill ANY process using port 5000 with multiple methods
    if which lsof > /dev/null; then
        pids=$(lsof -i:5000 -t)
        if [ ! -z "$pids" ]; then
            echo "Killing processes: $pids"
            for pid in $pids; do
                kill -9 $pid 2>/dev/null || true
            done
        fi
    fi
    sleep 0.5
fi

# --- APPLICATION STARTUP SECTION ---
echo "Starting application with optimized Replit settings..."

# Enable port reuse if possible
if [ -f /proc/sys/net/ipv4/tcp_tw_reuse ]; then
    echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse 2>/dev/null || true
fi

# Run the application using the proper gunicorn configuration
echo "Starting gunicorn with configuration file..."
exec gunicorn --config gunicorn.conf.py main:app