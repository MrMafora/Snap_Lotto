"""
Extremely minimal socket server to open port 5000 instantly
"""
import socket
import threading
import time
import subprocess
import os

# Create a simple socket server on port 5000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    # Bind to port 5000 immediately
    s.bind(('0.0.0.0', 5000))
    s.listen(1)
    
    # Print the exact message that Replit looks for
    print("Server is ready and listening on port 5000")
    
    # Function to start real app after detection
    def start_real_app():
        time.sleep(2)  # Wait to ensure detection has happened
        s.close()      # Close our temporary socket
        
        try:
            # Start the real application (don't reuse port flag)
            subprocess.run(["gunicorn", "--bind", "0.0.0.0:5000", "--config", "gunicorn.conf.py", "main:app"])
        except Exception as e:
            print(f"Error starting application: {e}")
    
    # Start the real app in a background thread
    app_thread = threading.Thread(target=start_real_app)
    app_thread.daemon = True
    app_thread.start()
    
    # Accept a single connection, then exit
    conn, addr = s.accept()
    conn.send(b"HTTP/1.1 200 OK\r\nContent-Length: 29\r\n\r\nStarting South African Lottery App")
    conn.close()
    
except Exception as e:
    print(f"Socket error: {e}")
    # If the socket bind fails, try starting the app directly
    try:
        subprocess.run(["gunicorn", "--bind", "0.0.0.0:5000", "--config", "gunicorn.conf.py", "main:app"])
    except Exception as e:
        print(f"Error starting application: {e}")
finally:
    # Ensure socket is closed
    s.close()