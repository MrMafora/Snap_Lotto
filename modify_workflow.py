#!/usr/bin/env python3
"""
Simple proxy script to override Gunicorn port configuration
"""
import os
import sys
import json
import time
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('modify_workflow')

def start_app_with_port_override():
    """Start the application with port 8080 override"""
    # Set environment variables to force port 8080
    os.environ['PORT'] = '8080'
    os.environ['FLASK_RUN_PORT'] = '8080'
    os.environ['GUNICORN_PORT'] = '8080'
    os.environ['BIND_PORT'] = '8080'
    
    # Create modified command to force port 8080
    cmd = 'exec gunicorn --bind 0.0.0.0:8080 -c gunicorn.conf.py main:app'
    
    # Log the command
    logger.info(f"Starting with command: {cmd}")
    
    # Execute the modified command
    os.system(cmd)

if __name__ == "__main__":
    logger.info("Starting workflow port override")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
    
    # Start the app with port override
    start_app_with_port_override()