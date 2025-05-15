def sync_all_screenshots():
    """Synchronize all screenshots from settings entries using Puppeteer"""
    if not current_user.is_admin:
        flash('You must be an admin to sync screenshots.', 'danger')
        return redirect(url_for('index'))
    
    # Check if already in progress
    if puppeteer_capture_status['in_progress']:
        flash('A screenshot capture operation is already in progress.', 'warning')
        return redirect(url_for('export_screenshots'))
    
    try:
        # Get URL configurations from settings
        missing_entries = session.get('missing_screenshot_entries', [])
        schedule_configs = ScheduleConfig.query.filter_by(active=True).all()
        
        # Build URL dictionary
        config_urls = {}
        
        # Add missing entries first
        for entry in missing_entries:
            if entry.get('url') and entry.get('lottery_type'):
                lottery_type = standardize_lottery_type(entry.get('lottery_type'))
                config_urls[lottery_type] = entry.get('url')
                app.logger.info(f"Adding missing entry for {lottery_type}")
        
        # Add scheduled entries
        for config in schedule_configs:
            if config.url:
                lottery_type = standardize_lottery_type(config.lottery_type)
                if lottery_type not in config_urls:
                    config_urls[lottery_type] = config.url
        
        # Use defaults if no other sources
        if not config_urls:
            from puppeteer_service import LOTTERY_URLS
            for key, url in LOTTERY_URLS.items():
                standard_type = standardize_lottery_type(key.replace('_', ' '))
                config_urls[standard_type] = url
        
        # Initialize status
        puppeteer_capture_status.update({
            'in_progress': True,
            'total_screenshots': len(config_urls),
            'completed_screenshots': 0,
            'start_time': datetime.now(),
            'success_count': 0,
            'error_count': 0,
            'status_message': 'Starting screenshot capture...',
            'errors': []
        })
        
        # Start background thread for processing
        threading.Thread(target=lambda: process_screenshots(config_urls), daemon=True).start()
        
        flash('Screenshot synchronization started in the background.', 'info')
        return redirect(url_for('export_screenshots'))
        
    except Exception as e:
        app.logger.error(f"Error initiating screenshot capture: {str(e)}")
        session['sync_status'] = {
            'status': 'danger',
            'message': f'Error initiating screenshot capture: {str(e)}'
        }
        puppeteer_capture_status['in_progress'] = False
        return redirect(url_for('export_screenshots'))

def process_screenshots(config_urls):
    """Process screenshots in a background thread"""
    with app.app_context():
        try:
            start_time = time.time()
            results = {}
            db_updates = 0
            db_creates = 0
            
            # Process each URL
            for i, (original_type, url) in enumerate(config_urls.items()):
                lottery_type = standardize_lottery_type(original_type)
                puppeteer_capture_status['status_message'] = f"Capturing {lottery_type} ({i+1}/{len(config_urls)})..."
                
                try:
                    # Import the function here to avoid circular imports
                    from fixed_process_screenshots import capture_single_screenshot
                    
                    # Capture the screenshot
                    capture_result = capture_single_screenshot(lottery_type, url, timeout=120)
                    
                    # Process result
                    if capture_result.get('status') == 'success':
                        filepath = capture_result.get('path')
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            result = {'status': 'success', 'path': filepath, 'url': url}
                            puppeteer_capture_status['success_count'] += 1
                            
                            # Update database
                            screenshot = Screenshot.query.filter_by(lottery_type=lottery_type, url=url).first()
                            
                            if screenshot:
                                screenshot.path = filepath
                                screenshot.timestamp = datetime.now()
                                db_updates += 1
                            else:
                                screenshot = Screenshot(
                                    lottery_type=lottery_type,
                                    path=filepath,
                                    url=url,
                                    timestamp=datetime.now()
                                )
                                db.session.add(screenshot)
                                db_creates += 1
                            
                            db.session.commit()
                        else:
                            result = {'status': 'failed', 'error': 'Empty screenshot file', 'url': url}
                            puppeteer_capture_status['error_count'] += 1
                    else:
                        result = {'status': 'failed', 'error': capture_result.get('error', 'Unknown error'), 'url': url}
                        puppeteer_capture_status['error_count'] += 1
                    
                    results[lottery_type] = result
                    puppeteer_capture_status['completed_screenshots'] = i + 1
                    
                except Exception as e:
                    app.logger.error(f"Error capturing {lottery_type}: {str(e)}")
                    puppeteer_capture_status['error_count'] += 1
                    puppeteer_capture_status['errors'].append(f"{lottery_type}: {str(e)}")
            
            # Create summary
            elapsed_time = time.time() - start_time
            success_count = puppeteer_capture_status['success_count']
            error_count = puppeteer_capture_status['error_count']
            
            if success_count > 0 and error_count == 0:
                status_message = f'Successfully captured {success_count} screenshots.'
                puppeteer_capture_status['overall_status'] = 'success'
            elif success_count > 0:
                status_message = f'Partially successful: {success_count} succeeded, {error_count} failed.'
                puppeteer_capture_status['overall_status'] = 'warning'
            else:
                status_message = f'Failed to capture any screenshots. {error_count} errors.'
                puppeteer_capture_status['overall_status'] = 'danger'
            
            if db_updates > 0 or db_creates > 0:
                status_message += f' Updated {db_updates} and created {db_creates} database records.'
            
            puppeteer_capture_status['status_message'] = status_message
            
        except Exception as e:
            app.logger.error(f"Processing error: {str(e)}")
            puppeteer_capture_status['status_message'] = f'Error: {str(e)}'
            puppeteer_capture_status['overall_status'] = 'danger'
        
        finally:
            puppeteer_capture_status['in_progress'] = False
            puppeteer_capture_status['last_updated'] = datetime.now()
            
            # Clear missing entries from session
            try:
                if session.get('missing_screenshot_entries'):
                    session.pop('missing_screenshot_entries', None)
                    session.modified = True
            except Exception as sess_err:
                app.logger.error(f"Session error: {str(sess_err)}")