"""
Special script for Replit that runs the application on port 8080.
This script is designed to be the entry point for Replit workflows,
completely bypassing port 5000 which seems to be causing conflicts.
"""
import subprocess
import os
import sys
import time
import signal

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("Shutting down server...")
    sys.exit(0)

def main():
    """Main entry point for the Replit starter script"""
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # First, forcibly kill any processes on port 5000
        print("Killing any processes on port 5000...")
        subprocess.run(["./force_kill_port_5000.sh"], check=True)
        
        # Then clear any other port conflicts
        print("Clearing all ports...")
        subprocess.run(["./clear_ports.sh"], check=True)
        
        # Start the application directly on port 8080 using direct Flask
        print("Starting application directly on port 8080...")
        subprocess.run(["python", "main_8080.py"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Server shutdown requested...")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()