# Workflow Configuration Instructions

This document provides instructions for manually updating the Replit workflow configuration to use our optimized port handling system.

## Current Issue

The default Replit workflow tries to run gunicorn directly with:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

This can cause port conflicts and fails to handle the Replit 20-second timeout requirement properly.

## Solution

We've created a workflow wrapper system that:
1. Opens port 5000 immediately (to satisfy Replit's detection)
2. Handles process cleanup to avoid port conflicts
3. Runs the actual application on a different port (8080)
4. Proxies requests between ports

## How to Update Your Workflow

Since you can't directly edit the .replit file using our tools, you'll need to manually update the workflow task in the Replit UI:

1. Click on the "Tools" button in the sidebar
2. Select "Workflow" 
3. Find the "Start application" workflow
4. Edit the "shell.exec" task command
5. Replace:
   ```
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```
   With:
   ```
   ./workflow_wrapper.sh
   ```
6. Save the changes

## Verifying It Works

After making these changes:
1. Restart the workflow using the restart button
2. Check that port 5000 is opened immediately
3. Verify the application is running on port 8080
4. Confirm the proxy is handling requests between the ports

## Troubleshooting

If you encounter issues:
1. Run `./clear_ports.sh` to kill any existing processes
2. Check logs for any specific errors
3. Verify file permissions (`chmod +x` on all the .sh files)
4. Ensure all required scripts are in the correct location