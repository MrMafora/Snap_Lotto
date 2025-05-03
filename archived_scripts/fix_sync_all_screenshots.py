"""
Fix the sync_all_screenshots function in main.py to ensure all screenshots
get updated with the same timestamp when clicking "Sync All Screenshots"
"""
import sys
import logging
from main import app
from sync_all_timestamps import sync_all_timestamps

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger("fix_sync")

def fix_main_py():
    """
    Apply the fix to main.py to use sync_all_timestamps instead of scheduler.retake_all_screenshots
    """
    logger.info("Fixing main.py to use sync_all_timestamps for 'Sync All Screenshots'")
    
    # Get path to main.py
    main_py_path = "main.py"
    
    # Read the current content
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Find the sync_all_screenshots function
    start_marker = "def sync_all_screenshots():"
    end_marker = "@app.route('/sync-single-screenshot/"
    
    # Check if the function exists
    if start_marker not in content:
        logger.error(f"Could not find '{start_marker}' in {main_py_path}")
        return False
    
    if end_marker not in content:
        logger.error(f"Could not find '{end_marker}' in {main_py_path}")
        return False
    
    # Get the start and end positions
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)
    
    if start_pos < 0 or end_pos < 0 or start_pos >= end_pos:
        logger.error(f"Invalid positions: start={start_pos}, end={end_pos}")
        return False
    
    # Extract the function content
    function_content = content[start_pos:end_pos]
    
    # Create the new function
    new_function = '''def sync_all_screenshots():
    """Sync all screenshots from their source URLs"""
    if not current_user.is_admin:
        flash('You must be an admin to sync screenshots.', 'danger')
        return redirect(url_for('index'))
    
    # For GET requests, just redirect to the export screenshots page
    if request.method == 'GET':
        return redirect(url_for('export_screenshots'))
    
    # For POST requests, perform the sync operation
    try:
        app.logger.info("Starting screenshot sync process")
        
        # Use sync_all_timestamps instead of scheduler.retake_all_screenshots
        # This ensures all screenshots get the same timestamp
        from sync_all_timestamps import sync_all_timestamps
        count = sync_all_timestamps()
        
        app.logger.info(f"Screenshot sync completed with count: {count}")
        
        # Store status in session for display on next page load
        if count > 0:
            session['sync_status'] = {
                'status': 'success',
                'message': f'Successfully synced {count} screenshots.'
            }
        else:
            session['sync_status'] = {
                'status': 'warning',
                'message': 'No screenshots were synced. Check configured URLs.'
            }
    except Exception as e:
        app.logger.error(f"Error syncing screenshots: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        session['sync_status'] = {
            'status': 'danger',
            'message': f'Error syncing screenshots: {str(e)}'
        }
    
    return redirect(url_for('export_screenshots'))

'''
    
    # Replace the old function with the new one
    new_content = content[:start_pos] + new_function + content[end_pos:]
    
    # Write back to main.py
    with open(main_py_path, 'w') as f:
        f.write(new_content)
    
    logger.info(f"Successfully updated {main_py_path}")
    return True

if __name__ == "__main__":
    if fix_main_py():
        print("\nSUCCESS: Updated main.py to ensure all screenshots get updated with the same timestamp")
    else:
        print("\nERROR: Failed to update main.py")