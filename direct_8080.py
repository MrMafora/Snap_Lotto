#!/usr/bin/env python3
"""
Direct launcher for port 8080 with no configuration overrides
"""
import os
import sys
import subprocess

# Kill any existing processes on port 8080
try:
    subprocess.run(["fuser", "-k", "8080/tcp"], stderr=subprocess.PIPE)
except Exception:
    pass  # Ignore if fuser fails

# Set environment variables to force port 8080
os.environ['PORT'] = '8080'
os.environ['FLASK_RUN_PORT'] = '8080'
os.environ['GUNICORN_PORT'] = '8080'

# Direct command execution with explicit port binding
cmd = "gunicorn --bind 0.0.0.0:8080 main:app"
print(f"Starting direct gunicorn on port 8080: {cmd}", file=sys.stderr)

# Execute the command directly
os.execvp("gunicorn", ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"])