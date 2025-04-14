#!/bin/bash
# Script to move redundant scripts to backup_deployments directory

# Create backup directory if it doesn't exist
mkdir -p ./backup_deployments

# List of files to move from the screenshot
REDUNDANT_FILES=(
  # Port binding and server management scripts
  "check_html.py"
  "cleanup_duplicates.sh"
  "deploy_preview.sh"
  "final_preview.sh"
  "immediate_port.py"
  "inspect_html.py"
  "instant_port.py"
  "instant_server.py"
  "instant_socket.py"
  "main_8080.py"
  "minimal_starter.py"
  "port_detector.py"
  "port_opener.py"
  "preview.sh"
  "quick_bind.py"
  "quick_server.py"
  "replit_8080_starter.py"
  "run_preview.sh"
  "simple_app.py"
  "simple_launcher.py"
  "start_app.sh"
  "start_direct.py"
  "start_direct.sh"
  "start_fast.sh"
  "start_immediate.sh"
  "start_instant.sh"
  "start_minimal.py"
  "start_on_port_8080.sh"
  "start_preview_fixed.sh"
  "start_preview.sh"
  "start_proxy.sh"
  "start_replit.py"
  "start_replit.sh"
  "start_server.sh"
  "start.sh"
  "start_simple.sh"
  "trace_port_5000.sh"
  "workflow_starter.py"
  # Documentation that has been consolidated
  "PORT_CONFIGURATION.md"
  "WORKFLOW_CONFIGURATION.md"
)

echo "Moving redundant files to backup_deployments directory..."
for file in "${REDUNDANT_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "  Moving: $file"
    mv "$file" ./backup_deployments/ 2>/dev/null || true
  fi
done

echo "Cleanup complete!"
echo "Moved redundant files to backup_deployments/"