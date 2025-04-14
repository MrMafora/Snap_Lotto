"""
Extremely minimal launcher for Replit workflows
This bypasses port 5000 entirely and goes straight to port 8080
"""
import subprocess
import sys
import os
import time

def main():
    """Main entry point for simple launcher"""
    try:
        # First, run our script to forcibly kill any processes on port 5000
        print("Killing any processes on port 5000...")
        subprocess.run(["./force_kill_port_5000.sh"], check=True)
        
        # Then run our aggressive port clearing script to ensure 8080 is free
        print("Clearing all ports for use...")
        subprocess.run(["./clear_ports.sh"], check=True)
        
        # Start the application directly on port 8080 (no port 5000 or 4999)
        print("Starting application directly on port 8080...")
        subprocess.run(["./start.sh"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error starting application: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()