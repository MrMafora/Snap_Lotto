#!/bin/bash
# ULTRA-MINIMAL launcher for Replit
# Port 8080 version - critical for Replit detection
# This is our final solution to address Replit's strict port detection timeout

# Kill ALL processes that might interfere with port binding
# This is critical for reliable startup
echo "Performing complete port cleanup..."
pkill -9 -f "python" 2>/dev/null || true
pkill -9 -f "gunicorn" 2>/dev/null || true
pkill -9 -f "node" 2>/dev/null || true
pkill -9 -f ":8080" 2>/dev/null || true
pkill -9 -f ":5000" 2>/dev/null || true
sleep 0.5

# Verify port is free with advanced detection
if which netstat > /dev/null && netstat -tln | grep :8080 > /dev/null; then
    echo "CRITICAL: Port 8080 still in use! Performing emergency cleanup..."
    
    # Find ALL processes using port 8080 with multiple detection methods
    if which lsof > /dev/null; then
        pids=$(lsof -i:8080 -t)
        if [ ! -z "$pids" ]; then
            echo "Force killing processes: $pids"
            for pid in $pids; do
                kill -9 $pid 2>/dev/null || true
            done
        fi
    fi
    
    # Alternative detection for zombie processes
    if which ss > /dev/null; then
        zombie_pids=$(ss -lptn sport = :8080 | grep -oP '(?<=pid=)[0-9]+')
        if [ ! -z "$zombie_pids" ]; then
            echo "Force killing zombie processes: $zombie_pids"
            for pid in $zombie_pids; do
                kill -9 $pid 2>/dev/null || true
            done
        fi
    fi
    
    sleep 0.5
fi

# Check for port 5000 as well since the workflow still tries to use it
if which netstat > /dev/null && netstat -tln | grep :5000 > /dev/null; then
    echo "CRITICAL: Port 5000 still in use! Performing emergency cleanup..."
    
    # Find ALL processes using port 5000 with multiple detection methods
    if which lsof > /dev/null; then
        pids=$(lsof -i:5000 -t)
        if [ ! -z "$pids" ]; then
            echo "Force killing processes: $pids"
            for pid in $pids; do
                kill -9 $pid 2>/dev/null || true
            done
        fi
    fi
    
    sleep 0.5
fi

# Final verification
if which netstat > /dev/null && netstat -tln | grep :8080 > /dev/null; then
    echo "FATAL: Port 8080 cannot be released! Trying final approach..."
    # Modify kernel settings to allow immediate port reuse
    if [ -f /proc/sys/net/ipv4/tcp_tw_reuse ]; then
        echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse 2>/dev/null || true
    fi
    sleep 0.5
fi

# Start with absolute minimal approach for port 8080
echo "Starting ABSOLUTE MINIMAL port binder for port 8080..."
exec python absolute_minimal.py