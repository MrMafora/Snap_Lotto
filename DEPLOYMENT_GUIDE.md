# Lottery Application Deployment Guide

This document outlines the deployment process for the Lottery Application on Replit's Cloud Run service.

## Deployment Configuration

The application is configured to run on port **8080** for deployment, which is a requirement for Replit Cloud Run deployments.

### Key Configuration Files

1. **replit_deployment.toml**: The deployment configuration for Replit that specifies:
   - The Gunicorn command with direct port 8080 binding
   - The deployment target (`cloudrun`)
   - Health check path (`/`)
   - Environment variables (`ENVIRONMENT=production`, `DEBUG=false`)

2. **Procfile**: Contains the web process configuration for deployment:
   - Uses direct Gunicorn binding to port 8080 with the command:
     ```
     web: gunicorn --bind 0.0.0.0:8080 main:app
     ```

3. **.replit-ports**: Contains port mapping configuration:
   - Maps local port 8080 to external port 80, which allows the deployed application to be accessible on the standard HTTP port

### Environment-Aware Components

The application includes environment-aware components that adjust their behavior based on whether they're running in development or production:

1. **Health Monitoring System**: 
   - Automatically checks port 5000 in development environment
   - Automatically checks port 8080 in production environment
   - Uses the `ENVIRONMENT` environment variable to determine which port to check

## Deployment Steps

1. **Prepare for Deployment**:
   - Make sure all dependencies are listed in `requirements.txt`
   - Ensure the database connection is correctly configured for production

2. **Deploy to Replit**:
   - Click the "Deploy" button in the Replit interface
   - Replit will use the configuration in `replit_deployment.toml`
   - The application will be built and deployed using Cloud Run

3. **Post-Deployment Verification**:
   - Check the health monitoring dashboard
   - Verify that all features function correctly
   - Confirm that scheduled tasks are running

## Deployment Architecture

### Port Binding Solution

This deployment uses a direct port 8080 binding approach specifically required by Replit Cloud Run:

- **Direct Gunicorn Binding**: We configure Gunicorn to bind directly to port 8080 in the deployment command
- **No Shell Scripts**: We avoid using shell scripts which can cause issues with Replit deployments
- **Consistent Configuration**: The same port binding approach is used in both Procfile and replit_deployment.toml
- **Port Mapping**: External traffic on port 80 is mapped to the application's port 8080

### Deployment vs. Development

The project supports different port configurations for development and production:

| Environment | Port | Purpose | Configuration |
|-------------|------|---------|---------------|
| Development | 5000 | Local development with debugging enabled | Used by Replit workspace |
| Production  | 8080 | Required by Replit Cloud Run for deployment | Used by deployment configuration |

### Health Monitoring

The health monitoring system is designed to be environment-aware:
- Automatically adapts to the appropriate port based on the `ENVIRONMENT` variable
- Eliminates false alerts by checking for the proper port in each environment
- Provides consistent health reporting across environments

## Troubleshooting

If you encounter issues with the deployment:

1. **Check Port Binding**: Verify that the application is properly binding to port 8080
2. **Review Logs**: Check the application logs for any error messages
3. **Check Health Status**: Use the health monitoring dashboard to identify issues

## Environment Variables

The following environment variables are set in deployment:

- `ENVIRONMENT`: Set to `production` for deployment
- `DEBUG`: Set to `false` for deployment

Additional environment variables like database credentials should be configured through Replit Secrets.