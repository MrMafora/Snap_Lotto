#!/bin/bash
# Final cleanup script to remove redundant files and tidy up the project

echo "======================================================"
echo "PERFORMING FINAL CLEANUP OF UNNECESSARY FILES"
echo "======================================================"

# Create backup directory if it doesn't exist
mkdir -p ./backup_deployments

# List of redundant files to move to backup
REDUNDANT_FILES=(
  "quick_bind.py"        # Redundant with absolute_minimal.py
  "check_html.py"        # Testing utility not needed in production
  "inspect_html.py"      # Testing utility not needed in production
  "screenshot_manager.py.new"  # Duplicate file
  "PORT_CONFIGURATION.md"      # Consolidated into FINAL_PORT_SOLUTION.md
  "WORKFLOW_CONFIGURATION.md"  # Consolidated into FINAL_PORT_SOLUTION.md
  "instant_port.py"      # We now use absolute_minimal.py
  "start.py"             # Not needed with gunicorn.conf.py
)

# Move the redundant files to backup
echo "Moving redundant files to backup..."
for file in "${REDUNDANT_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "  Moving: $file"
    mv "$file" ./backup_deployments/ 2>/dev/null || true
  else
    echo "  Not found: $file"
  fi
done

# Make sure essential scripts are executable
echo ""
echo "Making essential scripts executable..."
chmod +x workflow_wrapper.sh start_manually.sh 2>/dev/null || true

echo ""
echo "Essential files we're keeping:"
echo "-----------------------------"
echo "1. absolute_minimal.py - Dual-port binding solution for Replit"
echo "2. gunicorn.conf.py - Optimized gunicorn configuration for port 8080"
echo "3. workflow_wrapper.sh - Enhanced wrapper for workflow startup"
echo "4. start_manually.sh - Reliable manual startup script"
echo "5. FINAL_PORT_SOLUTION.md - Comprehensive documentation"
echo "6. main.py - Main Flask application with enhanced lazy loading"

echo ""
echo "CLEANUP COMPLETE!"
echo "======================================================"