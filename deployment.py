"""
Deployment-specific script for Replit Deployments.
This script ensures the application binds directly to port 8080 
which is required for Replit deployment to succeed.
"""
import os
import sys
import signal
import logging
import subprocess
from werkzeug.serving import run_simple

from main import app

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_on_port_8080():
    """Run the application directly on port 8080 for deployment"""
    try:
        port = int(os.environ.get('PORT', 8080))  # Use PORT from environment if available
        host = "0.0.0.0"  # Bind to all interfaces
        
        logger.info(f"Starting application on {host}:{port} for deployment")
        
        # Custom handling for graceful shutdown
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down gracefully")
            sys.exit(0)
            
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # In production mode
        if os.environ.get('ENVIRONMENT') == 'production':
            # Disable debug mode in production
            app.debug = False
            
            # Use Werkzeug's run_simple for more reliable operation in production
            run_simple(
                hostname=host,
                port=port,
                application=app,
                threaded=True,  # Use threading for better handling of multiple requests
                use_reloader=False,  # Disable reloader in production
                use_debugger=False,  # Disable debugger in production
            )
        else:
            # For local development, use standard Flask run
            app.run(
                host=host, 
                port=port, 
                debug=True,
                threaded=True
            )
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Set environment variable for deployment if not already set
    if not os.environ.get('ENVIRONMENT'):
        os.environ['ENVIRONMENT'] = 'production'
    
    # Run directly on port 8080
    run_on_port_8080()