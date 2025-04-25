# Port Configuration and Web Server Access Documentation

## Port Conflict Issue
The Snap Lotto application was configured to run on port 5000, but Replit expects applications to be accessible via port 8080. This created an accessibility issue for the web interface.

## Current Configuration
- Gunicorn is configured to bind to port 5000 (internal server configuration)
- Replit expects applications to be accessible on port 8080
- The workflow is configured in `.replit` to run Gunicorn on port 5000

## Access Solution
1. **Port Proxy**: Created a port proxy script (`port_proxy.py`) that:
   - Listens on port 8080
   - Forwards all requests to the application running on port 5000
   - Handles all HTTP methods (GET, POST, PUT, DELETE, etc.)
   - Preserves headers and response data

2. **Run Script**: Created a startup script (`run_proxy.sh`) to:
   - Start the proxy in the background
   - Log proxy activity to `proxy_log.txt`

3. **Application Port Configuration**:
   - Added explicit port configuration to `gunicorn.conf.py`
   - Set environment variables to ensure consistent port usage:
     ```
     os.environ['PORT'] = '8080'
     os.environ['REPLIT_PORT'] = '8080'
     ```

## Usage Instructions
1. Start the main application using the workflow "Start application"
2. Run the proxy script to enable external access:
   ```
   ./run_proxy.sh
   ```
3. The application will now be accessible through port 8080

## Future Improvements
For long-term solution, the better approach would be:
1. Modify the workflow configuration in `.replit` to use port 8080 directly
2. Update all internal references from port 5000 to 8080
3. Remove the proxy script once the direct port binding is working correctly

## Port Mapping
- 5000: Internal application server (Gunicorn)
- 8080: External access port (via proxy)