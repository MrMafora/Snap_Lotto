#!/bin/bash
# Script to clean up processes using crucial ports (5000 and 8080)
# Run this script manually if you encounter port conflicts

# Function to kill processes on a specific port
kill_process_on_port() {
  local port=$1
  echo "Checking for existing processes on port $port..."
  
  # Get all PIDs using the port (there might be multiple)
  local pids=$(lsof -t -i:$port 2>/dev/null)
  
  if [ -n "$pids" ]; then
    echo "Found process(es) on port $port: $pids"
    
    # Kill each process individually
    for pid in $pids; do
      echo "Killing process with PID $pid..."
      kill -9 $pid 2>/dev/null || true
    done
    
    # Give processes time to fully terminate
    sleep 2
    
    # Verify the port is actually free now
    local check_pids=$(lsof -t -i:$port 2>/dev/null)
    if [ -n "$check_pids" ]; then
      echo "WARNING: Port $port is still in use by PID(s): $check_pids"
      echo "Attempting forceful termination..."
      
      # Try one more time with stronger force
      for pid in $check_pids; do
        echo "Force killing PID $pid..."
        kill -9 $pid 2>/dev/null || true
      done
      
      sleep 1
      
      # Final check
      local final_check=$(lsof -t -i:$port 2>/dev/null)
      if [ -n "$final_check" ]; then
        echo "ERROR: Failed to clear port $port. You may need to restart the repl."
      else
        echo "Port $port finally cleared successfully"
      fi
    else
      echo "Port $port cleared successfully"
    fi
  else
    echo "No process found using port $port"
  fi
  
  # Additional check to make sure socket is fully released
  if ! netstat -tuln | grep ":$port " > /dev/null; then
    echo "Confirmed port $port is free"
  fi
}

echo "======== PORT CLEANUP UTILITY ========"
echo "This script will terminate any processes using ports 5000 and 8080"

# Kill processes on both development and production ports
kill_process_on_port 5000
kill_process_on_port 8080

echo "Port cleanup completed"
echo "=================================="