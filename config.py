import os

class Config:
    """Application configuration settings"""
    # Flask settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'lottery-scraper-default-secret')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "connect_args": {
            "sslmode": "require"
        }
    }
    
    # Anthropic API settings (Custom environment variable name as requested)
    ANTHROPIC_API_KEY = os.environ.get('Lotto_scape_ANTHROPIC_KEY', '')
    MISTRAL_API_KEY = os.environ.get('Snap_Lotto_Mistral', '')
    
    # Screenshot directory
    SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
    
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
        
        # Validate required environment variables
        if not Config.ANTHROPIC_API_KEY:
            app.logger.warning("Lotto_scape_ANTHROPIC_KEY environment variable not set. OCR functionality will not work.")
