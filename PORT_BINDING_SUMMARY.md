# Port Binding Solution for Lottery Application

## Overview
This document describes the port binding solution implemented for the lottery application. The solution ensures the application works correctly in both development and production environments, specifically addressing the dual-port requirements for Replit deployment.

## Port Requirements
- **Development**: Primary port 5000
- **Production/Replit**: Port 8080 (external access via port 80)

## Solution Architecture
We've implemented multiple approaches to solve the port binding requirements:

### 1. Bridge Approach
The bridge approach uses separate processes:
- Main application runs on port 5000
- A bridge service forwards requests from port 8080 to port 5000

**Components**:
- `bridge.py`: HTTP proxy that forwards requests from port 8080 to port 5000
- `start_combined.sh`: Script that starts both the main app and bridge
- `gunicorn.conf.py`: Configuration that can automatically start the bridge

### 2. Direct Port Binding Approach
This approach eliminates the need for a separate bridge by directly binding to both ports:
- `direct_port_binding.py`: Self-contained solution that can run in various modes
- `start_dual_port.sh`: User-friendly wrapper script with common configurations

**Available Modes**:
- **Single Port Mode**: Run on a single specified port (5000 or 8080)
- **Dual Port Mode**: Run on port 5000 and forward requests from 8080

### 3. Integrated in Main Application
The main application can also handle dual port binding:
- `main.py`: Updated to support direct running on both ports
- Command-line arguments to control port binding behavior

## Startup Scripts

### Bridge-based Solution
```bash
# Start both main application and bridge
./start_combined.sh

# Start only the bridge (if application is already running)
python bridge.py
```

### Direct Port Binding Solution
```bash
# Development mode (port 5000 primary with 8080 bridge)
./start_dual_port.sh --dev

# Production mode (port 8080 only)
./start_dual_port.sh --prod

# Custom port specification
./start_dual_port.sh --single 3000
```

## Health Monitoring
The health monitoring system has been enhanced to check both ports:
- Port status checks for both 5000 and 8080
- Detailed diagnostic information about port availability
- Environment-aware monitoring (different expectations in dev vs prod)

## Port Conflict Resolution
We've included tools to help diagnose and resolve port conflicts:
- `check_port_status.py`: Diagnoses port status and connectivity issues
- `clear_ports.sh`: Utility to clear ports 5000 and 8080 if they're blocked

## Deployment Configuration
The Replit deployment configuration has been updated to properly handle port 8080 directly:

```toml
# Configuration file for Replit Deployments
run = "python production_server.py"
deploymentTarget = "cloudrun"

# Health check endpoint
healthCheckPath = "/health_check"

# Environment configuration
[env]
ENVIRONMENT = "production"
DEBUG = "false"

# Additional deployment settings
[deployment]
ignorePorts = true  # Let production_server.py handle port binding

# Specify the port mapping for Replit
[[ports]]
localPort = 8080
externalPort = 80
```

### Production Server
A specialized `production_server.py` script is used for deployment:
- Binds directly to port 8080 as required by Replit
- Sets environment to production automatically
- Includes automatic port cleanup
- Handles proper process lifecycle and signals
- Uses multiple workers for better performance

## Troubleshooting

### Port 5000 Working, Port 8080 Not Working
This indicates the bridge is not running or has failed to start.
```bash
# Check bridge status
python check_port_status.py

# Restart the bridge
./clear_ports.sh
python bridge.py
```

### Neither Port Working
This indicates the main application has failed to start.
```bash
# Restart everything
./clear_ports.sh
./start_dual_port.sh --dev
```

### Checking Port Status
```bash
# Check port status and connectivity
python check_port_status.py

# Get detailed port information in JSON format
python check_port_status.py --json
```

## Implementation Details

### Bridge Implementation
The bridge uses Python's built-in `http.server` module to create a simple HTTP proxy:
1. Listens on port 8080
2. Forwards all requests to port 5000
3. Copies request headers, body, and method
4. Returns the response from port 5000 to the original client

### Direct Port Binding Implementation
The direct port binding solution uses a more sophisticated approach:
1. Uses `ThreadingMixIn` to handle concurrent requests
2. Creates a subprocess running Gunicorn on port 5000
3. Sets up a proxy server on port 8080
4. Manages the lifecycle of both components

### Health Monitoring Integration
The health monitoring system connects to both ports to verify operation:
1. Tries to connect to port 5000 and port 8080
2. Verifies the health check endpoint responds correctly
3. Logs warnings for any port that fails to respond
4. Provides detailed diagnostic information in the admin dashboard