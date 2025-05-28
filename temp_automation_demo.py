#!/usr/bin/env python3
"""
Temporary automation demo route - bypasses admin requirement for testing
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import logging

logger = logging.getLogger(__name__)

# Create a demo blueprint
demo_bp = Blueprint('demo', __name__)

@demo_bp.route('/demo/automation-control')
def demo_automation_control():
    """Demo automation control center without admin requirement"""
    # Get any status messages from session
    automation_status = session.pop('automation_status', None)
    
    return render_template('admin/automation_control.html',
                         screenshots=[],
                         automation_status=automation_status,
                         test_result=None)

@demo_bp.route('/demo/run-automation-step', methods=['POST'])
def demo_run_automation_step():
    """Demo automation step runner without admin requirement"""
    step = request.form.get('step')
    
    try:
        from daily_automation import DailyLotteryAutomation
        from main import app
        
        automation = DailyLotteryAutomation(app)
        
        if step == 'cleanup':
            success, count = automation.cleanup_old_screenshots()
            message = f"Successfully cleared {count} old screenshots"
            
        elif step == 'capture':
            success, count = automation.capture_fresh_screenshots()
            message = f"Successfully captured {count} fresh screenshots"
            
        elif step == 'ai_process':
            success, count = automation.process_screenshots_with_ai()
            message = f"Successfully processed {count} screenshots with AI"
            
        elif step == 'database_update':
            success, count = automation.update_database_with_results()
            message = f"Successfully updated database with {count} results"
            
        else:
            raise ValueError(f"Unknown automation step: {step}")
        
        session['automation_status'] = {
            'success': success,
            'message': message,
            'details': f"Processed {count} items" if success else "Operation failed"
        }
        flash(f'{message}', 'success' if success else 'danger')
        
    except Exception as e:
        error_msg = f"Failed to run {step}: {str(e)}"
        session['automation_status'] = {
            'success': False,
            'message': error_msg,
            'details': str(e)
        }
        flash(error_msg, 'danger')
        logger.error(f"Demo automation error: {error_msg}")
    
    return redirect(url_for('demo.demo_automation_control'))