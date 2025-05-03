#!/usr/bin/env python3
"""
Script to modify the workflow to use optimized server settings
"""
import os
import logging
import time
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('modify_workflow')

def create_optimized_workflow_config():
    """Create a new workflow config file with optimized settings"""
    logger.info("Creating optimized workflow configuration...")
    
    config_content = '''
# Optimized workflow configuration
# Copy and paste these settings into the .replit file manually

[[workflows.workflow]]
name = "Optimized Server"
author = "agent"
    
[workflows.workflow.metadata]
agentRequireRestartOnSave = false
    
[[workflows.workflow.tasks]]
task = "packager.installForAll"
    
[[workflows.workflow.tasks]]
task = "shell.exec"
args = "python run_optimized.py"
waitForPort = 8080
'''
    
    with open('new_workflow_config.md', 'w') as f:
        f.write(config_content)
    
    logger.info("Workflow configuration file created at: new_workflow_config.md")
    logger.info("Please copy and paste these settings into the .replit file manually")
    
    return True

def setup_optimized_server():
    """Create startup script for optimized server"""
    logger.info("Creating startup script for optimized server...")
    
    script_content = '''#!/bin/bash
# Optimized server startup script
echo "Starting optimized server..."
pkill -9 python
pkill -9 gunicorn
sleep 2
python run_optimized.py
'''
    
    with open('start_optimized_server.sh', 'w') as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod('start_optimized_server.sh', 0o755)
    
    logger.info("Startup script created at: start_optimized_server.sh")
    
    return True

def create_documentation():
    """Create documentation for optimized server configuration"""
    logger.info("Creating documentation for workflow modifications...")
    
    doc_content = '''# Optimized Workflow Configuration

To use the optimized server configuration:

## Option 1: Manually run the optimized server

```bash
./start_optimized_server.sh
```

This will:
1. Kill all existing Python and Gunicorn processes
2. Wait for 2 seconds to ensure all processes are terminated
3. Start the optimized server using `run_optimized.py`

## Option 2: Create a new workflow (Recommended)

To create a new optimized workflow:

1. Open the Replit workflow editor
2. Create a new workflow named "Optimized Server"
3. Add the following tasks:
   - Task 1: `packager.installForAll`
   - Task 2: `shell.exec` with args `python run_optimized.py`
   - Set waitForPort to 8080

## Why this configuration is better

1. Directly binds to port 8080 (no port forwarding overhead)
2. Uses only 4 worker processes (reduced resource contention)
3. Optimized connection handling settings
4. Proper process management (no orphaned processes)

For more details, see the PERFORMANCE_OPTIMIZATION_GUIDE.md file.
'''
    
    with open('NEW_WORKFLOW_CONFIG.md', 'w') as f:
        f.write(doc_content)
    
    logger.info("Documentation created at: NEW_WORKFLOW_CONFIG.md")
    
    return True

def main():
    """Main function"""
    logger.info("Starting workflow modification process...")
    
    # Create optimized workflow configuration
    create_optimized_workflow_config()
    
    # Setup optimized server
    setup_optimized_server()
    
    # Create documentation
    create_documentation()
    
    logger.info("Workflow modification process completed")
    logger.info("Please review the documentation and follow the instructions to update your workflow")
    
    return True

if __name__ == "__main__":
    main()