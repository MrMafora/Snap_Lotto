#!/bin/bash
# Start the lottery application on both port 5000 and 8080
# This script provides dual-port support for the application

# Print banner
echo "====================================================="
echo "  LOTTERY APPLICATION DUAL-PORT STARTUP"
echo "====================================================="
echo "Starting application on ports 5000 and 8080..."

# Clear ports if they're in use
echo "Checking port availability..."
for PORT in 5000 8080; do
    if lsof -i ":$PORT" > /dev/null 2>&1; then
        echo "Port $PORT is in use. Clearing..."
        if command -v fuser > /dev/null; then
            fuser -k "$PORT/tcp"
        else
            for pid in $(lsof -t -i:"$PORT"); do
                echo "Killing process $pid"
                kill -9 "$pid"
            done
        fi
        sleep 1
    else
        echo "Port $PORT is available."
    fi
done

# Create a very simple port forwarder using netcat
create_port_forwarder() {
    # Parameters
    local source_port=$1
    local target_port=$2
    
    # Create a port forwarder using netcat in the background
    echo "Creating port forwarder from $source_port to $target_port..."
    
    # Create a bash script for the port forwarding
    cat > forward_$source_port.sh << EOF
#!/bin/bash
while true; do
    echo "Starting port forwarding $source_port -> $target_port..."
    nc -l -p $source_port -c "nc localhost $target_port" || true
    echo "Port forwarding $source_port -> $target_port interrupted, restarting..."
    sleep 1
done
EOF
    
    # Make it executable
    chmod +x forward_$source_port.sh
    
    # Run it in the background
    nohup ./forward_$source_port.sh > forward_$source_port.log 2>&1 &
    echo "Port forwarder started with PID: $!"
}

# Environment detection
if [ "$ENVIRONMENT" == "production" ]; then
    # Production mode - run directly on port 8080
    echo "Running in production mode on port 8080..."
    exec gunicorn --bind 0.0.0.0:8080 --workers 4 --reuse-port main:app
else
    # Development mode - run on port 5000 and create a forwarder on port 8080
    echo "Running in development mode (dual port)..."
    
    # Start the main application on port 5000
    echo "Starting main application on port 5000..."
    nohup gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app > gunicorn_5000.log 2>&1 &
    MAIN_PID=$!
    echo "Main application started with PID: $MAIN_PID"
    
    # Wait for main application to become available
    echo "Waiting for main application to start..."
    MAX_ATTEMPTS=10
    for ((i=1; i<=$MAX_ATTEMPTS; i++)); do
        if curl -s http://127.0.0.1:5000/health_check > /dev/null; then
            echo "Main application is ready!"
            break
        else
            if [ $i -eq $MAX_ATTEMPTS ]; then
                echo "Failed to start main application after $MAX_ATTEMPTS attempts"
                kill -9 $MAIN_PID 2>/dev/null
                exit 1
            fi
            echo "Waiting for main application... (attempt $i/$MAX_ATTEMPTS)"
            sleep 2
        fi
    done
    
    # Start the second application instance directly on port 8080
    echo "Starting second application instance on port 8080..."
    exec gunicorn --bind 0.0.0.0:8080 --reuse-port main:app
fi