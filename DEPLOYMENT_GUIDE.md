# Lottery Application Deployment Guide

This guide provides comprehensive instructions for deploying the Lottery Application on Replit, with a focus on proper port binding and environment configuration.

## Deployment Requirements

1. **Port Requirements**:
   - **Development**: Main port is 5000
   - **Production**: Must use port 8080 for Replit deployment (mapped to external port 80)

2. **Environment Variables**:
   - `ENVIRONMENT`: Set to "production" for deployment
   - `DATABASE_URL`: PostgreSQL database connection string (automatically provided by Replit)
   - `Lotto_scape_ANTHROPIC_KEY`: API key for OCR functionality (must be added as a Secret in Replit)

## Deployment Options

We provide multiple deployment approaches to suit different needs:

### 1. Simplified Deployment (Recommended)

The simplest approach using the production-specific server:

```bash
# For Replit deployment
python production_server.py
```

This method:
- Runs directly on port 8080
- Sets the environment to production
- Handles port conflicts automatically
- Designed specifically for Replit's Cloud Run infrastructure

### 2. Direct Port Binding

For more control over the deployment:

```bash
# For Replit deployment (production mode)
./start_dual_port.sh --prod

# For local development
./start_dual_port.sh --dev
```

This method:
- Provides control over environment and ports
- Includes diagnostic capabilities
- Can run in dual-port mode (development) or single-port mode (production)

### 3. Bridge Approach

For advanced deployment scenarios:

```bash
# For running main app + bridge
./start_combined.sh

# For running bridge only (if app is already running)
python bridge.py
```

This method:
- Keeps application logic on port 5000
- Uses a bridge to forward requests from port 8080
- Good for specialized configurations

## Deployment Steps

1. **Prepare for Deployment**:
   ```bash
   # Ensure all dependencies are installed
   pip install -r requirements.txt
   
   # Clear any port conflicts
   ./clear_ports.sh
   ```

2. **Test the Application Locally**:
   ```bash
   # Check port status
   python check_port_status.py
   
   # Run in development mode
   ./start_dual_port.sh --dev
   ```

3. **Deploy on Replit**:
   - Ensure the `replit_deployment.toml` file is configured correctly
   - Click the "Deploy" button in the Replit interface
   - The deployment will automatically use `production_server.py`

4. **Verify Deployment**:
   - The deployment will be available at your Replit subdomain (e.g., https://your-repl-name.replit.app)
   - Use the health check endpoint (https://your-repl-name.replit.app/health_check) to verify the deployment is working

## Troubleshooting

### Port Conflicts

If you experience port conflicts:

```bash
# Check port status and get detailed information
python check_port_status.py

# Clear ports forcefully
./clear_ports.sh
```

### Deployment Issues

1. **Application not starting**:
   - Check logs using the Replit logs panel
   - Verify `production_server.py` is working correctly

2. **Database connection issues**:
   - Ensure the PostgreSQL database is accessible
   - Check DATABASE_URL environment variable

3. **API Integration issues**:
   - Verify all required secrets are set in Replit Secrets panel
   - Check connectivity to external APIs

## Environment Differences

| Feature | Development (port 5000) | Production (port 8080) |
|---------|-------------------------|------------------------|
| Debug mode | Enabled | Disabled |
| Logging | Verbose | Essential only |
| Workers | 1 | 4 |
| Port binding | 5000 (with 8080 bridge) | 8080 directly |
| Session Secret | Development key | Secure production key |

## Maintenance

For routine maintenance:

1. **Database maintenance**:
   - Use admin interface at `/admin` route
   - Run database cleanup tasks periodically

2. **Log maintenance**:
   - Review logs in Replit logs panel
   - Archive logs if needed

3. **Performance monitoring**:
   - Use health monitoring dashboard at `/admin/health-dashboard`
   - Monitor port usage and system resources