#!/bin/bash
# Script to trace what process is using port 5000

echo "============================================"
echo "CHECKING WHAT'S USING PORT 5000"
echo "============================================"

# Method 1: Using lsof
echo -e "\n[Method 1] Using lsof:"
if command -v lsof >/dev/null 2>&1; then
  lsof -i:5000 -n || echo "No processes found with lsof"
else
  echo "lsof tool not available"
fi

# Method 2: Using netstat
echo -e "\n[Method 2] Using netstat:"
if command -v netstat >/dev/null 2>&1; then
  netstat -tlnp 2>/dev/null | grep ":5000 " || echo "No processes found with netstat"
else
  echo "netstat tool not available"
fi

# Method 3: Using ss
echo -e "\n[Method 3] Using ss:"
if command -v ss >/dev/null 2>&1; then
  ss -tlnp | grep ":5000 " || echo "No processes found with ss"
else
  echo "ss tool not available"
fi

# Method 4: Using fuser
echo -e "\n[Method 4] Using fuser:"
if command -v fuser >/dev/null 2>&1; then
  fuser 5000/tcp 2>/dev/null || echo "No processes found with fuser"
else
  echo "fuser tool not available"
fi

# Method 5: List all Python processes to find suspicious ones
echo -e "\n[Method 5] All running Python processes:"
ps aux | grep python | grep -v grep || echo "No Python processes running"

# Method 6: List all running gunicorn processes
echo -e "\n[Method 6] All running Gunicorn processes:"
ps aux | grep gunicorn | grep -v grep || echo "No Gunicorn processes running"

# Method 7: Check files that might be starting servers on port 5000
echo -e "\n[Method 7] Files that might start servers on port 5000:"
grep -r "0.0.0.0:5000" --include="*.py" --include="*.sh" . || echo "No files found referencing 0.0.0.0:5000"

echo -e "\nDONE CHECKING FOR PORT 5000 USAGE"
echo "============================================"