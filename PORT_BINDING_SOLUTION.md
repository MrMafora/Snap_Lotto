# Port Binding Solution for Replit

## Overview

This document provides a comprehensive explanation of the port binding solution for the Lottery Data Intelligence Platform when deployed on Replit. The solution addresses the specific requirements of Replit's environment, where external access requires binding to port 8080 while our application's workflow is configured to use port 5000.

## Problem Statement

1. The application is configured to run on port 5000 via Gunicorn in the workflow.
2. Replit requires services to bind to port 8080 for external access.
3. We need a solution that allows both internal access (port 5000) and external access (port 8080).

## Solution Components

### 1. `port_binding_solution.py`

A central, reusable module that provides:

- A standalone HTTP server on port 8080 that redirects to port 5000
- Functions that can be imported by other scripts to ensure port 8080 binding
- Command-line interface for manual control

Usage options:
```bash
# Start the port 8080 redirector pointing to port 5000
python port_binding_solution.py

# Start the port 8080 redirector pointing to a different port
python port_binding_solution.py 3000

# Just check if port 8080 is in use
python port_binding_solution.py --check
```

### 2. `workflow_dual_port_starter.py`

A script specifically designed to be used with the Replit workflow that:

- Starts the port 8080 binding solution in a background thread
- Launches Gunicorn on port 5000 with the correct arguments
- Monitors both services and ensures proper operation

### 3. `absolute_minimal_8080.py`

A minimalist version that:
- Uses only standard library modules
- Provides a simple HTTP server on port 8080 that redirects to port 5000
- Can be used as a fallback if other solutions fail

### 4. `dual_port_app.py`

A comprehensive script that:
- Launches both the port 8080 redirector and the main application
- Monitors both services and restarts if needed
- Logs all output for troubleshooting

## Implementation Details

### Redirect Handler

The core of the solution is a custom HTTP handler that:

1. Receives requests on port 8080
2. Sends a 302 redirect response with the same path but on port 5000
3. Preserves all request parameters and paths

```python
def redirect_request(self):
    """Send a redirect to the same path on port 5000"""
    self.send_response(302)
    host = self.headers.get('Host', '')
    redirect_host = host.replace(':8080', ':5000') if ':8080' in host else host
    self.send_header('Location', f'https://{redirect_host}{self.path}')
    self.end_headers()
```

### Port Checking

Before starting any server, we check if the ports are already in use:

```python
def is_port_in_use(port):
    """Check if the specified port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0
```

## How to Use

### Option 1: Standalone Port 8080 Binding

Run the port binding solution in the background:

```bash
nohup python port_binding_solution.py > port_8080.log 2>&1 &
```

### Option 2: Dual Port Startup

Use the dual port starter script:

```bash
python workflow_dual_port_starter.py
```

### Option 3: Integration with Workflow

Modify the Replit workflow to use the dual port starter.

## Troubleshooting

If the port binding solution fails to start:

1. Check if another process is already using port 8080:
   ```bash
   ps aux | grep 8080
   ```

2. Verify port accessibility:
   ```bash
   curl -v localhost:8080
   ```

3. Check the logs:
   ```bash
   tail -f port_8080.log
   ```

## Conclusion

This port binding solution ensures that the Lottery Data Intelligence Platform is accessible both internally (port 5000) and externally (port 8080) when deployed on Replit, meeting all the platform's requirements while maintaining the existing workflow configuration.