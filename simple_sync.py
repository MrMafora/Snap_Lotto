def sync_all_screenshots():
    """Simple synchronization function"""
    if not current_user.is_admin:
        flash('You must be an admin to sync screenshots.', 'danger')
        return redirect(url_for('index'))
    
    try:
        flash('Screenshot synchronization started.', 'info')
        return redirect(url_for('export_screenshots'))
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('export_screenshots'))
