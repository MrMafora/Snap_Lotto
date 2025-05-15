def process_screenshots():
    """
    Process screenshots using thread-safe approach that doesn't use Flask's session object.
    This avoids the "Working outside of request context" error.
    """
    global puppeteer_capture_status
    
    # Create a new app context for this thread
    with app.app_context():
        try:
            # Start the capture process
            start_time = time.time()
            
            # Initialize tracking
            results = {}
            db_updates = 0
            db_creates = 0
            
            # Import our improved puppeteer service with standardization
            from puppeteer_service import capture_single_screenshot, standardize_lottery_type, STANDARDIZED_LOTTERY_URLS
            
            # Process each URL individually to update status as we go
            for i, (original_type, url) in enumerate(config_urls.items()):
                # Standardize the lottery type to reduce duplicates
                lottery_type = standardize_lottery_type(original_type)
                
                # If the standardized type is different, log it
                if original_type != lottery_type:
                    app.logger.info(f"Standardized lottery type from '{original_type}' to '{lottery_type}'")
                
                # Update status - thread-safe, doesn't use session
                puppeteer_capture_status['status_message'] = f"Capturing {lottery_type} screenshot ({i+1}/{len(config_urls)})..."
                puppeteer_capture_status['last_updated'] = datetime.now()
                
                try:
                    # Capture individual screenshot using our improved service
                    app.logger.info(f"Capturing {lottery_type} from {url}")
                    
                    # Use our enhanced puppeteer service that handles standardization
                    capture_result = capture_single_screenshot(lottery_type, url, timeout=120)
                    
                    # Check if the capture was successful
                    if capture_result.get('status') == 'success':
                        filepath = capture_result.get('path')
                        success = True
                    else:
                        success = False
                    
                    # Check if the screenshot was created successfully
                    if success and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        result = {
                            'status': 'success',
                            'path': filepath,
                            'url': url
                        }
                    else:
                        result = {
                            'status': 'failed',
                            'error': f"Failed to capture screenshot",
                            'url': url
                        }
                    
                    results[lottery_type] = result
                    
                    # Update progress - thread-safe, doesn't use session
                    puppeteer_capture_status['completed_screenshots'] = i + 1
                    puppeteer_capture_status['progress'] = (i + 1) / len(config_urls) * 100
                    
                    if result.get('status') == 'success':
                        puppeteer_capture_status['success_count'] += 1
                        
                        # Find or create screenshot record - search by BOTH lottery_type AND url
                        screenshot = Screenshot.query.filter_by(lottery_type=lottery_type, url=url).first()
                        
                        # If not found by both, try to find just by lottery_type for backward compatibility
                        if not screenshot:
                            existing_by_type = Screenshot.query.filter_by(lottery_type=lottery_type).all()
                            if existing_by_type:
                                # Log that we found multiple entries
                                app.logger.warning(f"Found {len(existing_by_type)} existing screenshots for {lottery_type}, using the most recent one")
                                # Sort by timestamp descending and use the most recent one
                                screenshot = sorted(existing_by_type, key=lambda x: x.timestamp, reverse=True)[0]
                        
                        if screenshot:
                            # Update existing record
                            screenshot.path = result.get('path')
                            screenshot.url = url  # Make sure the URL is updated to match the settings
                            screenshot.timestamp = datetime.now()
                            db_updates += 1
                            app.logger.info(f"Updated existing screenshot for {lottery_type} at {url}")
                        else:
                            # Create new record
                            screenshot = Screenshot(
                                lottery_type=lottery_type,
                                path=result.get('path'),
                                url=url,
                                timestamp=datetime.now()
                            )
                            db.session.add(screenshot)
                            db_creates += 1
                            app.logger.info(f"Created new screenshot for {lottery_type} at {url}")
                            
                            # Commit after each successful screenshot
                            db.session.commit()
                    else:
                        puppeteer_capture_status['error_count'] += 1
                        error_msg = result.get('error', 'Unknown error')
                        puppeteer_capture_status['errors'].append(f"{lottery_type}: {error_msg}")
                        app.logger.error(f"Error capturing {lottery_type} screenshot: {error_msg}")
                
                except Exception as e:
                    # Handle individual screenshot errors
                    puppeteer_capture_status['error_count'] += 1
                    puppeteer_capture_status['errors'].append(f"{lottery_type}: {str(e)}")
                    app.logger.error(f"Error capturing {lottery_type} screenshot: {str(e)}")
            
            # All screenshots processed - finalize
            elapsed_time = time.time() - start_time
            app.logger.info(f"Puppeteer screenshot capture completed in {elapsed_time:.2f} seconds")
            
            # Update final status
            success_count = puppeteer_capture_status['success_count']
            error_count = puppeteer_capture_status['error_count']
            
            # Prepare status message - thread-safe, doesn't use session
            if success_count > 0 and error_count == 0:
                status_message = f'Successfully synchronized {success_count} screenshots with Puppeteer. Updated {db_updates} records, created {db_creates} new records.'
                puppeteer_capture_status['status_message'] = status_message
                puppeteer_capture_status['overall_status'] = 'success'
            elif success_count > 0 and error_count > 0:
                status_message = f'Partially synchronized. {success_count} successful, {error_count} failed with Puppeteer. Database: {db_updates} updated, {db_creates} created.'
                puppeteer_capture_status['status_message'] = status_message
                puppeteer_capture_status['overall_status'] = 'warning'
            else:
                status_message = f'Failed to synchronize screenshots with Puppeteer. {error_count} errors encountered.'
                puppeteer_capture_status['status_message'] = status_message
                puppeteer_capture_status['overall_status'] = 'danger'
        
        except Exception as e:
            app.logger.error(f"Error in screenshot processing thread: {str(e)}")
            traceback.print_exc()
            puppeteer_capture_status['status_message'] = f'Error: {str(e)}'
            puppeteer_capture_status['errors'].append(f"General error: {str(e)}")
            puppeteer_capture_status['overall_status'] = 'danger'
        
        finally:
            # Mark process as completed
            puppeteer_capture_status['in_progress'] = False
            puppeteer_capture_status['last_updated'] = datetime.now()
            
            # Clear the missing entries from session at the end of processing
            # This requires app context, but we're already in one
            try:
                # We can't directly access session here, so we use a database-level flag
                # The next time the export_screenshots page is loaded, it will clear the session data
                app.logger.info("Finished processing screenshots, setting flag to clear missing entries")
                with app.test_request_context('/'):
                    if session.get('missing_screenshot_entries'):
                        del session['missing_screenshot_entries']
                        app.logger.info("Cleared missing screenshot entries from session")
            except Exception as sess_err:
                app.logger.error(f"Could not clear session data: {str(sess_err)}")