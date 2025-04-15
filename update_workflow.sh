#!/bin/bash
# Update the workflow configuration for local testing

# Create the workflow directory if it doesn't exist
mkdir -p workflows

cat > workflows/Start_application.toml << 'EOL'
name = "Start application"
entrypoint = "gunicorn -c gunicorn.conf.py main:app"
environment = []
run-as = "replit"
hidden = false
persistent = false
on-boot = false
EOL

echo "Workflow configuration updated to use gunicorn.conf.py"
echo "This will make the application bind to port 8080 during local testing"
echo "Restart the workflow to apply the changes"