"""
Process monitoring specific to the OCR functionality.

This module provides instrumentation for the OCR processing to help
diagnose performance issues and delays in the Anthropic API communication.
"""

import logging
import time
from datetime import datetime
from functools import wraps

# Set up logger
logger = logging.getLogger('monitor_ocr')

# Import flask if available for request context tracking
try:
    from flask import g
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    logger.warning("Flask not available, some monitoring features will be limited")

def instrument_ocr_processor(ocr_module):
    """
    Add instrumentation to the OCR processor module to monitor its performance.
    
    Args:
        ocr_module: The ocr_processor module to instrument
    """
    logger.info("Instrumenting OCR processor module")
    
    # Import process_monitor here to avoid circular imports
    import process_monitor
    
    # Store original functions
    original_process_with_anthropic = ocr_module.process_with_anthropic
    original_get_anthropic_client = ocr_module.get_anthropic_client
    
    @wraps(original_process_with_anthropic)
    def monitored_process_with_anthropic(base64_content, lottery_type, system_prompt, image_format='jpeg', screenshot_id=None):
        """Monitored version of process_with_anthropic"""
        start_time = time.time()
        
        # Get request session ID if available
        session_id = None
        if HAS_FLASK and hasattr(g, 'monitoring_session_id'):
            session_id = g.monitoring_session_id
        
        # Create monitoring data
        content_size = len(base64_content) if base64_content else 0
        monitoring_data = {
            'content_size_bytes': content_size,
            'lottery_type': lottery_type,
            'image_format': image_format,
            'screenshot_id': screenshot_id,
            'timestamp': datetime.now().isoformat(),
            'prompt_size': len(system_prompt) if system_prompt else 0
        }
        
        if session_id:
            monitoring_data['session_id'] = session_id
        
        # Monitor the OCR process
        with process_monitor.monitor_process('ocr_processor', 'process_with_anthropic', monitoring_data):
            try:
                # Record event at the start of API call
                process_monitor._record_event('anthropic_api_call_started', {
                    'lottery_type': lottery_type,
                    'screenshot_id': screenshot_id,
                    'timestamp': datetime.now().isoformat(),
                    'session_id': session_id
                })
                
                # Call the original function
                result = original_process_with_anthropic(base64_content, lottery_type, system_prompt, image_format, screenshot_id)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Record success information
                process_monitor._record_event('anthropic_api_call_completed', {
                    'duration': duration,
                    'lottery_type': lottery_type,
                    'screenshot_id': screenshot_id,
                    'success': True,
                    'session_id': session_id,
                    'response_length': len(str(result)) if result else 0
                })
                
                return result
            except Exception as e:
                # Calculate duration
                duration = time.time() - start_time
                
                # Record error information
                process_monitor._record_event('anthropic_api_call_error', {
                    'duration': duration,
                    'lottery_type': lottery_type,
                    'screenshot_id': screenshot_id,
                    'error': str(e),
                    'session_id': session_id
                }, severity='error')
                
                # Re-raise the exception
                raise
    
    @wraps(original_get_anthropic_client)
    def monitored_get_anthropic_client():
        """Monitored version of get_anthropic_client"""
        start_time = time.time()
        
        # Monitor the client creation
        with process_monitor.monitor_process('ocr_processor', 'get_anthropic_client', {
            'timestamp': datetime.now().isoformat()
        }):
            try:
                # Call the original function
                result = original_get_anthropic_client()
                
                # Record success information
                process_monitor._record_event('anthropic_client_created', {
                    'duration': time.time() - start_time,
                    'success': True,
                    'client_type': type(result).__name__ if result else 'None'
                })
                
                return result
            except Exception as e:
                # Record error information
                process_monitor._record_event('anthropic_client_error', {
                    'duration': time.time() - start_time,
                    'error': str(e)
                }, severity='error')
                
                # Re-raise the exception
                raise
    
    # Replace the original functions with the monitored versions
    ocr_module.process_with_anthropic = monitored_process_with_anthropic
    ocr_module.get_anthropic_client = monitored_get_anthropic_client
    
    logger.info("OCR processor instrumentation complete")
    
    return ocr_module

if __name__ == "__main__":
    print("This module should be imported, not run directly.")