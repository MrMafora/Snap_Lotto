# Port Configuration for Replit Deployment

This document explains the port configuration used in this application for Replit deployments.

## Port Setup

The application uses a dual-port configuration to ensure compatibility with Replit's requirements:

1. **External Port Configuration (Port 4999):**
   - Used to avoid conflicts with Replit's workflow configuration at port 5000
   - Could be mapped to external port (e.g., 80) through Replit configuration
   - First to open during startup to satisfy Replit's 20-second detection requirement

2. **Internal Port Configuration (Port 8080):**
   - Used for the actual application server (gunicorn)
   - Internal routing only, not directly exposed to the internet

## How It Works

The `start_direct.py` script orchestrates this configuration:

1. Immediately opens port 4999 to satisfy Replit's port detection
2. Shows a "loading" screen to users while the main application starts 
3. Starts the actual Flask application with gunicorn on port 8080
4. Proxies requests between port 4999 and port 8080

This approach ensures:
- Fast startup time to meet Replit's requirements
- Proper external access via port 80 (HTTP)
- Clean separation between external access and internal processing

## Startup Scripts

- `start_direct.sh`: Main entry point that launches the dual-port configuration
- `deploy_preview.sh`: Used by Replit for deployment, calls start_direct.sh

## Advanced Port Handling

The system includes robust handling for port conflicts and other issues:

1. **Port Conflict Resolution:**
   - Multiple attempts to bind to port 4999 are made
   - If the port is in use, the system attempts to kill conflicting processes
   - As a last resort, a raw socket is used to ensure port 4999 is opened

2. **Process Cleanup:**
   - Aggressive process termination to free up ports
   - Multiple methods to identify and kill potentially conflicting processes
   - Safety pauses to ensure ports are fully freed before starting new processes

3. **Error Recovery:**
   - Fallback behavior when primary strategy fails
   - Redundant approaches to port availability detection

## Replit Configuration

In an ideal configuration, the `.replit` file would contain port configuration as follows:

```toml
[[ports]]
localPort = 4999
externalPort = 80

[[ports]]
localPort = 8080
```

However, since we cannot directly edit the `.replit` file, our script adapts by using port 4999 to avoid conflicts with port 5000 that might be specified in Replit's configuration.

## Troubleshooting

If you encounter port conflicts during deployment:

1. Use the provided `deploy_preview.sh` script which includes aggressive process cleanup
2. Check for lingering processes with `ps aux | grep -E '(4999|5000|8080)'`
3. Run `./clear_ports.sh` to forcefully terminate all processes using these ports
4. Restart the workflow with `restart_workflow` if needed