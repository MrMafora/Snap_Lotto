#!/bin/bash
# Script to clean up duplicate deployment files

echo "Cleaning up duplicate deployment files..."

# Create backup directory
mkdir -p ./backup_deployments

# Move unnecessary Python server scripts to backup
echo "Moving unnecessary Python server scripts..."
mv instant_server.py quick_server.py port_detector.py ./backup_deployments/ 2>/dev/null || true
mv immediate_port.py instant_port.py ./backup_deployments/ 2>/dev/null || true
mv start_minimal.py ./backup_deployments/ 2>/dev/null || true
mv start_replit.py ./backup_deployments/ 2>/dev/null || true

# Move unnecessary shell scripts to backup
echo "Moving unnecessary shell scripts..."
mv start_instant.sh start_proxy.sh start_immediate.sh ./backup_deployments/ 2>/dev/null || true
mv start_simple.sh start_fast.sh run_preview.sh ./backup_deployments/ 2>/dev/null || true
mv start_preview.sh start_preview_fixed.sh ./backup_deployments/ 2>/dev/null || true
mv start_app.sh preview.sh final_preview.sh ./backup_deployments/ 2>/dev/null || true
mv start_replit.sh ./backup_deployments/ 2>/dev/null || true

echo "Keeping only essential deployment files:"
echo "- workflow_wrapper.sh (main workflow entry point)"
echo "- start_on_port_8080.sh (direct port 8080 starter)"
echo "- start.sh (production deployment starter)"
echo "- force_kill_port_5000.sh (port conflict resolver)"
echo "- clear_ports.sh (general port cleaner)"
echo "- deploy_preview.sh (for Replit deployment)"
echo "- start_direct.py (port forwarder for direct URL access)"

echo "Cleanup complete!"