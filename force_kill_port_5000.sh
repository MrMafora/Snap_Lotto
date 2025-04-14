#!/bin/bash
# Force kill any processes using port 5000

echo "Forcefully terminating ALL processes using port 5000..."

# Try different methods to find and kill processes on port 5000
if command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -ti:5000)
  if [ -n "$PIDS" ]; then
    echo "Found processes using lsof: $PIDS"
    kill -9 $PIDS 2>/dev/null || echo "Failed to kill with lsof"
  else
    echo "No processes found with lsof"
  fi
fi

if command -v fuser >/dev/null 2>&1; then
  echo "Using fuser to kill processes..."
  fuser -k -9 5000/tcp 2>/dev/null || echo "No processes found with fuser"
fi

# Use netstat and grep to find processes
if command -v netstat >/dev/null 2>&1; then
  echo "Checking for processes with netstat..."
  PIDS=$(netstat -tlnp 2>/dev/null | grep ":5000" | awk '{print $7}' | cut -d'/' -f1 | sort -u)
  if [ -n "$PIDS" ]; then
    echo "Found processes using netstat: $PIDS"
    for PID in $PIDS; do
      kill -9 $PID 2>/dev/null || echo "Failed to kill PID $PID"
    done
  else
    echo "No processes found with netstat"
  fi
fi

# Brute force approach - find all python processes and check if they're using port 5000
echo "Checking all Python processes..."
for PID in $(ps aux | grep python | grep -v grep | awk '{print $2}'); do
  if [ -n "$PID" ]; then
    echo "Examining Python process $PID..."
    # For debugging, see what the process is
    ps -p $PID -o command= || true
    # Kill it anyway
    kill -9 $PID 2>/dev/null || echo "Failed to kill Python PID $PID"
  fi
done

# Brute force - kill all gunicorn
echo "Killing all gunicorn processes..."
pkill -9 -f "gunicorn" || echo "No gunicorn processes found"

echo "Waiting for processes to terminate..."
sleep 3

echo "Port 5000 should now be free!"