# Lottery Application Deployment Guide

This document outlines the deployment process for the Lottery Application on Replit's Cloud Run service.

## Deployment Configuration

The application is configured to run on port **8080** for deployment, which is a requirement for Replit Cloud Run deployments.

### Key Files

1. **gunicorn.conf.py**: This is the main configuration file for Gunicorn that ensures the application binds to port 8080.

2. **direct_start.sh**: A simple bash script that launches Gunicorn with the configuration file.

3. **replit_deployment.toml**: The deployment configuration for Replit that specifies:
   - Which script to run (`direct_start.sh`)
   - The deployment target (`cloudrun`)
   - Health check path (`/`)
   - Environment variables

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

## Port Binding Solution

This deployment uses a direct port 8080 binding solution through Gunicorn's configuration file. This approach:

- Ensures consistent binding across environments
- Simplifies the deployment process
- Works reliably with Replit's Cloud Run service

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