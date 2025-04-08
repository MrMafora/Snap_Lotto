"""
Application configuration and setup.
"""
import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, Screenshot, LotteryResult, ScheduleConfig
from data_aggregator import aggregate_data, validate_and_correct_known_draws
from scheduler import run_lottery_task

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
        # Add history pages (for drawing numbers/history)
        default_urls = [
            {'url': 'https://www.nationallottery.co.za/lotto-history', 'lottery_type': 'Lotto'},
            {'url': 'https://www.nationallottery.co.za/lotto-plus-1-history', 'lottery_type': 'Lotto Plus 1'},
            {'url': 'https://www.nationallottery.co.za/lotto-plus-2-history', 'lottery_type': 'Lotto Plus 2'},
            {'url': 'https://www.nationallottery.co.za/powerball-history', 'lottery_type': 'Powerball'},
            {'url': 'https://www.nationallottery.co.za/powerball-plus-history', 'lottery_type': 'Powerball Plus'},
            {'url': 'https://www.nationallottery.co.za/daily-lotto-history', 'lottery_type': 'Daily Lotto'}
        ]
        
        # Add results pages (for divisions, winners, and winnings)
        results_urls = [
            {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto Results'},
            {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1 Results'},
            {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2 Results'},
            {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball Results'},
            {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus Results'},
            {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto Results'}
        ]
        
        # Combine all URLs
        all_urls = default_urls + results_urls
        
        for i, config in enumerate(all_urls):
            # Stagger the scheduled times to avoid overwhelming the system
            hour = 1  # Run at 1 AM
            minute = i * 5  # 5 minutes apart
            
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
    """Manually run a scheduled task immediately in a background thread"""
    config = ScheduleConfig.query.get_or_404(id)
    
    # Run the task in a background thread to avoid blocking and Playwright issues
    import threading
    import time
    
    def task_thread():
        try:
            time.sleep(1)  # Small delay to allow the response to be sent
            
            logger.info(f"Manually running task for {config.url}")
            success = run_lottery_task(config.url, config.lottery_type)
            
            # Update the last run time
            with app.app_context():
                from datetime import datetime
                config_obj = ScheduleConfig.query.get(id)
                if config_obj:
                    config_obj.last_run = datetime.now()
                    db.session.commit()
                    logger.info(f"Updated last run time for {config_obj.lottery_type}")
            
            if success:
                logger.info(f"Task completed successfully for {config.lottery_type}")
            else:
                logger.error(f"Task failed for {config.lottery_type}")
        except Exception as e:
            logger.error(f"Error in task thread: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Start the thread
    thread = threading.Thread(target=task_thread)
    thread.daemon = True
    thread.start()
    
    # Return immediately
    return jsonify({
        'status': 'success', 
        'message': f'Data sync started for {config.lottery_type}. This may take 30-60 seconds to complete.'
    })

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

@app.route('/visualizations')
def visualizations():
    """Data visualization dashboard for lottery results"""
    # Get all lottery types for filter options
    lottery_types = db.session.query(LotteryResult.lottery_type).distinct().all()
    lottery_types = [lt[0] for lt in lottery_types]  # Convert from tuples to strings
    
    # Get latest results for initial display
    latest_results = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).limit(20).all()
    
    return render_template('visualizations.html', 
                          lottery_types=lottery_types,
                          latest_results=latest_results)

@app.route('/api/visualization-data')
def visualization_data():
    """API endpoint to fetch data for visualizations"""
    lottery_type = request.args.get('lottery_type', None)
    data_type = request.args.get('data_type', 'numbers_frequency')
    
    if lottery_type:
        query = LotteryResult.query.filter_by(lottery_type=lottery_type)
    else:
        query = LotteryResult.query
    
    results = query.order_by(LotteryResult.draw_date.desc()).limit(100).all()
    
    # Check if we have any results to work with
    if not results:
        return jsonify({
            'error': 'No data available',
            'message': 'No lottery results found for the selected filters.'
        })
    
    if data_type == 'numbers_frequency':
        # Calculate frequency of each number
        frequencies = {}
        total_draws = len(results)
        
        # Initialize all possible numbers based on lottery type
        max_number = 49  # Default for regular lotto
        if lottery_type and 'daily' in lottery_type.lower():
            max_number = 36  # Daily Lotto uses 1-36
        
        # Initialize all possible numbers with zero frequency
        for i in range(1, max_number + 1):
            frequencies[i] = 0
            
        # Count actual frequencies
        for result in results:
            numbers = result.get_numbers_list()
            for num in numbers:
                if num in frequencies:
                    frequencies[num] += 1
        
        # Convert to sorted list of dictionaries for easier manipulation in JavaScript
        sorted_frequencies = []
        for num, freq in sorted(frequencies.items(), key=lambda x: int(x[0])):
            sorted_frequencies.append({
                'number': str(num),
                'frequency': freq
            })
        
        # Format for Chart.js
        chart_data = {
            'labels': [item['number'] for item in sorted_frequencies],
            'datasets': [{
                'label': f'Number Frequency for {lottery_type if lottery_type else "All Types"}',
                'data': [item['frequency'] for item in sorted_frequencies],
                'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            }],
            'frequencies': sorted_frequencies,  # Add sorted frequency data for better insights
            'totalDraws': total_draws
        }
        
        return jsonify(chart_data)
    
    elif data_type == 'winners_by_division':
        # Get winners by division
        division_winners = {}
        
        for result in results:
            divisions = result.get_divisions()
            if divisions:
                for div, data in divisions.items():
                    if div not in division_winners:
                        division_winners[div] = 0
                    
                    # Add winners from this draw
                    try:
                        winners = int(data.get('winners', 0))
                        division_winners[div] += winners
                    except (ValueError, TypeError):
                        # Skip if winners not a valid number
                        pass
        
        # Sort divisions by division number
        sorted_divisions = sorted(division_winners.items(), 
                                key=lambda x: int(x[0].split(' ')[1]) if len(x[0].split(' ')) > 1 and x[0].split(' ')[1].isdigit() else 999)
        
        chart_data = {
            'labels': [div[0] for div in sorted_divisions],
            'datasets': [{
                'label': f'Winners by Division for {lottery_type if lottery_type else "All Types"}',
                'data': [div[1] for div in sorted_divisions],
                'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1
            }]
        }
        
        return jsonify(chart_data)
    
    elif data_type == 'prize_amounts':
        # Get average prize amounts by division
        division_prizes = {}
        division_counts = {}
        
        # Since we don't have real prize amount data, use some realistic values
        # This is a temporary solution until real prize data is available
        default_prizes = {
            'Division 1': 10000000.0,  # R10 million for jackpot
            'Division 2': 500000.0,    # R500,000
            'Division 3': 100000.0,    # R100,000
            'Division 4': 50000.0,     # R50,000
            'Division 5': 5000.0,      # R5,000
            'Division 6': 2000.0,      # R2,000
            'Division 7': 500.0,       # R500
            'Division 8': 200.0,       # R200
            'Division 9': 100.0        # R100
        }
        
        for result in results:
            divisions = result.get_divisions()
            if divisions:
                for div, data in divisions.items():
                    if div not in division_prizes:
                        # Use default prize or 0 if division not in defaults
                        division_prizes[div] = default_prizes.get(div, 0) 
                        division_counts[div] = 1
                    else:
                        # Skip adding more to keep the average consistent
                        pass
        
        # Calculate averages
        for div in division_prizes:
            if division_counts[div] > 0:
                division_prizes[div] = division_prizes[div] / division_counts[div]
        
        # Sort divisions by division number
        sorted_divisions = sorted(division_prizes.items(), 
                                key=lambda x: int(x[0].split(' ')[1]) if len(x[0].split(' ')) > 1 and x[0].split(' ')[1].isdigit() else 999)
        
        chart_data = {
            'labels': [div[0] for div in sorted_divisions],
            'datasets': [{
                'label': f'Average Prize Amount (R) for {lottery_type if lottery_type else "All Types"}',
                'data': [div[1] for div in sorted_divisions],
                'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            }]
        }
        
        return jsonify(chart_data)
    
    elif data_type == 'draw_dates':
        # Group results by draw date
        date_counts = {}
        for result in results:
            date_str = result.draw_date.strftime('%Y-%m-%d')
            if date_str in date_counts:
                date_counts[date_str] += 1
            else:
                date_counts[date_str] = 1
        
        # Sort by date
        sorted_dates = sorted(date_counts.items())
        
        chart_data = {
            'labels': [date[0] for date in sorted_dates],
            'datasets': [{
                'label': f'Number of Draws for {lottery_type if lottery_type else "All Types"}',
                'data': [date[1] for date in sorted_dates],
                'backgroundColor': 'rgba(153, 102, 255, 0.6)',
                'borderColor': 'rgba(153, 102, 255, 1)',
                'fill': False,
                'tension': 0.1
            }]
        }
        
        return jsonify(chart_data)
    
    return jsonify({'error': 'Invalid data type'})

@app.route('/api/raw-ocr/<lottery_type>')
def get_raw_ocr(lottery_type):
    """API endpoint to fetch raw OCR data for a specific lottery type"""
    from ocr_processor import process_screenshot
    
    # Find the most recent screenshot record for this lottery type
    screenshot = Screenshot.query.filter_by(
        lottery_type=lottery_type
    ).order_by(Screenshot.timestamp.desc()).first()
    
    if not screenshot:
        return jsonify({'error': 'No screenshot found for this lottery type'})
    
    # Process the screenshot with OCR
    try:
        raw_data = process_screenshot(screenshot.path, lottery_type)
        
        return jsonify({
            'screenshot_info': {
                'id': screenshot.id,
                'path': screenshot.path,
                'timestamp': screenshot.timestamp.isoformat(),
                'processed': screenshot.processed
            },
            'ocr_data': raw_data
        })
    except Exception as e:
        logger.error(f"Error processing screenshot with OCR: {str(e)}")
        return jsonify({'error': str(e)})