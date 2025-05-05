"""
Process Monitoring System

This module provides functionality to monitor various processes within the application
and collect performance data for analysis and debugging.
"""

import os
import sys
import time
import json
import uuid
import psutil
import logging
import threading
import traceback
from datetime import datetime, timedelta
from contextlib import contextmanager
from functools import wraps

# Set up logger
logger = logging.getLogger('process_monitor')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Store monitoring data in memory (for development and short-term tracking)
# In production, this would be stored in a database or external service
_monitoring_data = {
    'processes': [],
    'events': [],
    'sessions': {}
}

# Import flask if available for request context tracking
try:
    from flask import request, g
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    logger.warning("Flask not available, some monitoring features will be limited")

# Lock for thread-safe operations on shared data
_monitor_lock = threading.Lock()

def get_new_session_id():
    """Generate a unique session ID for tracking related operations"""
    return str(uuid.uuid4())

def get_memory_usage():
    """Get current memory usage of the application"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss,  # Resident Set Size
        'vms': memory_info.vms,  # Virtual Memory Size
        'percent': process.memory_percent(),
        'total_system': psutil.virtual_memory().total
    }

def get_cpu_usage():
    """Get current CPU usage of the application"""
    process = psutil.Process(os.getpid())
    return {
        'percent': process.cpu_percent(interval=0.1),
        'num_threads': process.num_threads(),
        'system_percent': psutil.cpu_percent(interval=0.1)
    }

def get_disk_usage():
    """Get current disk usage"""
    path = os.getcwd()
    disk_usage = psutil.disk_usage(path)
    return {
        'total': disk_usage.total,
        'used': disk_usage.used,
        'free': disk_usage.free,
        'percent': disk_usage.percent
    }

def get_network_usage():
    """Get current network usage"""
    # psutil.net_io_counters() provides cumulative data
    # We store the previous values and calculate the difference
    # for actual usage rate
    net_io = psutil.net_io_counters()
    return {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv,
    }

def get_system_metrics():
    """Get comprehensive system metrics"""
    return {
        'memory': get_memory_usage(),
        'cpu': get_cpu_usage(),
        'disk': get_disk_usage(),
        'network': get_network_usage(),
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - psutil.boot_time()
    }

def _record_process(category, name, data=None):
    """
    Record a process with its metadata
    
    Args:
        category (str): The category of the process (e.g., 'api', 'ocr', 'database')
        name (str): The name of the specific process
        data (dict, optional): Additional data about the process
    """
    # Add timestamp if not provided
    if data is None:
        data = {}
    
    if 'timestamp' not in data:
        data['timestamp'] = datetime.now().isoformat()
    
    # Add request information if available
    if HAS_FLASK:
        try:
            # Import Flask request and g objects for this specific function
            from flask import request, g, has_request_context
            
            # Only access request object if we're in a request context
            if has_request_context():
                data['request'] = {
                    'path': request.path,
                    'method': request.method,
                    'ip': request.remote_addr,
                    'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'Unknown'
                }
                
                # Add session ID if available in the current request context
                if hasattr(g, 'monitoring_session_id'):
                    data['session_id'] = g.monitoring_session_id
        except Exception as e:
            logger.error(f"Error capturing request data: {e}")
    
    # Add system metrics
    try:
        data['system'] = {
            'memory_percent': psutil.Process(os.getpid()).memory_percent(),
            'cpu_percent': psutil.Process(os.getpid()).cpu_percent(interval=0.1)
        }
    except Exception as e:
        logger.error(f"Error capturing system metrics: {e}")
    
    # Create the process record
    process_record = {
        'id': str(uuid.uuid4()),
        'category': category,
        'name': name,
        'data': data,
        'timestamp': data.get('timestamp', datetime.now().isoformat())
    }
    
    # Add to memory store (thread-safe)
    with _monitor_lock:
        _monitoring_data['processes'].append(process_record)
        
        # Limit the number of records to prevent memory issues
        if len(_monitoring_data['processes']) > 1000:
            _monitoring_data['processes'] = _monitoring_data['processes'][-1000:]
    
    return process_record['id']

def _record_event(name, details=None, severity='info'):
    """
    Record an event with its metadata
    
    Args:
        name (str): The name of the event
        details (dict, optional): Additional details about the event
        severity (str): The severity level of the event (info, warning, error, critical)
    """
    if details is None:
        details = {}
    
    # Add timestamp if not provided
    if 'timestamp' not in details:
        details['timestamp'] = datetime.now().isoformat()
    
    # Add session ID if available
    if HAS_FLASK:
        try:
            # Import Flask g object here to avoid issues
            from flask import g, has_request_context
            
            # Only access g if we're in a request context
            if has_request_context() and hasattr(g, 'monitoring_session_id'):
                details['session_id'] = g.monitoring_session_id
        except Exception as e:
            logger.error(f"Error accessing Flask request context: {e}")
    
    # Create the event record
    event_record = {
        'id': str(uuid.uuid4()),
        'name': name,
        'details': details,
        'severity': severity,
        'timestamp': details.get('timestamp', datetime.now().isoformat())
    }
    
    # Add to memory store (thread-safe)
    with _monitor_lock:
        _monitoring_data['events'].append(event_record)
        
        # Limit the number of records to prevent memory issues
        if len(_monitoring_data['events']) > 1000:
            _monitoring_data['events'] = _monitoring_data['events'][-1000:]
    
    return event_record['id']

@contextmanager
def monitor_process(category, name, data=None):
    """
    Monitor a process and record its execution time and other metrics
    
    Args:
        category (str): The category of the process (e.g., 'api', 'ocr', 'database')
        name (str): The name of the specific process
        data (dict, optional): Additional data about the process
    """
    if data is None:
        data = {}
    
    # Record the start time
    start_time = time.time()
    start_timestamp = datetime.now().isoformat()
    
    # Initialize data with start information
    process_data = data.copy()
    process_data['start_time'] = start_timestamp
    
    # Generate a tracking ID for this process
    process_id = _record_process(category, name, process_data)
    
    # Execute the monitored code
    try:
        yield
        # Record successful completion
        end_time = time.time()
        duration = end_time - start_time
        
        # Update the process data with completion information
        with _monitor_lock:
            for i, process in enumerate(_monitoring_data['processes']):
                if process['id'] == process_id:
                    _monitoring_data['processes'][i]['data']['end_time'] = datetime.now().isoformat()
                    _monitoring_data['processes'][i]['data']['duration'] = duration
                    _monitoring_data['processes'][i]['data']['success'] = True
                    _monitoring_data['processes'][i]['data']['system_end'] = {
                        'memory_percent': psutil.Process(os.getpid()).memory_percent(),
                        'cpu_percent': psutil.Process(os.getpid()).cpu_percent(interval=0.1)
                    }
                    break
    except Exception as e:
        # Record failure
        end_time = time.time()
        duration = end_time - start_time
        
        # Update the process data with error information
        with _monitor_lock:
            for i, process in enumerate(_monitoring_data['processes']):
                if process['id'] == process_id:
                    _monitoring_data['processes'][i]['data']['end_time'] = datetime.now().isoformat()
                    _monitoring_data['processes'][i]['data']['duration'] = duration
                    _monitoring_data['processes'][i]['data']['success'] = False
                    _monitoring_data['processes'][i]['data']['error'] = str(e)
                    _monitoring_data['processes'][i]['data']['traceback'] = traceback.format_exc()
                    _monitoring_data['processes'][i]['data']['system_end'] = {
                        'memory_percent': psutil.Process(os.getpid()).memory_percent(),
                        'cpu_percent': psutil.Process(os.getpid()).cpu_percent(interval=0.1)
                    }
                    break
        
        # Re-raise the exception
        raise

def monitored(category, name=None, data=None):
    """
    Decorator to monitor a function's execution
    
    Args:
        category (str): The category of the function (e.g., 'api', 'ocr', 'database')
        name (str, optional): The name of the specific function (defaults to the function name)
        data (dict, optional): Additional data about the function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided name or function name
            func_name = name or func.__name__
            
            # Create a copy of the data dictionary
            func_data = data.copy() if data else {}
            
            # Add argument information (safely)
            try:
                # Only include simple types in args to avoid huge data
                safe_args = []
                for arg in args:
                    if isinstance(arg, (str, int, float, bool, type(None))):
                        safe_args.append(arg)
                    else:
                        safe_args.append(f"<{type(arg).__name__}>")
                
                # Only include simple types in kwargs to avoid huge data
                safe_kwargs = {}
                for key, value in kwargs.items():
                    if isinstance(value, (str, int, float, bool, type(None))):
                        safe_kwargs[key] = value
                    else:
                        safe_kwargs[key] = f"<{type(value).__name__}>"
                
                func_data['args'] = safe_args
                func_data['kwargs'] = safe_kwargs
            except Exception as e:
                logger.error(f"Error capturing function arguments: {e}")
            
            # Monitor the function execution
            with monitor_process(category, func_name, func_data):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def record_client_event(event_type, event_data, session_id=None):
    """
    Record an event from the client-side (JavaScript)
    
    Args:
        event_type (str): The type of event
        event_data (dict): Additional data about the event
        session_id (str, optional): The session ID for tracking related events
    """
    # Create a copy of the event data
    data = event_data.copy() if event_data else {}
    
    # Add timestamp if not provided
    if 'timestamp' not in data:
        data['timestamp'] = datetime.now().isoformat()
    
    # Add session ID if provided or available
    if session_id:
        data['session_id'] = session_id
    elif HAS_FLASK:
        try:
            # Import Flask g object here to avoid issues
            from flask import g, has_request_context
            
            # Only access g if we're in a request context
            if has_request_context() and hasattr(g, 'monitoring_session_id'):
                data['session_id'] = g.monitoring_session_id
        except Exception as e:
            logger.error(f"Error accessing Flask request context in client event: {e}")
    
    # Record the event
    return _record_event(f"client_{event_type}", data)

def get_process_data(filters=None, limit=100, offset=0):
    """
    Get the recorded process data with optional filtering
    
    Args:
        filters (dict, optional): Filters to apply (e.g., {'category': 'api'})
        limit (int, optional): Maximum number of records to return
        offset (int, optional): Offset for pagination
    
    Returns:
        list: Process records
    """
    with _monitor_lock:
        # Get a copy of the processes to avoid thread issues
        processes = _monitoring_data['processes'].copy()
    
    # Apply filters if provided
    if filters:
        filtered_processes = []
        for process in processes:
            match = True
            
            for key, value in filters.items():
                # Handle nested filters with dot notation (e.g., 'data.success')
                if '.' in key:
                    parts = key.split('.')
                    process_value = process
                    for part in parts:
                        if part in process_value:
                            process_value = process_value[part]
                        else:
                            process_value = None
                            break
                else:
                    process_value = process.get(key)
                
                if process_value != value:
                    match = False
                    break
            
            if match:
                filtered_processes.append(process)
        
        processes = filtered_processes
    
    # Sort by timestamp (newest first)
    processes.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Apply pagination
    return processes[offset:offset+limit]

def get_event_data(filters=None, limit=100, offset=0):
    """
    Get the recorded event data with optional filtering
    
    Args:
        filters (dict, optional): Filters to apply (e.g., {'severity': 'error'})
        limit (int, optional): Maximum number of records to return
        offset (int, optional): Offset for pagination
    
    Returns:
        list: Event records
    """
    with _monitor_lock:
        # Get a copy of the events to avoid thread issues
        events = _monitoring_data['events'].copy()
    
    # Apply filters if provided
    if filters:
        filtered_events = []
        for event in events:
            match = True
            
            for key, value in filters.items():
                # Handle nested filters with dot notation (e.g., 'details.session_id')
                if '.' in key:
                    parts = key.split('.')
                    event_value = event
                    for part in parts:
                        if part in event_value:
                            event_value = event_value[part]
                        else:
                            event_value = None
                            break
                else:
                    event_value = event.get(key)
                
                if event_value != value:
                    match = False
                    break
            
            if match:
                filtered_events.append(event)
        
        events = filtered_events
    
    # Sort by timestamp (newest first)
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Apply pagination
    return events[offset:offset+limit]

def get_session_data(session_id):
    """
    Get all data related to a specific session
    
    Args:
        session_id (str): The session ID to retrieve data for
    
    Returns:
        dict: Session data including events and processes
    """
    # Get processes for the session
    processes = get_process_data({'data.session_id': session_id}, limit=1000)
    
    # Get events for the session
    events = get_event_data({'details.session_id': session_id}, limit=1000)
    
    return {
        'session_id': session_id,
        'processes': processes,
        'events': events
    }

def get_performance_stats(category=None, timeframe=None):
    """
    Get performance statistics for processes
    
    Args:
        category (str, optional): Filter by category
        timeframe (timedelta, optional): Time frame to consider
    
    Returns:
        dict: Performance statistics
    """
    with _monitor_lock:
        # Get a copy of the processes to avoid thread issues
        processes = _monitoring_data['processes'].copy()
    
    # Filter by category if provided
    if category:
        processes = [p for p in processes if p['category'] == category]
    
    # Filter by timeframe if provided
    if timeframe:
        cutoff = datetime.now() - timeframe
        cutoff_str = cutoff.isoformat()
        processes = [p for p in processes if p['timestamp'] >= cutoff_str]
    
    # Calculate statistics
    if not processes:
        return {
            'count': 0,
            'avg_duration': 0,
            'min_duration': 0,
            'max_duration': 0,
            'success_rate': 0,
            'total_errors': 0
        }
    
    # Group by name for detailed stats
    grouped_stats = {}
    
    total_duration = 0
    min_duration = float('inf')
    max_duration = 0
    success_count = 0
    error_count = 0
    
    for process in processes:
        duration = process.get('data', {}).get('duration', 0)
        success = process.get('data', {}).get('success', False)
        
        # Skip processes that don't have duration (still running or failed to record)
        if duration == 0:
            continue
        
        # Update global stats
        total_duration += duration
        min_duration = min(min_duration, duration)
        max_duration = max(max_duration, duration)
        
        if success:
            success_count += 1
        else:
            error_count += 1
        
        # Update grouped stats
        name = process['name']
        if name not in grouped_stats:
            grouped_stats[name] = {
                'count': 0,
                'total_duration': 0,
                'min_duration': float('inf'),
                'max_duration': 0,
                'success_count': 0,
                'error_count': 0
            }
        
        grouped_stats[name]['count'] += 1
        grouped_stats[name]['total_duration'] += duration
        grouped_stats[name]['min_duration'] = min(grouped_stats[name]['min_duration'], duration)
        grouped_stats[name]['max_duration'] = max(grouped_stats[name]['max_duration'], duration)
        
        if success:
            grouped_stats[name]['success_count'] += 1
        else:
            grouped_stats[name]['error_count'] += 1
    
    # Calculate averages and rates for grouped stats
    for name, stats in grouped_stats.items():
        stats['avg_duration'] = stats['total_duration'] / stats['count'] if stats['count'] > 0 else 0
        stats['success_rate'] = (stats['success_count'] / stats['count']) * 100 if stats['count'] > 0 else 0
    
    # Finalize the global stats
    completed_count = success_count + error_count
    avg_duration = total_duration / completed_count if completed_count > 0 else 0
    success_rate = (success_count / completed_count) * 100 if completed_count > 0 else 0
    
    # Return the combined stats
    return {
        'count': len(processes),
        'completed_count': completed_count,
        'avg_duration': avg_duration,
        'min_duration': min_duration if min_duration != float('inf') else 0,
        'max_duration': max_duration,
        'success_count': success_count,
        'error_count': error_count,
        'success_rate': success_rate,
        'by_name': grouped_stats
    }

if __name__ == "__main__":
    print("This module should be imported, not run directly.")