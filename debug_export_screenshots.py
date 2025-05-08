"""
Debug script for export_screenshots.

This script will:
1. Import the Flask app
2. Try to access the export_screenshots route
3. Capture any errors that occur
"""
import sys
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_export_screenshots():
    """Debug the export_screenshots route"""
    try:
        from main import app
        from flask_login import LoginManager, UserMixin, login_user
        from models import User
        
        # Create a test client
        client = app.test_client()
        
        # Print app routes
        logger.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.info(f"Route: {rule.endpoint} - {rule.rule}")
        
        # Check if the export-screenshots route exists
        if any(rule.endpoint == 'export_screenshots' for rule in app.url_map.iter_rules()):
            logger.info("export_screenshots route exists")
            
            # Try to find the route URL
            export_screenshots_url = None
            for rule in app.url_map.iter_rules():
                if rule.endpoint == 'export_screenshots':
                    export_screenshots_url = rule.rule
                    break
                    
            logger.info(f"export_screenshots URL: {export_screenshots_url}")
            
            # Get a User object to simulate login
            with app.app_context():
                # Get admin user
                admin_user = User.query.filter_by(username='admin').first()
                if admin_user:
                    logger.info(f"Found admin user: {admin_user.username}")
                    
                    # Try to login properly
                    logger.info("Trying to login...")
                    login_data = {
                        'username': 'admin',
                        'password': 'St0n3@g3',
                        'csrf_token': 'dummy_token'  # This might need a real token
                    }
                    login_response = client.post('/login', data=login_data, follow_redirects=True)
                    logger.info(f"Login response: {login_response.status_code}")
                    
                    # Try to access the route
                    logger.info("Trying to access export_screenshots route after login...")
                    response = client.get(export_screenshots_url)
                    
                    logger.info(f"Response status: {response.status_code}")
                    logger.info(f"Response data: {response.data[:500]}")
                else:
                    logger.error("Admin user not found")
        else:
            logger.error("export_screenshots route does not exist in the application")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        traceback.print_exc()
        
if __name__ == "__main__":
    logger.info("Starting export_screenshots debugging...")
    debug_export_screenshots()
    logger.info("Debugging complete")