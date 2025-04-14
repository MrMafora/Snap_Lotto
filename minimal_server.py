"""
Minimal server script to help diagnose Replit port detection issues
"""
import socket
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Create a minimal server that opens port 5000 then launches the main app"""
    # First, create a socket on port 5000 to make Replit detect it
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Bind to all interfaces on port 5000
        s.bind(('0.0.0.0', 5000))
        s.listen(1)
        logger.info("Socket opened and listening on port 5000")
        print("Socket opened and listening on port 5000")
        
        # Sleep briefly to allow Replit to detect the port
        time.sleep(1)
        
        # Now start the actual app in a separate thread
        def start_app():
            # Close our socket first to free up the port
            s.close()
            logger.info("Socket closed, starting main application")
            
            # Now start the actual application
            import subprocess
            subprocess.call(["gunicorn", "--bind", "0.0.0.0:5000", "main:app"])
        
        # Start the app in a thread
        app_thread = threading.Thread(target=start_app)
        app_thread.daemon = True
        app_thread.start()
        
        # Keep the main thread alive with a sleep loop
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
    finally:
        try:
            s.close()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    main()