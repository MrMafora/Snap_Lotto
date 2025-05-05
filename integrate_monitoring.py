"""
Process Monitoring System Integration

This module integrates the process monitoring system into the application.
It patches key modules and functions to collect performance data and make it
available in the monitoring dashboard.
"""

import os
import sys
import importlib
import logging
import inspect
from functools import wraps
from datetime import datetime

# Setup logger
logger = logging.getLogger('process_monitor_integration')

def integrate_monitoring(app):
    """
    Integrate the process monitoring system into the application
    
    Args:
        app: The Flask application
    """
    logger.info("Integrating process monitoring system into application")
    
    # Import process monitoring modules
    import process_monitor
    import process_monitor_routes
    
    # Register routes
    process_monitor_routes.register_monitor_routes(app)
    
    # Instrument OCR processing
    try:
        import ocr_processor
        import monitor_ocr
        
        # Patch the OCR processor module
        monitor_ocr.instrument_ocr_processor(ocr_processor)
        logger.info("OCR processor successfully instrumented")
    except ImportError:
        logger.warning("Could not instrument OCR processor: module not found")
    except Exception as e:
        logger.error(f"Error instrumenting OCR processor: {str(e)}")
    
    # Instrument ticket scanner
    try:
        import ticket_scanner
        import monitor_ticket_scanner
        
        # Patch the ticket scanner module
        monitor_ticket_scanner.instrument_ticket_scanner(ticket_scanner)
        logger.info("Ticket scanner successfully instrumented")
    except ImportError:
        logger.warning("Could not instrument ticket scanner: module not found")
    except Exception as e:
        logger.error(f"Error instrumenting ticket scanner: {str(e)}")
    
    # Add JavaScript monitoring to templates
    add_monitoring_js(app)
    
    # Add monitoring to scan-ticket endpoint
    patch_scan_ticket_endpoint(app)
    
    # Add monitoring to app startup events
    track_app_startup_events(app)
    
    logger.info("Process monitoring system successfully integrated")
    
    return app

def add_monitoring_js(app):
    """
    Add JavaScript monitoring to templates
    
    Args:
        app: The Flask application
    """
    # Get the original before_request function
    original_before_request = app.before_request_funcs.get(None, [])
    
    def add_monitoring_js_to_response():
        """Add monitoring JS to all HTML responses"""
        # Get the response
        from flask import request, g, current_app
        
        # Skip if this isn't an HTML request
        if request.path.startswith('/static/') or request.path.startswith('/api/'):
            return
            
        # Set up monitoring session ID
        if not hasattr(g, 'monitoring_session_id'):
            import process_monitor as pm
            g.monitoring_session_id = pm.get_new_session_id()
    
    # Add the function to the before_request pipeline
    app.before_request_funcs[None] = [add_monitoring_js_to_response] + original_before_request
    
    # Get the original after_request function
    original_after_request = app.after_request_funcs.get(None, [])
    
    def inject_monitoring_js(response):
        """Inject monitoring JS into HTML responses"""
        # Import Flask's global request context only when needed
        from flask import g, request
        
        if response.content_type and 'text/html' in response.content_type:
            # Make sure we don't inject into JSON or other non-HTML responses
            response_data = response.get_data(as_text=True)
            
            # Check if the response has a </body> tag and monitoring script isn't already included
            if '</body>' in response_data and 'process-monitor.js' not in response_data:
                # Get session ID or use a fallback
                session_id = getattr(g, 'monitoring_session_id', 'unknown') if hasattr(g, 'monitoring_session_id') else 'unknown'
                
                # Create script tag to load the monitoring JS
                monitoring_script = """
                <!-- Process Monitoring -->
                <script src="/static/js/process-monitor.js"></script>
                <script>
                  document.addEventListener('DOMContentLoaded', function() {
                    if (window.ProcessMonitor) {
                      // Initialize with session ID
                      window.ProcessMonitor.init({
                        sessionId: "%s",
                        enabled: true,
                        serverEndpoint: '/api/process-monitor/client-event'
                      });
                      
                      console.log('[ProcessMonitor] Initialized with session ID: %s');
                    }
                  });
                </script>
                """ % (session_id, session_id)
                
                # Inject the script before the closing body tag
                response_data = response_data.replace('</body>', monitoring_script + '</body>')
                response.set_data(response_data)
                
        return response
    
    # Add the function to the after_request pipeline
    app.after_request_funcs[None] = original_after_request + [inject_monitoring_js]
    
    logger.info("JavaScript monitoring added to templates")

def patch_scan_ticket_endpoint(app):
    """
    Add monitoring to the scan-ticket endpoint
    
    Args:
        app: The Flask application
    """
    try:
        # Get all the view functions
        for endpoint, view_func in app.view_functions.items():
            # Find the scan_ticket function
            if endpoint == 'scan_ticket':
                # Store the original function
                original_scan_ticket = view_func
                
                @wraps(original_scan_ticket)
                def monitored_scan_ticket(*args, **kwargs):
                    """Monitored version of scan_ticket endpoint"""
                    import process_monitor as pm
                    from flask import request, g
                    
                    # Set up monitoring session
                    if not hasattr(g, 'monitoring_session_id'):
                        g.monitoring_session_id = pm.get_new_session_id()
                    
                    # Start monitoring
                    with pm.monitor_process('api_endpoints', 'scan_ticket', {
                        'method': request.method,
                        'content_type': request.content_type,
                        'file_keys': list(request.files.keys()) if request.files else [],
                        'form_keys': list(request.form.keys()) if request.form else [],
                        'remote_addr': request.remote_addr,
                        'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'Unknown'
                    }):
                        # Call the original function
                        return original_scan_ticket(*args, **kwargs)
                
                # Replace the original function
                app.view_functions[endpoint] = monitored_scan_ticket
                logger.info("scan_ticket endpoint successfully instrumented")
                break
    except Exception as e:
        logger.error(f"Error patching scan_ticket endpoint: {str(e)}")

def track_app_startup_events(app):
    """
    Track application startup events
    
    Args:
        app: The Flask application
    """
    import process_monitor as pm
    
    # Record application startup
    pm._record_process('application', 'startup', {
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'app_name': app.name,
        'debug_mode': app.debug,
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'config': {k: str(v) for k, v in app.config.items() if not k.startswith('_') and k not in ['SECRET_KEY']}
    })
    
    # Track imports for key modules
    core_modules = ['ticket_scanner', 'ocr_processor', 'data_aggregator', 'models']
    
    for module_name in core_modules:
        try:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                
                # Get information about the module
                functions = [name for name, obj in inspect.getmembers(module) if inspect.isfunction(obj)]
                classes = [name for name, obj in inspect.getmembers(module) if inspect.isclass(obj)]
                
                pm._record_process('imports', module_name, {
                    'timestamp': datetime.now().isoformat(),
                    'function_count': len(functions),
                    'class_count': len(classes),
                    'functions': functions,
                    'classes': classes
                })
                
                logger.info(f"Tracked module import: {module_name}")
        except Exception as e:
            logger.error(f"Error tracking module import for {module_name}: {str(e)}")
    
    logger.info("Application startup events tracked")

if __name__ == "__main__":
    print("This module should be imported, not run directly.")