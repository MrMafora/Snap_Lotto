# Port Configuration for Replit Deployment

This document provides instructions for properly configuring the port settings in Replit for deployment.

## Current Configuration

The application has been configured with:
- Port 4999 opened immediately (for Replit detection)
- Application running on port 8080 (internal)
- Port 8080 (internal) forwarded to port 80 (external)

Note: We're using port 4999 instead of 5000 to avoid conflicts with Replit's detection system.

## Scripts Created

We've created several scripts to handle the port configuration properly:

1. **start.sh**
   - Starts the application on port 8080
   - Contains port conflict resolution logic

2. **clear_ports.sh**
   - Aggressively clears any processes using ports 4999, 5000, and 8080
   - Ensures ports are available before application start

3. **workflow_starter.py**
   - Opens port 4999 immediately for Replit detection
   - Starts the actual application on port 8080 in parallel
   - Handles threading and process management

4. **workflow_wrapper.sh**
   - Wrapper script for Replit workflows
   - Calls clear_ports.sh and workflow_starter.py

5. **deploy_preview.sh**
   - Script for the deployment command
   - Uses port 8080 directly (no need for port 5000 in deployment)

## Required Manual Changes

Since you cannot directly edit the `.replit` file using our tools, you'll need to manually update:

### 1. Change the Workflow Command

The workflow configuration in `.replit` needs to be updated:

**Current command (line 35):**
```
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

**New command (to be changed manually):**
```
./workflow_wrapper.sh
```

### 2. Update Deployment Run Command

The deployment run command also needs updating:

**Current command (line 8):**
```
["sh", "-c", "gunicorn --bind 0.0.0.0:5000 main:app"]
```

**New command (to be changed manually):**
```
["sh", "-c", "./deploy_preview.sh"]
```

## How to Make These Changes

### For Workflow:
1. Click on the "Tools" button in the sidebar
2. Select "Workflow" 
3. Find the "Start application" workflow
4. Edit the "shell.exec" task command
5. Replace the gunicorn command with `./workflow_wrapper.sh`
6. Click Save

### For Deployment:
1. Go to the "Deploy" tab
2. Update the run command to use `./deploy_preview.sh`

## Verification Process

After making these changes:
1. Restart the workflow
2. You should see "Port 4999 immediately opened for Replit detection" 
3. Followed by "Starting server on port 8080..."
4. Confirm external access works through port 80

## Additional Port Configuration

You'll also need to add this port entry to your .replit file:
```
[[ports]]
localPort = 4999
```

This tells Replit that our application will be opening port 4999.

## Troubleshooting

If you encounter issues:
1. Run `./clear_ports.sh` manually to clear any port conflicts
2. Check logs for specific error messages
3. Verify all script permissions with `chmod +x *.sh`
4. Try restarting the Replit environment completely