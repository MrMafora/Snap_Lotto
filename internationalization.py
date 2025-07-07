"""
Internationalization (i18n) Support
Phase 4 Implementation - Multi-language Support for English and Afrikaans
"""

import json
import logging
from flask import request, session, redirect, url_for

logger = logging.getLogger(__name__)

# Language translations
TRANSLATIONS = {
    'en': {
        # Navigation
        'nav_home': 'Home',
        'nav_scanner': 'Ticket Scanner',
        'nav_results': 'Latest Results',
        'nav_analytics': 'Analytics',
        'nav_admin': 'Admin',
        'nav_login': 'Login',
        'nav_logout': 'Logout',
        
        # Main Content
        'app_title': 'Snap Lottery',
        'app_subtitle': 'South Africa\'s #1 Lottery Scanner',
        'welcome_message': 'Check your lottery tickets instantly with AI-powered scanning',
        'latest_results': 'Latest Lottery Results',
        'scan_ticket': 'Scan Your Ticket',
        'upload_image': 'Upload Ticket Image',
        'processing': 'Processing...',
        'results_found': 'Results Found',
        'no_results': 'No winning numbers found',
        
        # Lottery Types
        'lotto': 'Lotto',
        'lotto_plus_1': 'Lotto Plus 1',
        'lotto_plus_2': 'Lotto Plus 2',
        'powerball': 'PowerBall',
        'powerball_plus': 'PowerBall Plus',
        'daily_lotto': 'Daily Lotto',
        
        # Form Labels
        'username': 'Username',
        'password': 'Password',
        'email': 'Email',
        'confirm_password': 'Confirm Password',
        'login_button': 'Login',
        'register_button': 'Register',
        'submit': 'Submit',
        'cancel': 'Cancel',
        'save': 'Save',
        'delete': 'Delete',
        'edit': 'Edit',
        'view': 'View',
        
        # Lottery Information
        'draw_number': 'Draw Number',
        'draw_date': 'Draw Date',
        'winning_numbers': 'Winning Numbers',
        'bonus_numbers': 'Bonus Numbers',
        'jackpot': 'Jackpot',
        'prize_divisions': 'Prize Divisions',
        'division': 'Division',
        'winners': 'Winners',
        'prize_amount': 'Prize Amount',
        'total_winnings': 'Total Winnings',
        'rollover': 'Rollover',
        'next_jackpot': 'Next Jackpot',
        
        # Analytics
        'frequency_analysis': 'Frequency Analysis',
        'most_frequent': 'Most Frequent Numbers',
        'least_frequent': 'Least Frequent Numbers',
        'hot_numbers': 'Hot Numbers',
        'cold_numbers': 'Cold Numbers',
        'number_trends': 'Number Trends',
        'predictions': 'Predictions',
        'confidence_score': 'Confidence Score',
        'historical_data': 'Historical Data',
        
        # Admin
        'admin_dashboard': 'Admin Dashboard',
        'system_health': 'System Health',
        'database_stats': 'Database Statistics',
        'user_management': 'User Management',
        'data_management': 'Data Management',
        'security_settings': 'Security Settings',
        'performance_monitoring': 'Performance Monitoring',
        
        # Messages
        'success': 'Success',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Information',
        'login_required': 'Please login to access this page',
        'access_denied': 'Access denied',
        'data_saved': 'Data saved successfully',
        'data_deleted': 'Data deleted successfully',
        'invalid_input': 'Invalid input provided',
        'processing_error': 'Error processing request',
        'upload_success': 'File uploaded successfully',
        'upload_error': 'Error uploading file',
        
        # Time and Dates
        'today': 'Today',
        'yesterday': 'Yesterday',
        'last_week': 'Last Week',
        'last_month': 'Last Month',
        'last_year': 'Last Year',
        'days_ago': 'days ago',
        'hours_ago': 'hours ago',
        'minutes_ago': 'minutes ago',
        'just_now': 'Just now',
        
        # Footer
        'footer_about': 'About Snap Lottery',
        'footer_contact': 'Contact Us',
        'footer_privacy': 'Privacy Policy',
        'footer_terms': 'Terms of Service',
        'footer_copyright': '© 2025 Snap Lottery. All rights reserved.',
        
        # SEO Meta
        'meta_description': 'South Africa\'s most accurate lottery ticket scanner. Check Lotto, PowerBall, and Daily Lotto results instantly with AI-powered technology.',
        'meta_keywords': 'lottery scanner, South Africa lottery, Lotto results, PowerBall, Daily Lotto, ticket checker',
    },
    
    'af': {
        # Navigation
        'nav_home': 'Tuis',
        'nav_scanner': 'Kaartjieskandeerder',
        'nav_results': 'Nuutste Uitslae',
        'nav_analytics': 'Analise',
        'nav_admin': 'Admin',
        'nav_login': 'Meld Aan',
        'nav_logout': 'Meld Af',
        
        # Main Content
        'app_title': 'Snap Lotery',
        'app_subtitle': 'Suid-Afrika se #1 Lotery Skandeerder',
        'welcome_message': 'Gaan jou lotery kaartjies dadelik na met KI-aangedrewe skandering',
        'latest_results': 'Nuutste Lotery Uitslae',
        'scan_ticket': 'Skandeer Jou Kaartjie',
        'upload_image': 'Laai Kaartjie Beeld Op',
        'processing': 'Verwerk...',
        'results_found': 'Uitslae Gevind',
        'no_results': 'Geen wengetalle gevind nie',
        
        # Lottery Types
        'lotto': 'Lotto',
        'lotto_plus_1': 'Lotto Plus 1',
        'lotto_plus_2': 'Lotto Plus 2',
        'powerball': 'PowerBall',
        'powerball_plus': 'PowerBall Plus',
        'daily_lotto': 'Daaglikse Lotto',
        
        # Form Labels
        'username': 'Gebruikersnaam',
        'password': 'Wagwoord',
        'email': 'E-pos',
        'confirm_password': 'Bevestig Wagwoord',
        'login_button': 'Meld Aan',
        'register_button': 'Registreer',
        'submit': 'Stuur',
        'cancel': 'Kanselleer',
        'save': 'Stoor',
        'delete': 'Skrap',
        'edit': 'Wysig',
        'view': 'Bekyk',
        
        # Lottery Information
        'draw_number': 'Trek Nommer',
        'draw_date': 'Trek Datum',
        'winning_numbers': 'Wengetalle',
        'bonus_numbers': 'Bonus Getalle',
        'jackpot': 'Hoofprys',
        'prize_divisions': 'Prys Afdelings',
        'division': 'Afdeling',
        'winners': 'Wenners',
        'prize_amount': 'Prys Bedrag',
        'total_winnings': 'Totale Wenste',
        'rollover': 'Oorskiet',
        'next_jackpot': 'Volgende Hoofprys',
        
        # Analytics
        'frequency_analysis': 'Frekwensie Analise',
        'most_frequent': 'Mees Gereelde Getalle',
        'least_frequent': 'Mins Gereelde Getalle',
        'hot_numbers': 'Warm Getalle',
        'cold_numbers': 'Koue Getalle',
        'number_trends': 'Getal Neigings',
        'predictions': 'Voorspellings',
        'confidence_score': 'Vertroue Telling',
        'historical_data': 'Historiese Data',
        
        # Admin
        'admin_dashboard': 'Admin Beheerspan',
        'system_health': 'Stelsel Gesondheid',
        'database_stats': 'Databasis Statistieke',
        'user_management': 'Gebruiker Bestuur',
        'data_management': 'Data Bestuur',
        'security_settings': 'Sekuriteit Instellings',
        'performance_monitoring': 'Prestasie Monitering',
        
        # Messages
        'success': 'Sukses',
        'error': 'Fout',
        'warning': 'Waarskuwing',
        'info': 'Inligting',
        'login_required': 'Meld asseblief aan om hierdie bladsy te benader',
        'access_denied': 'Toegang geweier',
        'data_saved': 'Data suksesvol gestoor',
        'data_deleted': 'Data suksesvol geskrap',
        'invalid_input': 'Ongeldige invoer verskaf',
        'processing_error': 'Fout tydens verwerking van versoek',
        'upload_success': 'Lêer suksesvol opgelaai',
        'upload_error': 'Fout tydens oplaai van lêer',
        
        # Time and Dates
        'today': 'Vandag',
        'yesterday': 'Gister',
        'last_week': 'Verlede Week',
        'last_month': 'Verlede Maand',
        'last_year': 'Verlede Jaar',
        'days_ago': 'dae gelede',
        'hours_ago': 'ure gelede',
        'minutes_ago': 'minute gelede',
        'just_now': 'Sopas',
        
        # Footer
        'footer_about': 'Oor Snap Lotery',
        'footer_contact': 'Kontak Ons',
        'footer_privacy': 'Privaatheid Beleid',
        'footer_terms': 'Terme van Diens',
        'footer_copyright': '© 2025 Snap Lotery. Alle regte voorbehou.',
        
        # SEO Meta
        'meta_description': 'Suid-Afrika se mees akkurate lotery kaartjie skandeerder. Gaan Lotto, PowerBall, en Daaglikse Lotto uitslae dadelik na met KI-tegnologie.',
        'meta_keywords': 'lotery skandeerder, Suid-Afrika lotery, Lotto uitslae, PowerBall, Daaglikse Lotto, kaartjie gaan na',
    }
}

class LocalizationManager:
    """Manages language localization and translations"""
    
    def __init__(self):
        self.supported_languages = ['en', 'af']
        self.default_language = 'en'
        self.current_language = 'en'
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return [
            {'code': 'en', 'name': 'English', 'native_name': 'English'},
            {'code': 'af', 'name': 'Afrikaans', 'native_name': 'Afrikaans'}
        ]
    
    def set_language(self, language_code):
        """Set the current language"""
        if language_code in self.supported_languages:
            self.current_language = language_code
            session['language'] = language_code
            logger.info(f"Language set to: {language_code}")
        else:
            logger.warning(f"Unsupported language code: {language_code}")
    
    def get_language(self):
        """Get the current language"""
        # Check session first
        if 'language' in session and session['language'] in self.supported_languages:
            return session['language']
        
        # Check browser accept-language header
        if request:
            browser_lang = request.accept_languages.best_match(self.supported_languages)
            if browser_lang:
                return browser_lang
        
        return self.default_language
    
    def translate(self, key, **kwargs):
        """Translate a key to the current language"""
        lang = self.get_language()
        
        # Get translation
        translation = TRANSLATIONS.get(lang, {}).get(key, 
                     TRANSLATIONS.get(self.default_language, {}).get(key, key))
        
        # Apply formatting if kwargs provided
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                logger.warning(f"Translation formatting failed for key: {key}")
        
        return translation
    
    def get_all_translations(self, language_code=None):
        """Get all translations for a language"""
        lang = language_code or self.get_language()
        return TRANSLATIONS.get(lang, TRANSLATIONS[self.default_language])
    
    def add_translation(self, language_code, key, value):
        """Add a new translation"""
        if language_code not in TRANSLATIONS:
            TRANSLATIONS[language_code] = {}
        
        TRANSLATIONS[language_code][key] = value
        logger.info(f"Added translation for {language_code}: {key}")
    
    def format_number(self, number, language_code=None):
        """Format numbers according to locale"""
        lang = language_code or self.get_language()
        
        if lang == 'af':
            # Afrikaans number formatting (similar to European)
            return f"{number:,}".replace(',', ' ')
        else:
            # English number formatting
            return f"{number:,}"
    
    def format_currency(self, amount, language_code=None):
        """Format currency according to locale"""
        lang = language_code or self.get_language()
        formatted_amount = self.format_number(amount, lang)
        
        if lang == 'af':
            return f"R{formatted_amount}"
        else:
            return f"R{formatted_amount}"
    
    def format_date(self, date, format_type='medium', language_code=None):
        """Format dates according to locale"""
        lang = language_code or self.get_language()
        
        if format_type == 'short':
            if lang == 'af':
                return date.strftime('%d/%m/%Y')
            else:
                return date.strftime('%m/%d/%Y')
        elif format_type == 'medium':
            if lang == 'af':
                months_af = ['Jan', 'Feb', 'Mrt', 'Apr', 'Mei', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Des']
                return f"{date.day} {months_af[date.month-1]} {date.year}"
            else:
                return date.strftime('%d %b %Y')
        else:  # long format
            if lang == 'af':
                months_af = ['Januarie', 'Februarie', 'Maart', 'April', 'Mei', 'Junie',
                           'Julie', 'Augustus', 'September', 'Oktober', 'November', 'Desember']
                return f"{date.day} {months_af[date.month-1]} {date.year}"
            else:
                return date.strftime('%d %B %Y')

# Global localization manager
localization = LocalizationManager()

def init_localization(app):
    """Initialize localization for Flask app"""
    # Template context processor to make translation function available
    @app.context_processor
    def inject_localization():
        return {
            't': localization.translate,
            'current_language': localization.get_language(),
            'supported_languages': localization.get_supported_languages(),
            'format_number': localization.format_number,
            'format_currency': localization.format_currency,
            'format_date': localization.format_date
        }
    
    # Route for changing language
    @app.route('/set-language/<language_code>')
    def set_language(language_code):
        localization.set_language(language_code)
        # Redirect back to referring page or home
        return redirect(request.referrer or url_for('home'))
    
    logger.info("Localization system initialized")
    return True

def get_localized_lottery_types():
    """Get lottery types in current language"""
    return {
        'LOTTO': localization.translate('lotto'),
        'LOTTO PLUS 1': localization.translate('lotto_plus_1'),
        'LOTTO PLUS 2': localization.translate('lotto_plus_2'),
        'PowerBall': localization.translate('powerball'),
        'POWERBALL PLUS': localization.translate('powerball_plus'),
        'DAILY LOTTO': localization.translate('daily_lotto')
    }

def localized_error_messages():
    """Get localized error messages"""
    return {
        'required_field': localization.translate('required_field', field='{field}'),
        'invalid_email': localization.translate('invalid_email'),
        'password_mismatch': localization.translate('password_mismatch'),
        'login_failed': localization.translate('login_failed'),
        'file_too_large': localization.translate('file_too_large'),
        'invalid_file_type': localization.translate('invalid_file_type')
    }