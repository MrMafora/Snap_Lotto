#!/usr/bin/env python3
"""
Custom Gunicorn starter script that forces port 8080 binding
"""
import os
import sys
import subprocess

# Force port 8080 binding
os.environ['PORT'] = '8080'

# Set command directly without using gunicorn.conf.py
cmd = [
    "gunicorn",
    "--bind", "0.0.0.0:8080",
    "--worker-class", "gthread",
    "--workers", "2",
    "--timeout", "60",
    "--log-level", "info",
    "main:app"
]

print(f"Starting: {' '.join(cmd)}", file=sys.stderr)
subprocess.run(cmd)