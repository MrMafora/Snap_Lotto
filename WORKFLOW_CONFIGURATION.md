# Replit Workflow Configuration

## Current Configuration

The application is configured to work with Replit's expected port configuration:

1. **gunicorn on port 5000**:
   - Replit expects the application to run on port 5000
   - We use gunicorn to bind to this port: `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`

2. **Essential files**:
   - `main.py`: The main Flask application
   - `workflow_wrapper.sh`: The script that Replit runs when starting the workflow
   - `force_kill_port_5000.sh`: Script to forcefully terminate any processes on port 5000
   - `clear_ports.sh`: Script to clear any processes on required ports

## Workflow Explanation

When Replit starts the application:

1. The workflow runs `./workflow_wrapper.sh`
2. This runs `force_kill_port_5000.sh` to ensure the port is free
3. Then it launches gunicorn directly on port 5000, binding to `main:app`
4. Gunicorn handles the application, with automatic reloading for development

## Deployment Configuration

For deployment:

1. Replit uses the command in the "run" field of the deployment configuration
2. We use the same approach: gunicorn binding to port 5000

## Important Notes

1. **Don't change ports**: Keep using port 5000 as this is what Replit expects
2. **Don't modify `.replit`**: The workflow configuration in the Replit UI should match our approach
3. **Keep it simple**: Avoid complex port forwarding or dual-port approaches

This configuration ensures compatibility with Replit's workflow system and avoids port conflicts.