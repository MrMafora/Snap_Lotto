"""
Process monitoring specific to the ticket scanner functionality.

This module provides instrumentation for the ticket scanning process to help
diagnose performance issues and delays.
"""

import os
import time
import datetime
import logging
import functools
from flask import request, g

# Import monitoring module
import process_monitor as pm

# Setup logger
logger = logging.getLogger('monitor_ticket_scanner')

def instrument_ticket_scanner(ticket_scanner_module):
    """
    Add instrumentation to the ticket scanner module to monitor its performance.
    
    Args:
        ticket_scanner_module: The ticket_scanner module to instrument
    """
    logger.info("Instrumenting ticket_scanner module")
    
    # Instrument the process_ticket_image function
    original_process_ticket_image = ticket_scanner_module.process_ticket_image
    
    @functools.wraps(original_process_ticket_image)
    def monitored_process_ticket_image(image_data, lottery_type, draw_number=None, file_extension='.jpeg'):
        """Monitored version of process_ticket_image"""
        # Start monitoring
        image_size = len(image_data) if image_data else 0
        
        start_time = time.time()
        start_memory = pm._get_current_resource_usage()
        
        session_id = getattr(g, 'monitoring_session_id', None)
        if not session_id:
            session_id = pm.get_new_session_id()
            g.monitoring_session_id = session_id
            
        process_id = f"ticket_scan:{lottery_type}:{start_time}"
        
        monitoring_data = {
            'id': process_id,
            'session_id': session_id,
            'lottery_type': lottery_type,
            'draw_number': draw_number,
            'file_extension': file_extension,
            'image_size': image_size,
            'start_time': start_time,
            'start_resources': start_memory,
            'client_ip': request.remote_addr if 'request' in globals() else 'Unknown',
            'user_agent': request.user_agent.string if 'request' in globals() and hasattr(request, 'user_agent') else 'Unknown'
        }
        
        # Log the scan start
        logger.info(f"Starting ticket scan: lottery_type={lottery_type}, draw_number={draw_number}, size={image_size} bytes")
        pm._record_process('ticket_scanning', 'process_ticket_image', monitoring_data)
        
        try:
            # Call the original function
            result = original_process_ticket_image(image_data, lottery_type, draw_number, file_extension)
            
            # Measure the end time and resources
            end_time = time.time()
            end_memory = pm._get_current_resource_usage()
            duration = end_time - start_time
            
            # Update monitoring data
            monitoring_data.update({
                'end_time': end_time,
                'duration': duration,
                'end_resources': end_memory,
                'status': 'completed',
                'result_keys': list(result.keys()) if result else [],
                'has_error': 'error' in result if result else False,
                'matched_numbers': result.get('matched_numbers', []) if result else [],
                'has_prize': result.get('has_prize', False) if result else False
            })
            
            # Calculate resource usage delta
            cpu_delta = end_memory['cpu_percent'] - start_memory['cpu_percent']
            memory_delta = end_memory['memory_percent'] - start_memory['memory_percent']
            
            monitoring_data['resource_usage'] = {
                'cpu_delta': cpu_delta,
                'memory_delta': memory_delta
            }
            
            # Log the scan completion
            log_level = logging.INFO
            if duration > 5.0:
                log_level = logging.WARNING
            elif duration > 10.0:
                log_level = logging.ERROR
                
            logger.log(log_level, f"Completed ticket scan in {duration:.2f}s: lottery_type={lottery_type}, success={not monitoring_data['has_error']}")
            
            if monitoring_data['has_error']:
                logger.warning(f"Ticket scan error: {result.get('error', 'Unknown error')}")
                
            # Record final process data
            pm._record_process('ticket_scanning', 'process_ticket_image_complete', monitoring_data)
            
            return result
        except Exception as e:
            # Measure the end time and resources
            end_time = time.time()
            end_memory = pm._get_current_resource_usage()
            duration = end_time - start_time
            
            # Update monitoring data
            monitoring_data.update({
                'end_time': end_time,
                'duration': duration,
                'end_resources': end_memory,
                'status': 'error',
                'error': str(e)
            })
            
            # Log the error
            logger.error(f"Error in ticket scan after {duration:.2f}s: {str(e)}")
            
            # Record error process data
            pm._record_process('ticket_scanning', 'process_ticket_image_error', monitoring_data)
            
            # Re-raise the exception
            raise
    
    # Replace the original function with our monitored version
    ticket_scanner_module.process_ticket_image = monitored_process_ticket_image
    
    # Instrument the extract_ticket_numbers function
    original_extract_ticket_numbers = ticket_scanner_module.extract_ticket_numbers
    
    @functools.wraps(original_extract_ticket_numbers)
    def monitored_extract_ticket_numbers(image_base64, lottery_type, file_extension='.jpeg'):
        """Monitored version of extract_ticket_numbers"""
        # Start monitoring
        start_time = time.time()
        
        session_id = getattr(g, 'monitoring_session_id', None)
        if not session_id:
            session_id = pm.get_new_session_id()
            g.monitoring_session_id = session_id
            
        process_id = f"ocr:{lottery_type}:{start_time}"
        
        monitoring_data = {
            'id': process_id,
            'session_id': session_id,
            'lottery_type': lottery_type,
            'file_extension': file_extension,
            'start_time': start_time
        }
        
        # Log the OCR start
        logger.info(f"Starting OCR extraction: lottery_type={lottery_type}")
        pm._record_process('ticket_scanning', 'extract_ticket_numbers', monitoring_data)
        
        try:
            # Call the original function
            result = original_extract_ticket_numbers(image_base64, lottery_type, file_extension)
            
            # Measure the end time
            end_time = time.time()
            duration = end_time - start_time
            
            # Update monitoring data
            monitoring_data.update({
                'end_time': end_time,
                'duration': duration,
                'status': 'completed',
                'result_keys': list(result.keys()) if result else []
            })
            
            # Log the OCR completion
            log_level = logging.INFO
            if duration > 3.0:
                log_level = logging.WARNING
            elif duration > 7.0:
                log_level = logging.ERROR
                
            logger.log(log_level, f"Completed OCR extraction in {duration:.2f}s")
            
            # Record final process data
            pm._record_process('ticket_scanning', 'extract_ticket_numbers_complete', monitoring_data)
            
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
            logger.error(f"Error in OCR extraction after {duration:.2f}s: {str(e)}")
            
            # Record error process data
            pm._record_process('ticket_scanning', 'extract_ticket_numbers_error', monitoring_data)
            
            # Re-raise the exception
            raise
    
    # Replace the original function with our monitored version
    ticket_scanner_module.extract_ticket_numbers = monitored_extract_ticket_numbers
    
    # Instrument the get_lottery_result function
    original_get_lottery_result = ticket_scanner_module.get_lottery_result
    
    @functools.wraps(original_get_lottery_result)
    def monitored_get_lottery_result(lottery_type, draw_number=None):
        """Monitored version of get_lottery_result"""
        # Start monitoring
        start_time = time.time()
        
        session_id = getattr(g, 'monitoring_session_id', None)
        if not session_id:
            session_id = pm.get_new_session_id()
            g.monitoring_session_id = session_id
            
        process_id = f"get_result:{lottery_type}:{draw_number}:{start_time}"
        
        monitoring_data = {
            'id': process_id,
            'session_id': session_id,
            'lottery_type': lottery_type,
            'draw_number': draw_number,
            'start_time': start_time
        }
        
        # Log the database query start
        logger.info(f"Fetching lottery result: lottery_type={lottery_type}, draw_number={draw_number}")
        pm._record_process('ticket_scanning', 'get_lottery_result', monitoring_data)
        
        try:
            # Call the original function
            result = original_get_lottery_result(lottery_type, draw_number)
            
            # Measure the end time
            end_time = time.time()
            duration = end_time - start_time
            
            # Update monitoring data
            monitoring_data.update({
                'end_time': end_time,
                'duration': duration,
                'status': 'completed',
                'found_result': result is not None,
                'result_draw_number': result.draw_number if result else None,
                'result_draw_date': str(result.draw_date) if result else None
            })
            
            # Log the database query completion
            if result:
                logger.info(f"Found lottery result in {duration:.2f}s: draw_number={result.draw_number}, draw_date={result.draw_date}")
            else:
                logger.warning(f"No lottery result found in {duration:.2f}s: lottery_type={lottery_type}, draw_number={draw_number}")
            
            # Record final process data
            pm._record_process('ticket_scanning', 'get_lottery_result_complete', monitoring_data)
            
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
            logger.error(f"Error fetching lottery result after {duration:.2f}s: {str(e)}")
            
            # Record error process data
            pm._record_process('ticket_scanning', 'get_lottery_result_error', monitoring_data)
            
            # Re-raise the exception
            raise
    
    # Replace the original function with our monitored version
    ticket_scanner_module.get_lottery_result = monitored_get_lottery_result
    
    logger.info("Ticket scanner instrumentation complete")
    
    return ticket_scanner_module