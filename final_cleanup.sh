#!/bin/bash
# Final cleanup script to keep only essential deployment files

echo "======================================================"
echo "PERFORMING FINAL CLEANUP OF DUPLICATE DEPLOYMENT FILES"
echo "======================================================"

# Create backup directory if it doesn't exist
mkdir -p ./backup_deployments

# Back up all alternative port configuration files
echo "Moving all alternative port configuration files to backup..."
mv main_8080.py replit_8080_starter.py start_direct.py ./backup_deployments/ 2>/dev/null || true
mv start_on_port_8080.sh ./backup_deployments/ 2>/dev/null || true

# Keep only the essential files and shell scripts
echo "Keeping only essential deployment files..."
for file in *.sh; do
  if [[ "$file" != "workflow_wrapper.sh" && "$file" != "force_kill_port_5000.sh" && "$file" != "clear_ports.sh" && "$file" != "final_cleanup.sh" ]]; then
    if [ -f "$file" ]; then
      echo "  Backing up: $file"
      mv "$file" ./backup_deployments/ 2>/dev/null || true
    fi
  fi
done

# Verify our essential files exist and are executable
echo "Making sure essential files are executable..."
chmod +x workflow_wrapper.sh force_kill_port_5000.sh clear_ports.sh 2>/dev/null || true

echo ""
echo "Essential files we're keeping:"
echo "-----------------------------"
echo "1. workflow_wrapper.sh - Main entry point for Replit workflows (uses port 5000)"
echo "2. force_kill_port_5000.sh - Port conflict resolver"
echo "3. clear_ports.sh - General port cleaner"
echo "4. main.py - Main Flask application"

echo ""
echo "CLEANUP COMPLETE!"
echo "======================================================"