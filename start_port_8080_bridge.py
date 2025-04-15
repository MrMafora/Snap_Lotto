#!/usr/bin/env python3
"""
Start the port 8080 bridge as a standalone service.
This script starts a bridge that forwards requests from port 8080 to port 5000.
"""
import argparse
import logging
import sys
import signal
import time
import threading
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('port_8080_bridge.log')
    ]
)
logger = logging.getLogger('port_8080_bridge')

def main():
    """Start the port 8080 bridge"""
    parser = argparse.ArgumentParser(description='Start the port 8080 bridge')
    parser.add_argument('--check-interval', type=int, default=5,
                      help='Interval in seconds to check if the bridge is still running')
    parser.add_argument('--restart', action='store_true',
                      help='Restart the bridge if it crashes')
    args = parser.parse_args()
    
    # Create a flag for shutdown
    shutdown_event = threading.Event()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bridge_thread = None
    
    def start_bridge():
        """Import and start the bridge in a separate thread"""
        try:
            # Save current directory
            cwd = os.getcwd()
            
            # Set up an event to know when the bridge has started
            started_event = threading.Event()
            
            # Define the bridge thread function
            def run_bridge():
                try:
                    # Import the bridge module
                    import bridge
                    logger.info("Starting port 8080 bridge...")
                    
                    # Signal that we've started
                    started_event.set()
                    
                    # Run the bridge
                    bridge.run_bridge()
                except Exception as e:
                    logger.error(f"Bridge crashed: {str(e)}")
                    started_event.set()  # Signal that we're done, even though we failed
            
            # Start the bridge in a new thread
            thread = threading.Thread(target=run_bridge)
            thread.daemon = True
            thread.start()
            
            # Wait for the bridge to start (or fail)
            if not started_event.wait(timeout=10):
                logger.error("Timed out waiting for bridge to start")
                return None
            
            return thread
        except Exception as e:
            logger.error(f"Failed to start bridge: {str(e)}")
            return None
    
    # Start the bridge
    logger.info("Starting port 8080 bridge service...")
    bridge_thread = start_bridge()
    
    if not bridge_thread:
        logger.error("Initial bridge start failed")
        sys.exit(1)
    
    # Main loop to keep the service running
    while not shutdown_event.is_set():
        # If the bridge thread has died and we're set to restart, restart it
        if args.restart and (not bridge_thread or not bridge_thread.is_alive()):
            logger.warning("Bridge thread has died, restarting...")
            bridge_thread = start_bridge()
            
            if not bridge_thread:
                logger.error("Bridge restart failed")
                sys.exit(1)
        
        # Wait a bit before checking again
        shutdown_event.wait(args.check_interval)
    
    logger.info("Bridge service shutting down")
    sys.exit(0)

if __name__ == "__main__":
    main()