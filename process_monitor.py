"""
Process Monitoring System for Snap Lotto Application

This module provides comprehensive process monitoring capabilities to:
1. Track function execution times
2. Monitor resource usage
3. Identify bottlenecks in processing
4. Log and visualize process flows
5. Detect redundant operations

Usage:
- Import this module into any file that needs monitoring
- Use the provided decorators and context managers to monitor performance
- Access the dashboard to visualize monitoring data
"""

import time
import functools
import datetime
import logging
import json
import os
import inspect
import threading
import psutil
import traceback
from collections import defaultdict
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from flask import request, g

# Configure logging
logger = logging.getLogger('process_monitor')
logger.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Create file handler for detailed logs
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'process_monitor.log'))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Store monitoring data
_monitoring_data = {
    'processes': [],
    'function_calls': defaultdict(list),
    'resource_usage': [],
    'user_interactions': [],
    'button_clicks': [],
    'file_uploads': [],
    'page_navigations': [],
    'advertisement_events': [],
    'result_processing': [],
    'duplicate_detections': [],
    'api_calls': [],
    'session_id_counter': 0
}

# Thread local storage for tracking nested calls
_thread_local = threading.local()

# Lock for thread-safe operations
_data_lock = threading.Lock()

def get_new_session_id():
    """Generate a new session ID for tracking related operations"""
    with _data_lock:
        _monitoring_data['session_id_counter'] += 1
        return _monitoring_data['session_id_counter']

def _get_caller_info():
    """Get information about the caller function"""
    stack = inspect.stack()
    # Look for the first frame that isn't in this module
    for frame in stack[1:]:
        if frame.filename != __file__:
            return {
                'file': os.path.basename(frame.filename),
                'function': frame.function,
                'line': frame.lineno
            }
    return {'file': 'unknown', 'function': 'unknown', 'line': 0}

def _record_process(category, name, data):
    """Record a process event with thread safety"""
    with _data_lock:
        timestamp = datetime.datetime.now().isoformat()
        process_data = {
            'timestamp': timestamp,
            'category': category,
            'name': name,
            'data': data
        }
        
        # Add to the appropriate category
        _monitoring_data[category].append(process_data)
        
        # Also add to the general processes list for timeline visualization
        _monitoring_data['processes'].append(process_data)
        
        return process_data

def _get_current_resource_usage():
    """Get current resource usage for the process"""
    process = psutil.Process(os.getpid())
    return {
        'cpu_percent': process.cpu_percent(),
        'memory_percent': process.memory_percent(),
        'memory_info': dict(process.memory_info()._asdict()),
        'num_threads': process.num_threads(),
        'open_files': len(process.open_files()),
        'connections': len(process.connections())
    }

@contextmanager
def monitor_process(category, name, additional_data=None):
    """
    Context manager to monitor a process execution
    
    Args:
        category: Process category for organization
        name: Name of the process being monitored
        additional_data: Any additional data to record
    """
    if not hasattr(_thread_local, 'active_processes'):
        _thread_local.active_processes = []
        _thread_local.current_session_id = get_new_session_id()
    
    process_id = f"{category}:{name}:{time.time()}"
    
    caller_info = _get_caller_info()
    start_time = time.time()
    start_resources = _get_current_resource_usage()
    
    # Record process start
    process_data = {
        'id': process_id,
        'session_id': _thread_local.current_session_id,
        'start_time': start_time,
        'caller': caller_info,
        'start_resources': start_resources,
        'status': 'started',
        'parent_process': _thread_local.active_processes[-1] if _thread_local.active_processes else None,
        'additional_data': additional_data or {}
    }
    
    recorded_data = _record_process(category, name, process_data)
    logger.debug(f"Started process {name} in category {category}")
    
    # Add to active processes stack
    _thread_local.active_processes.append(process_id)
    
    try:
        yield process_id
    except Exception as e:
        # Record exception
        error_data = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        process_data['error'] = error_data
        process_data['status'] = 'error'
        logger.error(f"Error in process {name}: {str(e)}")
        raise
    finally:
        # Always record process completion
        end_time = time.time()
        end_resources = _get_current_resource_usage()
        duration = end_time - start_time
        
        # Remove from active processes
        if _thread_local.active_processes and _thread_local.active_processes[-1] == process_id:
            _thread_local.active_processes.pop()
        
        # Update process data
        process_data.update({
            'end_time': end_time,
            'duration': duration,
            'end_resources': end_resources,
            'status': process_data.get('status', 'completed')
        })
        
        # Calculate resource usage delta
        cpu_delta = end_resources['cpu_percent'] - start_resources['cpu_percent']
        memory_delta = end_resources['memory_percent'] - start_resources['memory_percent']
        
        process_data['resource_usage'] = {
            'cpu_delta': cpu_delta,
            'memory_delta': memory_delta
        }
        
        _record_process(category, name, process_data)
        logger.debug(f"Completed process {name} in {duration:.4f}s")
        
        # Check if this is a long running process
        if duration > 1.0:  # Adjust threshold as needed
            logger.warning(f"Long-running process detected: {name} took {duration:.4f}s")

def monitor_function(category=None):
    """
    Decorator to monitor function execution time and resources
    
    Args:
        category: Category for the function (defaults to the module name)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine category if not provided
            nonlocal category
            if category is None:
                category = func.__module__.split('.')[-1]
            
            func_name = func.__name__
            
            # Capture arguments (excluding self/cls for methods)
            arg_values = {}
            try:
                # Get function signature
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                
                # Filter out self/cls for instance/class methods
                if args and (func.__qualname__.split('.')[0] in str(type(args[0])) or
                           args[0].__class__.__name__ == func.__qualname__.split('.')[0]):
                    arg_values = dict(list(bound_args.arguments.items())[1:])
                else:
                    arg_values = dict(bound_args.arguments)
                
                # Convert non-serializable objects to their string representation
                for k, v in arg_values.items():
                    if not isinstance(v, (int, float, str, bool, list, dict, tuple, type(None))):
                        arg_values[k] = str(v)
            except Exception as e:
                logger.debug(f"Error capturing function arguments: {str(e)}")
                arg_values = {"note": "Could not capture arguments"}
            
            additional_data = {
                'function_name': func_name,
                'arguments': arg_values,
                'is_method': '.' in func.__qualname__
            }
            
            with monitor_process('function_calls', func_name, additional_data):
                return func(*args, **kwargs)
        
        return wrapper
    
    # Handle case when decorator is used without parentheses
    if callable(category):
        func = category
        category = None
        return monitor_function(category)(func)
    
    return decorator

def monitor_user_interaction(interaction_type, details=None):
    """
    Record a user interaction event
    
    Args:
        interaction_type: Type of interaction (click, navigate, etc.)
        details: Additional details about the interaction
    """
    data = {
        'type': interaction_type,
        'details': details or {},
        'timestamp': time.time(),
        'user_agent': getattr(request, 'user_agent', 'Unknown') if 'request' in globals() else 'Unknown',
        'ip_address': getattr(request, 'remote_addr', 'Unknown') if 'request' in globals() else 'Unknown'
    }
    
    if hasattr(g, 'user') and g.user:
        data['user_id'] = g.user.id
    
    _record_process('user_interactions', interaction_type, data)
    logger.info(f"User interaction: {interaction_type}")
    
    if interaction_type == 'button_click':
        _record_process('button_clicks', details.get('button_id', 'unknown'), data)
    elif interaction_type == 'file_upload':
        _record_process('file_uploads', details.get('file_type', 'unknown'), data)
    elif interaction_type == 'page_navigation':
        _record_process('page_navigations', details.get('route', 'unknown'), data)
    
    return data

def monitor_advertisement(ad_type, details=None):
    """
    Record an advertisement-related event
    
    Args:
        ad_type: Type of ad event (load, display, complete, etc.)
        details: Additional details about the ad event
    """
    data = {
        'type': ad_type,
        'details': details or {},
        'timestamp': time.time()
    }
    
    _record_process('advertisement_events', ad_type, data)
    logger.info(f"Advertisement event: {ad_type}")
    return data

def monitor_api_call(endpoint, method, status_code, duration):
    """
    Record an API call
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        duration: Request duration in seconds
    """
    data = {
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'duration': duration,
        'timestamp': time.time()
    }
    
    _record_process('api_calls', endpoint, data)
    
    # Flag slow API calls
    if duration > 1.0:  # Adjust threshold as needed
        logger.warning(f"Slow API call detected: {method} {endpoint} took {duration:.4f}s")
    
    return data

def detect_duplicate_processes(time_window=5.0):
    """
    Detect duplicate process executions within a time window
    
    Args:
        time_window: Time window in seconds to consider for duplicates
    """
    duplicates = []
    
    with _data_lock:
        # Group processes by name and check for duplicates within time window
        process_groups = defaultdict(list)
        
        for process in _monitoring_data['processes']:
            name = process['name']
            timestamp = datetime.datetime.fromisoformat(process['timestamp'])
            process_groups[name].append((timestamp, process))
        
        # Check each group for potential duplicates
        for name, processes in process_groups.items():
            if len(processes) > 1:
                # Sort by timestamp
                processes.sort(key=lambda x: x[0])
                
                # Check consecutive processes for time proximity
                for i in range(len(processes) - 1):
                    time_diff = (processes[i+1][0] - processes[i][0]).total_seconds()
                    if time_diff < time_window:
                        duplicate = {
                            'name': name,
                            'first_occurrence': processes[i][1],
                            'second_occurrence': processes[i+1][1],
                            'time_difference': time_diff
                        }
                        duplicates.append(duplicate)
                        _record_process('duplicate_detections', name, duplicate)
                        logger.warning(f"Possible duplicate process detected: {name} executed twice in {time_diff:.4f}s")
    
    return duplicates

def get_monitoring_data():
    """Get all recorded monitoring data"""
    with _data_lock:
        return dict(_monitoring_data)

def get_process_timeline():
    """Get process execution timeline for visualization"""
    with _data_lock:
        # Sort all processes by timestamp
        timeline = []
        for process in _monitoring_data['processes']:
            # Create a simplified timeline entry
            try:
                data = process['data']
                duration = data.get('duration', 0)
                
                entry = {
                    'category': process['category'],
                    'name': process['name'],
                    'start_time': data.get('start_time', 0),
                    'end_time': data.get('end_time', data.get('start_time', 0) + duration),
                    'duration': duration,
                    'status': data.get('status', 'unknown')
                }
                
                timeline.append(entry)
            except (KeyError, TypeError) as e:
                # Skip incomplete process data
                logger.debug(f"Skipping incomplete process data: {str(e)}")
                continue
        
        # Sort by start time
        timeline.sort(key=lambda x: x['start_time'])
        return timeline

def get_slow_processes(threshold=1.0):
    """
    Get slow processes that exceed the duration threshold
    
    Args:
        threshold: Duration threshold in seconds
    """
    timeline = get_process_timeline()
    return [process for process in timeline if process['duration'] > threshold]

def clear_monitoring_data():
    """Clear all monitoring data"""
    with _data_lock:
        for key in _monitoring_data:
            if key == 'session_id_counter':
                continue
            if isinstance(_monitoring_data[key], list):
                _monitoring_data[key] = []
            elif isinstance(_monitoring_data[key], dict):
                _monitoring_data[key] = {}
            elif isinstance(_monitoring_data[key], defaultdict):
                _monitoring_data[key] = defaultdict(list)

def export_monitoring_data(format='json'):
    """
    Export monitoring data to the specified format
    
    Args:
        format: Export format ('json' or 'html')
    """
    data = get_monitoring_data()
    
    if format == 'json':
        # Convert defaultdict to dict for JSON serialization
        for key, value in data.items():
            if isinstance(value, defaultdict):
                data[key] = dict(value)
        
        return json.dumps(data, indent=2, default=str)
    
    elif format == 'html':
        # Create a simple HTML report
        timeline = get_process_timeline()
        slow_processes = get_slow_processes()
        duplicates = detect_duplicate_processes()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Process Monitoring Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .section { margin-bottom: 30px; }
                .timeline { border: 1px solid #ccc; padding: 10px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                tr:hover { background-color: #f5f5f5; }
                .warning { color: orange; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <h1>Process Monitoring Report</h1>
            
            <div class="section">
                <h2>Slow Processes</h2>
                <table>
                    <tr>
                        <th>Category</th>
                        <th>Name</th>
                        <th>Duration (s)</th>
                        <th>Status</th>
                    </tr>
        """
        
        for process in slow_processes:
            status_class = ''
            if process['status'] == 'error':
                status_class = 'class="error"'
            
            html += f"""
                <tr {status_class}>
                    <td>{process['category']}</td>
                    <td>{process['name']}</td>
                    <td>{process['duration']:.4f}</td>
                    <td>{process['status']}</td>
                </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Duplicate Processes</h2>
                <table>
                    <tr>
                        <th>Name</th>
                        <th>Time Difference (s)</th>
                    </tr>
        """
        
        for duplicate in duplicates:
            html += f"""
                <tr class="warning">
                    <td>{duplicate['name']}</td>
                    <td>{duplicate['time_difference']:.4f}</td>
                </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Process Timeline</h2>
                <div class="timeline">
                    <table>
                        <tr>
                            <th>Category</th>
                            <th>Name</th>
                            <th>Start Time</th>
                            <th>Duration (s)</th>
                            <th>Status</th>
                        </tr>
        """
        
        for process in timeline:
            status_class = ''
            if process['status'] == 'error':
                status_class = 'class="error"'
            elif process['duration'] > 1.0:
                status_class = 'class="warning"'
            
            start_time = datetime.datetime.fromtimestamp(process['start_time']).strftime('%H:%M:%S.%f')[:-3]
            
            html += f"""
                <tr {status_class}>
                    <td>{process['category']}</td>
                    <td>{process['name']}</td>
                    <td>{start_time}</td>
                    <td>{process['duration']:.4f}</td>
                    <td>{process['status']}</td>
                </tr>
            """
        
        html += """
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    else:
        raise ValueError(f"Unsupported export format: {format}")

# JavaScript code for browser-side monitoring
browser_monitoring_js = """
// Process Monitoring System - Browser-side component
window.ProcessMonitor = (function() {
    let monitoringData = {
        interactions: [],
        clicks: [],
        navigations: [],
        fileUploads: [],
        apiCalls: [],
        advertisements: [],
        resourceLoads: [],
        renderingEvents: []
    };
    
    const config = {
        enabled: true,
        trackClicks: true,
        trackNavigation: true,
        trackFileUploads: true,
        trackApiCalls: true,
        trackAdvertisements: true,
        trackResourceLoads: true,
        logToConsole: true,
        serverEndpoint: '/api/process-monitor/client-event'
    };
    
    function getTimestamp() {
        return new Date().toISOString();
    }
    
    function logEvent(category, data) {
        const eventData = {
            ...data,
            timestamp: getTimestamp(),
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        if (monitoringData[category]) {
            monitoringData[category].push(eventData);
        }
        
        if (config.logToConsole) {
            console.log(`[ProcessMonitor] [${category}]`, eventData);
        }
        
        // Send to server if endpoint is configured
        if (config.serverEndpoint) {
            try {
                fetch(config.serverEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        category: category,
                        data: eventData
                    }),
                    // Use keepalive to ensure data is sent even during page unload
                    keepalive: true
                }).catch(err => {
                    console.warn('[ProcessMonitor] Failed to send event to server:', err);
                });
            } catch (e) {
                console.warn('[ProcessMonitor] Error sending event to server:', e);
            }
        }
        
        return eventData;
    }
    
    // Track button clicks
    function trackButtonClick(e) {
        if (!config.trackClicks) return;
        
        const target = e.target.closest('button, a, [role="button"], input[type="submit"], input[type="button"]');
        if (!target) return;
        
        const rect = target.getBoundingClientRect();
        
        const data = {
            elementType: target.tagName.toLowerCase(),
            elementId: target.id || null,
            elementClass: target.className || null,
            elementText: target.innerText || target.value || null,
            location: {
                x: e.clientX,
                y: e.clientY,
                screenX: e.screenX,
                screenY: e.screenY
            },
            elementRect: {
                top: rect.top,
                left: rect.left,
                width: rect.width,
                height: rect.height
            },
            modifiers: {
                ctrl: e.ctrlKey,
                alt: e.altKey,
                shift: e.shiftKey,
                meta: e.metaKey
            }
        };
        
        logEvent('clicks', data);
    }
    
    // Track page navigation
    function trackNavigation() {
        if (!config.trackNavigation) return;
        
        const data = {
            from: document.referrer || null,
            to: window.location.href,
            title: document.title
        };
        
        logEvent('navigations', data);
    }
    
    // Track file uploads
    function trackFileUpload() {
        if (!config.trackFileUploads) return;
        
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', function(e) {
                if (!this.files || !this.files.length) return;
                
                const files = Array.from(this.files).map(file => ({
                    name: file.name,
                    type: file.type,
                    size: file.size,
                    lastModified: new Date(file.lastModified).toISOString()
                }));
                
                const data = {
                    elementId: this.id || null,
                    elementName: this.name || null,
                    files: files
                };
                
                logEvent('fileUploads', data);
            });
        });
    }
    
    // Override XMLHttpRequest to track API calls
    function trackApiCalls() {
        if (!config.trackApiCalls) return;
        
        const originalXHROpen = XMLHttpRequest.prototype.open;
        const originalXHRSend = XMLHttpRequest.prototype.send;
        const originalFetch = window.fetch;
        
        // Override XMLHttpRequest
        XMLHttpRequest.prototype.open = function(method, url) {
            this._monitorData = {
                method: method,
                url: url,
                startTime: Date.now()
            };
            return originalXHROpen.apply(this, arguments);
        };
        
        XMLHttpRequest.prototype.send = function() {
            if (this._monitorData) {
                const xhr = this;
                const originalOnReadyStateChange = xhr.onreadystatechange;
                
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        const endTime = Date.now();
                        const duration = endTime - xhr._monitorData.startTime;
                        
                        const data = {
                            method: xhr._monitorData.method,
                            url: xhr._monitorData.url,
                            status: xhr.status,
                            duration: duration,
                            contentType: xhr.getResponseHeader('Content-Type'),
                            responseSize: xhr.responseText ? xhr.responseText.length : 0
                        };
                        
                        logEvent('apiCalls', data);
                    }
                    
                    if (originalOnReadyStateChange) {
                        originalOnReadyStateChange.apply(this, arguments);
                    }
                };
            }
            
            return originalXHRSend.apply(this, arguments);
        };
        
        // Override fetch
        window.fetch = function() {
            const startTime = Date.now();
            const fetchArgs = arguments;
            
            let method = 'GET';
            let url = arguments[0];
            
            if (typeof url === 'object') {
                url = url.url;
            }
            
            if (arguments[1] && arguments[1].method) {
                method = arguments[1].method;
            }
            
            return originalFetch.apply(this, arguments)
                .then(response => {
                    const endTime = Date.now();
                    const duration = endTime - startTime;
                    
                    const data = {
                        method: method,
                        url: url,
                        status: response.status,
                        duration: duration,
                        contentType: response.headers.get('Content-Type')
                    };
                    
                    logEvent('apiCalls', data);
                    
                    return response;
                })
                .catch(error => {
                    const endTime = Date.now();
                    const duration = endTime - startTime;
                    
                    const data = {
                        method: method,
                        url: url,
                        status: 0,
                        duration: duration,
                        error: error.message
                    };
                    
                    logEvent('apiCalls', data);
                    
                    throw error;
                });
        };
    }
    
    // Track advertisement events
    function trackAdEvents() {
        if (!config.trackAdvertisements) return;
        
        // This needs to be customized based on the ad implementation
        // Example for monitoring the dual-ad-manager.js
        if (window.DualAdManager) {
            const originalShowPublicServiceAd = window.DualAdManager.showPublicServiceAd;
            const originalShowMonetizationAd = window.DualAdManager.showMonetizationAd;
            const originalCompletePublicServiceAd = window.DualAdManager.completePublicServiceAd;
            const originalCompleteMonetizationAd = window.DualAdManager.completeMonetizationAd;
            
            window.DualAdManager.showPublicServiceAd = function() {
                logEvent('advertisements', {
                    action: 'show',
                    adType: 'publicService',
                    startTime: Date.now()
                });
                return originalShowPublicServiceAd.apply(this, arguments);
            };
            
            window.DualAdManager.showMonetizationAd = function() {
                logEvent('advertisements', {
                    action: 'show',
                    adType: 'monetization',
                    startTime: Date.now()
                });
                return originalShowMonetizationAd.apply(this, arguments);
            };
            
            window.DualAdManager.completePublicServiceAd = function() {
                logEvent('advertisements', {
                    action: 'complete',
                    adType: 'publicService',
                    endTime: Date.now()
                });
                return originalCompletePublicServiceAd.apply(this, arguments);
            };
            
            window.DualAdManager.completeMonetizationAd = function() {
                logEvent('advertisements', {
                    action: 'complete',
                    adType: 'monetization',
                    endTime: Date.now()
                });
                return originalCompleteMonetizationAd.apply(this, arguments);
            };
        }
    }
    
    // Track resource loads
    function trackResourceLoads() {
        if (!config.trackResourceLoads) return;
        
        window.addEventListener('load', () => {
            if (window.performance && window.performance.getEntriesByType) {
                const resources = window.performance.getEntriesByType('resource');
                
                resources.forEach(resource => {
                    const data = {
                        name: resource.name,
                        entryType: resource.entryType,
                        startTime: resource.startTime,
                        duration: resource.duration,
                        initiatorType: resource.initiatorType,
                        size: resource.transferSize || 0,
                        timing: {
                            dns: resource.domainLookupEnd - resource.domainLookupStart,
                            tcp: resource.connectEnd - resource.connectStart,
                            request: resource.responseStart - resource.requestStart,
                            response: resource.responseEnd - resource.responseStart
                        }
                    };
                    
                    // Only log resources that took significant time
                    if (resource.duration > 100) {
                        logEvent('resourceLoads', data);
                    }
                });
            }
        });
    }
    
    // Initialize monitoring
    function init(customConfig = {}) {
        // Merge custom config with defaults
        Object.assign(config, customConfig);
        
        if (!config.enabled) return;
        
        // Register event listeners
        if (config.trackClicks) {
            document.addEventListener('click', trackButtonClick, { capture: true });
        }
        
        if (config.trackNavigation) {
            trackNavigation();
            window.addEventListener('popstate', trackNavigation);
        }
        
        if (config.trackFileUploads) {
            trackFileUpload();
        }
        
        if (config.trackApiCalls) {
            trackApiCalls();
        }
        
        if (config.trackAdvertisements) {
            trackAdEvents();
        }
        
        if (config.trackResourceLoads) {
            trackResourceLoads();
        }
        
        console.log('[ProcessMonitor] Initialized with config:', config);
    }
    
    // Public API
    return {
        init: init,
        trackEvent: function(category, data) {
            return logEvent(category, data);
        },
        getMonitoringData: function() {
            return monitoringData;
        },
        clearMonitoringData: function() {
            Object.keys(monitoringData).forEach(key => {
                monitoringData[key] = [];
            });
        }
    };
})();

// Auto-initialize with default config
document.addEventListener('DOMContentLoaded', function() {
    window.ProcessMonitor.init();
});
"""