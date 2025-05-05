"""
Process monitoring specific to the ticket scanner functionality.

This module provides instrumentation for the ticket scanning process to help
diagnose performance issues and delays.
"""

import os
import logging
import time
from datetime import datetime
from functools import wraps

# Set up logger
logger = logging.getLogger('monitor_ticket_scanner')

# Import flask if available for request context tracking
try:
    from flask import request, g
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    logger.warning("Flask not available, some monitoring features will be limited")

def instrument_ticket_scanner(ticket_scanner_module):
    """
    Add instrumentation to the ticket scanner module to monitor its performance.
    
    Args:
        ticket_scanner_module: The ticket_scanner module to instrument
    """
    # Import process_monitor here to avoid circular imports
    import process_monitor
    
    # Store original functions
    original_process_ticket_image = ticket_scanner_module.process_ticket_image
    original_extract_ticket_numbers = ticket_scanner_module.extract_ticket_numbers
    original_get_lottery_result = ticket_scanner_module.get_lottery_result
    
    @wraps(original_process_ticket_image)
    def monitored_process_ticket_image(image_data, lottery_type, draw_number=None, file_extension='.jpeg'):
        """Monitored version of process_ticket_image"""
        start_time = time.time()
        image_size = len(image_data) if image_data else 0
        
        # Get initial resource usage
        resource_data = {
            'ticket_size_bytes': image_size,
            'lottery_type': lottery_type,
            'draw_number': draw_number,
            'file_extension': file_extension,
            'timestamp': datetime.now().isoformat(),
        }
        
        # Create a session ID for tracking this ticket scan
        session_id = process_monitor.get_new_session_id()
        
        # Set session ID in flask request context if available
        if HAS_FLASK:
            try:
                # Import Flask request context only when needed
                from flask import g, has_request_context
                
                # Only access g if we're in a request context
                if has_request_context():
                    if hasattr(g, 'monitoring_session_id'):
                        # Use existing session ID if available
                        session_id = g.monitoring_session_id
                    else:
                        # Set new session ID if not available
                        g.monitoring_session_id = session_id
            except Exception as e:
                logger.error(f"Error accessing Flask request context: {e}")
        
        resource_data['session_id'] = session_id
        
        # Monitor the process
        with process_monitor.monitor_process('ticket_scanner', 'process_ticket_image', resource_data):
            try:
                result = original_process_ticket_image(image_data, lottery_type, draw_number, file_extension)
                
                # Record success information
                process_monitor._record_event('ticket_scan_completed', {
                    'duration': time.time() - start_time,
                    'lottery_type': lottery_type,
                    'success': True,
                    'session_id': session_id
                })
                
                return result
            except Exception as e:
                # Record error information
                process_monitor._record_event('ticket_scan_error', {
                    'duration': time.time() - start_time,
                    'lottery_type': lottery_type,
                    'error': str(e),
                    'session_id': session_id
                }, severity='error')
                
                # Re-raise the exception
                raise
    
    @wraps(original_extract_ticket_numbers)
    def monitored_extract_ticket_numbers(image_base64, lottery_type, file_extension='.jpeg'):
        """Monitored version of extract_ticket_numbers"""
        start_time = time.time()
        image_size = len(image_base64) if image_base64 else 0
        
        # Get request session ID if available
        session_id = None
        if HAS_FLASK:
            try:
                # Import Flask request context only when needed
                from flask import g, has_request_context
                
                # Only access g if we're in a request context
                if has_request_context() and hasattr(g, 'monitoring_session_id'):
                    session_id = g.monitoring_session_id
            except Exception as e:
                logger.error(f"Error accessing Flask request context: {e}")
        
        resource_data = {
            'ticket_size_bytes': image_size,
            'lottery_type': lottery_type,
            'file_extension': file_extension,
            'timestamp': datetime.now().isoformat(),
        }
        
        if session_id:
            resource_data['session_id'] = session_id
        
        # Monitor the OCR process
        with process_monitor.monitor_process('ticket_scanner', 'extract_ticket_numbers', resource_data):
            try:
                result = original_extract_ticket_numbers(image_base64, lottery_type, file_extension)
                
                # Record success information including the detected numbers
                process_monitor._record_event('ticket_numbers_extracted', {
                    'duration': time.time() - start_time,
                    'lottery_type': lottery_type,
                    'numbers_detected': len(result.get('numbers', [])) if isinstance(result, dict) else 0,
                    'session_id': session_id
                })
                
                return result
            except Exception as e:
                # Record error information
                process_monitor._record_event('ticket_numbers_extraction_error', {
                    'duration': time.time() - start_time,
                    'lottery_type': lottery_type,
                    'error': str(e),
                    'session_id': session_id
                }, severity='error')
                
                # Re-raise the exception
                raise
    
    @wraps(original_get_lottery_result)
    def monitored_get_lottery_result(lottery_type, draw_number=None):
        """Monitored version of get_lottery_result"""
        start_time = time.time()
        
        # Get request session ID if available
        session_id = None
        if HAS_FLASK:
            try:
                # Import Flask request context only when needed
                from flask import g, has_request_context
                
                # Only access g if we're in a request context
                if has_request_context() and hasattr(g, 'monitoring_session_id'):
                    session_id = g.monitoring_session_id
            except Exception as e:
                logger.error(f"Error accessing Flask request context: {e}")
        
        resource_data = {
            'lottery_type': lottery_type,
            'draw_number': draw_number,
            'timestamp': datetime.now().isoformat(),
        }
        
        if session_id:
            resource_data['session_id'] = session_id
        
        # Monitor the database query
        with process_monitor.monitor_process('ticket_scanner', 'get_lottery_result', resource_data):
            try:
                result = original_get_lottery_result(lottery_type, draw_number)
                
                # Record success information
                result_found = result is not None
                process_monitor._record_event('lottery_result_queried', {
                    'duration': time.time() - start_time,
                    'lottery_type': lottery_type,
                    'draw_number': draw_number,
                    'result_found': result_found,
                    'session_id': session_id
                })
                
                return result
            except Exception as e:
                # Record error information
                process_monitor._record_event('lottery_result_query_error', {
                    'duration': time.time() - start_time,
                    'lottery_type': lottery_type,
                    'draw_number': draw_number,
                    'error': str(e),
                    'session_id': session_id
                }, severity='error')
                
                # Re-raise the exception
                raise
    
    # Replace the original functions with the monitored versions
    ticket_scanner_module.process_ticket_image = monitored_process_ticket_image
    ticket_scanner_module.extract_ticket_numbers = monitored_extract_ticket_numbers
    ticket_scanner_module.get_lottery_result = monitored_get_lottery_result
    
    logger.info("Ticket scanner module instrumented with performance monitoring")
    
    return ticket_scanner_module

if __name__ == "__main__":
    print("This module should be imported, not run directly.")