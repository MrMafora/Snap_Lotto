# Deployment Guide for Lottery Data Intelligence Platform

This guide documents the steps needed to properly deploy the Lottery Data Intelligence Platform on Replit.

## Deployment Configuration Errors Fixed

The application has been configured to resolve deployment errors. The following issues have been addressed:

1. **Application configured to listen on port 5000 but deployment forwarding to 8080**
   - Updated all port configurations to use port 8080 consistently across the application
   - Fixed gunicorn command to use `--bind 0.0.0.0:8080`
   - Modified health monitoring to check only port 8080

2. **Multiple port handling scripts with inconsistent configurations**
   - Removed redundant port configuration scripts
   - Ensured all references use the same port

3. **Run command mismatch**
   - Updated replit_deployment.toml to use the correct command:
   ```
   run = "gunicorn --bind 0.0.0.0:8080 main:app"
   ```

4. **Deployment target correction**
   - Changed from "gce" to "cloudrun" for better compatibility:
   ```
   deploymentTarget = "cloudrun"
   ```

5. **Health check path update**
   - Changed to use standard route that's guaranteed to exist:
   ```
   healthCheckPath = "/"
   ```

6. **Port mapping configuration**
   - Removed port 5000 mapping and only kept port 8080:80 mapping:
   ```
   [[ports]]
   localPort = 8080
   externalPort = 80
   ```

## Key Solution: Custom Port 8080 Script

We've created a dedicated script to ensure the application always binds to port 8080:

**run_on_port_8080.sh**
```bash
#!/bin/bash
# Run the application on port 8080 for Replit deployment compatibility
echo "Starting server on port 8080..."
gunicorn --bind 0.0.0.0:8080 --workers=4 --reuse-port --reload main:app
```

This script is made executable with `chmod +x run_on_port_8080.sh` and is referenced in all configuration files.

## Updated Configuration Files

1. **replit_deployment.toml**
   ```
   run = "./run_on_port_8080.sh"
   deploymentTarget = "cloudrun"
   healthCheckPath = "/"
   ```

2. **.replit-deployment**
   ```
   deploymentTarget = "cloudrun"
   ```

3. **.replit-ports**
   ```
   [[ports]]
   localPort = 8080
   externalPort = 80
   ```

4. **.replit-run-command**
   ```
   run = ["sh", "-c", "./run_on_port_8080.sh"]
   ```

5. **workflows/Start application.toml**
   ```
   [[tasks]]
   task = "packager.installForAll"

   [[tasks]]
   task = "shell.exec"
   args = "./run_on_port_8080.sh"
   waitForPort = 8080
   ```

5. **gunicorn.conf.py**
   ```python
   # Bind to 0.0.0.0:8080 for deployment
   bind = "0.0.0.0:8080"
   ```

## Health Monitoring Update

The health monitoring system has been updated to check port 8080 only:

```python
# We now only check port 8080 as we're binding directly to it for deployment
port_8080_status = check_server_port(8080)
```

## Additional Health Check Endpoints

Added health check endpoints:
1. `/health_port_check` - Simple endpoint for port availability checking
2. `/health_check` - Comprehensive health check endpoint for Replit deployment

## Additional Configuration

1. **Gunicorn Configuration**: The `gunicorn.conf.py` file is already correctly configured to bind to port 8080:
   ```python
   # Bind to 0.0.0.0:8080 for deployment
   bind = "0.0.0.0:8080"
   
   # Recommended number of workers
   workers = 4
   
   # Timeout value
   timeout = 60
   ```

2. **Database Configuration**: The application uses the `DATABASE_URL` environment variable for PostgreSQL connection. This is already properly configured.

## Deployment Process

1. Ensure all configuration files are properly set up as described above.
2. Click the "Deploy" button in the Replit interface.
3. The application will be deployed with the correct port configurations.
4. After deployment, the application will be accessible at the Replit deployment URL.

## Troubleshooting

- If the application fails to start, check the logs for port binding issues.
- Verify that only port 8080 is being used for external connections.
- Check the health monitoring dashboard to ensure all services are running correctly.