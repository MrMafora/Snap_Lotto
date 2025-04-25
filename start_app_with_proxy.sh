#!/bin/bash
# Kill any existing proxy processes
pkill -f "simple_proxy.py" || true

# Start the proxy in the background
echo "Starting port proxy (8080->5000)..."
python simple_proxy.py > proxy_output.log 2>&1 &
PROXY_PID=$!
echo "Proxy started with PID: $PROXY_PID"
echo $PROXY_PID > proxy.pid

# Wait for proxy to initialize
sleep 2

# Show status
echo "Application available at port 8080"
echo "Proxy running and forwarding requests from port 8080 to 5000"