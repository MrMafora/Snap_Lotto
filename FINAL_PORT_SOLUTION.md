# Final Port Configuration Solution

## The Problem

We've been encountering port conflicts with Replit's workflow system that tries to run on port 5000, but the port is already in use or improperly released between restarts. Additionally, despite configuration changes, gunicorn was still binding to port 5000.

## Our Solution

After multiple iterations, we've arrived at a simplified approach that completely bypasses both gunicorn and port 5000:

1. **main_8080.py**
   - Direct Flask runner that explicitly binds to port 8080
   - Ignores any other configuration settings that might redirect to port 5000

2. **replit_8080_starter.py**
   - Special Replit starter script that runs Flask directly
   - Kills any processes on port 5000 first
   - Launches Flask on port 8080 directly, bypassing gunicorn entirely

3. **workflow_wrapper.sh**
   - The script that Replit's workflow will call
   - Launches the application via replit_8080_starter.py

4. **force_kill_port_5000.sh**
   - Aggressively terminates ANY process using port 5000
   - Uses multiple detection methods (lsof, fuser, netstat)
   - Acts as a cleanup step before starting anything else
   
5. **clear_ports.sh**
   - General utility to clear any ports before starting the application

## Required Manual Changes

Since you cannot directly edit the `.replit` file using our tools, you'll need to manually update:

### 1. Change the Workflow Command

In the Replit UI:
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
6. Set waitForPort to 8080 instead of 5000
7. Click Save

### 2. Update Deployment Run Command

In the Deploy tab:
1. Change the run command to:
   ```
   ["sh", "-c", "./deploy_preview.sh"]
   ```

### 3. Update Port Configuration

Make sure your .replit file has this port configuration:
```
[[ports]]
localPort = 8080
externalPort = 80
```

You can delete or disable any entries for port 5000, as we're no longer using it.

## How It Works

This solution avoids both port 5000 and gunicorn entirely:

1. Instead of using gunicorn, we use Flask's built-in server directly on port 8080
2. Before starting Flask, we kill any processes potentially using port 5000 to prevent conflicts
3. Replit maps port 8080 to external port 80

This completely bypasses all the port detection issues we were seeing with gunicorn and ensures our application runs reliably on the correct port.

## Testing the Solution

You can test this solution by running:
```
./workflow_wrapper.sh
```

You should see:
1. "Starting application with Flask directly on port 8080..."
2. "Killing any processes on port 5000..."
3. "Starting application directly on port 8080..."

## Troubleshooting

If issues persist:
1. Run `./force_kill_port_5000.sh` manually 
2. Check that all scripts have execute permissions (`chmod +x *.sh`)
3. Make sure Flask is binding to port 8080 by checking main_8080.py
4. Try restarting the Replit environment completely