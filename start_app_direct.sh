#!/bin/bash
# Kill any existing processes using port 8080
fuser -k 8080/tcp 2>/dev/null || true
sleep 1

# Export environment variables to ensure port 8080 is used
export PORT=8080
export FLASK_RUN_PORT=8080
export GUNICORN_PORT=8080

# Start Flask directly on port 8080
echo "Starting Flask directly on port 8080"
exec python3 -c "from main import app; app.run(host='0.0.0.0', port=8080, debug=True)"