#!/bin/bash
# Cleanup script for redundant port binding and deployment solution files

echo "=== Lottery Application Cleanup ==="
echo "Removing redundant port binding solutions and deployment scripts..."

# Files to keep (primary solution files)
# - main.py (main application)
# - replit_deployment.toml (deployment configuration)
# - FINAL_DEPLOYMENT_SOLUTION.md (documentation)
# - DEPLOYMENT_FIXES.md (documentation)
# - .env (production environment)
# - gunicorn.conf.py (server configuration)
# - health_monitor.py (health monitoring)

# Redundant port binding solutions
PORT_BINDING_FILES=(
  "bridge.py"
  "check_port_status.py"
  "cleanup_legacy_port_solutions.sh"
  "cleanup_redundant_port_configs.sh"
  "clear_ports.sh"
  "direct_binding.py"
  "direct_gunicorn.sh"
  "direct_port_8080.py"
  "direct_port_binding.py"
  "direct_start.sh"
  "dual_bind_server.py"
  "dual_port_binding.py"
  "dual_port_server.py"
  "dual_port_server.sh"
  "dual_port_solution.py"
  "dual_port_startup.sh"
  "dual_server.log"
  "final_cleanup.sh"
  "final_direct_port.log"
  "final_direct_port.pid"
  "final_direct_port_solution.py"
  "final_port.pid"
  "final_port_solution.py"
  "final_port_solution.sh"
  "final_solution.py"
  "launch.sh"
  "port8080.pid"
  "port_8080_bridge.py"
  "port_8080_direct.sh"
  "port_8080_server.py"
  "port_bridge.py"
  "run_on_port_8080.sh"
  "run_port_8080.sh"
  "run_port_8080_bridge.py"
  "run_with_proxy.py"
  "simple_8080.log"
  "simple_8080_redirector.py"
  "simple_port8080.py"
  "simple_port_8080.py"
  "start_app.sh"
  "start_combined.sh"
  "start_dual_port.sh"
  "start_dual_server.py"
  "start_dual_server.sh"
  "start_final_solution.sh"
  "start_manually.sh"
  "start_on_port_8080.sh"
  "start_port_8080_bridge.py"
  "start_production.sh"
  "start_replit_server.sh"
  "replit_start.sh"
  "replit_start_8080.sh"
  "replit_proxy.py"
  "production_server.py"
  "deployment.py"
  "deployment.sh"
)

# Redundant documentation files
DOC_FILES=(
  "PORT_BINDING_SOLUTION.md"
  "PORT_BINDING_SUMMARY.md"
  "DEPLOYMENT_GUIDE.md"
  "DEPLOYMENT_NOTES.md"
  "FINAL_PORT_SOLUTION.md"
)

# Count removed files
removed_count=0

# Remove redundant port binding files
for file in "${PORT_BINDING_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Removing: $file"
    rm "$file"
    removed_count=$((removed_count + 1))
  fi
done

# Remove redundant documentation
for file in "${DOC_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Removing: $file"
    rm "$file"
    removed_count=$((removed_count + 1))
  fi
done

echo ""
echo "=== Cleanup Summary ==="
echo "Removed $removed_count redundant files."
echo "Kept essential files:"
echo "- main.py (Main application)"
echo "- replit_deployment.toml (Deployment configuration)"
echo "- .env (Production environment variables)"
echo "- FINAL_DEPLOYMENT_SOLUTION.md (Final deployment documentation)"
echo "- DEPLOYMENT_FIXES.md (Deployment fixes documentation)"
echo "- gunicorn.conf.py (Gunicorn server configuration)"
echo "- health_monitor.py (Health monitoring system)"
echo ""
echo "The project is now clean and ready for deployment!"