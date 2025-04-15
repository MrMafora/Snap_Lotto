# Deployment Notes for Replit Cloud Run

This document outlines the specific changes made to support direct port binding for Replit Cloud Run deployment.

## Changes Made

1. **Changed run command to use port 8080 instead of 5000**
   - Updated `replit_deployment.toml` to use `gunicorn --bind 0.0.0.0:8080 main:app`
   - Updated `Procfile` to use the same direct binding approach

2. **Updated port forwarding configuration**
   - Modified `.replit-ports` to map internal port 8080 to external port 80
   - Removed unnecessary port 5000 mapping from configuration

3. **Added ENVIRONMENT variable to deployment configuration**
   - Added `[env]` section to `replit_deployment.toml` with `ENVIRONMENT = "production"`
   - This ensures health monitoring works correctly by checking the appropriate port

4. **Used more direct Gunicorn configuration**
   - Changed shell wrapper command to direct Gunicorn call
   - Updated `gunicorn.conf.py` to be environment-aware for port binding

5. **Created environment-aware start script**
   - Added `start_app.sh` that intelligently binds to port 5000 for development or port 8080 for production
   - Made the script executable with `chmod +x start_app.sh`

## Configuration Files

### replit_deployment.toml
```toml
run = "gunicorn --bind 0.0.0.0:8080 main:app"
deploymentTarget = "cloudrun"

# Health check endpoint
healthCheckPath = "/"

# Environment configuration
[env]
ENVIRONMENT = "production"
DEBUG = "false"
```

### .replit-ports
```toml
[[ports]]
localPort = 8080
externalPort = 80
```

### Procfile
```
web: gunicorn --bind 0.0.0.0:8080 main:app
```

## Health Monitoring

The health monitoring system now adapts to the environment:
- In development, it checks port 5000
- In production, it checks port 8080

This ensures that health checks are accurate regardless of which environment the application is running in.

## Starting the Application

For development:
```bash
./start_app.sh
```

For production deployment:
- Click "Deploy" in Replit
- The application will use the configuration in `replit_deployment.toml`

## Port Conflict Resolution

Two scripts have been added to handle port conflicts:

1. **Automatic Port Clearing**: The `start_app.sh` script automatically checks and kills any processes using ports 5000 and 8080 before starting the application.

2. **Manual Port Clearing**: If you encounter persistent port conflicts, you can manually run:
```bash
./clear_ports.sh
```

This will:
- Check for processes using ports 5000 and 8080
- Kill any found processes
- Verify that the ports are actually free after killing

If port conflicts persist after running these scripts, restarting the repl completely will resolve the issue.