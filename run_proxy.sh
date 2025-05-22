#!/bin/bash
# Stop any existing proxies
pkill -f "port_proxy_service.py" || true
pkill -f "simple_proxy.py" || true

# Set port and proxy permissions
chmod +x port_proxy_service.py

# Launch the proxy in the background
echo "Starting port proxy service (8080 → 5000)..."
python port_proxy_service.py > proxy_output.log 2>&1 &
echo "Proxy PID: $!"
echo $! > proxy.pid

# Wait for it to initialize
sleep 2

# Show status
echo "Port proxy running in background"
echo "Web application accessible on port 8080"
echo "Logs available in proxy_service.log and proxy_output.log"