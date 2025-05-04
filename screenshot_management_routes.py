"""
Screenshot Management Routes for Snap Lotto Admin Interface

This module provides routes for managing screenshots, including:
1. Viewing and managing captured screenshots
2. Capturing individual URLs with the National Lottery specialized capture
3. Configuration of screenshot capture schedule
"""
import os
import logging
import time
import multiprocessing
from math import ceil
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, URL, Optional, NumberRange
from sqlalchemy import desc

from main import admin_required
from models import db, Screenshot, ScheduleConfig

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
screenshot_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

# Simple Pagination class
class Pagination(object):
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self):
        return self.page + 1 if self.has_next else None

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

# Forms
class CaptureSingleForm(FlaskForm):
    """Form for capturing a single URL"""
    url = StringField('URL', validators=[Optional(), URL()])
    url_type = SelectField('URL Type', choices=[
        ('custom', 'Enter Custom URL'),
        ('configured', 'Select from Configured URLs')
    ])
    configured_url = SelectField('Configured URL', choices=[], validators=[Optional()])
    lottery_type = StringField('Lottery Type', validators=[DataRequired()])
    save_to_db = BooleanField('Save to Database', default=True)
    use_requests = BooleanField('Use Requests Method')
    timeout = IntegerField('Timeout (seconds)', validators=[
        NumberRange(min=30, max=900)
    ], default=300)
    submit = SubmitField('Capture URL')

# Routes
@screenshot_blueprint.route('/screenshots')
@login_required
@admin_required
def view_screenshots():
    """View all screenshots"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    lottery_type = request.args.get('lottery_type')
    
    # Base query
    query = Screenshot.query
    
    # Apply filter if lottery type is specified
    if lottery_type:
        query = query.filter(Screenshot.lottery_type == lottery_type)
    
    # Order by timestamp descending (newest first)
    query = query.order_by(desc(Screenshot.timestamp))
    
    # Paginate the results
    total = query.count()
    offset = (page - 1) * per_page
    screenshots = query.offset(offset).limit(per_page).all()
    
    # Create pagination object
    pagination = Pagination(page, per_page, total)
    
    # Get unique lottery types for filter dropdown
    lottery_types = db.session.query(Screenshot.lottery_type).distinct().all()
    lottery_types = [lt[0] for lt in lottery_types]
    
    return render_template('admin/screenshots.html',
                          title="Screenshot Management",
                          screenshots=screenshots,
                          pagination=pagination,
                          lottery_types=lottery_types,
                          selected_type=lottery_type)

@screenshot_blueprint.route('/screenshots/<int:screenshot_id>')
@login_required
@admin_required
def view_screenshot(screenshot_id):
    """View a specific screenshot"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    
    # Get HTML content preview if exists
    html_content = None
    if screenshot.html_path and os.path.exists(screenshot.html_path):
        try:
            with open(screenshot.html_path, 'r', encoding='utf-8') as f:
                html_content = f.read(1000)  # Just get first 1000 chars for preview
        except Exception as e:
            logger.error(f"Error reading HTML content: {str(e)}")
            html_content = f"Error reading HTML content: {str(e)}"
            
    return render_template('admin/screenshot_detail.html',
                          title=f"Screenshot: {screenshot.lottery_type}",
                          screenshot=screenshot,
                          html_content=html_content)

@screenshot_blueprint.route('/screenshot-file/<filename>')
@login_required
@admin_required
def view_screenshot_file(filename):
    """Serve a screenshot file"""
    screenshots_dir = os.path.join(current_app.root_path, 'screenshots')
    return send_from_directory(screenshots_dir, filename)

@screenshot_blueprint.route('/capture-single', methods=['GET', 'POST'])
@login_required
@admin_required
def capture_single():
    """Capture a single URL"""
    form = CaptureSingleForm()
    
    # Get configs for the dropdown
    configs = ScheduleConfig.query.all()
    form.configured_url.choices = [(str(c.id), f"{c.lottery_type} - {c.url}") for c in configs]
    
    result = None
    
    if form.validate_on_submit():
        # Get URL and lottery type based on selection
        url = None
        lottery_type = form.lottery_type.data
        
        if form.url_type.data == 'custom':
            url = form.url.data
        else:
            # Get URL from configured URL
            config_id = int(form.configured_url.data)
            config = ScheduleConfig.query.get(config_id)
            if config:
                url = config.url
                lottery_type = config.lottery_type
        
        if not url:
            flash('Please provide a valid URL', 'danger')
            return render_template('admin/capture_single.html', form=form, configs=configs)
        
        # Capture the URL
        try:
            # Import here to avoid circular imports
            from national_lottery_capture import capture_national_lottery_url
            
            # Set up a timeout using a process pool
            success = False
            html_path = None
            img_path = None
            error = None
            html_content = None
            
            # Use a process pool to handle timeout
            with multiprocessing.Pool(processes=1) as pool:
                try:
                    # Use the specified method if requested
                    method_index = 2 if form.use_requests.data else None
                    
                    # Start the capture with timeout
                    async_result = pool.apply_async(
                        capture_national_lottery_url,
                        (url, lottery_type, form.save_to_db.data, method_index)
                    )
                    
                    # Wait for result with timeout
                    success, html_path, img_path = async_result.get(timeout=form.timeout.data)
                    
                    # If successful, get preview of HTML content
                    if success and html_path:
                        try:
                            with open(html_path, 'r', encoding='utf-8') as f:
                                html_content = f.read(1000)  # Just get first 1000 chars for preview
                        except Exception as e:
                            logger.error(f"Error reading HTML content: {str(e)}")
                            html_content = f"Error reading HTML content: {str(e)}"
                    
                except multiprocessing.TimeoutError:
                    error = f"Capture operation timed out after {form.timeout.data} seconds"
                    pool.terminate()
                except Exception as e:
                    error = f"Error during capture: {str(e)}"
            
            # Prepare result for template
            result = {
                'success': success,
                'html_path': html_path,
                'img_path': img_path,
                'html_content': html_content,
                'error': error
            }
            
            if success:
                flash(f'Successfully captured {lottery_type} from {url}', 'success')
            else:
                flash(f'Failed to capture {lottery_type} from {url}: {error}', 'danger')
                
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            logger.error(f"Error in capture_single: {str(e)}")
    
    return render_template('admin/capture_single.html',
                         form=form,
                         configs=configs,
                         result=result)

@screenshot_blueprint.route('/capture-all')
@login_required
@admin_required
def capture_all():
    """Capture all configured URLs"""
    # Import here to avoid circular imports
    from scheduler import retake_all_screenshots
    
    try:
        from main import app
        with app.app_context():
            success_count = retake_all_screenshots(app=current_app)
        
        if success_count > 0:
            flash(f'Successfully captured {success_count} screenshots', 'success')
        else:
            flash('No screenshots were captured', 'warning')
    except Exception as e:
        flash(f'Error capturing screenshots: {str(e)}', 'danger')
        logger.error(f"Error in capture_all: {str(e)}")
    
    return redirect(url_for('admin.view_screenshots'))

@screenshot_blueprint.route('/delete-screenshot/<int:screenshot_id>', methods=['POST'])
@login_required
@admin_required
def delete_screenshot(screenshot_id):
    """Delete a screenshot"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    
    try:
        # Delete files first if they exist
        if screenshot.html_path and os.path.exists(screenshot.html_path):
            os.remove(screenshot.html_path)
        
        if screenshot.image_path and os.path.exists(screenshot.image_path):
            os.remove(screenshot.image_path)
        
        # Then delete from database
        db.session.delete(screenshot)
        db.session.commit()
        
        flash(f'Screenshot {screenshot_id} deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting screenshot: {str(e)}', 'danger')
        logger.error(f"Error deleting screenshot {screenshot_id}: {str(e)}")
    
    return redirect(url_for('admin.view_screenshots'))

@screenshot_blueprint.route('/retake-screenshot/<int:screenshot_id>')
@login_required
@admin_required
def retake_screenshot(screenshot_id):
    """Retake a specific screenshot"""
    # Import here to avoid circular imports
    from scheduler import retake_screenshot_by_id
    
    try:
        from main import app
        with app.app_context():
            success = retake_screenshot_by_id(screenshot_id, app=current_app)
        
        if success:
            flash(f'Successfully retook screenshot {screenshot_id}', 'success')
        else:
            flash(f'Failed to retake screenshot {screenshot_id}', 'warning')
    except Exception as e:
        flash(f'Error retaking screenshot: {str(e)}', 'danger')
        logger.error(f"Error retaking screenshot {screenshot_id}: {str(e)}")
    
    return redirect(url_for('admin.view_screenshots'))

def register_screenshot_routes(app):
    """Register screenshot management routes with the app"""
    app.register_blueprint(screenshot_blueprint)