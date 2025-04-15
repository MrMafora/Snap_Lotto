#!/usr/bin/env python3
"""
Production Server for Replit Deployment

This script provides a simplified approach to run the application directly on port 8080
for Replit deployment. It doesn't use the bridge approach, instead binding directly to
port 8080 as required by Replit's platform.
"""
import os
import sys
import logging
import signal
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('production_server')

# Configuration
PORT = 8080
HOST = "0.0.0.0"
APP = "main:app"
TIMEOUT = 120
WORKERS = 4

def check_port(port):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0

def clear_port(port):
    """Clear a port if it's in use"""
    if sys.platform.startswith('win'):
        # Windows
        subprocess.run(
            f"FOR /F \"tokens=5\" %P IN ('netstat -a -n -o | findstr :{port}') DO taskkill /F /PID %P", 
            shell=True
        )
    else:
        # Linux
        try:
            # Try different methods
            try:
                subprocess.run(f"fuser -k {port}/tcp", shell=True, check=False)
            except:
                pass
                
            try:
                pids = subprocess.check_output(f"lsof -ti:{port}", shell=True, stderr=subprocess.DEVNULL)
                for pid in pids.decode().strip().split('\n'):
                    if pid:
                        subprocess.run(f"kill -9 {pid}", shell=True)
            except:
                pass
        except Exception as e:
            logger.warning(f"Could not clear port {port}: {e}")

def run_server():
    """Run the server on port 8080"""
    # Set environment to production
    os.environ['ENVIRONMENT'] = 'production'
    
    # Ensure port is available
    logger.info(f"Checking if port {PORT} is available...")
    if not check_port(PORT):
        logger.warning(f"Port {PORT} is in use, attempting to clear...")
        clear_port(PORT)
        time.sleep(1)
        
        if not check_port(PORT):
            logger.error(f"Failed to clear port {PORT}!")
            return False
    
    # Start Gunicorn
    logger.info(f"Starting Gunicorn on port {PORT}...")
    cmd = [
        "gunicorn",
        "--bind", f"{HOST}:{PORT}",
        "--workers", str(WORKERS),
        "--timeout", str(TIMEOUT),
        "--reuse-port",
        APP
    ]
    
    process = subprocess.Popen(cmd)
    
    # Check if process started successfully
    time.sleep(2)
    if process.poll() is not None:
        logger.error("Failed to start Gunicorn!")
        return False
    
    logger.info(f"Server running on http://{HOST}:{PORT}/ (PID: {process.pid})")
    
    # Setup signal handlers for clean shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Monitor the process
    try:
        while True:
            if process.poll() is not None:
                logger.error(f"Server process exited with code {process.returncode}")
                return False
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    
    return True

if __name__ == "__main__":
    logger.info("=== Production Server for Replit Deployment ===")
    sys.exit(0 if run_server() else 1)