"""
Application configuration and setup.
"""
import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, Screenshot, LotteryResult, ScheduleConfig
from data_aggregator import aggregate_data, validate_and_correct_known_draws

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "lottery-scraper-default-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///lottery_data.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the database
db.init_app(app)

# Create all database tables
with app.app_context():
    db.create_all()

# Import components after database is initialized
from scheduler import init_scheduler, schedule_task, remove_task
from screenshot_manager import capture_screenshot
from data_aggregator import aggregate_data, validate_and_correct_known_draws

# Initialize scheduler
scheduler = init_scheduler(app)

# Schedule any active tasks
with app.app_context():
    # Set up initial schedules if none exist
    if ScheduleConfig.query.count() == 0:
        default_urls = [
            {'url': 'https://www.nationallottery.co.za/lotto-history', 'lottery_type': 'Lotto'},
            {'url': 'https://www.nationallottery.co.za/lotto-plus-1-history', 'lottery_type': 'Lotto Plus 1'},
            {'url': 'https://www.nationallottery.co.za/lotto-plus-2-history', 'lottery_type': 'Lotto Plus 2'},
            {'url': 'https://www.nationallottery.co.za/powerball-history', 'lottery_type': 'Powerball'},
            {'url': 'https://www.nationallottery.co.za/powerball-plus-history', 'lottery_type': 'Powerball Plus'},
            {'url': 'https://www.nationallottery.co.za/daily-lotto-history', 'lottery_type': 'Daily Lotto'}
        ]
        
        for i, config in enumerate(default_urls):
            # Stagger the scheduled times to avoid overwhelming the system
            hour = 1  # Run at 1 AM
            minute = i * 10  # 10 minutes apart
            
            schedule = ScheduleConfig(
                url=config['url'],
                lottery_type=config['lottery_type'],
                frequency='daily',
                hour=hour,
                minute=minute,
                active=True
            )
            db.session.add(schedule)
        
        db.session.commit()
        logger.info("Added default lottery schedule configurations")
    
    # Schedule active tasks
    for config in ScheduleConfig.query.filter_by(active=True).all():
        schedule_task(scheduler, config)

# Routes
# Export route functions for use by main.py
@app.route('/')
def index():
    """Home page showing scheduled tasks and latest results"""
    schedules = ScheduleConfig.query.all()
    latest_results = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).limit(10).all()
    return render_template('index.html', schedules=schedules, results=latest_results)

@app.route('/results')
def results():
    """Page showing all lottery results"""
    # Run validation to ensure known correct data is used
    try:
        corrected = validate_and_correct_known_draws()
        if corrected > 0:
            logger.info(f"Corrected {corrected} draws with known correct data")
    except Exception as e:
        logger.error(f"Error validating known draws: {str(e)}")
    
    lottery_type = request.args.get('lottery_type', None)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = LotteryResult.query
    if lottery_type:
        query = query.filter_by(lottery_type=lottery_type)
    
    results = query.order_by(LotteryResult.draw_date.desc()).paginate(page=page, per_page=per_page)
    return render_template('results.html', results=results, lottery_type=lottery_type)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Page for configuring screenshot schedules"""
    if request.method == 'POST':
        url = request.form.get('url')
        lottery_type = request.form.get('lottery_type')
        frequency = request.form.get('frequency', 'daily')
        hour = request.form.get('hour', 0, type=int)
        minute = request.form.get('minute', 0, type=int)
        
        if not url or not lottery_type:
            flash('URL and lottery type are required', 'danger')
            return redirect(url_for('settings'))
        
        # Create or update schedule
        config = ScheduleConfig.query.filter_by(url=url).first()
        if not config:
            config = ScheduleConfig(url=url, lottery_type=lottery_type, 
                                  frequency=frequency, hour=hour, minute=minute, active=True)
            db.session.add(config)
        else:
            config.lottery_type = lottery_type
            config.frequency = frequency
            config.hour = hour
            config.minute = minute
            config.active = True
        
        db.session.commit()
        
        # Add to scheduler
        schedule_task(scheduler, config)
        
        flash('Schedule updated successfully', 'success')
        return redirect(url_for('settings'))
    
    schedules = ScheduleConfig.query.all()
    return render_template('settings.html', schedules=schedules)

@app.route('/toggle_schedule/<int:id>')
def toggle_schedule(id):
    """Toggle a schedule on or off"""
    config = ScheduleConfig.query.get_or_404(id)
    config.active = not config.active
    db.session.commit()
    
    if config.active:
        schedule_task(scheduler, config)
        flash(f'Schedule for {config.lottery_type} activated', 'success')
    else:
        remove_task(scheduler, config.id)
        flash(f'Schedule for {config.lottery_type} deactivated', 'warning')
        
    return redirect(url_for('settings'))

@app.route('/delete_schedule/<int:id>')
def delete_schedule(id):
    """Delete a schedule"""
    config = ScheduleConfig.query.get_or_404(id)
    remove_task(scheduler, config.id)
    db.session.delete(config)
    db.session.commit()
    flash(f'Schedule for {config.lottery_type} deleted', 'warning')
    return redirect(url_for('settings'))

@app.route('/api/run_now/<int:id>')
def run_now(id):
    """Manually run a scheduled task immediately"""
    config = ScheduleConfig.query.get_or_404(id)
    try:
        logger.info(f"Manually capturing HTML content for {config.url}")
        filepath, extracted_data = capture_screenshot(config.url, config.lottery_type)
        if filepath and extracted_data:
            logger.info(f"Aggregating data for {config.lottery_type}")
            aggregate_data(extracted_data, config.lottery_type, config.url)
            return jsonify({'status': 'success', 'message': f'Data for {config.lottery_type} updated'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to capture HTML content'})
    except Exception as e:
        logger.error(f"Error running task: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/screenshots')
def get_screenshots():
    """API endpoint to fetch recent screenshots"""
    screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).limit(20).all()
    return jsonify([{
        'id': s.id,
        'url': s.url,
        'lottery_type': s.lottery_type,
        'timestamp': s.timestamp.isoformat(),
        'path': s.path
    } for s in screenshots])

@app.route('/api/results/<lottery_type>')
def get_results(lottery_type):
    """API endpoint to fetch results for a specific lottery type"""
    limit = request.args.get('limit', 10, type=int)
    results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).limit(limit).all()
    return jsonify([r.to_dict() for r in results])

@app.route('/api/raw-html/<lottery_type>')
def get_raw_ocr(lottery_type):
    """API endpoint to fetch raw HTML data for a specific lottery type"""
    import html_parser
    
    # Find the most recent screenshot record for this lottery type
    screenshot = Screenshot.query.filter_by(
        lottery_type=lottery_type
    ).order_by(Screenshot.timestamp.desc()).first()
    
    if not screenshot:
        return jsonify({'error': 'No content found for this lottery type'})
    
    # Read the HTML file and parse it
    try:
        with open(screenshot.path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse the HTML content
        raw_data = html_parser.parse_lottery_html(html_content, lottery_type)
        
        return jsonify({
            'content_info': {
                'id': screenshot.id,
                'path': screenshot.path,
                'timestamp': screenshot.timestamp.isoformat(),
                'processed': screenshot.processed
            },
            'parsed_data': raw_data
        })
    except Exception as e:
        logger.error(f"Error processing HTML content: {str(e)}")
        return jsonify({'error': str(e)})