#!/usr/bin/env python3
"""
Direct launcher for port 8080 with no configuration overrides
"""
import os
import sys
import subprocess

# Force environment variable to be 8080
os.environ['PORT'] = '8080'

# Run Gunicorn with explicit config and bind
cmd = [
    "gunicorn",
    "-c", "direct_gunicorn.conf.py",
    "--bind", "0.0.0.0:8080",
    "main:app"
]

print(f"Running direct command: {' '.join(cmd)}", file=sys.stderr)
subprocess.run(cmd)