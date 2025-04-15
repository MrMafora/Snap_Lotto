"""
Test script to check if port 8080 can be bound.
This is a standalone script that only tries to bind to port 8080.
"""
import socket
import sys
import time

print("Attempting to bind to port 8080...")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 8080))
    s.listen(1)
    print("SUCCESS: Successfully bound to port 8080!")
    print("Keeping socket open for 30 seconds to verify...")
    
    # Keep socket open for a while to verify
    time.sleep(30)
    
    s.close()
    print("Socket closed")
    
except Exception as e:
    print(f"ERROR: Failed to bind to port 8080: {str(e)}")
    sys.exit(1)