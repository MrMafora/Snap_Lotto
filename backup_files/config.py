import os
from datetime import timezone, timedelta

class Config:
    """Application configuration settings"""
    # Environment settings
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')  # 'development' or 'production'
    
    # South Africa is UTC+2
    TIMEZONE = timezone(timedelta(hours=2))
    TIMEZONE_NAME = 'SAST'  # South Africa Standard Time
    
    # Flask settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'lottery-scraper-default-secret')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///lottery.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,  # Reduced pool size to prevent too many connections
        "max_overflow": 10,  # Reduced max overflow
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 30
    }
    
    # Only add SSL requirement for PostgreSQL connections
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        # Enhanced Neon PostgreSQL connection parameters
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
            "sslmode": "require",
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "application_name": "snaplotto-flask-app",
            "options": "-c statement_timeout=30000"  # 30 second timeout
        }
    
    # Anthropic API settings (Custom environment variable name as requested)
    ANTHROPIC_API_KEY = os.environ.get('Lotto_scape_ANTHROPIC_KEY', '')
    
    # Screenshot directory
    SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    
    # Default lottery URLS for history pages
    DEFAULT_LOTTERY_URLS = [
        'https://www.nationallottery.co.za/lotto-history',
        'https://www.nationallottery.co.za/lotto-plus-1-history',
        'https://www.nationallottery.co.za/lotto-plus-2-history',
        'https://www.nationallottery.co.za/powerball-history',
        'https://www.nationallottery.co.za/powerball-plus-history',
        'https://www.nationallottery.co.za/daily-lotto-history'
    ]
    
    # Current results URLs with divisions data
    RESULTS_URLS = [
        {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
        {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
        {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
        {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
    ]
    
    # Default schedule settings
    DEFAULT_HOUR = 1  # 1 AM
    DEFAULT_MINUTE = 0
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create screenshot directory if it doesn't exist
        os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)
        
        # Create uploads directory if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Validate required environment variables
        if not Config.ANTHROPIC_API_KEY:
            app.logger.warning("Lotto_scape_ANTHROPIC_KEY environment variable not set. OCR functionality will not work.")
