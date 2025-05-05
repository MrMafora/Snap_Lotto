"""
Process monitoring specific to the OCR functionality.

This module provides instrumentation for the OCR processing to help
diagnose performance issues and delays in the Anthropic API communication.
"""

import os
import time
import datetime
import logging
import functools
from flask import g

# Import monitoring module
import process_monitor as pm

# Setup logger
logger = logging.getLogger('monitor_ocr')

def instrument_ocr_processor(ocr_module):
    """
    Add instrumentation to the OCR processor module to monitor its performance.
    
    Args:
        ocr_module: The ocr_processor module to instrument
    """
    logger.info("Instrumenting OCR processor module")
    
    # Instrument the process_with_anthropic function
    original_process_with_anthropic = ocr_module.process_with_anthropic
    
    @functools.wraps(original_process_with_anthropic)
    def monitored_process_with_anthropic(base64_content, lottery_type, system_prompt, image_format='jpeg', screenshot_id=None):
        """Monitored version of process_with_anthropic"""
        # Start monitoring
        start_time = time.time()
        
        session_id = getattr(g, 'monitoring_session_id', None)
        if not session_id:
            session_id = pm.get_new_session_id()
            g.monitoring_session_id = session_id
            
        process_id = f"anthropic_ocr:{lottery_type}:{start_time}"
        
        # Determine content size for logging
        content_size = len(base64_content) if base64_content else 0
        prompt_size = len(system_prompt) if system_prompt else 0
        
        monitoring_data = {
            'id': process_id,
            'session_id': session_id,
            'lottery_type': lottery_type,
            'image_format': image_format,
            'screenshot_id': screenshot_id,
            'start_time': start_time,
            'content_size': content_size,
            'prompt_size': prompt_size
        }
        
        # Log the API request start
        logger.info(f"Starting Anthropic API request: lottery_type={lottery_type}, content_size={content_size}bytes, format={image_format}")
        pm._record_process('ocr_processing', 'process_with_anthropic', monitoring_data)
        
        try:
            # Call the original function
            result = original_process_with_anthropic(base64_content, lottery_type, system_prompt, image_format, screenshot_id)
            
            # Measure the end time
            end_time = time.time()
            duration = end_time - start_time
            
            # Extract useful metrics from the result
            result_keys = []
            raw_response_size = 0
            ocr_model = "unknown"
            ocr_provider = "unknown"
            ocr_timestamp = None
            has_error = False
            
            if result:
                result_keys = list(result.keys())
                raw_response_size = len(result.get('raw_response', ''))
                ocr_model = result.get('ocr_model', 'unknown')
                ocr_provider = result.get('ocr_provider', 'unknown')
                ocr_timestamp = result.get('ocr_timestamp')
                has_error = 'error' in result
            
            # Update monitoring data
            monitoring_data.update({
                'end_time': end_time,
                'duration': duration,
                'status': 'error' if has_error else 'completed',
                'result_keys': result_keys,
                'raw_response_size': raw_response_size,
                'ocr_model': ocr_model,
                'ocr_provider': ocr_provider,
                'ocr_timestamp': ocr_timestamp,
                'has_error': has_error,
                'error_message': result.get('error') if has_error else None
            })
            
            # Log the API request completion
            log_level = logging.INFO
            if duration > 5.0:
                log_level = logging.WARNING
            elif duration > 15.0:
                log_level = logging.ERROR
                
            logger.log(log_level, f"Completed Anthropic API request in {duration:.2f}s: success={not has_error}, response_size={raw_response_size}bytes")
            
            if has_error:
                logger.warning(f"Anthropic API error: {result.get('error', 'Unknown error')}")
                
            # Record final process data
            pm._record_process('ocr_processing', 'process_with_anthropic_complete', monitoring_data)
            
            return result
        except Exception as e:
            # Measure the end time
            end_time = time.time()
            duration = end_time - start_time
            
            # Update monitoring data
            monitoring_data.update({
                'end_time': end_time,
                'duration': duration,
                'status': 'error',
                'error': str(e)
            })
            
            # Log the error
            logger.error(f"Error in Anthropic API request after {duration:.2f}s: {str(e)}")
            
            # Record error process data
            pm._record_process('ocr_processing', 'process_with_anthropic_error', monitoring_data)
            
            # Re-raise the exception
            raise
    
    # Replace the original function with our monitored version
    ocr_module.process_with_anthropic = monitored_process_with_anthropic
    
    # Instrument the get_anthropic_client function
    original_get_anthropic_client = ocr_module.get_anthropic_client
    
    @functools.wraps(original_get_anthropic_client)
    def monitored_get_anthropic_client():
        """Monitored version of get_anthropic_client"""
        # Start monitoring
        start_time = time.time()
        
        session_id = getattr(g, 'monitoring_session_id', None)
        if not session_id:
            session_id = pm.get_new_session_id()
            g.monitoring_session_id = session_id
            
        process_id = f"anthropic_client:{start_time}"
        
        monitoring_data = {
            'id': process_id,
            'session_id': session_id,
            'start_time': start_time
        }
        
        # Log the client initialization
        logger.info("Initializing Anthropic client")
        pm._record_process('ocr_processing', 'get_anthropic_client', monitoring_data)
        
        try:
            # Call the original function
            result = original_get_anthropic_client()
            
            # Measure the end time
            end_time = time.time()
            duration = end_time - start_time
            
            # Update monitoring data
            monitoring_data.update({
                'end_time': end_time,
                'duration': duration,
                'status': 'completed',
                'client_initialized': result is not None
            })
            
            # Log the client initialization result
            if result:
                logger.info(f"Anthropic client initialized successfully in {duration:.2f}s")
            else:
                logger.warning(f"Failed to initialize Anthropic client in {duration:.2f}s")
            
            # Record final process data
            pm._record_process('ocr_processing', 'get_anthropic_client_complete', monitoring_data)
            
            return result
        except Exception as e:
            # Measure the end time
            end_time = time.time()
            duration = end_time - start_time
            
            # Update monitoring data
            monitoring_data.update({
                'end_time': end_time,
                'duration': duration,
                'status': 'error',
                'error': str(e)
            })
            
            # Log the error
            logger.error(f"Error initializing Anthropic client after {duration:.2f}s: {str(e)}")
            
            # Record error process data
            pm._record_process('ocr_processing', 'get_anthropic_client_error', monitoring_data)
            
            # Re-raise the exception
            raise
    
    # Replace the original function with our monitored version
    ocr_module.get_anthropic_client = monitored_get_anthropic_client
    
    logger.info("OCR processor instrumentation complete")
    
    return ocr_module