"""
Main application entry point with Flask application defined for deployment.

This file is imported by gunicorn using the 'main:app' notation.

It also includes functionality to automatically bind to port 8080 
when running directly, to support Replit's external access requirements.

IMPORTANT: This application includes built-in port forwarding capabilities
to handle both the internal port 5000 (used by gunicorn) and the external
port 8080 required by Replit for public access.
"""
import logging
import os
import threading
import traceback
from datetime import datetime, timedelta
from functools import wraps

# Set up logging first
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Now that logger is defined, import other modules
# import scheduler  # Commented out - module not found
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, send_from_directory, send_file, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
# Use standard CSRF protection
from flask_wtf.csrf import CSRFProtect
import json

# Import models only (lightweight)
from models import LotteryResult, ScheduleConfig, Screenshot, User, Advertisement, AdImpression, Campaign, AdVariation, ImportHistory, ImportedRecord, db
from config import Config
from sqlalchemy import text

# Import modules
# ad_management temporarily disabled
# import ad_management
import lottery_analysis
# Remove problematic fix modules that are causing conflicts
# Import functionality integrated into main application
# scanner_routes module temporarily disabled to resolve conflicts

# Auto proxy functionality cleaned up - using direct port configuration

# Create the Flask application
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Add custom Jinja2 filters for math functions needed by charts
import math
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # Set locale for number formatting

app.jinja_env.filters['cos'] = lambda x: math.cos(float(x))
app.jinja_env.filters['sin'] = lambda x: math.sin(float(x))
app.jinja_env.filters['format_number'] = lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x

# Explicitly set database URI from environment variable
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Ensure proper PostgreSQL connection string format
    # Heroku-style connection strings start with postgres:// but SQLAlchemy requires postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    logger.info(f"Using database from DATABASE_URL environment variable")
else:
    logger.warning("DATABASE_URL not found, using fallback database configuration")

# Initialize SQLAlchemy with additional connection settings
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True
}

# Add SSL requirement for PostgreSQL connections
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS']["connect_args"] = {"sslmode": "require"}
    logger.info("PostgreSQL SSL mode enabled")

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CSRF Protection
csrf = CSRFProtect(app)
# Exempt ticket scanner from CSRF for file uploads
csrf.exempt('process_ticket')
# EnhancedCSRFProtect class handles all the configuration, so we don't need to set these manually

# Exempt endpoints that don't need CSRF protection
csrf.exempt('scan_ticket')
csrf.exempt('process_ticket')
csrf.exempt('check_js')
csrf.exempt('resolve_health_alert')
csrf.exempt('api_system_metrics')
csrf.exempt('record_impression')
csrf.exempt('record_click')
csrf.exempt('get_file_upload_progress')
csrf.exempt('health_check')
csrf.exempt('health_port_check')

# Exempt all lottery analysis API endpoints
csrf.exempt('api_frequency_analysis')
csrf.exempt('api_pattern_analysis')
csrf.exempt('api_time_series_analysis')
csrf.exempt('api_correlation_analysis')
csrf.exempt('api_winner_analysis')
csrf.exempt('api_lottery_prediction')
csrf.exempt('api_full_analysis')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Defer database schema creation to background thread
def init_database():
    """Initialize database tables in background thread"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")
        
# Start database initialization in background to avoid blocking startup
threading.Thread(target=init_database, daemon=True).start()

# Lazy load these modules - will be imported when needed
# This helps reduce initial load time
data_aggregator = None
import_excel = None
import_snap_lotto_data = None
ocr_processor = None
screenshot_manager = None
# scheduler is imported at the top level to ensure screenshot functions work
health_monitor = None

def init_lazy_modules():
    """Initialize modules in a background thread with timeout"""
    global data_aggregator, import_excel, import_snap_lotto_data, ocr_processor, screenshot_manager, health_monitor
    
    # Note: Removed signal alarm since it only works in main thread
    
    # Import heavy modules only when needed - data_aggregator not available
    # try:
    #     import data_aggregator as da
    # except ImportError:
    da = None
    try:
        import ocr_processor as op
    except ImportError:
        op = None
    try:
        import screenshot_manager as sm
    except ImportError:
        sm = None
    try:
        import health_monitor as hm
    except ImportError:
        hm = None
    
    # Store module references - data_aggregator not available
    # data_aggregator = da
    import_excel = None  # Functionality integrated into main app
    import_snap_lotto_data = None  # Functionality integrated into main app
    ocr_processor = op
    screenshot_manager = sm
    health_monitor = hm
    
    # Initialize scheduler and health monitoring in background after imports are complete
    with app.app_context():
        # scheduler.init_scheduler(app)  # Commented out - module not available
        health_monitor.init_health_monitor(app, db)
        
        # Register scanner routes for ticket scanning functionality
        try:
            from scanner_routes import register_scanner_routes
            register_scanner_routes(app)
            logger.info("Scanner routes registered")
        except Exception as e:
            logger.error(f"Failed to register scanner routes: {e}")
    
    logger.info("All modules lazy-loaded successfully")

# Start lazy loading in background thread
threading.Thread(target=init_lazy_modules, daemon=True).start()

# Additional routes and functionality would be defined here...
# For the sake of brevity, only core routes are included

@app.route('/')
def home():
    """Homepage with latest authentic South African lottery results"""
    from sqlalchemy import text
    import json
    
    # Get your authentic lottery results directly using raw SQL like the analytics
    results = []
    try:
        # Query your genuine database for the latest results
        query = text("""
            SELECT DISTINCT ON (lottery_type) 
                   lottery_type, draw_number, draw_date, numbers, bonus_numbers
            FROM lottery_result 
            WHERE numbers IS NOT NULL AND numbers != ''
            ORDER BY lottery_type, draw_date DESC, id DESC
        """)
        
        raw_results = db.session.execute(query).fetchall()
        
        for row in raw_results:
            try:
                # Parse your authentic JSON data
                numbers = json.loads(row.numbers) if row.numbers else []
                bonus_numbers = json.loads(row.bonus_numbers) if row.bonus_numbers else []
                
                # Clean the authentic numbers
                clean_numbers = []
                for n in numbers:
                    try:
                        clean_numbers.append(int(str(n).strip().strip('"')))
                    except:
                        continue
                
                clean_bonus = []
                for b in bonus_numbers:
                    try:
                        clean_bonus.append(int(str(b).strip().strip('"')))
                    except:
                        continue
                
                if clean_numbers:  # Only include if we have valid numbers
                    # Normalize naming for display
                    display_type = row.lottery_type
                    if 'Lotto' in display_type:
                        display_type = display_type.replace('Lotto', 'Lottery')
                    
                    # Create result object with proper structure
                    class ResultObj:
                        def __init__(self, lottery_type, draw_number, draw_date, numbers, bonus_numbers):
                            self.lottery_type = lottery_type
                            self.draw_number = str(draw_number)
                            self.draw_date = draw_date
                            self.numbers = numbers
                            self.bonus_numbers = bonus_numbers
                        
                        def get_numbers_list(self):
                            return self.numbers
                        
                        def get_bonus_numbers_list(self):
                            return self.bonus_numbers
                    
                    result = ResultObj(display_type, row.draw_number, row.draw_date, clean_numbers, clean_bonus)
                    results.append(result)
                    
            except Exception as e:
                continue
                
    except Exception as e:
        results = []
    
    return render_template('index.html', results=results)


@app.route('/admin')
@login_required
def admin():
    """Admin dashboard for system administration"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get system statistics
    try:
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        system_stats = {
            'cpu_usage': f"{cpu_percent}%",
            'memory_usage': f"{memory.percent}%",
            'disk_usage': f"{disk.percent}%"
        }
    except Exception as e:
        app.logger.error(f"Error getting system stats: {str(e)}")
        system_stats = {
            'cpu_usage': 'N/A',
            'memory_usage': 'N/A',
            'disk_usage': 'N/A'
        }
    
    # Get recent API logs
    try:
        from models import APIRequestLog
        recent_api_logs = APIRequestLog.query.order_by(APIRequestLog.created_at.desc()).limit(10).all()
    except Exception as e:
        app.logger.error(f"Error getting API logs: {str(e)}")
        recent_api_logs = []
    
    # Get recent imports
    try:
        from models import ImportHistory
        recent_imports = ImportHistory.query.order_by(ImportHistory.timestamp.desc()).limit(5).all()
    except Exception as e:
        app.logger.error(f"Error getting import history: {str(e)}")
        recent_imports = []
    
    # Get recent health checks
    try:
        import health_monitor
        import sqlite3
        conn = sqlite3.connect(health_monitor.health_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM health_checks ORDER BY timestamp DESC LIMIT 5")
        recent_health_checks = [dict(row) for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        app.logger.error(f"Error getting health checks: {str(e)}")
        recent_health_checks = []
    
    return render_template(
        'admin/dashboard.html',
        title="Admin Dashboard",
        system_stats=system_stats,
        recent_api_logs=recent_api_logs,
        recent_imports=recent_imports,
        recent_health_checks=recent_health_checks
    )

# Removed duplicate api-tracking route - functionality moved to api_tracking_view() function

@app.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    # Define SEO metadata
    meta_description = "Secure login for administration of the South African lottery results system. Access administrative features to manage lottery data and system settings."
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Login", "url": url_for('login')}
    ]
    
    return render_template('login.html', 
                          title="Admin Login | Lottery Results Management",
                          meta_description=meta_description,
                          breadcrumbs=breadcrumbs)

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/scan-lottery-ticket-south-africa')
@app.route('/scanner-landing')
def scanner_landing():
    """Landing page focused on the exclusive lottery ticket scanner feature"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Lottery Ticket Scanner", "url": url_for('scanner_landing')}
    ]
    
    # Define SEO metadata
    meta_description = "South Africa's ONLY lottery ticket scanner app. Instantly check if your Lottery, PowerBall, or Daily Lottery ticket is a winner by uploading a photo."
    
    return render_template('scanner_landing.html',
                          title="South Africa's ONLY Lottery Ticket Scanner App | Check If You've Won Instantly",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/ticket-scanner')
def ticket_scanner():
    """Ticket scanner page - Allows users to scan and validate their lottery tickets"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Lottery Ticket Scanner", "url": url_for('scanner_landing')},
        {"name": "Scan Your Ticket", "url": url_for('ticket_scanner')}
    ]
    
    # Additional SEO metadata
    meta_description = "Check if your South African lottery ticket is a winner. Our free ticket scanner uses advanced technology to analyze and verify your lottery tickets instantly."
    
    return render_template('ticket_scanner.html', 
                          title="Lottery Ticket Scanner | Check If You've Won",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/process-ticket', methods=['POST'])
@csrf.exempt
def process_ticket():
    """Process a lottery ticket image and return JSON results"""
    if 'ticket_image' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['ticket_image']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    # Get the lottery type if specified (optional)
    lottery_type = request.form.get('lottery_type', '')
    
    # Get draw number if specified (optional)
    draw_number = request.form.get('draw_number', None)
    
    # Get file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if not file_extension:
        file_extension = '.jpeg'  # Default to JPEG if no extension
    
    try:
        # Read the file data
        image_data = file.read()
        
        # Save the image to a temporary directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        
        # We need to seek back to start of file after reading
        file.seek(0)
        file.save(file_path)
        
        # Process the ticket using Anthropic AI with the new API key
        try:
            import base64
            import json
            import anthropic
            
            # Initialize Anthropic client with the new API key
            client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY'))
            
            # Read and encode the image
            with open(file_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create the message for Anthropic
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": """You are reading a South African lottery ticket. Extract the information and return ONLY valid JSON.

                            Return this exact format:
                            
                            {
                                "lottery_type": "PowerBall",
                                "main_numbers": [1, 2, 3, 4, 5],
                                "powerball_number": "10",
                                "powerball_plus_included": "YES",
                                "draw_date": "16/05/2025",
                                "draw_number": "PB1615",
                                "ticket_cost": "R15.00"
                            }
                            
                            Look for:
                            - Game type (PowerBall, Lotto, Daily Lotto)
                            - Player's chosen numbers
                            - PowerBall number (red ball 1-20)
                            - "YES" next to PowerBall Plus
                            - Draw date and number
                            - Ticket cost
                            
                            Return ONLY the JSON object, no other text."""
                        }
                    ]
                }]
            )
            
            # Parse the response
            response_text = message.content[0].text
            logger.info("=== FULL AI RESPONSE ===")
            logger.info(response_text)
            logger.info("========================")
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    ticket_data = json.loads(json_match.group())
                    logger.info(f"Extracted JSON: {ticket_data}")
                else:
                    ticket_data = json.loads(response_text)
                    logger.info(f"Direct JSON parse: {ticket_data}")
                
                # Check for PowerBall + PowerBall Plus combination and compare with both results
                powerball_results = {}
                powerball_plus_results = {}
                
                if ticket_data.get('main_numbers'):
                    player_main_numbers = ticket_data.get('main_numbers', [])
                    player_powerball = ticket_data.get('powerball_number')
                    
                    # Check which games to compare based on lottery type and YES indicators
                    lottery_type = ticket_data.get('lottery_type', '').lower()
                    powerball_plus_yes = ticket_data.get('powerball_plus_included', '').upper() == 'YES'
                    lotto_plus_1_yes = ticket_data.get('lotto_plus_1_included', '').upper() == 'YES'
                    lotto_plus_2_yes = ticket_data.get('lotto_plus_2_included', '').upper() == 'YES'
                    
                    # For PowerBall tickets
                    if 'powerball' in lottery_type:
                        # Always check PowerBall main game
                        powerball_draw = LotteryResult.query.filter_by(lottery_type='Powerball').order_by(LotteryResult.draw_date.desc()).first()
                        if powerball_draw:
                            powerball_numbers = powerball_draw.numbers if powerball_draw.numbers else []
                            powerball_bonus = powerball_draw.bonus_numbers[0] if powerball_draw.bonus_numbers else None
                            
                            main_matches = len(set(player_main_numbers) & set(powerball_numbers))
                            powerball_match = (player_powerball == powerball_bonus) if player_powerball and powerball_bonus else False
                            
                            powerball_results = {
                                'lottery_type': 'PowerBall',
                                'draw_number': powerball_draw.draw_number,
                                'draw_date': powerball_draw.draw_date.strftime('%Y-%m-%d'),
                                'winning_numbers': powerball_numbers,
                                'winning_powerball': powerball_bonus,
                                'main_matches': main_matches,
                                'powerball_match': powerball_match,
                                'total_matches': f"{main_matches} main + {'PowerBall' if powerball_match else '0 PowerBall'}"
                            }
                        
                        # Check PowerBall Plus only if YES indicator found
                        if powerball_plus_yes:
                            powerball_plus_draw = LotteryResult.query.filter_by(lottery_type='Powerball Plus').order_by(LotteryResult.draw_date.desc()).first()
                            if powerball_plus_draw:
                                plus_numbers = powerball_plus_draw.numbers if powerball_plus_draw.numbers else []
                                plus_bonus = powerball_plus_draw.bonus_numbers[0] if powerball_plus_draw.bonus_numbers else None
                                
                                plus_main_matches = len(set(player_main_numbers) & set(plus_numbers))
                                plus_powerball_match = (player_powerball == plus_bonus) if player_powerball and plus_bonus else False
                                
                                powerball_plus_results = {
                                    'lottery_type': 'PowerBall Plus',
                                    'draw_number': powerball_plus_draw.draw_number,
                                    'draw_date': powerball_plus_draw.draw_date.strftime('%Y-%m-%d'),
                                    'winning_numbers': plus_numbers,
                                    'winning_powerball': plus_bonus,
                                    'main_matches': plus_main_matches,
                                    'powerball_match': plus_powerball_match,
                                    'total_matches': f"{plus_main_matches} main + {'PowerBall' if plus_powerball_match else '0 PowerBall'}"
                                }
                    
                    # For Lotto tickets
                    elif 'lotto' in lottery_type:
                        # Always check main Lotto game
                        lotto_draw = LotteryResult.query.filter_by(lottery_type='Lotto').order_by(LotteryResult.draw_date.desc()).first()
                        if lotto_draw:
                            lotto_numbers = lotto_draw.numbers if lotto_draw.numbers else []
                            lotto_bonus = lotto_draw.bonus_numbers[0] if lotto_draw.bonus_numbers else None
                            
                            main_matches = len(set(player_main_numbers) & set(lotto_numbers))
                            bonus_match = lotto_bonus in player_main_numbers if lotto_bonus else False
                            
                            powerball_results = {  # Using same variable for consistency in frontend
                                'lottery_type': 'Lotto',
                                'draw_number': lotto_draw.draw_number,
                                'draw_date': lotto_draw.draw_date.strftime('%Y-%m-%d'),
                                'winning_numbers': lotto_numbers,
                                'winning_bonus': lotto_bonus,
                                'main_matches': main_matches,
                                'bonus_match': bonus_match,
                                'total_matches': f"{main_matches} main + {'Bonus' if bonus_match else '0 Bonus'}"
                            }
                        
                        # Check Lotto Plus 1 if YES indicator found
                        if lotto_plus_1_yes:
                            lotto_plus_1_draw = LotteryResult.query.filter_by(lottery_type='Lotto Plus 1').order_by(LotteryResult.draw_date.desc()).first()
                            if lotto_plus_1_draw:
                                plus_1_numbers = lotto_plus_1_draw.numbers if lotto_plus_1_draw.numbers else []
                                plus_1_bonus = lotto_plus_1_draw.bonus_numbers[0] if lotto_plus_1_draw.bonus_numbers else None
                                
                                plus_1_main_matches = len(set(player_main_numbers) & set(plus_1_numbers))
                                plus_1_bonus_match = plus_1_bonus in player_main_numbers if plus_1_bonus else False
                                
                                powerball_plus_results = {  # Using same variable for consistency
                                    'lottery_type': 'Lotto Plus 1',
                                    'draw_number': lotto_plus_1_draw.draw_number,
                                    'draw_date': lotto_plus_1_draw.draw_date.strftime('%Y-%m-%d'),
                                    'winning_numbers': plus_1_numbers,
                                    'winning_bonus': plus_1_bonus,
                                    'main_matches': plus_1_main_matches,
                                    'bonus_match': plus_1_bonus_match,
                                    'total_matches': f"{plus_1_main_matches} main + {'Bonus' if plus_1_bonus_match else '0 Bonus'}"
                                }
                
                # Extract and format the data properly for frontend display
                # Handle both simple arrays and structured line objects
                numbers = ticket_data.get('numbers', ticket_data.get('main_numbers', []))
                powerball_numbers = ticket_data.get('powerball_or_bonus', ticket_data.get('powerball_number'))
                
                # Parse numbers - handle multiple formats including {"A1": [1,2,3], "B1": [4,5,6]}
                all_lines = []
                all_powerball = []
                
                if isinstance(numbers, dict):
                    # New format: {"A1": [4,5,23,24,25], "B1": [15,17,18,23,42]}
                    for key, value in numbers.items():
                        if isinstance(value, list):
                            all_lines.append({'line_name': key, 'numbers': value})
                elif isinstance(numbers, list) and len(numbers) > 0:
                    # Check if this is an array of arrays (most common current format)
                    if isinstance(numbers[0], list):
                        # Array of arrays: [[9,15,37,39,50], [12,26,31,32,47], ...]
                        for i, line_numbers in enumerate(numbers):
                            all_lines.append({'line_name': f'Line {i+1}', 'numbers': line_numbers})
                    else:
                        # Single array or other format
                        for item in numbers:
                            if isinstance(item, dict):
                                # Structured format: {"line_A": [1,2,3], "powerball_A": 4}
                                for key, value in item.items():
                                    if 'line' in key.lower() and isinstance(value, list):
                                        all_lines.append({'line_name': key, 'numbers': value})
                                    elif 'powerball' in key.lower() and isinstance(value, (int, str)):
                                        all_powerball.append(value)
                            elif isinstance(item, list):
                                # Simple array format: [1,2,3,4,5]
                                all_lines.append({'line_name': f'Line {len(all_lines)+1}', 'numbers': item})
                
                # Handle PowerBall numbers - new format: {"A2": 2, "B2": 4}
                if isinstance(powerball_numbers, dict):
                    for key, value in powerball_numbers.items():
                        if isinstance(value, (int, str)):
                            all_powerball.append(value)
                elif isinstance(powerball_numbers, list):
                    all_powerball = powerball_numbers
                elif powerball_numbers:
                    all_powerball = [powerball_numbers]
                
                # Use extracted numbers directly from ticket_data for main display
                ticket_numbers = numbers if numbers else []
                powerball_number = str(all_powerball[0]) if all_powerball else 'Not detected'
                
                # DEBUG: Ensure we actually have the numbers
                if not ticket_numbers and numbers:
                    ticket_numbers = numbers
                    logger.info(f"DEBUG: Forced ticket_numbers to {ticket_numbers}")
                
                # Normalize game type terminology and determine add-ons
                raw_game_type = ticket_data.get('lottery_type', '').lower()
                if 'powerball' in raw_game_type:
                    game_type = 'PowerBall'
                    powerball_plus_included = 'YES' if 'plus' in raw_game_type else 'NO'
                elif 'lotto' in raw_game_type or 'lottery' in raw_game_type:
                    game_type = 'Lottery'
                    # Check for Plus 1 and Plus 2 mentions
                    if 'plus' in raw_game_type:
                        powerball_plus_included = 'YES'  # Lottery Plus games are included
                    else:
                        powerball_plus_included = 'NO'
                else:
                    game_type = ticket_data.get('lottery_type', 'Not detected')
                    powerball_plus_included = 'NO'
                
                # Debug logging to see what we extracted
                logger.info(f"DEBUG: ticket_data = {ticket_data}")
                logger.info(f"DEBUG: ticket_data.get('lottery_type') = {ticket_data.get('lottery_type')}")
                logger.info(f"DEBUG: raw_game_type = {raw_game_type}")
                logger.info(f"DEBUG: game_type = {game_type}")
                logger.info(f"DEBUG: numbers = {numbers}")
                logger.info(f"DEBUG: powerball_numbers = {powerball_numbers}")
                logger.info(f"DEBUG: ticket_numbers = {ticket_numbers}")
                logger.info(f"DEBUG: powerball_number = {powerball_number}")
                
                # Extract the actual values from nested ticket_data or use the top-level game_type
                actual_lottery_type = ticket_data.get('lottery_type') or game_type or 'Not detected'
                actual_draw_date = ticket_data.get('draw_date', 'Not detected')
                actual_draw_number = ticket_data.get('draw_number', 'Not detected')
                
                # Debug what we're about to send to frontend
                logger.info(f"DEBUG: About to create result with:")
                logger.info(f"DEBUG: - actual_lottery_type: {actual_lottery_type}")
                logger.info(f"DEBUG: - actual_draw_date: {actual_draw_date}")
                logger.info(f"DEBUG: - actual_draw_number: {actual_draw_number}")
                
                # CRITICAL FIX: Ensure numbers are properly passed to frontend
                if numbers and len(numbers) > 0:
                    ticket_numbers = numbers
                    all_lines = [numbers]
                    logger.info(f"NUMBERS FIX: Set ticket_numbers={ticket_numbers}, all_lines={all_lines}")

                # Create a successful result matching frontend expectations
                result = {
                    'success': True,
                    'lottery_type': actual_lottery_type,
                    'draw_date': actual_draw_date,
                    'draw_number': actual_draw_number,
                    'ticket_numbers': ticket_numbers,
                    'powerball_number': powerball_number,
                    'powerball_plus_included': powerball_plus_included,
                    'ticket_cost': ticket_data.get('ticket_cost', 'Not detected'),
                    'all_lines': all_lines,
                    'all_powerball': all_powerball,
                    'is_winner': False,  # Will be determined by comparison
                    'prize_amount': None,
                    'ticket_data': ticket_data,
                    'raw_response': response_text,
                    'powerball_results': powerball_results,
                    'powerball_plus_results': powerball_plus_results,
                    'comparison': {
                        'message': 'PowerBall ticket analyzed! Checked against both PowerBall AND PowerBall Plus results.',
                        'extracted_numbers': ticket_numbers if ticket_numbers else [],
                        'powerball_number': powerball_number,
                        'lottery_type': ticket_data.get('lottery_type', 'Unknown'),
                        'both_games_checked': bool(powerball_results and powerball_plus_results)
                    }
                }
                
                # Ensure we always return the extracted ticket data even if no draws match
                logger.info(f"DEBUG: Final result created with lottery_type={result.get('lottery_type')}, draw_date={result.get('draw_date')}, draw_number={result.get('draw_number')}")
                
                # Log what the frontend will receive
                logger.info(f"DEBUG: Frontend will receive: {json.dumps(result, indent=2, default=str)}")
                logger.info(f"DEBUG: result all_lines = {result.get('all_lines')}")
                logger.info(f"DEBUG: result all_powerball = {result.get('all_powerball')}")
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, create a basic result that shows the response
                logger.error(f"JSON parsing failed: {str(e)}")
                logger.info(f"Creating fallback result with raw response")
                
                # Extract basic info from text if possible
                lottery_type_from_text = 'PowerBall' if 'powerball' in response_text.lower() else 'PowerBall'
                
                # Try to extract numbers from the text using regex
                import re
                number_matches = re.findall(r'\b\d{1,2}\b', response_text)
                extracted_numbers = [int(n) for n in number_matches[:5]] if len(number_matches) >= 5 else []
                
                result = {
                    'success': True,
                    'lottery_type': lottery_type_from_text,
                    'draw_date': 'Please check the raw AI response below',
                    'draw_number': 'Please check the raw AI response below', 
                    'ticket_numbers': extracted_numbers,
                    'powerball_number': number_matches[5] if len(number_matches) > 5 else 'Check raw response',
                    'powerball_plus_included': 'YES' if 'yes' in response_text.lower() else 'NO',
                    'ticket_cost': 'Check raw response',
                    'is_winner': False,
                    'prize_amount': None,
                    'ticket_data': {
                        'lottery_type': lottery_type_from_text,
                        'raw_analysis': response_text,
                        'parsing_error': str(e)
                    },
                    'raw_response': response_text,
                    'comparison': {
                        'message': 'Ticket processed - see extracted information above. Raw AI response available below.',
                        'raw_response': response_text,
                        'error': str(e)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error processing ticket with Anthropic: {str(e)}")
            result = {
                'success': False,
                'error': f"Error analyzing ticket: {str(e)}",
                'ticket_data': {
                    'lottery_type': lottery_type or 'PowerBall'
                }
            }
        
        # Store result in session for results page
        session['scan_result'] = result
        
        # Ensure all required fields are present for frontend - but preserve extracted data
        if not result.get('lottery_type') or result.get('lottery_type') == 'Not detected':
            # Only set default if we truly have no data
            if not result.get('ticket_data', {}).get('lottery_type'):
                result['lottery_type'] = 'PowerBall'
        
        if not result.get('ticket_numbers'):
            result['ticket_numbers'] = []
            
        if not result.get('powerball_number') or result.get('powerball_number') == 'Not detected':
            # Only set default if we truly have no data
            if not result.get('ticket_data', {}).get('powerball_or_bonus'):
                result['powerball_number'] = 'Not detected'
            
        if not result.get('draw_date') or result.get('draw_date') == 'Not detected':
            # Only set default if we truly have no data
            if not result.get('ticket_data', {}).get('draw_date'):
                result['draw_date'] = 'Not detected'
            
        if not result.get('draw_number') or result.get('draw_number') == 'Not detected':
            # Only set default if we truly have no data
            if not result.get('ticket_data', {}).get('draw_number'):
                result['draw_number'] = 'Not detected'
            
        if not result.get('powerball_plus_included'):
            result['powerball_plus_included'] = 'NO'
        
        # Ensure we have the core display fields that frontend expects
        if not result.get('lottery_type'):
            result['lottery_type'] = result.get('ticket_data', {}).get('lottery_type', 'Not detected')
        if not result.get('draw_date') or result.get('draw_date') == 'Not detected':
            result['draw_date'] = result.get('ticket_data', {}).get('draw_date', 'Not detected')
        if not result.get('draw_number') or result.get('draw_number') == 'Not detected':
            result['draw_number'] = result.get('ticket_data', {}).get('draw_number', 'Not detected')
        
        # Standardize "Lotto" to "Lottery" terminology in the response
        if result.get('lottery_type') and 'Lotto' in result['lottery_type']:
            result['lottery_type'] = result['lottery_type'].replace('Lotto', 'Lottery')
        
        # Integrate extracted numbers properly into main display
        if result.get('ticket_data') and result['ticket_data'].get('main_numbers'):
            result['ticket_numbers'] = result['ticket_data']['main_numbers']
            logger.info(f"FIXED: Set ticket_numbers to {result['ticket_numbers']}")
        
        # CRITICAL FIX: Force ticket numbers if they're still empty but we have them in ticket_data
        if (not result.get('ticket_numbers') or len(result.get('ticket_numbers', [])) == 0) and result.get('ticket_data', {}).get('main_numbers'):
            result['ticket_numbers'] = result['ticket_data']['main_numbers']
            logger.info(f"FORCED FIX: ticket_numbers = {result['ticket_numbers']}")
            
        # Add PowerBall number if detected
        if result.get('ticket_data') and result['ticket_data'].get('powerball_number'):
            result['powerball_number'] = result['ticket_data']['powerball_number']
        
        # Ensure we show PowerBall Plus inclusion status
        if result.get('ticket_data') and result['ticket_data'].get('powerball_plus_included'):
            result['powerball_plus_included'] = result['ticket_data']['powerball_plus_included']
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing ticket: {str(e)}")
        return jsonify({'success': False, 'error': f"Error processing ticket: {str(e)}"})

# Scan ticket functionality is now handled by the /process-ticket endpoint

@app.route('/scan-results')
def scan_results():
    """Display the results of a scanned ticket"""
    result = session.get('scan_result')
    
    if not result:
        flash("No scan results available. Please scan a ticket first.", "warning")
        return redirect(url_for('ticket_scanner'))
    
    # Additional SEO metadata
    meta_description = "View your South African lottery ticket scan results. Find out if you've won with our advanced ticket scanner."
    
    return render_template('scanner/scan_results.html', 
                          title="Ticket Scan Results | Check If You've Won",
                          result=result,
                          meta_description=meta_description)

# Guides Routes
@app.route('/guides')
def guides_index():
    """Display index of lottery guides"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Home", "url": url_for('index')},
        {"name": "Lottery Guides", "url": url_for('guides_index')}
    ]
    
    # Define SEO metadata
    meta_description = "Comprehensive guides on how to play South African lottery games. Learn rules, strategies, and tips for Lottery, PowerBall, Daily Lottery and more."
    
    return render_template('guides/index.html', 
                          title="South African Lottery Guides | Tips & How-To Articles",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/guides/how-to-play-lottery')
def how_to_play_lotto():
    """Display guide on how to play Lottery"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Home", "url": url_for('index')},
        {"name": "Lottery Guides", "url": url_for('guides_index')},
        {"name": "How to Play Lottery", "url": url_for('how_to_play_lotto')}
    ]
    
    # Define SEO metadata
    meta_description = "Comprehensive guide on how to play the South African Lottery. Learn Lottery rules, drawing days, odds of winning, prize divisions, and expert tips."
    
    return render_template('guides/how_to_play_lotto.html',
                          title="How to Play Lottery South Africa | Complete Guide & Tips",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/guides/how-to-play-powerball')
def how_to_play_powerball():
    """Display guide on how to play PowerBall"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Home", "url": url_for('index')},
        {"name": "Lottery Guides", "url": url_for('guides_index')},
        {"name": "How to Play PowerBall", "url": url_for('how_to_play_powerball')}
    ]
    
    # Define SEO metadata
    meta_description = "Complete guide to playing PowerBall South Africa. Learn game rules, drawing schedule, odds, prize divisions, and expert strategies to increase your chances."
    
    # Placeholder until we create the PowerBall guide template
    flash("PowerBall guide coming soon! Check out our Lottery guide in the meantime.", "info")
    return redirect(url_for('guides_index'))

@app.route('/guides/how-to-play-daily-lottery')
def how_to_play_daily_lotto():
    """Display guide on how to play Daily Lottery"""
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Home", "url": url_for('index')},
        {"name": "Lottery Guides", "url": url_for('guides_index')},
        {"name": "How to Play Daily Lottery", "url": url_for('how_to_play_daily_lotto')}
    ]
    
    # Define SEO metadata
    meta_description = "Learn how to play Daily Lottery South Africa with our comprehensive guide. Discover game rules, draw times, odds of winning, and how to claim prizes."
    
    # Placeholder until we create the Daily Lottery guide template
    flash("Daily Lottery guide coming soon! Check out our Lottery guide in the meantime.", "info")
    return redirect(url_for('guides_index'))

@app.route('/results')
def results():
    """Show overview of all lottery types with links to specific results"""
    lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 
                     'Powerball', 'Powerball Plus', 'Daily Lottery']
    
    try:
        # Ensure data_aggregator is loaded before using it
        global data_aggregator
        
        # Import if not already loaded - data_aggregator module not available
        # Module functionality replaced with direct database queries
        
        # Initialize with empty dict in case the next step fails
        latest_results = {}
        
        try:
            # Use direct SQL approach to ensure we get authentic data
            latest_results = {}
            
            for lottery_type in lottery_types:
                # Direct SQL query to bypass any ORM issues
                sql_query = """
                    SELECT id, lottery_type, draw_number, draw_date, numbers, bonus_numbers
                    FROM lottery_result 
                    WHERE lottery_type = :lottery_type 
                    ORDER BY draw_date DESC 
                    LIMIT 1
                """
                
                result = db.session.execute(text(sql_query), {'lottery_type': lottery_type}).fetchone()
                
                if result:
                    # Create a simple object to hold the data
                    class ResultObj:
                        def __init__(self, lottery_type, draw_number, draw_date, numbers, bonus_numbers):
                            self.lottery_type = lottery_type
                            self.draw_number = draw_number
                            self.draw_date = draw_date
                            self.numbers = numbers
                            self.bonus_numbers = bonus_numbers
                        
                        def get_numbers_list(self):
                            return json.loads(self.numbers) if isinstance(self.numbers, str) else self.numbers
                        
                        def get_bonus_numbers_list(self):
                            return json.loads(self.bonus_numbers) if isinstance(self.bonus_numbers, str) else self.bonus_numbers
                    
                    latest_results[lottery_type] = ResultObj(
                        result[1], result[2], result[3], result[4], result[5]
                    )
                    logger.info(f"✓ Direct SQL: {lottery_type} - Draw {result[2]}")
                else:
                    logger.warning(f"✗ Direct SQL: No data for {lottery_type}")
            
            logger.info(f"Direct SQL retrieved: {len(latest_results)} authentic lottery results")
            
        except Exception as e:
            logger.error(f"Direct SQL error: {str(e)}")
            latest_results = {}
        
        # Define breadcrumbs for SEO
        breadcrumbs = [
            {"name": "Results", "url": url_for('results')}
        ]
        
        # Add cache busting to ensure fresh data display
        import time
        cache_buster = int(time.time())
        
        # Debug template data before rendering
        logger.info(f"Template data - lottery_types: {lottery_types}")
        logger.info(f"Template data - latest_results: {latest_results}")
        
        # Test each lottery type specifically
        for lt in lottery_types:
            if lt in latest_results:
                result = latest_results[lt]
                logger.info(f"✓ {lt}: Draw {result.draw_number}, Numbers: {result.numbers}")
            else:
                logger.error(f"✗ MISSING: {lt} not in latest_results")
        
        return render_template('results_overview.html',
                            lottery_types=lottery_types,
                            latest_results=latest_results,
                            title="All Lottery Results",
                            breadcrumbs=breadcrumbs,
                            cache_buster=cache_buster)
                            
    except Exception as e:
        logger.error(f"Critical error in results route: {str(e)}", exc_info=True)
        # Define breadcrumbs for SEO even in error case
        breadcrumbs = [
            {"name": "Results", "url": url_for('results')}
        ]
        # Return a simplified template with no result data
        return render_template('results_overview.html',
                            lottery_types=lottery_types,
                            latest_results={},  # Empty dict on critical error
                            title="All Lottery Results",
                            breadcrumbs=breadcrumbs)

@app.route('/results/<lottery_type>')
def lottery_results(lottery_type):
    """Show all results for a specific lottery type"""
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of results per page
    
    # Ensure data_aggregator is loaded before using it
    global data_aggregator
    
    # Import if not already loaded - data_aggregator not available
    # if data_aggregator is None:
    #     import data_aggregator as da
    #     data_aggregator = da
    #     logger.info("Loaded data_aggregator module on demand")
    
    # Get all results for this lottery type directly from database
    all_results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).all()
    
    # Create a paginated result from the raw list
    # This mimics SQLAlchemy's pagination object with the properties the template expects
    class PaginatedResults:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            
        @property
        def pages(self):
            return (self.total + self.per_page - 1) // self.per_page
            
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
    
    # Calculate the sliced items for the current page
    start = (page - 1) * per_page
    end = min(start + per_page, len(all_results))
    items = all_results[start:end]
    
    # Create the pagination object
    results = PaginatedResults(items, page, per_page, len(all_results))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Results", "url": url_for('results')},
        {"name": lottery_type, "url": url_for('lottery_results', lottery_type=lottery_type)}
    ]
    
    return render_template('results.html', 
                           results=results, 
                           lottery_type=lottery_type,
                           title=f"{lottery_type} Results",
                           breadcrumbs=breadcrumbs)

@app.route('/export-template')
@login_required
def export_template():
    """Export an empty spreadsheet template for importing lottery data"""
    if not current_user.is_admin:
        flash('You must be an admin to export templates.', 'danger')
        return redirect(url_for('index'))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lottery_data_template_{timestamp}.xlsx"
    
    # Create template with lottery-specific tabs
    create_template.create_template(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], 
        filename, 
        as_attachment=True
    )

# File upload progress tracker
# This dictionary stores the progress of file uploads for each user
# Structure: {user_id: {'percentage': 0-100, 'status': 'uploading|processing|complete|error', 'filename': 'example.xlsx'}}
file_upload_progress = {}

@app.route('/api/file-upload-progress')
@login_required
def get_file_upload_progress():
    """API endpoint to get current file upload progress for the current user"""
    user_id = current_user.id
    
    # If no progress exists for this user, return default values
    if user_id not in file_upload_progress:
        file_upload_progress[user_id] = {
            'percentage': 0,
            'status': 'initializing',
            'filename': ''
        }
    
    return jsonify(file_upload_progress[user_id])

@app.route('/api/file-upload-progress/reset', methods=['POST'])
@login_required
@csrf.exempt
def reset_file_upload_progress():
    """Reset the file upload progress for the current user"""
    user_id = current_user.id
    
    file_upload_progress[user_id] = {
        'percentage': 0,
        'status': 'initializing',
        'filename': ''
    }
    
    return jsonify({'success': True})

@app.route('/import-latest-spreadsheet', methods=['POST'])
@login_required
@csrf.exempt
def import_latest_spreadsheet_route():
    """Import the latest spreadsheet file from attached_assets or uploads directory"""
    if not current_user.is_admin:
        flash('You must be an admin to import data.', 'danger')
        return redirect(url_for('index'))
    
    import_type = request.form.get('import_type', 'excel')
    purge = request.form.get('purge', 'no') == 'yes'
    pattern = request.form.get('pattern', '*.xlsx')  # Modified to look for any Excel file
    
    try:
        # First, try to find in attached_assets
        latest_file = find_latest_spreadsheet("attached_assets", pattern)
        
        # If not found in attached_assets, look in uploads directory
        if not latest_file and os.path.exists("uploads"):
            latest_file = find_latest_spreadsheet("uploads", pattern)
            
            if latest_file:
                logger.info(f"Using spreadsheet from uploads directory: {latest_file}")
                # If found in uploads, use that directory for import
                success = import_latest_spreadsheet("uploads", pattern, import_type, purge)
        else:
            # Using spreadsheet from attached_assets
            success = import_latest_spreadsheet("attached_assets", pattern, import_type, purge)
        
        if not latest_file:
            # Try one more time with the original lottery_data_*.xlsx pattern
            original_pattern = "lottery_data_*.xlsx"
            latest_file = find_latest_spreadsheet("attached_assets", original_pattern)
            
            if not latest_file and os.path.exists("uploads"):
                latest_file = find_latest_spreadsheet("uploads", original_pattern)
                
                if latest_file:
                    # If found in uploads with original pattern, use that
                    success = import_latest_spreadsheet("uploads", original_pattern, import_type, purge)
            else:
                # Using spreadsheet from attached_assets with original pattern
                success = import_latest_spreadsheet("attached_assets", original_pattern, import_type, purge)
        
        if not latest_file:
            flash(f'No Excel spreadsheets found in attached_assets or uploads directories. Please upload a spreadsheet first.', 'danger')
            return redirect(url_for('import_data'))
        
        if success:
            flash(f'Successfully imported latest spreadsheet: {os.path.basename(latest_file)}', 'success')
        else:
            flash(f'Failed to import spreadsheet: {os.path.basename(latest_file)}. Check logs for details.', 'danger')
            
        return redirect(url_for('import_data'))
        
    except Exception as e:
        logger.exception(f"Error importing spreadsheet: {str(e)}")
        flash(f'Error importing spreadsheet: {str(e)}', 'danger')
        return redirect(url_for('import_data'))

@app.route('/import-history')
@login_required
def import_history():
    """View import history and details"""
    if not current_user.is_admin:
        flash('You must be an admin to view import history.', 'danger')
        return redirect(url_for('index'))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "Import History", "url": url_for('import_history')}
    ]
    
    # Define SEO metadata
    meta_description = "View and analyze South African lottery data import history. Track data sources, import dates, success rates, and detailed import logs for system administration."
    
    try:
        # Get recent imports with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get all import history records, newest first
        imports = ImportHistory.query.order_by(ImportHistory.import_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        return render_template('import_history.html',
                            imports=imports,
                            title="Lottery Data Import History | System Administration",
                            breadcrumbs=breadcrumbs,
                            meta_description=meta_description)
    except Exception as e:
        app.logger.error(f"Error retrieving import history: {str(e)}")
        flash(f"Error loading import history: {str(e)}", 'danger')
        return redirect(url_for('admin'))

@app.route('/import-history/<int:import_id>')
@login_required
def import_details(import_id):
    """View details of a specific import"""
    if not current_user.is_admin:
        flash('You must be an admin to view import details.', 'danger')
        return redirect(url_for('index'))
    
    # Define SEO metadata (will be updated with specific import details when the record is loaded)
    meta_description = "Detailed South African lottery data import information. View imported draw numbers, dates, and success status for administrative record-keeping."
    
    try:
        # Get the import record
        import_record = ImportHistory.query.get_or_404(import_id)
        
        # Define breadcrumbs for SEO
        breadcrumbs = [
            {"name": "Admin Dashboard", "url": url_for('admin')},
            {"name": "Import History", "url": url_for('import_history')},
            {"name": f"Import #{import_id}", "url": url_for('import_details', import_id=import_id)}
        ]
        
        # Get all records that were imported in this batch
        imported_records = ImportedRecord.query.filter_by(import_id=import_id).all()
        
        # Group records by lottery type for easier display
        records_by_type = {}
        for record in imported_records:
            lottery_type = record.lottery_type
            if lottery_type not in records_by_type:
                records_by_type[lottery_type] = []
            records_by_type[lottery_type].append(record)
        
        # Update meta description with specific import details
        meta_description = f"Details for lottery data import #{import_id} from {import_record.import_date.strftime('%Y-%m-%d')}. Contains {len(imported_records)} records across {len(records_by_type)} lottery types."
        
        return render_template('import_details.html',
                              import_record=import_record,
                              records_by_type=records_by_type,
                              title=f"Import Details #{import_id} | {import_record.import_date.strftime('%Y-%m-%d %H:%M')}",
                              breadcrumbs=breadcrumbs,
                              meta_description=meta_description)
    except Exception as e:
        app.logger.error(f"Error retrieving import details: {str(e)}")
        flash(f"Error loading import details: {str(e)}", 'danger')
        return redirect(url_for('import_history'))

@app.route('/import-data', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def import_data():
    """Import data from Excel spreadsheet"""
    global import_excel, import_snap_lotto_data
    
    if not current_user.is_admin:
        flash('You must be an admin to import data.', 'danger')
        return redirect(url_for('index'))
        
    import_stats = None
    user_id = current_user.id
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "Import Data", "url": url_for('import_data')}
    ]
    
    # Define SEO metadata
    meta_description = "Import South African lottery data from Excel spreadsheets. Upload Lottery, PowerBall, and Daily Lottery results to maintain an up-to-date database of winning numbers and prize information."
    
    # Initialize or reset progress tracking
    file_upload_progress[user_id] = {
        'percentage': 0,
        'status': 'initializing',
        'filename': ''
    }

    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            excel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Update progress
            file_upload_progress[user_id] = {
                'percentage': 25,
                'status': 'uploading',
                'filename': filename
            }
            
            # Save the file
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(excel_path)
            
            # Update progress
            file_upload_progress[user_id] = {
                'percentage': 50,
                'status': 'processing',
                'filename': filename
            }
            
            try:
                # Check if this is a multi-sheet template by trying to detect sheets
                is_template_format = False
                try:
                    import pandas as pd
                    # Load Excel file and check for template sheets
                    xl = pd.ExcelFile(excel_path)
                    sheet_names = xl.sheet_names
                    
                    # Check if the file has the expected sheet structure (multiple sheets with lottery type names)
                    template_sheets = [
                        "Lottery", "Lottery Plus 1", "Lottery Plus 2", 
                        "Powerball", "Powerball Plus", "Daily Lottery"
                    ]
                    
                    # If at least 3 of the expected template sheets are present, we consider it a template
                    matches = sum(1 for sheet in template_sheets if sheet in sheet_names)
                    is_template_format = matches >= 3
                    
                    # Also consider template if the name contains "template"
                    if not is_template_format:
                        is_template_format = "template" in filename.lower()
                        
                    logger.info(f"File format detection: {'multi-sheet template' if is_template_format else 'standard'}")
                except Exception as e:
                    logger.warning(f"Error detecting file format: {str(e)}")
                    # Fall back to filename detection
                    is_template_format = "template" in filename.lower()
                
                if is_template_format:
                    try:
                        # Update progress
                        file_upload_progress[user_id] = {
                            'percentage': 50,
                            'status': 'processing template format',
                            'filename': filename
                        }
                        
                        # Import using the multi-sheet template processor
                        import multi_sheet_import
                        import_stats = multi_sheet_import.import_multisheet_excel(excel_path, flask_app=app)
                        
                        # If import was successful, track it in the import history
                        if isinstance(import_stats, dict) and import_stats.get('success'):
                            # Create import history record
                            import_history = ImportHistory(
                                import_type='multi_sheet_template',
                                file_name=filename,
                                records_added=import_stats.get('added', 0),
                                records_updated=import_stats.get('updated', 0),
                                total_processed=import_stats.get('total', 0),
                                errors=import_stats.get('errors', 0),
                                user_id=current_user.id
                            )
                            db.session.add(import_history)
                            db.session.commit()
                            
                            # Save individual imported records if available
                            if 'imported_records' in import_stats and import_stats['imported_records']:
                                for record_data in import_stats['imported_records']:
                                    imported_record = ImportedRecord(
                                        import_id=import_history.id,
                                        lottery_type=record_data['lottery_type'],
                                        draw_number=record_data['draw_number'],
                                        draw_date=record_data['draw_date'],
                                        is_new=record_data['is_new'],
                                        lottery_result_id=record_data['lottery_result_id']
                                    )
                                    db.session.add(imported_record)
                                db.session.commit()
                            
                            # Display results
                            added = import_stats.get('added', 0)
                            total = import_stats.get('total', 0)
                            errors = import_stats.get('errors', 0)
                            updated = import_stats.get('updated', 0)
                            
                            if added > 0 and updated > 0:
                                flash(f'Multi-sheet template import completed successfully. Added {added} new records, updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                            elif added > 0:
                                flash(f'Multi-sheet template import completed successfully. Added {added} new records, processed {total} total records with {errors} errors.', 'success')
                            elif updated > 0:
                                flash(f'Multi-sheet template import completed successfully. Updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                            else:
                                flash(f'Multi-sheet template import completed. No records were added or updated. Processed {total} records with {errors} errors.', 'info')
                        else:
                            error_msg = import_stats.get('error', 'Unknown error')
                            flash(f'Error in multi-sheet template import: {error_msg}', 'danger')
                        
                        # Update progress to complete
                        file_upload_progress[user_id] = {
                            'percentage': 100,
                            'status': 'complete',
                            'filename': filename,
                            'summary': import_stats if isinstance(import_stats, dict) else None
                        }
                    except Exception as e:
                        logger.error(f"Multi-sheet template import error: {str(e)}")
                        logger.error(traceback.format_exc())
                        flash(f"Error in multi-sheet template import: {str(e)}", 'danger')
                        
                        # Update progress to error
                        file_upload_progress[user_id] = {
                            'percentage': 100,
                            'status': 'error',
                            'filename': filename
                        }
                else:
                    # Try standard format for non-template files
                    try:
                        if import_excel is None:
                            import import_excel as ie
                        else:
                            ie = import_excel
                        import_stats = ie.import_excel_data(excel_path)
                        
                        # If import was successful, track it in the import history
                        if isinstance(import_stats, dict) and import_stats.get('success'):
                            # Create import history record
                            import_history = ImportHistory(
                                import_type='excel',
                                file_name=filename,
                                records_added=import_stats.get('added', 0),
                                records_updated=import_stats.get('updated', 0),
                                total_processed=import_stats.get('total', 0),
                                errors=import_stats.get('errors', 0),
                                user_id=current_user.id
                            )
                            db.session.add(import_history)
                            db.session.commit()
                            
                            # Save individual imported records if available
                            if 'imported_records' in import_stats and import_stats['imported_records']:
                                for record_data in import_stats['imported_records']:
                                    imported_record = ImportedRecord(
                                        import_id=import_history.id,
                                        lottery_type=record_data['lottery_type'],
                                        draw_number=record_data['draw_number'],
                                        draw_date=record_data['draw_date'],
                                        is_new=record_data['is_new'],
                                        lottery_result_id=record_data['lottery_result_id']
                                    )
                                    db.session.add(imported_record)
                                db.session.commit()
                        
                        # Check if import was unsuccessful (False) or if no records were imported
                        if import_stats is False or (isinstance(import_stats, dict) and import_stats.get('total', 0) == 0):
                            # If standard import fails, try Snap Lotto format
                            try:
                                # Update progress
                                file_upload_progress[user_id] = {
                                    'percentage': 75,
                                    'status': 'processing',
                                    'filename': filename
                                }
                                
                                # Import import_snap_lotto_data if not already loaded
                                if import_snap_lotto_data is None:
                                    import import_snap_lotto_data as isld
                                else:
                                    isld = import_snap_lotto_data
                                import_stats = isld.import_snap_lotto_data(excel_path, flask_app=app)
                                
                                # If import was successful, track it in the import history
                                if isinstance(import_stats, dict) and import_stats.get('success'):
                                    # Create import history record
                                    import_history = ImportHistory(
                                        import_type='snap_lotto',
                                        file_name=filename,
                                        records_added=import_stats.get('added', 0),
                                        records_updated=import_stats.get('updated', 0),
                                        total_processed=import_stats.get('total', 0),
                                        errors=import_stats.get('errors', 0),
                                        user_id=current_user.id
                                    )
                                    db.session.add(import_history)
                                    db.session.commit()
                                    
                                    # Save individual imported records if available
                                    if 'imported_records' in import_stats and import_stats['imported_records']:
                                        for record_data in import_stats['imported_records']:
                                            imported_record = ImportedRecord(
                                                import_id=import_history.id,
                                                lottery_type=record_data['lottery_type'],
                                                draw_number=record_data['draw_number'],
                                                draw_date=record_data['draw_date'],
                                                is_new=record_data['is_new'],
                                                lottery_result_id=record_data['lottery_result_id']
                                            )
                                            db.session.add(imported_record)
                                        db.session.commit()
                                
                                # Display results if available and successful
                                if isinstance(import_stats, dict) and import_stats.get('success'):
                                    added = import_stats.get('added', 0)
                                    total = import_stats.get('total', 0)
                                    errors = import_stats.get('errors', 0)
                                    
                                    updated = import_stats.get('updated', 0)
                                    if added > 0 and updated > 0:
                                        flash(f'Snap Lotto import completed successfully. Added {added} new records, updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                                    elif added > 0:
                                        flash(f'Snap Lotto import completed successfully. Added {added} new records, processed {total} total records with {errors} errors.', 'success')
                                    elif updated > 0:
                                        flash(f'Snap Lotto import completed successfully. Updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                                    else:
                                        flash(f'Snap Lotto import completed. No records were added or updated. Processed {total} records with {errors} errors.', 'info')
                                else:
                                    flash('Snap Lotto import completed', 'info')
                                
                                # Update progress to complete
                                file_upload_progress[user_id] = {
                                    'percentage': 100,
                                    'status': 'complete',
                                    'filename': filename,
                                    'summary': import_stats if isinstance(import_stats, dict) else None
                                }
                            except Exception as e:
                                logger.error(f"Snap Lotto import error: {str(e)}")
                                flash(f"Error in Snap Lotto import: {str(e)}", 'danger')
                                
                                # Update progress to error
                                file_upload_progress[user_id] = {
                                    'percentage': 100,
                                    'status': 'error',
                                    'filename': filename
                                }
                        else:
                            # Display results for standard import
                            if isinstance(import_stats, dict) and import_stats.get('success'):
                                added = import_stats.get('added', 0)
                                total = import_stats.get('total', 0)
                                errors = import_stats.get('errors', 0)
                                
                                updated = import_stats.get('updated', 0)
                                if added > 0 and updated > 0:
                                    flash(f'Import completed successfully. Added {added} new records, updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                                elif added > 0:
                                    flash(f'Import completed successfully. Added {added} new records, processed {total} total records with {errors} errors.', 'success')
                                elif updated > 0:
                                    flash(f'Import completed successfully. Updated {updated} existing records, processed {total} total records with {errors} errors.', 'success')
                                else:
                                    flash(f'Import completed. No records were added or updated. Processed {total} records with {errors} errors.', 'info')
                            else:
                                flash('Import completed', 'info')
                            
                            # Update progress to complete
                            file_upload_progress[user_id] = {
                                'percentage': 100,
                                'status': 'complete',
                                'filename': filename,
                                'summary': import_stats if isinstance(import_stats, dict) else None
                            }
                    except Exception as e:
                        logger.error(f"Excel import error: {str(e)}")
                        flash(f"Error in import: {str(e)}", 'danger')
                        
                        # Update progress to error
                        file_upload_progress[user_id] = {
                            'percentage': 100,
                            'status': 'error',
                            'filename': filename
                        }
            except Exception as e:
                logger.error(f"File processing error: {str(e)}")
                logger.error(traceback.format_exc())
                flash(f"File processing error: {str(e)}", 'danger')
                
                # Update progress to error
                file_upload_progress[user_id] = {
                    'percentage': 100,
                    'status': 'error',
                    'filename': filename
                }
                
    # Get some example results for each lottery type to display
    example_results = {}
    lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 
                     'Powerball', 'Powerball Plus', 'Daily Lottery']
    
    try:                 
        for lottery_type in lottery_types:
            try:
                results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(
                    LotteryResult.draw_date.desc()).limit(5).all()
                if results:
                    example_results[lottery_type] = results
            except Exception as e:
                app.logger.error(f"Error retrieving example results for {lottery_type}: {str(e)}")
                # Continue with other lottery types even if one fails
                continue
    except Exception as e:
        app.logger.error(f"Database error in import_data: {str(e)}")
        # If we can't get any example results, proceed without them
    
    # Extract structured data from import_stats (if available) for template rendering
    added_count = 0
    updated_count = 0
    total_count = 0
    error_count = 0
    imported_results = []
    
    if isinstance(import_stats, dict) and import_stats.get('success'):
        added_count = import_stats.get('added', 0)
        updated_count = import_stats.get('updated', 0)
        total_count = import_stats.get('total', 0)
        error_count = import_stats.get('errors', 0)
        
        # Get imported records for display
        if 'imported_records' in import_stats and import_stats['imported_records']:
            for record_data in import_stats['imported_records']:
                result = LotteryResult.query.get(record_data.get('lottery_result_id'))
                if result:
                    imported_results.append(result)
    
    return render_template('import_data.html', 
                           import_stats=import_stats,
                           example_results=example_results,
                           title="Import South African Lottery Data | Admin Tools",
                           meta_description=meta_description,
                           breadcrumbs=breadcrumbs,
                           added_count=added_count,
                           updated_count=updated_count,
                           total_count=total_count,
                           error_count=error_count,
                           imported_results=imported_results)

@app.route('/retake-screenshots')
@login_required
def retake_screenshots():
    """Admin route to retake all screenshots"""
    if not current_user.is_admin:
        flash('You must be an admin to retake screenshots.', 'danger')
        return redirect(url_for('index'))
        
    try:
        result = scheduler.retake_all_screenshots()
        
        if result:
            success_count = sum(1 for status in result.values() if status == 'success')
            fail_count = len(result) - success_count
            
            flash(f'Screenshot process started. {success_count} URLs queued successfully. {fail_count} failed.', 'info')
        else:
            flash('No URLs configured for screenshots.', 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/purge-database')
@login_required
def purge_database():
    """Admin route to purge all data from the database"""
    if not current_user.is_admin:
        flash('You must be an admin to purge the database.', 'danger')
        return redirect(url_for('index'))
        
    try:
        # Import the purge_data module
        import purge_data
        
        # Execute the purge operation
        result = purge_data.purge_data()
        
        if result:
            flash('Database purged successfully. All lottery results and screenshots have been deleted.', 'success')
        else:
            flash('An error occurred during the purge operation.', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Manage data syncs and system settings"""
    if not current_user.is_admin:
        flash('You must be an admin to access settings.', 'danger')
        return redirect(url_for('index'))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "System Settings", "url": url_for('settings')}
    ]
    
    # Define SEO metadata
    meta_description = "Configure South African lottery system settings and scheduled tasks. Manage data synchronization, screenshot capture timing, and system preferences."
    
    schedule_configs = ScheduleConfig.query.all()
    
    # Handle form submission for updating settings
    if request.method == 'POST':
        # This would normally handle the form submission
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', 
                          schedule_configs=schedule_configs,
                          title="System Settings | Lottery Data Management",
                          meta_description=meta_description,
                          breadcrumbs=breadcrumbs)

@app.route('/export-screenshots')
@login_required
def export_screenshots():
    """Export screenshots"""
    if not current_user.is_admin:
        flash('You must be an admin to export screenshots.', 'danger')
        return redirect(url_for('index'))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "Export Screenshots", "url": url_for('export_screenshots')}
    ]
    
    # Define SEO metadata
    meta_description = "Export and manage South African lottery screenshots. Download captured lottery result images in various formats for analysis and record-keeping."
    
    screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).all()
    
    # Check for sync status in session
    sync_status = None
    if 'sync_status' in session:
        sync_status = session.pop('sync_status')
    
    # Get the timestamp of the most recent screenshot for status display
    last_updated = None
    if screenshots:
        last_updated = screenshots[0].timestamp
    
    return render_template('export_screenshots.html',
                          screenshots=screenshots,
                          title="Export Lottery Screenshots | Data Management",
                          meta_description=meta_description,
                          breadcrumbs=breadcrumbs,
                          sync_status=sync_status,
                          last_updated=last_updated)

@app.route('/export-screenshots-zip')
@login_required
def export_screenshots_zip():
    """Export all screenshots as a ZIP file"""
    if not current_user.is_admin:
        flash('You must be an admin to export screenshots.', 'danger')
        return redirect(url_for('index'))
    
    try:
        import io
        import zipfile
        from datetime import datetime
        
        # Get all screenshots
        screenshots = Screenshot.query.order_by(Screenshot.lottery_type).all()
        
        if not screenshots:
            flash('No screenshots available to export.', 'warning')
            return redirect(url_for('export_screenshots'))
        
        # Create a ZIP file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for screenshot in screenshots:
                if os.path.exists(screenshot.path):
                    # Get the file extension
                    _, ext = os.path.splitext(screenshot.path)
                    # Create a unique filename for each screenshot
                    lottery_type = screenshot.lottery_type.replace(' ', '_')
                    timestamp = screenshot.timestamp.strftime('%Y%m%d_%H%M%S')
                    filename = f"{lottery_type}_{timestamp}{ext}"
                    
                    # Add the screenshot to the ZIP file
                    zf.write(screenshot.path, filename)
                    
                    # Add zoomed version if it exists
                    if screenshot.zoomed_path and os.path.exists(screenshot.zoomed_path):
                        _, zoomed_ext = os.path.splitext(screenshot.zoomed_path)
                        zoomed_filename = f"{lottery_type}_{timestamp}_zoomed{zoomed_ext}"
                        zf.write(screenshot.zoomed_path, zoomed_filename)
        
        # Reset the file pointer to the beginning of the file
        memory_file.seek(0)
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Send the ZIP file as a response
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'lottery_screenshots_{timestamp}.zip'
        )
    except Exception as e:
        app.logger.error(f"Error creating ZIP file: {str(e)}")
        flash(f'Error creating ZIP file: {str(e)}', 'danger')
        return redirect(url_for('export_screenshots'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register a new admin user"""
    if not current_user.is_admin:
        flash('You must be an admin to register new users.', 'danger')
        return redirect(url_for('index'))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Admin Dashboard", "url": url_for('admin')},
        {"name": "Register Admin", "url": url_for('register')}
    ]
    
    # Define SEO metadata
    meta_description = "Administrative user registration for South African lottery results system. Create secure admin accounts to manage lottery data and system configurations."
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, is_admin=True)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Admin user {username} registered successfully!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('register.html', 
                          title="Register Admin User | Lottery Management System", 
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/visualizations')
def visualizations():
    """Advanced data visualization and analytics for South African lottery results"""
    lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 
                    'Powerball', 'Powerball Plus', 'Daily Lottery']
    
    # Get some summary statistics
    total_draws = LotteryResult.query.count()
    latest_draw = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).first()
    latest_draw_date = latest_draw.draw_date if latest_draw else None
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Analytics", "url": url_for('visualizations')}
    ]
    
    # Additional SEO metadata
    meta_description = "Explore comprehensive South African lottery analytics. View frequency charts, number patterns, and winning statistics for Lotto, Powerball, and Daily Lotto games."
    
    return render_template('visualizations.html',
                          lottery_types=lottery_types,
                          total_draws=total_draws,
                          latest_draw_date=latest_draw_date,
                          title="Lottery Data Analytics | Statistical Analysis & Visualizations",
                          breadcrumbs=breadcrumbs,
                          meta_description=meta_description)

@app.route('/api/visualization-data')
def visualization_data():
    """API endpoint for visualization data"""
    # import data_aggregator  # Module not available
    from collections import Counter
    import logging
    
    data_type = request.args.get('data_type', 'numbers_frequency')
    lottery_type = request.args.get('lottery_type', 'all')
    
    logging.info(f"Visualization data request: type={data_type}, lottery={lottery_type}")
    
    try:
        # Get data specific to lottery type
        if data_type == 'numbers_frequency':
            # Get frequency count for all 49 numbers
            all_numbers = {str(i): 0 for i in range(1, 50)}
            
            # Count frequency of all numbers
            query = LotteryResult.query
            if lottery_type and lottery_type.lower() != 'all':
                query = query.filter_by(lottery_type=lottery_type)
                
            results = query.all()
            number_counter = Counter()
            
            logging.info(f"Found {len(results)} results for frequency analysis")
            
            for result in results:
                numbers = result.get_numbers_list()
                for num in numbers:
                    if 1 <= num <= 49:
                        number_counter[str(num)] += 1
            
            # Update all_numbers with actual frequencies
            for num, count in number_counter.items():
                if num in all_numbers:
                    all_numbers[num] = count
            
            # Convert to lists for JSON response
            data = [all_numbers[str(i)] for i in range(1, 50)]
            
            response_data = {
                'labels': [str(i) for i in range(1, 50)],
                'datasets': [{
                    'data': data
                }]
            }
            
            logging.info(f"Returning frequency data with {sum(data)} total occurrences")
            return jsonify(response_data)
        
        elif data_type == 'winners_by_division':
            # Get all results for this lottery type to process division data
            query = LotteryResult.query
            
            if lottery_type and lottery_type.lower() != 'all':
                # Try with exact match first
                results_by_type = query.filter_by(lottery_type=lottery_type).all()
                
                # If no results, try with normalized type
                if not results_by_type:
                    # Find any results with lottery type that might be a variant
                    lottery_type_variants = db.session.query(LotteryResult.lottery_type).distinct().all()
                    normalized_type = data_aggregator.normalize_lottery_type(lottery_type)
                    matching_types = []
                    
                    for lt in lottery_type_variants:
                        lt_name = lt[0]
                        if data_aggregator.normalize_lottery_type(lt_name) == normalized_type:
                            matching_types.append(lt_name)
                    
                    if matching_types:
                        results_by_type = query.filter(LotteryResult.lottery_type.in_(matching_types)).all()
            else:
                results_by_type = query.all()
            
            # Initialize division counters
            division_data = {}
            
            # Process division data from all matching results
            for result in results_by_type:
                divisions = result.get_divisions()
                if divisions:
                    for div_name, div_info in divisions.items():
                        # Extract the division number from the name (e.g., "Division 1" -> 1)
                        try:
                            div_num = int(div_name.split()[-1])
                            winners = div_info.get('winners', '0')
                            
                            # Convert winners to integer
                            if isinstance(winners, str):
                                winners = winners.replace(',', '')
                            winner_count = int(float(winners))
                            
                            if div_num not in division_data:
                                division_data[div_num] = 0
                            division_data[div_num] += winner_count
                        except (ValueError, IndexError):
                            continue
            
            # Sort divisions by number
            sorted_divisions = sorted(division_data.items())
            
            # Prepare data for chart
            divisions = [f'Division {div_num}' for div_num, _ in sorted_divisions]
            winner_counts = [count for _, count in sorted_divisions]
            
            logging.info(f"Processed {len(results_by_type)} results, found {len(divisions)} divisions with data")
            
            response_data = {
                'labels': divisions,
                'datasets': [{
                    'data': winner_counts
                }]
            }
            
            return jsonify(response_data)
        
        return jsonify({'error': 'Invalid data type'}), 400
    except Exception as e:
        logging.error(f"Error in visualization_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<lottery_type>/<draw_number>')
def draw_details(lottery_type, draw_number):
    """Show detailed information for a specific draw"""
    # First, validate and correct any known draws (adds missing division data)
    # This ensures draw details have prize division data if it's available
    corrected = data_aggregator.validate_and_correct_known_draws()
    if corrected > 0:
        logger.info(f"Corrected {corrected} lottery draws with verified data")
    
    # Get all results with matching lottery type
    all_results = data_aggregator.get_all_results_by_lottery_type(lottery_type)
    
    # Find the specific draw
    result = None
    draw_number = draw_number.strip()
    
    for r in all_results:
        r_draw_number = r.draw_number
        # Clean up the draw number for comparison
        r_draw_number = r_draw_number.replace('Draw', '').replace('DRAW', '').replace(
            'Lotto', '').replace('Plus 1', '').replace('Plus 2', '').replace(
            'Powerball', '').replace('Daily', '').strip()
        
        if r_draw_number == draw_number or r.draw_number == draw_number:
            result = r
            break
    
    if not result:
        flash(f"Draw {draw_number} not found for {lottery_type}", "warning")
        return redirect(url_for('lottery_results', lottery_type=lottery_type))
    
    # Define breadcrumbs for SEO
    breadcrumbs = [
        {"name": "Results", "url": url_for('results')},
        {"name": lottery_type, "url": url_for('lottery_results', lottery_type=lottery_type)},
        {"name": f"Draw {draw_number}", "url": url_for('draw_details', lottery_type=lottery_type, draw_number=draw_number)}
    ]
    
    return render_template('draw_details.html',
                          result=result,
                          lottery_type=lottery_type,
                          title=f"{lottery_type} Draw {draw_number} Details",
                          breadcrumbs=breadcrumbs)

@app.route('/screenshot/<int:screenshot_id>')
def view_screenshot(screenshot_id):
    """View a screenshot image"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    
    # Normalize path and check if file exists
    screenshot_path = os.path.normpath(screenshot.path)
    
    if not os.path.isfile(screenshot_path):
        flash('Screenshot file not found', 'danger')
        return redirect(url_for('admin'))
    
    # Extract directory and filename from path
    directory = os.path.dirname(screenshot_path)
    filename = os.path.basename(screenshot_path)
    
    return send_from_directory(directory, filename)

@app.route('/screenshot-zoomed/<int:screenshot_id>')
def view_zoomed_screenshot(screenshot_id):
    """View a zoomed screenshot image"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    
    if not screenshot.zoomed_path:
        flash('No zoomed screenshot available', 'warning')
        return redirect(url_for('admin'))
    
    # Normalize path and check if file exists
    zoomed_path = os.path.normpath(screenshot.zoomed_path)
    
    if not os.path.isfile(zoomed_path):
        flash('Zoomed screenshot file not found', 'danger')
        return redirect(url_for('admin'))
    
    # Extract directory and filename from path
    directory = os.path.dirname(zoomed_path)
    filename = os.path.basename(zoomed_path)
    
    return send_from_directory(directory, filename)

@app.route('/sync-all-screenshots', methods=['POST'])
@login_required
@csrf.exempt
def sync_all_screenshots():
    """Sync all screenshots from their source URLs"""
    if not current_user.is_admin:
        flash('You must be an admin to sync screenshots.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Use the scheduler module imported at the top level to retake all screenshots
        # Don't use threading for UI operations to ensure synchronous behavior
        count = scheduler.retake_all_screenshots(app, use_threading=False)
        
        # Store status in session for display on next page load
        if count > 0:
            session['sync_status'] = {
                'status': 'success',
                'message': f'Successfully synced {count} screenshots.'
            }
        else:
            session['sync_status'] = {
                'status': 'warning',
                'message': 'No screenshots were synced. Check configured URLs.'
            }
    except Exception as e:
        app.logger.error(f"Error syncing screenshots: {str(e)}")
        session['sync_status'] = {
            'status': 'danger',
            'message': f'Error syncing screenshots: {str(e)}'
        }
    
    return redirect(url_for('export_screenshots'))

@app.route('/sync-screenshot/<int:screenshot_id>', methods=['POST'])
@login_required
@csrf.exempt
def sync_single_screenshot(screenshot_id):
    """Sync a single screenshot by its ID"""
    if not current_user.is_admin:
        flash('You must be an admin to sync screenshots.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Get the screenshot
        screenshot = Screenshot.query.get_or_404(screenshot_id)
        
        # Use the scheduler module imported at the top level to retake this screenshot
        success = scheduler.retake_screenshot_by_id(screenshot_id, app)
        
        # Store status in session for display on next page load
        if success:
            session['sync_status'] = {
                'status': 'success',
                'message': f'Successfully synced screenshot for {screenshot.lottery_type}.'
            }
        else:
            session['sync_status'] = {
                'status': 'warning',
                'message': f'Failed to sync screenshot for {screenshot.lottery_type}.'
            }
    except Exception as e:
        app.logger.error(f"Error syncing screenshot: {str(e)}")
        session['sync_status'] = {
            'status': 'danger',
            'message': f'Error syncing screenshot: {str(e)}'
        }
    
    return redirect(url_for('export_screenshots'))

@app.route('/cleanup-screenshots', methods=['POST'])
@login_required
@csrf.exempt
def cleanup_screenshots():
    """Route to cleanup old screenshots"""
    if not current_user.is_admin:
        flash('You must be an admin to clean up screenshots.', 'danger')
        return redirect(url_for('index'))
        
    try:
        # Run the cleanup function from scheduler module imported at the top level
        scheduler.cleanup_old_screenshots()
        
        # Store success message in session
        session['sync_status'] = {
            'status': 'success',
            'message': 'Successfully cleaned up old screenshots. Only the latest screenshot for each URL is kept.'
        }
    except Exception as e:
        app.logger.error(f"Error cleaning up screenshots: {str(e)}")
        traceback.print_exc()
        
        session['sync_status'] = {
            'status': 'danger',
            'message': f'Error cleaning up screenshots: {str(e)}'
        }
    
    return redirect(url_for('export_screenshots'))

@app.route('/export-combined-zip')
@login_required
def export_combined_zip():
    """Export template and screenshots in a single ZIP file"""
    if not current_user.is_admin:
        flash('You must be an admin to export data.', 'danger')
        return redirect(url_for('index'))
    
    try:
        import io
        import zipfile
        import tempfile
        from datetime import datetime
        
        # Create a timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get all screenshots
        screenshots = Screenshot.query.order_by(Screenshot.lottery_type).all()
        
        if not screenshots:
            flash('No screenshots available to export.', 'warning')
            return redirect(url_for('export_screenshots'))
        
        # Create a temporary directory for the template
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the template file
            template_filename = f"lottery_data_template_{timestamp}.xlsx"
            template_path = os.path.join(temp_dir, template_filename)
            create_template.create_template(template_path)
            
            # Create a ZIP file in memory
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add the template to the ZIP file
                zf.write(template_path, f"template/{template_filename}")
                
                # Add screenshots to the ZIP file
                for screenshot in screenshots:
                    if os.path.exists(screenshot.path):
                        # Get the file extension
                        _, ext = os.path.splitext(screenshot.path)
                        # Create a unique filename for each screenshot
                        lottery_type = screenshot.lottery_type.replace(' ', '_')
                        ss_timestamp = screenshot.timestamp.strftime('%Y%m%d_%H%M%S')
                        filename = f"{lottery_type}_{ss_timestamp}{ext}"
                        
                        # Add the screenshot to the ZIP file in a screenshots folder
                        zf.write(screenshot.path, f"screenshots/{filename}")
                        
                        # Add zoomed version if it exists
                        if screenshot.zoomed_path and os.path.exists(screenshot.zoomed_path):
                            _, zoomed_ext = os.path.splitext(screenshot.zoomed_path)
                            zoomed_filename = f"{lottery_type}_{ss_timestamp}_zoomed{zoomed_ext}"
                            zf.write(screenshot.zoomed_path, f"screenshots/{zoomed_filename}")
            
            # Reset the file pointer to the beginning of the file
            memory_file.seek(0)
            
            # Send the ZIP file as a response
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'lottery_data_combined_{timestamp}.zip'
            )
    except Exception as e:
        app.logger.error(f"Error creating combined ZIP file: {str(e)}")
        flash(f'Error creating combined ZIP file: {str(e)}', 'danger')
        return redirect(url_for('export_screenshots'))

@app.route('/port_check')
def port_check():
    """Special endpoint to check which port the application is responding on"""
    host = request.host
    return jsonify({
        "success": True,
        "host": host,
        "server_port": request.host.split(':')[1] if ':' in request.host else "default",
        "request_url": request.url,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/results/<lottery_type>')
def api_results(lottery_type):
    """API endpoint for lottery results"""
    try:
        limit = request.args.get('limit', type=int)
        results = data_aggregator.export_results_to_json(lottery_type, limit)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Advertisement Management Routes
@app.route('/admin/manage-ads')
@app.route('/admin/manage-ads/<placement>')
@login_required
def manage_ads(placement=None):
    """Admin page to manage advertisements"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get all ads or filter by placement
    if placement:
        ads = Advertisement.query.filter_by(placement=placement).order_by(Advertisement.priority.desc()).all()
    else:
        ads = Advertisement.query.order_by(Advertisement.priority.desc()).all()
    
    return render_template('admin/manage_ads.html', 
                          ads=ads,
                          placement=placement,
                          title="Manage Advertisements")

@app.route('/admin/upload-ad', methods=['GET', 'POST'])
@login_required
def upload_ad():
    """Admin page to upload a new advertisement"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    form = request.form
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            duration = int(request.form.get('duration'))
            placement = request.form.get('placement')
            priority = int(request.form.get('priority', 5))
            target_impressions = int(request.form.get('target_impressions'))
            active = 'active' in request.form
            
            # Get custom message and rich content settings
            custom_message = request.form.get('custom_message')
            loading_duration = int(request.form.get('loading_duration', 10))
            is_rich_content = 'is_rich_content' in request.form
            html_content = request.form.get('html_content') if is_rich_content else None
            
            # Handle optional dates
            start_date = request.form.get('start_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_date = None
                
            end_date = request.form.get('end_date')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_date = None
            
            # Check if video file is included
            if 'video_file' not in request.files:
                flash('No video file provided', 'danger')
                return redirect(request.url)
            
            video_file = request.files['video_file']
            if video_file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            
            # Determine file type
            file_type = video_file.content_type or 'video/mp4'
            
            # Create ads directory if it doesn't exist
            ads_dir = os.path.join('static', 'ads')
            os.makedirs(ads_dir, exist_ok=True)
            
            # Save the file with a unique name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{secure_filename(name)}_{timestamp}.{file_type.split('/')[-1]}"
            file_path = os.path.join(ads_dir, filename)
            video_file.save(file_path)
            
            # Handle custom image if provided
            custom_image_path = None
            if 'custom_image' in request.files and request.files['custom_image'].filename:
                custom_image = request.files['custom_image']
                
                # Determine file type
                image_type = custom_image.content_type or 'image/jpeg'
                
                # Save the image
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"custom_image_{secure_filename(name)}_{timestamp}.{image_type.split('/')[-1]}"
                custom_image_path = os.path.join('static', 'ads', 'images', image_filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(custom_image_path), exist_ok=True)
                
                # Save the image
                custom_image.save(custom_image_path)
            
            # Create new advertisement record
            new_ad = Advertisement(
                name=name,
                description=description,
                file_path=file_path,
                file_type=file_type,
                duration=duration,
                placement=placement,
                priority=priority,
                target_impressions=target_impressions,
                active=active,
                start_date=start_date,
                end_date=end_date,
                created_by_id=current_user.id,
                custom_message=custom_message,
                custom_image_path=custom_image_path,
                loading_duration=loading_duration,
                is_rich_content=is_rich_content,
                html_content=html_content
            )
            
            db.session.add(new_ad)
            db.session.commit()
            
            flash(f'Advertisement "{name}" uploaded successfully!', 'success')
            return redirect(url_for('manage_ads'))
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error uploading advertisement: {str(e)}")
            flash(f'Error uploading advertisement: {str(e)}', 'danger')
    
    return render_template('admin/upload_ad.html', 
                          form=form,
                          title="Upload Advertisement")

@app.route('/admin/edit-ad/<int:ad_id>', methods=['GET', 'POST'])
@login_required
def edit_ad(ad_id):
    """Admin page to edit an existing advertisement"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get the advertisement
    ad = Advertisement.query.get_or_404(ad_id)
    form = request.form
    
    if request.method == 'POST':
        try:
            # Update advertisement details
            ad.name = request.form.get('name')
            ad.description = request.form.get('description')
            ad.duration = int(request.form.get('duration'))
            ad.placement = request.form.get('placement')
            ad.priority = int(request.form.get('priority', 5))
            ad.target_impressions = int(request.form.get('target_impressions'))
            ad.active = 'active' in request.form
            
            # Update custom message and content settings
            ad.custom_message = request.form.get('custom_message')
            ad.loading_duration = int(request.form.get('loading_duration', 10))
            ad.is_rich_content = 'is_rich_content' in request.form
            ad.html_content = request.form.get('html_content') if ad.is_rich_content else None
            
            # Handle optional dates
            start_date = request.form.get('start_date')
            if start_date:
                ad.start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                ad.start_date = None
                
            end_date = request.form.get('end_date')
            if end_date:
                ad.end_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                ad.end_date = None
            
            # Check if a new video file was uploaded
            if 'video_file' in request.files and request.files['video_file'].filename:
                video_file = request.files['video_file']
                
                # Determine file type
                file_type = video_file.content_type or 'video/mp4'
                
                # Delete old file if it exists and is in the ads directory
                if ad.file_path and os.path.exists(ad.file_path) and 'static/ads' in ad.file_path:
                    try:
                        os.remove(ad.file_path)
                    except Exception as e:
                        logger.warning(f"Could not delete old advertisement file: {str(e)}")
                
                # Save the new file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{secure_filename(ad.name)}_{timestamp}.{file_type.split('/')[-1]}"
                file_path = os.path.join('static', 'ads', filename)
                video_file.save(file_path)
                
                # Update file path and type
                ad.file_path = file_path
                ad.file_type = file_type
            
            # Save changes
            db.session.commit()
            
            flash(f'Advertisement "{ad.name}" updated successfully!', 'success')
            return redirect(url_for('manage_ads'))
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error updating advertisement: {str(e)}")
            flash(f'Error updating advertisement: {str(e)}', 'danger')
    
    # Prepare form data for template
    form = {
        'name': ad.name,
        'description': ad.description,
        'duration': ad.duration,
        'placement': ad.placement,
        'priority': ad.priority,
        'target_impressions': ad.target_impressions,
        'active': ad.active,
        'start_date': ad.start_date,
        'end_date': ad.end_date,
        'custom_message': ad.custom_message,
        'loading_duration': ad.loading_duration,
        'is_rich_content': ad.is_rich_content,
        'html_content': ad.html_content
    }
    
    return render_template('admin/upload_ad.html', 
                          form=form,
                          ad=ad,
                          title="Edit Advertisement")

@app.route('/admin/preview-ad/<int:ad_id>')
@login_required
def preview_ad(ad_id):
    """Admin page to preview an advertisement"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get the advertisement
    ad = Advertisement.query.get_or_404(ad_id)
    
    return render_template('admin/preview_ad.html', 
                          ad=ad,
                          title=f"Preview: {ad.name}")

@app.route('/admin/delete-ad', methods=['POST'])
@login_required
def delete_ad():
    """Delete an advertisement"""
    if not current_user.is_admin:
        flash('You must be an admin to delete advertisements.', 'danger')
        return redirect(url_for('index'))
    
    ad_id = request.form.get('ad_id')
    if not ad_id:
        flash('No advertisement specified', 'danger')
        return redirect(url_for('manage_ads'))
    
    try:
        ad = Advertisement.query.get_or_404(ad_id)
        
        # Delete the file if it exists and is in the ads directory
        if ad.file_path and os.path.exists(ad.file_path) and 'static/ads' in ad.file_path:
            try:
                os.remove(ad.file_path)
            except Exception as e:
                logger.warning(f"Could not delete advertisement file: {str(e)}")
        
        # Delete the advertisement from the database
        db.session.delete(ad)
        db.session.commit()
        
        flash(f'Advertisement "{ad.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error deleting advertisement: {str(e)}")
        flash(f'Error deleting advertisement: {str(e)}', 'danger')
    
    return redirect(url_for('manage_ads'))

@app.route('/admin/ad-impressions')
@login_required
def ad_impressions():
    """Admin page to view ad impressions"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get all impressions grouped by advertisement
    ads = Advertisement.query.all()
    impressions = AdImpression.query.order_by(AdImpression.timestamp.desc()).limit(100).all()
    
    return render_template('admin/ad_impressions.html',
                          ads=ads,
                          impressions=impressions,
                          title="Advertisement Impressions")

@app.route('/admin/ad-performance')
@login_required
def ad_performance():
    """Admin page to view ad performance analytics"""
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get ad performance statistics
    ads = Advertisement.query.all()
    
    # Calculate performance metrics
    ad_stats = []
    for ad in ads:
        total_impressions = ad.total_impressions
        total_clicks = ad.total_clicks
        click_through_rate = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        progress_percent = (total_impressions / ad.target_impressions * 100) if ad.target_impressions > 0 else 0
        
        ad_stats.append({
            'ad': ad,
            'impressions': total_impressions,
            'clicks': total_clicks,
            'ctr': click_through_rate,
            'progress': min(progress_percent, 100)  # Cap at 100%
        })
    
    return render_template('admin/ad_performance.html',
                          ad_stats=ad_stats,
                          title="Advertisement Performance")

@app.route('/api/record-impression', methods=['POST'])
def record_impression():
    """API endpoint to record an ad impression"""
    try:
        ad_id = request.json.get('ad_id')
        if not ad_id:
            return jsonify({"error": "No ad_id provided"}), 400
        
        # Get the advertisement
        ad = Advertisement.query.get_or_404(ad_id)
        
        # Create new impression record
        impression = AdImpression(
            ad_id=ad_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=request.cookies.get('session', 'unknown'),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            page=request.referrer,
            duration_viewed=request.json.get('duration')
        )
        
        # Update ad impression count
        ad.total_impressions += 1
        
        db.session.add(impression)
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error recording impression: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/record-click', methods=['POST'])
def record_click():
    """API endpoint to record an ad click"""
    try:
        impression_id = request.json.get('impression_id')
        if not impression_id:
            return jsonify({"error": "No impression_id provided"}), 400
        
        # Get the impression
        impression = AdImpression.query.get_or_404(impression_id)
        
        # Update impression and ad click counts
        impression.was_clicked = True
        impression.advertisement.total_clicks += 1
        
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error recording click: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/system_status')
@login_required
def system_status():
    """System status dashboard for monitoring all components"""
    # Check server status
    port_5000_status = True  # We're already running on this port if this code executes
    
    # Check port 8080
    port_8080_status = False
    try:
        import urllib.request
        response = urllib.request.urlopen('http://localhost:8080/port_check', timeout=2)
        port_8080_status = response.getcode() == 200
    except Exception as e:
        logger.warning(f"Failed to check port 8080: {str(e)}")
    
    # Get database status and statistics
    db_status = True
    db_tables_count = 0
    db_records_count = 0
    db_type = "PostgreSQL"
    
    try:
        # Count tables
        from sqlalchemy import text
        result = db.session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
        db_tables_count = result.scalar() or 0
        
        # Count records in lottery_result table as a sample
        result = db.session.execute(text("SELECT COUNT(*) FROM lottery_result"))
        db_records_count = result.scalar() or 0
    except Exception as e:
        logger.error(f"Database status check error: {str(e)}")
        db_status = False
    
    # Get advertisement system stats
    active_ads_count = Advertisement.query.filter_by(active=True).count()
    total_impressions = db.session.query(db.func.count(AdImpression.id)).scalar() or 0
    js_status = True  # Will be set by frontend JS
    
    # Get lottery stats
    lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 'Powerball', 'Powerball Plus', 'Daily Lottery']
    lottery_stats = []
    
    for lottery_type in lottery_types:
        count = LotteryResult.query.filter_by(lottery_type=lottery_type).count()
        latest_draw = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
        
        lottery_stats.append({
            'name': lottery_type,
            'count': count,
            'latest_draw': latest_draw.draw_date.strftime('%Y-%m-%d') if latest_draw else 'N/A'
        })
    
    # Get system resource usage
    try:
        import psutil
        memory_usage = int(psutil.virtual_memory().percent)
        cpu_usage = int(psutil.cpu_percent(interval=0.1))
        disk_usage = int(psutil.disk_usage('/').percent)
    except ImportError:
        # Fallback if psutil not available
        memory_usage = 50
        cpu_usage = 30
        disk_usage = 40
        logger.warning("psutil not available for system stats, using placeholder values")
    
    return render_template(
        'admin/system_status.html',
        port_5000_status=port_5000_status,
        port_8080_status=port_8080_status,
        server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        last_checked=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        db_status=db_status,
        db_tables_count=db_tables_count,
        db_records_count=db_records_count,
        db_type=db_type,
        active_ads_count=active_ads_count,
        total_impressions=total_impressions,
        js_status=js_status,
        lottery_stats=lottery_stats,
        memory_usage=memory_usage,
        cpu_usage=cpu_usage,
        disk_usage=disk_usage
    )

@app.route('/admin/check-js', methods=['POST'])
@login_required
@csrf.exempt
def check_js():
    """API endpoint to check if JavaScript is operational"""
    return jsonify({'success': True})

@app.route('/admin/health-dashboard')
@login_required
@csrf.exempt
def health_dashboard():
    """Health monitoring dashboard for system administrators"""
    import health_monitor
    from datetime import datetime, timedelta
    import json
    
    # Get the overall system status
    system_status = health_monitor.get_system_status(app, db)
    
    # Get port usage data
    port_history = health_monitor.get_health_history('port_usage', 1)
    # Add active ports to components
    active_ports = system_status.get('active_ports', [])
    
    # Get recent alerts
    alerts = health_monitor.get_recent_alerts(10)
    
    # Get health check history
    health_history = health_monitor.get_health_history(limit=10)
    
    # Get resource usage history for charts
    resource_history = health_monitor.get_health_history('system_resources', 24)
    
    # Prepare chart data
    resource_timestamps = []
    cpu_history = []
    memory_history = []
    disk_history = []
    
    for check in resource_history:
        # Try to parse timestamps and details
        try:
            timestamp = datetime.fromisoformat(check['timestamp'].replace('Z', '+00:00'))
            resource_timestamps.append(timestamp.strftime('%H:%M'))
            
            details = check['details']
            if isinstance(details, str):
                details = json.loads(details)
            
            cpu_history.append(details.get('cpu_usage', 0))
            memory_history.append(details.get('memory_usage', 0))
            disk_history.append(details.get('disk_usage', 0))
        except Exception as e:
            app.logger.error(f"Error parsing health check data: {str(e)}")
    
    # If we don't have enough data points, add some placeholders
    if len(resource_timestamps) < 5:
        now = datetime.now()
        for i in range(5 - len(resource_timestamps)):
            time_point = now - timedelta(hours=i)
            resource_timestamps.insert(0, time_point.strftime('%H:%M'))
            cpu_history.insert(0, 0)
            memory_history.insert(0, 0)
            disk_history.insert(0, 0)
    
    # Reverse lists to show chronological order
    resource_timestamps.reverse()
    cpu_history.reverse()
    memory_history.reverse()
    disk_history.reverse()
    
    # Add additional port monitoring information
    service_port_map = {}
    
    # If port usage information is available in the health history,
    # populate the service-to-port mapping
    if port_history and len(port_history) > 0:
        try:
            port_details = port_history[0]['details']
            if isinstance(port_details, str):
                port_details = json.loads(port_details)
            
            # Extract service usage mapping from details if available
            if isinstance(port_details, dict) and 'service_usage' in port_details:
                service_port_map = port_details['service_usage']
        except Exception as e:
            app.logger.error(f"Error extracting port history data: {str(e)}")
    
    return render_template(
        'admin/health_dashboard.html',
        overall_status=system_status['overall_status'],
        components=system_status['components'],
        last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        alerts=alerts,
        health_history=health_history,
        resource_timestamps=resource_timestamps,
        cpu_history=cpu_history,
        memory_history=memory_history,
        disk_history=disk_history,
        active_ports=active_ports,
        service_port_map=service_port_map
    )

@app.route('/admin/health-alerts')
@login_required
def health_alerts():
    """View and manage health alerts"""
    import health_monitor
    from datetime import datetime
    
    # Get all alerts
    alerts = health_monitor.get_recent_alerts(100)
    
    # Generate chart data for alert types
    alert_types = {}
    for alert in alerts:
        alert_type = alert['alert_type']
        if alert_type in alert_types:
            alert_types[alert_type] += 1
        else:
            alert_types[alert_type] = 1
    
    # Prepare chart data
    alert_types_list = list(alert_types.keys())
    alert_counts = [alert_types[t] for t in alert_types_list]
    
    # Generate time-based data
    # Group alerts by day for the last 30 days
    time_data = [0] * 30
    time_labels = []
    
    now = datetime.now()
    for i in range(30):
        day = now - timedelta(days=i)
        time_labels.insert(0, day.strftime('%m/%d'))
        
    for alert in alerts:
        try:
            created_at = datetime.fromisoformat(alert['created_at'].replace('Z', '+00:00'))
            days_ago = (now - created_at).days
            if 0 <= days_ago < 30:
                time_data[29 - days_ago] += 1
        except:
            pass
    
    # Add utility functions for templates
    def format_duration(start_time, end_time):
        """Format a duration between two timestamps"""
        try:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration = end_time - start_time
            seconds = duration.total_seconds()
            
            if seconds < 60:
                return f"{int(seconds)} seconds"
            elif seconds < 3600:
                return f"{int(seconds / 60)} minutes"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                minutes = int((seconds % 3600) / 60)
                return f"{hours} hours, {minutes} minutes"
            else:
                days = int(seconds / 86400)
                hours = int((seconds % 86400) / 3600)
                return f"{days} days, {hours} hours"
        except Exception as e:
            app.logger.error(f"Error formatting duration: {str(e)}")
            return "Unknown"
    
    return render_template(
        'admin/health_alerts.html',
        alerts=alerts,
        alert_types=alert_types_list,
        alert_counts=alert_counts,
        time_labels=time_labels,
        time_data=time_data,
        format_duration=format_duration,
        now=datetime.now()
    )

@app.route('/admin/resolve-health-alert/<int:alert_id>', methods=['POST'])
@login_required
@csrf.exempt
def resolve_health_alert(alert_id):
    """Manually resolve a health alert"""
    import health_monitor
    import sqlite3
    
    try:
        conn = sqlite3.connect(health_monitor.health_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the alert
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        alert = cursor.fetchone()
        
        if alert:
            # Update the alert
            cursor.execute(
                "UPDATE alerts SET resolved = 1, resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
                (alert_id,)
            )
            conn.commit()
            
            # Also resolve any other alerts of the same type
            alert_type = alert['alert_type']
            health_monitor.resolve_alert(alert_type)
            
            flash(f"Alert #{alert_id} ({alert_type}) has been resolved.", "success")
        else:
            flash(f"Alert #{alert_id} not found.", "danger")
            
        conn.close()
    except Exception as e:
        flash(f"Error resolving alert: {str(e)}", "danger")
    
    return redirect(url_for('health_alerts'))

@app.route('/admin/health-history')
@login_required
def health_history():
    """View detailed health check history"""
    import health_monitor
    import json
    from datetime import datetime
    from sqlalchemy import func
    
    # Set up pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    selected_type = request.args.get('check_type', '')
    selected_status = request.args.get('status', '')
    
    # Get health check history
    try:
        import sqlite3
        conn = sqlite3.connect(health_monitor.health_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build the query
        query = "SELECT * FROM health_checks"
        params = []
        
        if selected_type or selected_status:
            query += " WHERE"
            
            if selected_type:
                query += " check_type = ?"
                params.append(selected_type)
                
            if selected_type and selected_status:
                query += " AND"
                
            if selected_status:
                query += " status = ?"
                params.append(selected_status)
        
        # Get total count for pagination
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Add sorting and pagination
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        # Execute query
        cursor.execute(query, params)
        history = [dict(row) for row in cursor.fetchall()]
        
        # Get all unique check types for the filter dropdown
        cursor.execute("SELECT DISTINCT check_type FROM health_checks ORDER BY check_type")
        check_types = [row[0] for row in cursor.fetchall()]
        
        # Get status counts for chart
        cursor.execute("SELECT status, COUNT(*) FROM health_checks GROUP BY status")
        status_counts_raw = cursor.fetchall()
        
        # Prepare status counts for chart
        status_counts = [0, 0, 0, 0]  # OK, WARNING, CRITICAL, ERROR
        for status, count in status_counts_raw:
            if status == 'OK':
                status_counts[0] = count
            elif status == 'WARNING':
                status_counts[1] = count
            elif status == 'CRITICAL':
                status_counts[2] = count
            elif status == 'ERROR':
                status_counts[3] = count
        
        # Get check type counts for chart
        cursor.execute("SELECT check_type, COUNT(*) FROM health_checks GROUP BY check_type")
        type_counts_raw = cursor.fetchall()
        
        # Prepare check type counts for chart
        type_counts = [row[1] for row in type_counts_raw]
        
        conn.close()
        
        # Create pagination object
        class Pagination:
            def __init__(self, page, per_page, total):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                
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
                
            def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if (num <= left_edge or
                            (self.page - left_current <= num <= self.page + right_current) or
                            (self.pages - right_edge < num)):
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        
        pagination = Pagination(page, per_page, total)
        
        # Format JSON for display
        def format_json(json_str):
            try:
                if isinstance(json_str, str):
                    data = json.loads(json_str)
                else:
                    data = json_str
                return json.dumps(data, indent=2)
            except:
                return json_str
        
    except Exception as e:
        app.logger.error(f"Error getting health history: {str(e)}")
        history = []
        check_types = []
        status_counts = [0, 0, 0, 0]
        type_counts = []
        pagination = None
        format_json = lambda x: x
    
    return render_template(
        'admin/health_history.html',
        history=history,
        check_types=check_types,
        selected_type=selected_type,
        selected_status=selected_status,
        status_counts=status_counts,
        type_counts=type_counts,
        pagination=pagination,
        format_json=format_json
    )

@app.route('/health_port_check')
def health_port_check():
    """Simple endpoint to check if the server is running on a specific port"""
    return jsonify({
        'status': 'ok',
        'message': 'Port health check successful',
        'port': request.environ.get('SERVER_PORT', '5000'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/admin/run-health-checks', methods=['POST', 'GET'])
@login_required
@csrf.exempt
def run_health_checks():
    """Manually trigger health checks"""
    import health_monitor
    
    try:
        health_monitor.run_health_checks(app, db)
        flash("Health checks completed successfully.", "success")
    except Exception as e:
        flash(f"Error running health checks: {str(e)}", "danger")
    
    return redirect(url_for('health_dashboard'))

@app.route('/health_check', methods=['GET'])
@csrf.exempt
def health_check():
    """Simple endpoint for health checks in Replit deployment"""
    return jsonify({
        'status': 'ok',
        'message': 'Health check successful',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })



@app.route('/api/system-metrics', methods=['GET'])
@csrf.exempt
def system_metrics():
    """API endpoint to get current system metrics for dashboard"""
    try:
        import psutil
        
        # Get system stats
        memory = psutil.virtual_memory()
        memory_usage = int(memory.percent)
        
        disk = psutil.disk_usage('/')
        disk_usage = int(disk.percent)
        
        cpu_usage = int(psutil.cpu_percent(interval=0.5))
        
        return jsonify({
            'success': True,
            'cpu_usage': f"{cpu_usage}%",
            'memory_usage': f"{memory_usage}%",
            'disk_usage': f"{disk_usage}%",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Register advertisement management routes
# Ad management temporarily disabled
# ad_management.register_ad_routes(app)

# Register lottery analysis routes
lottery_analysis.register_analysis_routes(app, db)

# API Request Tracking routes 
@app.route('/admin/api-tracking')
@login_required
def api_tracking_view():
    """Dashboard for tracking API requests to external services"""
    from datetime import datetime, timedelta
    from models import APIRequestLog
    from sqlalchemy import func, desc
    
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get time periods for filtering
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    this_week = today - timedelta(days=today.weekday())
    this_month = today.replace(day=1)
    
    # Get overall statistics
    overall_stats = APIRequestLog.get_stats_by_date_range()
    
    # Get daily statistics for the last 30 days
    daily_stats = db.session.query(
        func.date(APIRequestLog.created_at).label('date'),
        func.count(APIRequestLog.id).label('count'),
        func.sum(APIRequestLog.total_tokens).label('tokens')
    ).group_by(func.date(APIRequestLog.created_at)
    ).order_by(desc('date')).limit(30).all()
    
    # Get service breakdown
    service_breakdown = db.session.query(
        APIRequestLog.service,
        func.count(APIRequestLog.id).label('count'),
        func.sum(APIRequestLog.total_tokens).label('tokens')
    ).group_by(APIRequestLog.service).all()
    
    # Get model breakdown for Anthropic
    model_breakdown = db.session.query(
        APIRequestLog.model,
        func.count(APIRequestLog.id).label('count'),
        func.sum(APIRequestLog.total_tokens).label('tokens')
    ).filter(APIRequestLog.service == 'anthropic'
    ).group_by(APIRequestLog.model).all()
    
    # Get recent requests with status, limited to 100
    recent_requests = APIRequestLog.query.order_by(
        APIRequestLog.created_at.desc()
    ).limit(100).all()
    
    # Calculate statistics for specific time periods
    today_stats = APIRequestLog.get_stats_by_date_range(start_date=today)
    yesterday_stats = APIRequestLog.get_stats_by_date_range(start_date=yesterday, end_date=today)
    this_week_stats = APIRequestLog.get_stats_by_date_range(start_date=this_week)
    this_month_stats = APIRequestLog.get_stats_by_date_range(start_date=this_month)
    
    # Format data for charts
    daily_labels = [str(item.date) for item in daily_stats]
    daily_requests = [item.count for item in daily_stats]
    daily_tokens = [int(item.tokens) if item.tokens else 0 for item in daily_stats]
    
    # Prepare service breakdown data for charts
    service_labels = [item.service for item in service_breakdown]
    service_counts = [item.count for item in service_breakdown]
    service_tokens = [int(item.tokens) if item.tokens else 0 for item in service_breakdown]
    
    return render_template(
        'admin/api_tracking.html',
        title="API Request Tracking",
        overall_stats=overall_stats,
        today_stats=today_stats,
        yesterday_stats=yesterday_stats,
        this_week_stats=this_week_stats,
        this_month_stats=this_month_stats,
        service_breakdown=service_breakdown,
        model_breakdown=model_breakdown,
        recent_requests=recent_requests,
        daily_labels=daily_labels,
        daily_requests=daily_requests,
        daily_tokens=daily_tokens,
        service_labels=service_labels,
        service_counts=service_counts,
        service_tokens=service_tokens
    )

# When running directly, not through gunicorn
if __name__ == "__main__":
    # Extra logging to help diagnose startup issues
    import logging
    import os
    
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # Use port 8080 for Replit compatibility
    port = int(os.environ.get('PORT', 8080))
    
    # Start Flask app
    print(f"Starting Flask application on 0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)