# New Workflow Configuration for Replit

Note: This file contains configuration steps that need to be done in the Replit interface.

## Steps to Configure Proper Port Binding

1. Go to the "Workflows" tab in the Replit interface
2. Edit the "Start application" workflow
3. Change the existing command from:
   ```
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```
   
   to:
   ```
   gunicorn --bind 0.0.0.0:8080 --reuse-port --reload main:app
   ```

4. Change the "wait for port" value from 5000 to 8080
5. Save the workflow changes
6. Restart the workflow to apply the changes

## Why This Approach

Unfortunately, we cannot directly modify the `.replit` workflow configuration file through code. We need to make these changes through the Replit interface or through the user updating the configuration manually.

The changes will ensure that Gunicorn binds directly to port 8080 instead of port 5000, which is what Replit expects for web applications.