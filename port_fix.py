#!/usr/bin/env python3
"""
Port fix module that updates the gunicorn.conf.py file to use port 8080
"""
import os
import sys
import logging
import fileinput
import time
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('port_fix')

def fix_gunicorn_config():
    """Fix the gunicorn.conf.py file to use the correct port 8080"""
    gunicorn_conf = 'gunicorn.conf.py'
    port_to_use = "8080"
    
    if not os.path.exists(gunicorn_conf):
        logger.error(f"Could not find {gunicorn_conf}")
        return False
    
    logger.info(f"Fixing {gunicorn_conf} to use port {port_to_use}")
    
    try:
        # Back up the original file
        with open(gunicorn_conf, 'r') as file:
            original_content = file.read()
        
        with open(f"{gunicorn_conf}.bak", 'w') as file:
            file.write(original_content)
        
        # Update the file to bind to port 8080
        content_updated = False
        
        for line in fileinput.input(gunicorn_conf, inplace=True):
            # Look for line defining the bind
            if re.match(r'^bind\s*=', line.strip()):
                line = f'bind = "0.0.0.0:{port_to_use}"\n'
                content_updated = True
            sys.stdout.write(line)
        
        fileinput.close()
        
        # If the bind line wasn't found, append it
        if not content_updated:
            with open(gunicorn_conf, 'a') as file:
                file.write(f'\n# Added by port_fix.py\nbind = "0.0.0.0:{port_to_use}"\n')
            content_updated = True
        
        # Also ensure workflow command binds to port 8080
        restart_file = '.replit-run-command'
        if os.path.exists(restart_file):
            for line in fileinput.input(restart_file, inplace=True):
                # Update the port in the run command
                if '--bind' in line:
                    line = re.sub(r'--bind\s+\S+', f'--bind 0.0.0.0:{port_to_use}', line)
                sys.stdout.write(line)
            fileinput.close()
        
        return content_updated
    except Exception as e:
        logger.error(f"Error fixing {gunicorn_conf}: {e}")
        # Restore original file if needed
        if os.path.exists(f"{gunicorn_conf}.bak"):
            with open(f"{gunicorn_conf}.bak", 'r') as backup:
                with open(gunicorn_conf, 'w') as original:
                    original.write(backup.read())
        return False

def fix_workflow_config():
    """Fix the .replit workflow configuration to use port 8080"""
    replit_files = ['.replit-run-command']
    
    for file_path in replit_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Replace port 5000 with 8080 in any command
                updated_content = re.sub(r'--bind\s+[^:]+:5000', '--bind 0.0.0.0:8080', content)
                
                if updated_content != content:
                    with open(file_path, 'w') as f:
                        f.write(updated_content)
                    logger.info(f"Updated {file_path} to use port 8080")
            except Exception as e:
                logger.error(f"Error updating {file_path}: {e}")

if __name__ == "__main__":
    logger.info("Starting port fix...")
    
    # Fix the gunicorn config
    if fix_gunicorn_config():
        logger.info("Successfully updated gunicorn.conf.py")
    else:
        logger.error("Failed to update gunicorn.conf.py")
    
    # Fix the workflow config files
    fix_workflow_config()
    
    logger.info("Port fix completed")