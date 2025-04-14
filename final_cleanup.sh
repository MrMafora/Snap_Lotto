#!/bin/bash
# Final cleanup script to remove redundant files and tidy up the project

echo "======================================================"
echo "  FINAL CLEANUP OF LOTTERY DATA PLATFORM"
echo "======================================================"

# First run the redundant scripts cleanup if it exists
if [ -f "move_redundant_scripts.sh" ]; then
  echo "Running comprehensive redundant scripts cleanup..."
  chmod +x move_redundant_scripts.sh
  ./move_redundant_scripts.sh
else
  # Create backup directory if it doesn't exist
  mkdir -p ./backup_deployments
  
  # List of redundant files to move to backup
  REDUNDANT_FILES=(
    # Previously identified redundant files
    "quick_bind.py"        # Redundant with absolute_minimal.py
    "check_html.py"        # Testing utility not needed in production
    "inspect_html.py"      # Testing utility not needed in production
    "screenshot_manager.py.new"  # Duplicate file
    "PORT_CONFIGURATION.md"      # Consolidated into FINAL_PORT_SOLUTION.md
    "WORKFLOW_CONFIGURATION.md"  # Consolidated into FINAL_PORT_SOLUTION.md
    "instant_port.py"      # We now use absolute_minimal.py
    "start.py"             # Not needed with gunicorn.conf.py
    
    # Additional port handling scripts
    "immediate_port.py"
    "instant_server.py"
    "instant_socket.py" 
    "main_8080.py"
    "port_detector.py"
    "quick_server.py"
    "port_opener.py"
    
    # Various startup scripts
    "start_app.sh"
    "start_direct.py"
    "start_direct.sh"
    "start_fast.sh"
    "start_immediate.sh"
    "start_instant.sh"
    "start_minimal.py"
    "start_on_port_8080.sh"
    "start_preview_fixed.sh"
    "start_replit.py"
    "start_server.sh"
    "start.sh"
    "start_simple.sh"
    
    # Preview and deployment files
    "deploy_preview.sh"
    "final_preview.sh"
    "preview.sh"
    "run_preview.sh"
    
    # Utility scripts
    "simple_app.py"
    "simple_launcher.py"
    "trace_port_5000.sh"
    "workflow_starter.py"
    "minimal_starter.py"
    "replit_8080_starter.py"
    "quick_server.py"
  )
  
  # Move the redundant files to backup
  echo "Moving redundant files to backup..."
  for file in "${REDUNDANT_FILES[@]}"; do
    if [ -f "$file" ]; then
      echo "  Moving: $file"
      mv "$file" ./backup_deployments/ 2>/dev/null || true
    fi
  done
fi

# Remove any temporary or cache files
echo "Removing temporary files and Python caches..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.log" -delete 2>/dev/null || true

# Make sure essential scripts are executable
echo ""
echo "Making essential scripts executable..."
chmod +x workflow_wrapper.sh start_manually.sh 2>/dev/null || true

# Make a backup of requirements.txt for safety
cp requirements.txt requirements.txt.bak 2>/dev/null || true

echo ""
echo "Essential files we're keeping:"
echo "-----------------------------"
echo "1. absolute_minimal.py - Dual-port binding solution for Replit"
echo "2. gunicorn.conf.py - Optimized gunicorn configuration for port 8080"
echo "3. workflow_wrapper.sh - Enhanced wrapper for workflow startup"
echo "4. start_manually.sh - Reliable manual startup script"
echo "5. FINAL_PORT_SOLUTION.md - Comprehensive documentation"
echo "6. main.py - Main Flask application with enhanced lazy loading"
echo "7. PACKAGE_REQUIREMENTS.md - Dependency documentation"
echo "8. CLEANUP_SUMMARY.md - Documentation of cleanup efforts"

echo ""
echo "✅ CLEANUP COMPLETE!"
echo "✅ All scripts now have proper execute permissions"
echo "✅ Removed Python cache files for cleaner operation"
echo "✅ Unnecessary scripts moved to backup_deployments/"
echo ""
echo "🚀 The application is now ready to run"
echo "   - Use './start_manually.sh' to start the server manually"
echo "   - Or use the Replit workflow 'Start application'"
echo "======================================================"