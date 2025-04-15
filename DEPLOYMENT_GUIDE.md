# Deployment Guide for Lottery Data Intelligence Platform

This guide documents the steps needed to properly deploy the Lottery Data Intelligence Platform on Replit.

## Deployment Configuration

The application must be properly configured for deployment on Replit. Follow these steps to ensure correct configuration:

1. **Deployment Target**: Change the deployment target from "gce" to "cloudrun" for better compatibility.
   ```
   deploymentTarget = "cloudrun"
   ```
   This has been configured in `.replit-deployment`.

2. **Run Command**: Update the run command to bind to port 8080 instead of 5000.
   ```
   run = ["sh", "-c", "gunicorn --bind 0.0.0.0:8080 main:app"]
   ```
   This has been configured in `.replit-run-command`.

3. **Build Command**: Keep the build command as is, it's already correct.
   ```
   build = ["sh", "-c", "pip install -r requirements.txt"]
   ```

4. **Port Mapping**: Remove the port 5000 configuration and only keep the 8080:80 mapping.
   ```
   [[ports]]
   localPort = 8080
   externalPort = 80
   ```
   This has been configured in `.replit-ports`.

5. **Redundant Port Scripts**: Removed all redundant port configuration scripts from the backup_deployments directory to avoid conflicts.

6. **Health Monitoring**: Updated the health monitoring system to only check port 8080 instead of both port 5000 and 8080.

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