"""
Process Monitoring Routes

This module provides Flask routes for the process monitoring system.
"""

import os
import json
import logging
from datetime import datetime, timedelta

# Set up logger
logger = logging.getLogger('process_monitor_routes')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Import Flask dependencies
from flask import Blueprint, request, jsonify, render_template, current_app, g
from flask_login import login_required, current_user

# Import the process monitor module
import process_monitor

# Create the blueprint
process_monitor_bp = Blueprint('process_monitor', __name__, url_prefix='/monitor')

def register_monitor_routes(app):
    """
    Register the process monitoring routes with the Flask application.
    
    Args:
        app: The Flask application
    """
    # Register the blueprint
    app.register_blueprint(process_monitor_bp)
    
    # Register API routes directly on the app
    app.add_url_rule('/api/process-monitor/client-event', 'process_monitor_client_event', 
                    process_monitor_client_event, methods=['POST'])
    app.add_url_rule('/api/process-monitor/system-metrics', 'process_monitor_system_metrics',
                    process_monitor_system_metrics, methods=['GET'])
    
    logger.info("Process monitoring routes registered")
    
    return app

# Blueprint routes
@process_monitor_bp.route('/')
@login_required
def monitor_dashboard():
    """Process monitoring dashboard"""
    if not current_user.is_admin:
        return current_app.login_manager.unauthorized()
    
    # Get performance stats for the last 24 hours
    stats = process_monitor.get_performance_stats(timeframe=timedelta(hours=24))
    
    # Get the last 50 processes
    processes = process_monitor.get_process_data(limit=50)
    
    # Get the last 50 events
    events = process_monitor.get_event_data(limit=50)
    
    # Get current system metrics
    system_metrics = process_monitor.get_system_metrics()
    
    return render_template('monitor/dashboard.html',
                          stats=stats,
                          processes=processes,
                          events=events,
                          system_metrics=system_metrics,
                          title="Process Monitoring | Admin Dashboard")

@process_monitor_bp.route('/processes')
@login_required
def monitor_processes():
    """View detailed process data"""
    if not current_user.is_admin:
        return current_app.login_manager.unauthorized()
    
    # Get filter parameters
    category = request.args.get('category')
    name = request.args.get('name')
    status = request.args.get('status')  # success, error, running
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    # Build filters
    filters = {}
    if category:
        filters['category'] = category
    if name:
        filters['name'] = name
    if status:
        if status == 'success':
            filters['data.success'] = True
        elif status == 'error':
            filters['data.success'] = False
        # No filter for 'running' as it's more complex
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get the processes
    processes = process_monitor.get_process_data(filters=filters, limit=per_page, offset=offset)
    
    # Handle 'running' status filter post-query
    if status == 'running':
        processes = [p for p in processes if 'end_time' not in p.get('data', {})]
    
    return render_template('monitor/processes.html',
                          processes=processes,
                          category=category,
                          name=name,
                          status=status,
                          page=page,
                          per_page=per_page,
                          title="Process Monitoring | Processes")

@process_monitor_bp.route('/events')
@login_required
def monitor_events():
    """View detailed event data"""
    if not current_user.is_admin:
        return current_app.login_manager.unauthorized()
    
    # Get filter parameters
    name = request.args.get('name')
    severity = request.args.get('severity')
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    # Build filters
    filters = {}
    if name:
        filters['name'] = name
    if severity:
        filters['severity'] = severity
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get the events
    events = process_monitor.get_event_data(filters=filters, limit=per_page, offset=offset)
    
    return render_template('monitor/events.html',
                          events=events,
                          name=name,
                          severity=severity,
                          page=page,
                          per_page=per_page,
                          title="Process Monitoring | Events")

@process_monitor_bp.route('/sessions/<session_id>')
@login_required
def monitor_session(session_id):
    """View detailed session data"""
    if not current_user.is_admin:
        return current_app.login_manager.unauthorized()
    
    # Get the session data
    session_data = process_monitor.get_session_data(session_id)
    
    return render_template('monitor/session.html',
                          session_data=session_data,
                          title="Process Monitoring | Session Details")

@process_monitor_bp.route('/api/processes')
@login_required
def api_processes():
    """API endpoint for process data"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get filter parameters
    category = request.args.get('category')
    name = request.args.get('name')
    status = request.args.get('status')  # success, error, running
    
    # Get pagination parameters
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    # Build filters
    filters = {}
    if category:
        filters['category'] = category
    if name:
        filters['name'] = name
    if status:
        if status == 'success':
            filters['data.success'] = True
        elif status == 'error':
            filters['data.success'] = False
        # No filter for 'running' as it's more complex
    
    # Get the processes
    processes = process_monitor.get_process_data(filters=filters, limit=limit, offset=offset)
    
    # Handle 'running' status filter post-query
    if status == 'running':
        processes = [p for p in processes if 'end_time' not in p.get('data', {})]
    
    return jsonify({'processes': processes})

@process_monitor_bp.route('/api/events')
@login_required
def api_events():
    """API endpoint for event data"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get filter parameters
    name = request.args.get('name')
    severity = request.args.get('severity')
    
    # Get pagination parameters
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    # Build filters
    filters = {}
    if name:
        filters['name'] = name
    if severity:
        filters['severity'] = severity
    
    # Get the events
    events = process_monitor.get_event_data(filters=filters, limit=limit, offset=offset)
    
    return jsonify({'events': events})

@process_monitor_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for performance statistics"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get parameters
    category = request.args.get('category')
    hours = request.args.get('hours')
    
    # Build timeframe
    timeframe = None
    if hours:
        timeframe = timedelta(hours=int(hours))
    
    # Get the stats
    stats = process_monitor.get_performance_stats(category=category, timeframe=timeframe)
    
    return jsonify({'stats': stats})

# Direct app routes (not part of the blueprint)
def process_monitor_client_event():
    """API endpoint to record client-side events"""
    # Get the event data from the request
    try:
        event_data = request.json
        if not event_data:
            return jsonify({'error': 'No event data provided'}), 400
        
        event_type = event_data.get('type')
        if not event_type:
            return jsonify({'error': 'Event type not provided'}), 400
        
        # Get the session ID if provided
        session_id = event_data.get('sessionId')
        
        # Store the event
        event_details = event_data.get('details', {})
        event_id = process_monitor.record_client_event(event_type, event_details, session_id)
        
        return jsonify({'success': True, 'event_id': event_id})
    except Exception as e:
        logger.error(f"Error recording client event: {e}")
        return jsonify({'error': str(e)}), 500

def process_monitor_system_metrics():
    """API endpoint to get system metrics"""
    # Only allow access for admins
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get the metrics
    metrics = process_monitor.get_system_metrics()
    
    return jsonify({'metrics': metrics})