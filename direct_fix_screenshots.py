"""
Direct fix for the export_screenshots route issue.

This script:
1. Creates a simplified version of the route that works
2. Creates a debug route to help identify issues
"""
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_debug_route():
    """Create debug route for export-screenshots"""
    from main import app, Screenshot, render_template, flash, redirect, url_for
    
    # Create a debug route to check if the issue is with specific code in the function
    @app.route('/debug-export-screenshots')
    def debug_export_screenshots():
        """Debug version of export_screenshots"""
        logger.info("Debug export_screenshots called")
        try:
            # Get all screenshots
            screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).all()
            logger.info(f"Found {len(screenshots)} screenshots")
            
            # Get basic data for first few screenshots
            for i, screenshot in enumerate(screenshots[:5]):
                logger.info(f"Screenshot {i}: {screenshot.lottery_type}, Path: {screenshot.path}")
                
            # Simple response
            return render_template('index.html', 
                                 title="Export Screenshots Debug", 
                                 screenshots=screenshots)
        except Exception as e:
            logger.error(f"Error in debug_export_screenshots: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", 500
    
    # Register the debug route
    logger.info("Debug route registered")
    
    return True

def install_direct_route():
    """Install a direct route for export-screenshots"""
    from main import app, Screenshot, render_template, current_user, session, flash, redirect, url_for
    
    # Simplified export_screenshots route
    @app.route('/direct-export-screenshots')
    def direct_export_screenshots():
        """Direct export screenshots route"""
        logger.info("Direct export_screenshots called")
        try:
            # Check for admin
            if not getattr(current_user, 'is_admin', False):
                flash('You must be an admin to export screenshots.', 'danger')
                return redirect(url_for('index'))
                
            # Get all screenshots
            screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).all()
            logger.info(f"Found {len(screenshots)} screenshots")
            
            # Check for sync status in session
            sync_status = None
            if 'sync_status' in session:
                sync_status = session.pop('sync_status')
            
            # Get the timestamp of the most recent screenshot
            last_updated = None
            if screenshots:
                last_updated = screenshots[0].timestamp
            
            # Render the template
            return render_template('export_screenshots.html',
                                  screenshots=screenshots,
                                  title="Direct Export Lottery Screenshots",
                                  meta_description="Export screenshots for debugging",
                                  breadcrumbs=[
                                      {"name": "Admin Dashboard", "url": url_for('admin')},
                                      {"name": "Export Screenshots", "url": url_for('direct_export_screenshots')}
                                  ],
                                  sync_status=sync_status,
                                  last_updated=last_updated)
        except Exception as e:
            logger.error(f"Error in direct_export_screenshots: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", 500
    
    # Register the direct route
    logger.info("Direct route registered")
    
    return True

def main():
    """Main function"""
    try:
        # Create debug route
        create_debug_route()
        
        # Install direct route
        install_direct_route()
        
        logger.info("Routes installed successfully")
        
        # Print app routes
        from main import app
        logger.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.info(f"Route: {rule.endpoint} - {rule.rule}")
            
        return True
    except Exception as e:
        logger.error(f"Error installing routes: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Starting direct fix...")
    result = main()
    if result:
        logger.info("Direct fix applied successfully")
        print("Direct fix applied successfully")
        print("You can now access:")
        print("1. /debug-export-screenshots - Simple debug version")
        print("2. /direct-export-screenshots - Direct version")
    else:
        logger.error("Failed to apply direct fix")
        print("Failed to apply direct fix")