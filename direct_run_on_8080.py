"""
Direct application starter that binds directly to port 8080
This is a simpler approach that doesn't require a port proxy
"""
import os
import logging
from main import app

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the application directly on port 8080
    port = int(os.environ.get('PORT', 8080))
    logging.info(f"Starting application directly on port {port}")
    app.run(host='0.0.0.0', port=port, threaded=True)