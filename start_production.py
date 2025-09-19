#!/usr/bin/env python3
"""
Production startup script for Replit deployment
Ensures gunicorn is found and executed correctly
"""
import os
import sys
import subprocess

# Add Python site-packages to PATH to find gunicorn
python_path = sys.executable
site_packages = os.path.dirname(python_path)

# Get PORT from environment, default to 5000
port = os.environ.get('PORT', '5000')

# Run gunicorn with python -m to ensure it's found
cmd = [
    python_path, '-m', 'gunicorn',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '1',
    '--threads', '1', 
    '--timeout', '120',
    'main:app'
]

print(f"Starting gunicorn with command: {' '.join(cmd)}")
print(f"Port: {port}")
print(f"Python executable: {python_path}")

# Execute gunicorn
os.execv(python_path, [python_path, '-m', 'gunicorn'] + cmd[2:])