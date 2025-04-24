import http.server
import socketserver
import urllib.request
import threading
import time
import sys

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            response = urllib.request.urlopen(f'http://localhost:5000{self.path}')
            self.send_response(response.status)
            for header, value in response.getheaders():
                if header.lower() != 'transfer-encoding':
                    self.send_header(header, value)
            self.end_headers()
            self.wfile.write(response.read())
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(e).encode())
    
    def log_message(self, format, *args):
        pass  # Silence logs

socketserver.TCPServer.allow_reuse_address = True
server = socketserver.TCPServer(('', 8080), ProxyHandler)

def run_server():
    server.serve_forever()

thread = threading.Thread(target=run_server)
thread.daemon = True
thread.start()

print("Proxy server running on port 8080")
print("Testing proxy with a request to port 8080...")
try:
    time.sleep(1)
    result = urllib.request.urlopen('http://localhost:8080/').read(100)
    print(f"Success! Received {len(result)} bytes from port 8080")
    print(f"Response starts with: {result[:50]}")
except Exception as e:
    print(f"Error accessing port 8080: {e}")

# Keep the server running for a moment to allow external tests
time.sleep(5)
