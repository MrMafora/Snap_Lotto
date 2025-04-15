# Lottery Scraper Deployment Guide

This document outlines the deployment process for the Lottery Scraper application on Replit.

## Deployment Configuration

The application is configured to run directly on port 8080 for Replit's deployment service using the following files:

1. `deployment.py` - Main deployment script that binds directly to port 8080
2. `Procfile` - Specifies the command to run for web deployments
3. `replit_deployment.toml` - Replit-specific deployment configuration

## How to Deploy

1. Make sure all changes are committed to the repository
2. Click the "Deploy" button in the Replit interface
3. Select "Web Service" as the deployment type
4. Wait for the deployment process to complete

## Troubleshooting

If deployment fails, check the following:

### Port Binding Issues
- Ensure the application is binding to port 8080 (this is configured in `deployment.py`)
- Make sure no other process is using port 8080

### Database Connection
- Verify the `DATABASE_URL` environment variable is set correctly in Replit Secrets
- Check that the database is accessible from the deployment environment

### Application Errors
- Review the deployment logs for any application-specific errors
- Ensure all dependencies are properly installed

## Production Considerations

When running in production:

1. Debug mode is disabled for security
2. Threaded mode is enabled for better performance
3. The application uses environment variables for configuration
4. Proper signal handling is implemented for graceful shutdowns

## Environment Variables

The following environment variables should be set in Replit Secrets for deployment:

- `DATABASE_URL`: PostgreSQL database connection string
- `SESSION_SECRET`: Secret key for session management
- `ENVIRONMENT`: Set to "production" for production deployments
- `DEBUG`: Set to "false" for production deployments
- `Lotto_scape_ANTHROPIC_KEY`: API key for Anthropic (if OCR functionality is needed)

## Additional Files

- `final_direct_port_solution.py`: Alternative direct port binding solution
- `PORT_BINDING_SOLUTION.md`: Documentation on different port binding approaches