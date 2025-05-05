"""
Flask routes for the Process Monitoring System.

This module provides:
1. API endpoints for client-side monitoring
2. Admin dashboard for visualizing monitoring data
3. Reporting functionality for performance analysis
"""

import os
import json
import logging
import datetime
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, Response, abort, send_file
from flask_login import login_required, current_user

# Import monitoring module
import process_monitor as pm

# Setup logger
logger = logging.getLogger('process_monitor_routes')

# Create blueprint
monitor_bp = Blueprint('process_monitor', __name__, url_prefix='/process-monitor')

# Ensure monitor log directory exists
log_dir = os.path.join(os.getcwd(), 'logs', 'monitor')
os.makedirs(log_dir, exist_ok=True)

def admin_required(f):
    """Decorator to require admin access for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@monitor_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Render the process monitoring dashboard"""
    return render_template('monitor/dashboard.html')

@monitor_bp.route('/data')
@login_required
@admin_required
def get_data():
    """API endpoint to get monitoring data"""
    # Get monitoring data
    data = pm.get_monitoring_data()
    
    # Convert to JSON
    return jsonify(data)

@monitor_bp.route('/timeline')
@login_required
@admin_required
def get_timeline():
    """API endpoint to get process timeline"""
    # Get timeline data
    timeline = pm.get_process_timeline()
    
    # Convert to JSON
    return jsonify(timeline)

@monitor_bp.route('/api/process-monitor/client-event', methods=['POST'])
def client_event():
    """API endpoint to receive client-side monitoring events"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    
    # Validate data structure
    if not isinstance(data, dict) or 'data' not in data or not isinstance(data['data'], dict):
        return jsonify({"error": "Invalid data format"}), 400
    
    # Extract session ID
    session_id = data.get('sessionId', 'unknown')
    
    # Log the data to a file
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"client_event_{session_id}_{timestamp}.json"
    log_path = os.path.join(log_dir, log_filename)
    
    try:
        with open(log_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Process the data
        process_client_events(data)
        
        return jsonify({"status": "ok", "message": f"Logged {sum(len(events) for events in data['data'].values())} events"})
    except Exception as e:
        logger.error(f"Error processing client events: {str(e)}")
        return jsonify({"error": f"Error processing events: {str(e)}"}), 500

def process_client_events(data):
    """Process client-side monitoring events"""
    client_data = data.get('data', {})
    session_id = data.get('sessionId', 'unknown')
    
    # Process different types of events
    for category, events in client_data.items():
        for event in events:
            # Add event to our server-side monitoring
            event_data = {
                'client_event': True,
                'session_id': session_id,
                'original_data': event
            }
            
            # Record in the appropriate category
            pm._record_process(category, event.get('type', 'unknown'), event_data)
            
            # Special handling for different event types
            if category == 'advertisements':
                process_ad_event(event, session_id)
            elif category == 'clicks' and (event.get('isViewResultsButton') or event.get('isScanButton')):
                process_critical_button_event(event, session_id)
            elif category == 'apiCalls' and event.get('isTicketScan'):
                process_ticket_scan_api_event(event, session_id)
            elif category == 'fileUploads' and event.get('isTicketUpload'):
                process_ticket_upload_event(event, session_id)

def process_ad_event(event, session_id):
    """Process advertisement-related events"""
    # Log more detailed information about ad events
    function_name = event.get('function', '')
    phase = event.get('phase', '')
    
    if function_name in ['showPublicServiceAd', 'showMonetizationAd'] and phase == 'start':
        logger.info(f"[{session_id}] Starting ad display: {function_name}")
    elif function_name in ['completePublicServiceAd', 'completeMonetizationAd'] and phase == 'complete':
        logger.info(f"[{session_id}] Completed ad display: {function_name}")
    elif phase == 'error':
        logger.error(f"[{session_id}] Error in ad function {function_name}: {event.get('error', 'Unknown')}")

def process_critical_button_event(event, session_id):
    """Process critical button click events"""
    button_type = "View Results" if event.get('isViewResultsButton') else "Scan Ticket"
    logger.info(f"[{session_id}] Critical button clicked: {button_type}")
    
    # Special monitoring for View Results button
    if event.get('isViewResultsButton'):
        pm._record_process('user_interactions', 'view_results_click', {
            'client_session_id': session_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'button_text': event.get('elementText', ''),
            'button_state': {
                'disabled': 'disabled' in (event.get('elementClass', '') or ''),
                'classes': event.get('elementClass', ''),
            }
        })

def process_ticket_scan_api_event(event, session_id):
    """Process ticket scan API events"""
    phase = event.get('phase', '')
    duration = event.get('duration', 0)
    
    if phase == 'start':
        logger.info(f"[{session_id}] Starting ticket scan request")
    elif phase == 'complete':
        log_level = logging.INFO if duration < 5000 else logging.WARNING
        logger.log(log_level, f"[{session_id}] Completed ticket scan in {duration}ms with status {event.get('status', 'unknown')}")
    elif phase == 'error':
        logger.error(f"[{session_id}] Error in ticket scan: {event.get('error', 'Unknown')}")

def process_ticket_upload_event(event, session_id):
    """Process ticket upload events"""
    files = event.get('files', [])
    file_count = len(files)
    file_types = [f.get('type', 'unknown') for f in files]
    file_sizes = [f.get('size', 0) for f in files]
    
    logger.info(f"[{session_id}] Ticket upload detected: {file_count} files, types: {file_types}, sizes: {file_sizes}")

@monitor_bp.route('/report')
@login_required
@admin_required
def report():
    """Generate and display a report of monitoring data"""
    # Export as HTML
    html_report = pm.export_monitoring_data(format='html')
    
    # Return as HTML response
    return Response(html_report, mimetype='text/html')

@monitor_bp.route('/report/download')
@login_required
@admin_required
def download_report():
    """Download a report of monitoring data"""
    format = request.args.get('format', 'json')
    
    if format == 'json':
        # Export as JSON
        json_data = pm.export_monitoring_data(format='json')
        
        # Write to a temporary file
        filename = f"process_monitor_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(log_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(json_data)
        
        # Send the file
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    elif format == 'html':
        # Export as HTML
        html_data = pm.export_monitoring_data(format='html')
        
        # Write to a temporary file
        filename = f"process_monitor_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(log_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(html_data)
        
        # Send the file
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    else:
        return jsonify({"error": f"Unsupported format: {format}"}), 400

@monitor_bp.route('/clear', methods=['POST'])
@login_required
@admin_required
def clear_data():
    """Clear all monitoring data"""
    pm.clear_monitoring_data()
    return jsonify({"status": "ok", "message": "Monitoring data cleared"})

def register_monitor_routes(app):
    """Register the monitoring blueprint with the application"""
    app.register_blueprint(monitor_bp)
    logger.info("Process monitoring routes registered")
    
    # Patch Flask before_request and after_request for global monitoring
    original_before_request = app.before_request_funcs.get(None, [])
    original_after_request = app.after_request_funcs.get(None, [])
    
    def monitor_before_request():
        # Start timing the request
        request._start_time = datetime.datetime.now()
        
        # Log the request
        pm.monitor_process('api_calls', request.path, {
            'method': request.method,
            'path': request.path,
            'query_params': request.args.to_dict(),
            'remote_addr': request.remote_addr,
            'start_time': request._start_time.isoformat()
        })
    
    def monitor_after_request(response):
        # End timing the request
        end_time = datetime.datetime.now()
        
        # Calculate duration
        if hasattr(request, '_start_time'):
            duration_ms = (end_time - request._start_time).total_seconds() * 1000
            
            # Log the response
            pm.monitor_process('api_calls', request.path, {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'content_type': response.content_type,
                'content_length': response.content_length,
                'duration_ms': duration_ms,
                'end_time': end_time.isoformat()
            })
            
            # Log slow requests
            if duration_ms > 1000:  # More than 1 second
                logger.warning(f"Slow request: {request.method} {request.path} - {duration_ms:.2f}ms")
        
        return response
    
    # Register our monitoring functions
    app.before_request_funcs[None] = [monitor_before_request] + original_before_request
    app.after_request_funcs[None] = [monitor_after_request] + original_after_request
    
    logger.info("Request monitoring hooks installed")
    
    return app