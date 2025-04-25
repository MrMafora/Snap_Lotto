# Port Configuration for Snap Lotto App

## Overview

This document outlines the port configuration setup for the Snap Lotto application to ensure it's accessible via port 8080, which is the default port expected by Replit.

## Problem Statement

Our Flask application with Gunicorn was originally configured to run on port 5000, but Replit expects web applications to be accessible on port 8080. This discrepancy was causing accessibility issues in the Replit environment.

## Solutions Implemented

We've implemented several approaches to address this port configuration issue:

### 1. Direct Gunicorn Configuration

Modified `gunicorn.conf.py` to explicitly bind to port 8080:

```python
# Override bind setting - always use port 8080 for Replit compatibility
bind = "0.0.0.0:8080"

# Make absolutely certain we bind to port 8080
os.environ['PORT'] = '8080'
os.environ['GUNICORN_PORT'] = '8080'
os.environ['REPLIT_PORT'] = '8080'
```

### 2. Port Proxy Service

Created `port_proxy_service.py` to forward requests from port 8080 to port 5000:

```python
#!/usr/bin/env python3
"""
Port Proxy Service for Snap Lotto Application

This script creates a permanent proxy between port 8080 and port 5000
to ensure the application is accessible via Replit's expected port.
"""
```

The proxy service can be started using:

```bash
./run_proxy.sh
```

### 3. Direct Gunicorn Starter

Created `direct_gunicorn_start.py` to explicitly start Gunicorn on port 8080:

```python
#!/usr/bin/env python3
"""
Direct Gunicorn Starter for port 8080 binding
This script directly configures and starts Gunicorn to bind on port 8080
"""
```

This script ensures Gunicorn binds to port 8080 by:
- Setting environment variables
- Explicitly passing the bind argument to Gunicorn
- Managing the process directly

### 4. Health Monitor Updates

Updated `health_monitor.py` to check port 8080 instead of port 5000, ensuring our monitoring correctly aligns with Replit's expected port.

## Recommended Approach

The current recommended approach is using the `direct_gunicorn_start.py` script, which ensures the most reliable port configuration. This approach:

1. Directly binds Gunicorn to port 8080
2. Does not rely on a proxy service (avoiding an extra layer)
3. Uses environment variables to enforce consistent port behavior
4. Handles process management and signal handling properly

## Usage

The application is configured to start using:

```
python3 direct_gunicorn_start.py
```

This command is set in the `.replit-run-command` file to ensure consistent startup behavior.

## Troubleshooting

If the application is not accessible on port 8080:

1. Check running processes: `ps aux | grep gunicorn`
2. Verify the bind address: Look for `--bind 0.0.0.0:8080` in the process
3. Check port usage: `netstat -tulpn | grep 8080`
4. Examine logs: Check `proxy_service.log` (if using the proxy method)