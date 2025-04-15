#!/bin/bash
# Start Port 8080 Server Script

# This script starts a simple socket server on port 8080 that
# redirects all traffic to the main application on port 5000

echo "Starting port 8080 server at $(date)"

# Use a simple nc (netcat) command to listen on port 8080 and redirect
# Create a named pipe for the redirection
PIPE_NAME=$(mktemp -u)
mkfifo $PIPE_NAME

# HTTP redirect response template
cat > redirect_template.http << EOF
HTTP/1.1 302 Found
Location: http://localhost:5000\$path
Connection: close

EOF

# Function to handle incoming connections
handle_connection() {
    # Read the HTTP request to extract the path
    read -r line
    if [[ "$line" =~ ^(GET|POST|PUT|DELETE|HEAD|OPTIONS)\ (.*)\ HTTP ]]; then
        path="${BASH_REMATCH[2]}"
        # Replace template with actual path in redirect response
        sed "s|\\\$path|$path|g" redirect_template.http > $PIPE_NAME
    else
        # Default redirect if path couldn't be extracted
        cat redirect_template.http > $PIPE_NAME
    fi
    
    # Consume the rest of the HTTP request (headers)
    while read -r line && [ -n "$line" ]; do
        true
    done
}

# Start listening on port 8080 in the background
while true; do
    # Use nc to listen for connections
    nc -l 0.0.0.0 8080 < $PIPE_NAME | handle_connection
    echo "Restarting port 8080 listener at $(date)"
    sleep 1
done &

# Save the process ID for later cleanup
echo $! > port_8080.pid
echo "Port 8080 server started with PID $(cat port_8080.pid)"

# Cleanup function
cleanup() {
    if [ -f port_8080.pid ]; then
        echo "Stopping port 8080 server..."
        kill $(cat port_8080.pid) 2>/dev/null || true
        rm port_8080.pid
    fi
    rm -f $PIPE_NAME redirect_template.http
    exit 0
}

# Set up trap for cleanup
trap cleanup EXIT INT TERM

# Keep the script running
echo "Press Ctrl+C to stop the server"
tail -f /dev/null