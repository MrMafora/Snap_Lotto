import os

class Config:
    """Application configuration settings"""
    # Flask settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'lottery-scraper-default-secret')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///lottery_data.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Anthropic API settings (Custom environment variable name as requested)
    ANTHROPIC_API_KEY = os.environ.get('Lotto_scape_ANTHROPIC_KEY')
    
    # Screenshot directory
    SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
    
    # Default lottery URLS
    DEFAULT_LOTTERY_URLS = [
        'https://www.nationallottery.co.za/lotto-history',
        'https://www.nationallottery.co.za/lotto-plus-1-history',
        'https://www.nationallottery.co.za/lotto-plus-2-history',
        'https://www.nationallottery.co.za/powerball-history',
        'https://www.nationallottery.co.za/powerball-plus-history',
        'https://www.nationallottery.co.za/daily-lotto-history'
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
