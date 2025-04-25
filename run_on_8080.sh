#!/bin/bash
# Force kill any existing process on port 8080
echo "Stopping any process on port 8080..."
fuser -k 8080/tcp 2>/dev/null || true
sleep 1

# Also stop any existing proxy service
pkill -f "port_proxy_service.py" || true
sleep 1

# Start the port proxy service in the background
echo "Starting port proxy service..."
chmod +x port_proxy_service.py
./port_proxy_service.py > proxy_output.log 2>&1 &
PROXY_PID=$!
echo "Proxy PID: $PROXY_PID"
echo $PROXY_PID > proxy.pid

# Wait for the proxy to initialize
sleep 2

# Run gunicorn on port 5000 (which will be proxied to 8080)
echo "Starting application server on port 5000 (proxied to 8080)..."
exec gunicorn --bind=0.0.0.0:5000 --reuse-port --reload main:app