#!/usr/bin/env python3
"""
Production server startup script for SA Lottery Scanner
Optimized for deployment environments like Replit's Cloud Run
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Start the production server with gunicorn"""
    try:
        # First, try to install gunicorn if it's missing
        try:
            import gunicorn
        except ImportError:
            logger.info("Gunicorn not found, installing...")
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'gunicorn'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise ImportError(f"Failed to install gunicorn: {result.stderr}")

        # Import gunicorn programmatically
        import gunicorn.app.wsgiapp as wsgi

        # Get port from environment (Replit sets this)
        port = os.environ.get('PORT', '8080')

        # Configure gunicorn arguments for production
        sys.argv = [
            'gunicorn',
            'main:app',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '1',
            '--threads', '2', 
            '--timeout', '120',
            '--keep-alive', '5',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--access-logfile', '-',
            '--error-logfile', '-',
            '--log-level', 'info'
        ]

        logger.info(f"Starting production server on port {port}")

        # Start gunicorn
        wsgi.run()

    except ImportError as e:
        logger.error(f"Gunicorn not available: {e}. Starting with basic Flask server...")

        # Fallback to Flask development server
        try:
            from main import app
            port = int(os.environ.get('PORT', '8080'))
            logger.info(f"Starting Flask development server on port {port}")
            app.run(host='0.0.0.0', port=port, debug=False)
        except Exception as e:
            logger.error(f"Failed to start Flask server: {e}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Failed to start production server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()