#!/bin/bash
# Script to clear ports 5000 and 8080 before starting the application

set -e

echo "========================================"
echo "Port Clearing Utility"
echo "========================================"
echo "This script will check and free ports 5000 and 8080"

# Function to check if a port is in use
check_port() {
    local port=$1
    
    # Use netstat to check if port is in use
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":$port "; then
            echo "! Port $port is in use"
            return 0
        else
            echo "✓ Port $port is not in use"
            return 1
        fi
    elif command -v ss &> /dev/null; then
        # Alternative using ss if netstat isn't available
        if ss -tuln | grep -q ":$port "; then
            echo "! Port $port is in use"
            return 0
        else
            echo "✓ Port $port is not in use"
            return 1
        fi
    else
        # Last resort: try to bind to the port
        # Create a temporary Python script to check the port
        local temp_script=$(mktemp)
        cat > $temp_script << 'EOF'
import sys
import socket

port = int(sys.argv[1])
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', port))
    sock.close()
    print(f"Port {port} is not in use")
    sys.exit(1)  # Return 1 (not in use)
except OSError:
    print(f"Port {port} is in use")
    sys.exit(0)  # Return 0 (in use)
EOF
        
        python $temp_script $port
        local result=$?
        rm $temp_script
        return $result
    fi
}

# Function to kill a process on a port
kill_port() {
    local port=$1
    local pids=""
    
    # Try different methods to find processes
    if command -v fuser &> /dev/null; then
        # Using fuser
        pids=$(fuser -n tcp $port 2>/dev/null)
    elif command -v netstat &> /dev/null; then
        # Extract PIDs using netstat and awk
        pids=$(netstat -tuln | grep ":$port " | awk '{print $7}' | cut -d/ -f1)
    elif command -v ss &> /dev/null; then
        # Extract PIDs using ss and awk
        pids=$(ss -tuln | grep ":$port " | awk '{print $7}' | cut -d/ -f1)
    fi
    
    if [ -z "$pids" ]; then
        # Create a temporary Python script to kill processes by port
        local temp_script=$(mktemp)
        cat > $temp_script << 'EOF'
import sys
import socket
import os
import signal
import time

def get_pid_of_port(port):
    # This is very hacky and only works on Linux
    try:
        tcp_files = os.listdir('/proc/net/tcp')
        port_hex = format(port, '04X')
        
        for pid_dir in os.listdir('/proc'):
            if not pid_dir.isdigit():
                continue
                
            try:
                # Check if this process has this port open
                fd_dir = f"/proc/{pid_dir}/fd"
                if not os.path.exists(fd_dir):
                    continue
                    
                for fd in os.listdir(fd_dir):
                    try:
                        link = os.readlink(f"{fd_dir}/{fd}")
                        if f":{port}" in link or f":{port_hex.lower()}" in link:
                            return int(pid_dir)
                    except:
                        pass
            except:
                pass
    except:
        pass
    return None

port = int(sys.argv[1])
pid = get_pid_of_port(port)

if pid:
    print(f"Found process using port {port}: PID {pid}")
    try:
        os.kill(pid, signal.SIGKILL)
        print(f"Killed process {pid}")
        
        # Verify it was killed
        time.sleep(1)
        try:
            os.kill(pid, 0)  # Check if process still exists
            print(f"Process {pid} still running")
            sys.exit(1)
        except OSError:
            print(f"Process {pid} was successfully terminated")
            sys.exit(0)
    except:
        print(f"Failed to kill process {pid}")
        sys.exit(1)
else:
    print(f"No process found using port {port}")
    sys.exit(0)
EOF
        
        echo "Attempting to find and kill processes on port $port using Python..."
        python $temp_script $port
        rm $temp_script
        return
    fi
    
    # If we found PIDs using the standard tools
    for pid in $pids; do
        if [ ! -z "$pid" ]; then
            echo "Attempting to kill process on port $port (PID: $pid)..."
            kill -9 $pid 2>/dev/null
            
            # Verify it was killed
            sleep 1
            if kill -0 $pid 2>/dev/null; then
                echo "! Failed to kill process on port $port (PID: $pid)"
            else
                echo "✓ Successfully killed process on port $port (PID: $pid)"
            fi
        else
            echo "No process found on port $port"
        fi
    done
}

# Check port 5000
echo "Checking port 5000..."
check_port 5000
if [ $? -eq 0 ]; then
    kill_port 5000
fi

# Check port 8080
echo "Checking port 8080..."
check_port 8080
if [ $? -eq 0 ]; then
    kill_port 8080
fi

echo "========================================"
echo "Port clearing complete"
echo "========================================"