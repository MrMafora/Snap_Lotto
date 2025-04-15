#!/bin/bash
# Script to clean up legacy port binding solutions that are no longer needed

echo "Cleaning up outdated port binding solutions..."

# List of outdated scripts and files
outdated_files=(
  "bridge.py"
  "bridge.log"
  "dual_bind_server.py"
  "dual_port_binding.py"
  "dual_port_server.py"
  "dual_port_server.sh"
  "dual_port_solution.py"
  "dual_port_startup.sh"
  "dual_server.log"
  "final_direct_port.log"
  "final_direct_port.pid"
  "final_direct_port_solution.py"
  "final_port.pid"
  "port8080.pid"
  "port_8080_bridge.py"
  "port_bridge.py"
  "port_8080_server.py"
  "replit_proxy.py"
  "run_port_8080.sh"
  "run_port_8080_bridge.py"
  "run_on_port_8080.sh"
  "run_with_proxy.py"
  "simple_8080.log"
  "simple_8080_redirector.py"
  "simple_port8080.py"
  "simple_port_8080.py"
  "start_dual_server.py"
  "start_dual_server.sh"
)

# Counter for removed files
removed=0

# Check each file and remove if it exists
for file in "${outdated_files[@]}"; do
  if [ -f "$file" ]; then
    echo "Removing $file"
    mv "$file" "backup_deployments/$file" 2>/dev/null || rm -f "$file"
    removed=$((removed+1))
  fi
done

# Create backup directory if it doesn't exist
mkdir -p backup_deployments

echo "Cleanup complete. Removed or moved $removed outdated files."
echo "The current port binding solution is documented in FINAL_PORT_SOLUTION.md"