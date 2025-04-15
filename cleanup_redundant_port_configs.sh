#!/bin/bash

# Cleanup script to remove redundant port configuration scripts
# The deployment only needs to use port 8080

echo "Cleaning up redundant port configuration scripts..."

# Remove direct port configuration scripts
rm -f backup_deployments/immediate_port.py
rm -f backup_deployments/instant_port.py
rm -f backup_deployments/instant_server.py
rm -f backup_deployments/instant_socket.py
rm -f backup_deployments/main_8080.py
rm -f backup_deployments/port_detector.py
rm -f backup_deployments/port_opener.py
rm -f backup_deployments/quick_bind.py
rm -f backup_deployments/quick_server.py
rm -f backup_deployments/replit_8080_starter.py
rm -f backup_deployments/simple_app.py
rm -f backup_deployments/simple_launcher.py
rm -f backup_deployments/start.py
rm -f backup_deployments/start_direct.py
rm -f backup_deployments/start_minimal.py
rm -f backup_deployments/start_replit.py
rm -f backup_deployments/workflow_starter.py

# Remove start scripts
rm -f backup_deployments/start.sh
rm -f backup_deployments/start_app.sh
rm -f backup_deployments/start_direct.sh
rm -f backup_deployments/start_fast.sh
rm -f backup_deployments/start_immediate.sh
rm -f backup_deployments/start_instant.sh
rm -f backup_deployments/start_on_port_8080.sh
rm -f backup_deployments/start_preview.sh
rm -f backup_deployments/start_preview_fixed.sh
rm -f backup_deployments/start_proxy.sh
rm -f backup_deployments/start_replit.sh
rm -f backup_deployments/start_server.sh
rm -f backup_deployments/start_simple.sh
rm -f backup_deployments/trace_port_5000.sh

# Remove all files in port_binding_experiments directory
rm -rf backup_deployments/port_binding_experiments

echo "Cleanup completed. Only necessary configuration for port 8080 remains."