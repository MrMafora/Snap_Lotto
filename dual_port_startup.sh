#!/bin/bash

# Start the main application on port 5000
python dual_bind_server.py &
DUAL_PID=$!

# Log the started processes
echo "Started dual port server with PID: $DUAL_PID"

# Keep the script running
wait $DUAL_PID