"""
Database models for the application
"""
from datetime import datetime
import json
import os
import numpy as np
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

# Initialize SQLAlchemy base
class Base(DeclarativeBase):
    pass

class DuplicateCheckMixin:
    """Mixin to provide duplicate checking functionality"""
    
    @classmethod
    def exists(cls, **kwargs):
        """Check if an item exists with the given attributes"""
        return db.session.query(cls).filter_by(**kwargs).first() is not None
    
    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        """Get existing item or create new one if it doesn't exist"""
        instance = db.session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance, False
        
        params = dict((k, v) for k, v in kwargs.items())
        if defaults:
            params.update(defaults)
        
        instance = cls(**params)
        try:
            db.session.add(instance)
            db.session.commit()
            return instance, True
        except IntegrityError:
            db.session.rollback()
            instance = db.session.query(cls).filter_by(**kwargs).first()
            return instance, False

# Initialize database
db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    """User model for admin authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Screenshot(db.Model):
    """Model for storing screenshot information"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    lottery_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    path = db.Column(db.String(255), nullable=False)
    zoomed_path = db.Column(db.String(255), nullable=True)  # Path to zoomed-in screenshot
    processed = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<Screenshot {self.id}: {self.lottery_type}>"

class LotteryResult(db.Model):
    """Model for storing lottery results extracted from screenshots"""
    __tablename__ = 'lottery_results'  # Use the plural table name with current data
    id = db.Column(db.Integer, primary_key=True)
    lottery_type = db.Column(db.String(50), nullable=False, comment="Game Type")
    draw_number = db.Column(db.Integer, nullable=True, comment="Draw ID")
    draw_date = db.Column(db.DateTime, nullable=False, comment="Game Date")
    main_numbers = db.Column(db.String(255), nullable=True, comment="Winning Numbers (JSON string array)")  # Stored as JSON string
    bonus_numbers = db.Column(db.String(255), nullable=True, comment="Bonus Numbers (JSON string array)")  # Stored as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Prize division information (Section 2)
    prize_divisions = db.Column(db.JSON, nullable=True, comment="Prize divisions with winners and amounts")
    total_prize_pool = db.Column(db.String(100), nullable=True, comment="Total prize pool")
    rollover_amount = db.Column(db.String(100), nullable=True, comment="Rollover amount")
    
    # Additional information (Section 3) - More Info fields
    next_draw_date = db.Column(db.String(50), nullable=True, comment="Next draw date")
    estimated_jackpot = db.Column(db.String(100), nullable=True, comment="Estimated next jackpot")
    additional_info = db.Column(db.Text, nullable=True, comment="Additional lottery information")
    
    # Extended More Info fields (for Lotto, Lotto Plus 1, Lotto Plus 2, Powerball, Powerball Plus)
    rollover_number = db.Column(db.String(50), nullable=True, comment="Rollover number")
    total_pool_size = db.Column(db.String(100), nullable=True, comment="Total pool size")
    total_sales = db.Column(db.String(100), nullable=True, comment="Total sales")
    draw_machine = db.Column(db.String(50), nullable=True, comment="Draw machine")
    
    # Legacy fields (keeping for compatibility)
    divisions = db.Column(db.JSON, nullable=True, comment="Legacy prize divisions")
    next_jackpot = db.Column(db.String(100), nullable=True, comment="Legacy next jackpot")
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (
        db.UniqueConstraint('lottery_type', 'draw_number', name='uq_lottery_draw'),
    )
    
    def __repr__(self):
        return f"<LotteryResult {self.lottery_type} - {self.draw_number}>"
    
    def get_numbers_list(self):
        """Return numbers as a sorted Python list, handling both JSON and text formats"""
        if not self.main_numbers:
            return []
            
        numbers = []
        
        # If it's already JSON formatted (starts with [ )
        if isinstance(self.main_numbers, str) and self.main_numbers.strip().startswith('['):
            try:
                numbers = json.loads(self.main_numbers)
            except json.JSONDecodeError:
                pass
        
        # Handle comma-separated or space-separated numbers format
        elif isinstance(self.main_numbers, str):
            # Remove any bonus number indicator
            cleaned = self.main_numbers.split('+')[0].strip()
            
            # Check if comma-separated (like "1,2,3,18,29,32")
            if ',' in cleaned:
                numbers = [num.strip() for num in cleaned.split(',') if num.strip()]
            # Otherwise space-separated (like "09 18 19 30 31 40")
            else:
                numbers = [num.strip() for num in cleaned.split() if num.strip()]
            
        # If somehow numbers is already a list
        elif isinstance(self.main_numbers, list):
            numbers = self.main_numbers
            
        # Convert to integers and sort
        try:
            return sorted([int(num) for num in numbers if str(num).isdigit()])
        except (ValueError, TypeError):
            return numbers
    
    def get_bonus_numbers_list(self):
        """Return bonus numbers as a Python list, handling both JSON and text formats"""
        # If there's no bonus numbers
        if not self.bonus_numbers:
            # Check if bonus is in the main_numbers string (for text format like "09 18 19 30 31 40 + 28")
            if isinstance(self.main_numbers, str) and '+' in self.main_numbers:
                parts = self.main_numbers.split('+')
                if len(parts) > 1 and parts[1].strip():
                    return [parts[1].strip()]
            return []
            
        # If bonus_numbers is an integer, convert to string first
        if isinstance(self.bonus_numbers, int):
            return [str(self.bonus_numbers)]
            
        # If bonus_numbers is JSON formatted
        if isinstance(self.bonus_numbers, str) and self.bonus_numbers.strip().startswith('['):
            try:
                return json.loads(self.bonus_numbers)
            except json.JSONDecodeError:
                pass
                
        # If it's a space separated format
        if isinstance(self.bonus_numbers, str):
            # Handle comma-separated bonus numbers
            if ',' in self.bonus_numbers:
                return [num.strip() for num in self.bonus_numbers.split(',') if num.strip()]
            else:
                return [num.strip() for num in self.bonus_numbers.split() if num.strip()]
            
        # If somehow bonus_numbers is already a list
        if isinstance(self.bonus_numbers, list):
            return self.bonus_numbers
            
        # Fallback: convert whatever it is to string and return as single-item list
        return [str(self.bonus_numbers)]
    
    def get_divisions(self):
        """Return divisions data as a Python dict, or empty dict if None"""
        if self.divisions:
            try:
                return json.loads(self.divisions)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def get_parsed_divisions(self):
        """Return parsed divisions data for template display"""
        if not self.divisions or self.divisions == '[]':
            return None
            
        try:
            # Parse the JSON string from the database
            division_data = json.loads(self.divisions)
            return division_data
        except (json.JSONDecodeError, TypeError):
            return None
        
    def get_main_numbers_list(self):
        """Return main numbers as a list for analysis"""
        return self.get_numbers_list()
    
    def get_formatted_date(self):
        """Return properly formatted date string (YYYY-MM-DD)"""
        if self.draw_date:
            try:
                if isinstance(self.draw_date, datetime):
                    return self.draw_date.strftime('%Y-%m-%d')
                elif isinstance(self.draw_date, str):
                    return self.draw_date
                else:
                    return str(self.draw_date)
            except Exception:
                return str(self.draw_date)
        return "N/A"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'game_type': self.lottery_type,  # Updated field name for API
            'draw_id': self.draw_number,     # Updated field name for API
            'game_date': self.draw_date.isoformat() if self.draw_date else None,  # Updated field name for API
            'winning_numbers': self.get_numbers_list(),  # Updated field name for API
            'bonus_numbers': self.get_bonus_numbers_list(),
            'divisions': self.get_divisions(),
            'prize_divisions': json.loads(self.prize_divisions) if self.prize_divisions else None,
            'total_prize_pool': self.total_prize_pool,
            'rollover_amount': self.rollover_amount,
            'rollover_number': self.rollover_number,
            'total_pool_size': self.total_pool_size,
            'total_sales': self.total_sales,
            'draw_machine': self.draw_machine,
            'next_draw_date': self.next_draw_date,
            'estimated_jackpot': self.estimated_jackpot,
            'additional_info': self.additional_info
        }

class ScheduleConfig(db.Model):
    """Model for storing screenshot scheduling configurations"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False, unique=True)
    lottery_type = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(20), default='daily')  # daily, weekly, etc.
    hour = db.Column(db.Integer, default=1)  # Hour of day (0-23)
    minute = db.Column(db.Integer, default=0)  # Minute (0-59)
    active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScheduleConfig {self.lottery_type}: {self.frequency} at {self.hour}:{self.minute}>"

class ExtractionReview(DuplicateCheckMixin, db.Model):
    """Model for tracking lottery data extraction reviews and approvals"""
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    lottery_type = db.Column(db.String(50), nullable=False)
    
    # Extracted data fields
    extracted_numbers = db.Column(db.Text, nullable=True)  # JSON string
    extracted_bonus_numbers = db.Column(db.Text, nullable=True)  # JSON string
    extracted_draw_number = db.Column(db.Integer, nullable=True)
    extracted_draw_date = db.Column(db.Date, nullable=True)
    extracted_divisions = db.Column(db.Text, nullable=True)  # JSON string
    extracted_financial_info = db.Column(db.Text, nullable=True)  # JSON string
    
    # Review status
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, reprocessing
    reviewed_by = db.Column(db.String(100), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    
    # Processing information
    extraction_method = db.Column(db.String(50), default='gemini_2.5_pro')
    extraction_attempts = db.Column(db.Integer, default=1)
    confidence_score = db.Column(db.Float, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)  # seconds
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ExtractionReview {self.image_filename}: {self.status}>"
    
    def get_extracted_numbers_list(self):
        """Return extracted numbers as a list"""
        if self.extracted_numbers:
            try:
                return json.loads(self.extracted_numbers)
            except json.JSONDecodeError:
                return []
        return []
    
    def get_extracted_bonus_numbers_list(self):
        """Return extracted bonus numbers as a list"""
        if self.extracted_bonus_numbers:
            try:
                return json.loads(self.extracted_bonus_numbers)
            except json.JSONDecodeError:
                return []
        return []
    
    def get_extracted_divisions(self):
        """Return extracted divisions data"""
        if self.extracted_divisions:
            try:
                return json.loads(self.extracted_divisions)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def get_extracted_financial_info(self):
        """Return extracted financial information"""
        if self.extracted_financial_info:
            try:
                return json.loads(self.extracted_financial_info)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def approve(self, reviewed_by_name, notes=None):
        """Approve the extraction and save to main lottery_result table"""
        self.status = 'approved'
        self.reviewed_by = reviewed_by_name
        self.reviewed_at = datetime.utcnow()
        if notes:
            self.review_notes = notes
        
        # Create lottery result from approved data
        lottery_result = LotteryResult(
            lottery_type=self.lottery_type,
            draw_number=self.extracted_draw_number,
            draw_date=self.extracted_draw_date,
            numbers=self.extracted_numbers,
            bonus_numbers=self.extracted_bonus_numbers,
            divisions=self.extracted_divisions,
            total_prize_pool=self.get_extracted_financial_info().get('total_prize_pool'),
            rollover_amount=self.get_extracted_financial_info().get('rollover_amount'),
            rollover_number=self.get_extracted_financial_info().get('rollover_number'),
            total_pool_size=self.get_extracted_financial_info().get('total_pool_size'),
            total_sales=self.get_extracted_financial_info().get('total_sales'),
            draw_machine=self.get_extracted_financial_info().get('draw_machine'),
            next_draw_date=self.get_extracted_financial_info().get('next_draw_date'),
            estimated_jackpot=self.get_extracted_financial_info().get('estimated_jackpot'),
            additional_info=self.get_extracted_financial_info().get('additional_info')
        )
        
        db.session.add(lottery_result)
        db.session.commit()
        return lottery_result
    
    def reject(self, reviewed_by_name, notes=None):
        """Reject the extraction for reprocessing"""
        self.status = 'rejected'
        self.reviewed_by = reviewed_by_name
        self.reviewed_at = datetime.utcnow()
        if notes:
            self.review_notes = notes
        db.session.commit()
    
    def request_deeper_extraction(self, reviewed_by_name, notes=None):
        """Request deeper extraction processing"""
        self.status = 'reprocessing'
        self.reviewed_by = reviewed_by_name
        self.reviewed_at = datetime.utcnow()
        self.extraction_attempts += 1
        if notes:
            self.review_notes = notes
        db.session.commit()

class Campaign(DuplicateCheckMixin, db.Model):
    """Model for grouping advertisements into campaigns"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    budget = db.Column(db.Numeric(10, 2), nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    # Define relationship with ad impressions - using campaign_rel as backref to avoid conflicts
    impressions = db.relationship('AdImpression', backref='campaign_rel', lazy=True)
    status = db.Column(db.String(20), default='draft') # draft, active, paused, completed
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='campaigns')
    
    def __repr__(self):
        return f"<Campaign {self.name}>"
    
    def get_spent_budget(self):
        """Calculate spent budget based on impressions and kicks"""
        # Since we've removed the ad system, we always return 0
        return 0
    
    def get_remaining_budget(self):
        """Calculate remaining budget"""
        if not self.budget:
            return None
        return float(self.budget) - self.get_spent_budget()
    
    def get_budget_usage_percent(self):
        """Calculate budget usage as percentage"""
        if not self.budget or float(self.budget) == 0:
            return 0
        return min(100, round((self.get_spent_budget() / float(self.budget)) * 100, 2))
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        # Get ad count from database query
        from sqlalchemy import func
        from flask import current_app
        
        try:
            # This is a safer approach than relying on non-existent relationships
            ad_count = 0
            with current_app.app_context():
                from sqlalchemy.orm import Session
                session = Session(db.engine)
                ad_count_query = session.query(func.count(Advertisement.id)).filter_by(campaign_id=self.id).scalar()
                ad_count = ad_count_query or 0
        except:
            ad_count = 0
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'budget': float(self.budget) if self.budget else None,
            'spent_budget': self.get_spent_budget(),
            'budget_usage': self.get_budget_usage_percent(),
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'ad_count': ad_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AdVariation(db.Model):
    """Model for A/B testing ad variations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_ad_id = db.Column(db.Integer, db.ForeignKey('advertisement.id'), nullable=False)
    variation_type = db.Column(db.String(20), default='content', comment="Type of variation: content, message, image, duration")
    file_path = db.Column(db.String(255), nullable=True)
    file_type = db.Column(db.String(20), nullable=True)
    html_content = db.Column(db.Text, nullable=True)
    custom_message = db.Column(db.Text, nullable=True)
    custom_image_path = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    
    # Test parameters
    traffic_percentage = db.Column(db.Integer, default=50, comment="Percentage of traffic to show this variation")
    is_control = db.Column(db.Boolean, default=False, comment="Whether this is the control variation")
    
    # Statistics
    total_impressions = db.Column(db.Integer, default=0)
    total_clicks = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent_ad = db.relationship('Advertisement', backref='variations')
    impressions = db.relationship('AdImpression', backref='variation', 
                                foreign_keys='AdImpression.variation_id',
                                cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<AdVariation {self.name} for Ad {self.parent_ad_id}>"
    
    def get_ctr(self):
        """Calculate Click-Through Rate"""
        if not self.total_impressions:
            return 0
        return round((self.total_clicks / self.total_impressions) * 100, 2)
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_ad_id': self.parent_ad_id,
            'variation_type': self.variation_type,
            'traffic_percentage': self.traffic_percentage,
            'is_control': self.is_control,
            'total_impressions': self.total_impressions,
            'total_clicks': self.total_clicks,
            'ctr': self.get_ctr(),
            'created_at': self.created_at.isoformat()
        }

class Advertisement(DuplicateCheckMixin, db.Model):
    """Model for managing video advertisements"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), nullable=False, default='video/mp4')
    duration = db.Column(db.Integer, nullable=False, comment="Duration in seconds")
    
    # Ad placement and targeting
    placement = db.Column(db.String(50), nullable=False, default='scanner', 
                         comment="Where the ad appears: scanner, results, homepage")
    target_impressions = db.Column(db.Integer, nullable=False, default=1000,
                                 comment="Target number of impressions")
    
    # Status
    active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=5, comment="1-10, higher number = higher priority")
    
    # Statistics
    total_impressions = db.Column(db.Integer, default=0)
    total_clicks = db.Column(db.Integer, default=0)
    
    # Custom loading overlay content
    custom_message = db.Column(db.Text, nullable=True, comment="Custom message to display in the loading overlay")
    custom_image_path = db.Column(db.String(255), nullable=True, comment="Path to custom image for loading overlay")
    loading_duration = db.Column(db.Integer, default=10, comment="Duration in seconds for the loading overlay (default 10s)")
    is_rich_content = db.Column(db.Boolean, default=False, comment="Whether this ad uses rich HTML content")
    html_content = db.Column(db.Text, nullable=True, comment="Custom HTML content for the ad")
    
    # Constraints 
    start_date = db.Column(db.DateTime, nullable=True, comment="When to start showing this ad")
    end_date = db.Column(db.DateTime, nullable=True, comment="When to stop showing this ad")
    
    # Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Campaign association - Create this column in the database if needed for campaign functionality
    # Commented out until database migration is performed
    # campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True)
    
    # Relationships
    created_by = db.relationship('User', backref='advertisements')
    impressions = db.relationship('AdImpression', backref='advertisement', 
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Advertisement {self.name}>"
    
    def get_file_url(self):
        """Return the URL to the advertisement file"""
        if os.path.exists(self.file_path):
            # Convert absolute file path to relative URL
            relative_path = os.path.relpath(self.file_path, start=os.getcwd())
            if relative_path.startswith('static/'):
                return '/' + relative_path
            return '/static/ads/' + os.path.basename(self.file_path)
        return None
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'file_url': self.get_file_url(),
            'file_path': self.file_path,
            'file_type': self.file_type,
            'duration': self.duration,
            'placement': self.placement,
            'active': self.active,
            'priority': self.priority,
            'target_impressions': self.target_impressions,
            'total_impressions': self.total_impressions,
            'total_clicks': self.total_clicks,
            'custom_message': self.custom_message,
            'custom_image_path': self.custom_image_path,
            'loading_duration': self.loading_duration,
            'is_rich_content': self.is_rich_content,
            'html_content': self.html_content,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def is_eligible_for_display(self):
        """Check if this ad is eligible to be displayed"""
        now = datetime.utcnow()
        
        # Check if ad is active
        if not self.active:
            return False
        
        # Check start/end dates if set
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
            
        # Check if we've reached target impressions
        if self.target_impressions and self.total_impressions >= self.target_impressions:
            return False
            
        return True

class AdImpression(db.Model):
    """Model for tracking advertisement impressions"""
    id = db.Column(db.Integer, primary_key=True)
    ad_id = db.Column(db.Integer, db.ForeignKey('advertisement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(64), nullable=False, comment="Browser session ID")
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Variation tracking for A/B testing
    variation_id = db.Column(db.Integer, db.ForeignKey('ad_variation.id'), nullable=True)
    is_ab_test = db.Column(db.Boolean, default=False)
    
    # Demographic information
    country = db.Column(db.String(2), nullable=True)
    region = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    device_type = db.Column(db.String(20), nullable=True, comment="desktop, mobile, tablet")
    
    # Impression details
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    page = db.Column(db.String(100), nullable=True, comment="Page where impression occurred")
    duration_viewed = db.Column(db.Integer, nullable=True, comment="Seconds the ad was viewed")
    was_clicked = db.Column(db.Boolean, default=False)
    
    # Revenue tracking
    cost = db.Column(db.Numeric(10, 4), nullable=True, comment="Cost of this impression")
    revenue = db.Column(db.Numeric(10, 4), nullable=True, comment="Revenue from this impression")
    
    # Campaign tracking
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True)
    
    # Relationships 
    # Removed duplicate backref that was conflicting with Campaign.impressions
    
    def __repr__(self):
        return f"<AdImpression {self.id}: Ad {self.ad_id}>"
        
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'ad_id': self.ad_id,
            'timestamp': self.timestamp.isoformat(),
            'page': self.page,
            'duration_viewed': self.duration_viewed,
            'was_clicked': self.was_clicked,
            'variation_id': self.variation_id,
            'is_ab_test': self.is_ab_test,
            'device_type': self.device_type,
            'region': self.region
        }
        
class ImportHistory(db.Model):
    """Model for tracking data import history"""
    __tablename__ = 'import_history'
    
    id = db.Column(db.Integer, primary_key=True)
    import_date = db.Column(db.DateTime, default=datetime.utcnow)
    import_type = db.Column(db.String(50), nullable=False, comment="Type of import (excel, snap_lotto, etc.)")
    file_name = db.Column(db.String(255), nullable=True)
    records_added = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    total_processed = db.Column(db.Integer, default=0)
    errors = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='import_history')
    imported_records = db.relationship('ImportedRecord', backref='import_history',
                                     cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<ImportHistory {self.id}: {self.import_date}>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'import_date': self.import_date.isoformat(),
            'import_type': self.import_type,
            'file_name': self.file_name,
            'records_added': self.records_added,
            'records_updated': self.records_updated,
            'total_processed': self.total_processed,
            'errors': self.errors,
            'user': self.user.username if self.user else None
        }
    
    @classmethod
    def get_recent_imports(cls, limit=10):
        """Get the most recent imports"""
        return cls.query.order_by(cls.import_date.desc()).limit(limit).all()

class ImportedRecord(db.Model):
    """Model for tracking individual records that were added during an import"""
    __tablename__ = 'imported_record'
    
    id = db.Column(db.Integer, primary_key=True)
    import_id = db.Column(db.Integer, db.ForeignKey('import_history.id'), nullable=False)
    lottery_type = db.Column(db.String(50), nullable=False)
    draw_number = db.Column(db.String(20), nullable=True)
    draw_date = db.Column(db.DateTime, nullable=True)
    is_new = db.Column(db.Boolean, default=True, comment="Whether this was a new record or an update")
    lottery_result_id = db.Column(db.Integer, db.ForeignKey('lottery_results.id'), nullable=False)
    
    # Relationship to the actual lottery result
    lottery_result = db.relationship('LotteryResult', backref='import_entries')
    
    def __repr__(self):
        return f"<ImportedRecord {self.id}: {self.lottery_type} {self.draw_number}>"
        
class ScannedTicket(db.Model):
    """Model for storing scanned lottery ticket data and results"""
    __tablename__ = 'scanned_ticket'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Ticket information
    lottery_type = db.Column(db.String(50), nullable=False)
    ticket_lines = db.Column(db.JSON, nullable=False, comment="Array of number arrays for each ticket line")
    powerball_numbers = db.Column(db.JSON, nullable=True, comment="PowerBall numbers if applicable")
    draw_date = db.Column(db.String(20), nullable=True)
    draw_number = db.Column(db.String(20), nullable=True)
    ticket_cost = db.Column(db.String(20), nullable=True)
    powerball_plus_included = db.Column(db.String(10), nullable=True)
    
    # Scan metadata
    scan_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    original_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    
    # Match results
    match_results = db.Column(db.JSON, nullable=True, comment="Complete match analysis results")
    has_matches = db.Column(db.Boolean, default=False)
    total_matches = db.Column(db.Integer, default=0)
    
    # Processing info
    gemini_response = db.Column(db.Text, nullable=True, comment="Raw Gemini API response")
    processing_time = db.Column(db.Float, nullable=True, comment="Processing time in seconds")
    
    def __repr__(self):
        return f"<ScannedTicket {self.id}: {self.lottery_type}>"
    
    def get_ticket_lines_list(self):
        """Return ticket lines as list"""
        if self.ticket_lines:
            return json.loads(self.ticket_lines) if isinstance(self.ticket_lines, str) else self.ticket_lines
        return []
    
    def get_powerball_numbers_list(self):
        """Return powerball numbers as list"""
        if self.powerball_numbers:
            return json.loads(self.powerball_numbers) if isinstance(self.powerball_numbers, str) else self.powerball_numbers
        return []
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'lottery_type': self.lottery_type,
            'ticket_lines': self.get_ticket_lines_list(),
            'powerball_numbers': self.get_powerball_numbers_list(),
            'draw_date': self.draw_date,
            'draw_number': self.draw_number,
            'ticket_cost': self.ticket_cost,
            'powerball_plus_included': self.powerball_plus_included,
            'scan_timestamp': self.scan_timestamp.isoformat() if self.scan_timestamp else None,
            'original_filename': self.original_filename,
            'has_matches': self.has_matches,
            'total_matches': self.total_matches,
            'match_results': json.loads(self.match_results) if isinstance(self.match_results, str) else self.match_results,
            'processing_time': self.processing_time
        }

class LotteryPrediction(db.Model):
    """Model for storing lottery number predictions"""
    __tablename__ = 'lottery_prediction'
    
    id = db.Column(db.Integer, primary_key=True)
    lottery_type = db.Column(db.String(50), nullable=False)
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    draw_date = db.Column(db.DateTime, nullable=True)  # The date this prediction is for
    predicted_numbers = db.Column(db.Text, nullable=False)  # JSON string of predicted numbers
    bonus_number = db.Column(db.Integer, nullable=True)  # For Powerball-type games
    strategy = db.Column(db.String(50), nullable=False)  # Method used for prediction
    confidence_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0 confidence in prediction
    model_version = db.Column(db.String(20), nullable=True)  # Version of prediction model used
    parameters = db.Column(db.Text, nullable=True)  # JSON string of parameters used
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)  # Whether prediction has been verified against actual results
    
    # Relationships
    user = db.relationship('User', backref='predictions')
    
    def __repr__(self):
        return f"<LotteryPrediction {self.id}: {self.lottery_type} - {self.prediction_date.strftime('%Y-%m-%d')}, {self.strategy}>"
    
    def get_numbers_list(self):
        """Return predicted numbers as a Python list"""
        return json.loads(self.predicted_numbers)
    
    def get_parameters_dict(self):
        """Return parameters as a Python dict, or empty dict if None"""
        if self.parameters:
            return json.loads(self.parameters)
        return {}
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'lottery_type': self.lottery_type,
            'prediction_date': self.prediction_date.isoformat(),
            'draw_date': self.draw_date.isoformat() if self.draw_date else None,
            'predicted_numbers': self.get_numbers_list(),
            'bonus_number': self.bonus_number,
            'strategy': self.strategy,
            'confidence_score': self.confidence_score,
            'model_version': self.model_version,
            'parameters': self.get_parameters_dict(),
            'is_verified': self.is_verified
        }

class PredictionResult(db.Model):
    """Model for tracking results of predictions"""
    __tablename__ = 'prediction_result'
    
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey('lottery_prediction.id'), nullable=False)
    actual_draw_id = db.Column(db.Integer, db.ForeignKey('lottery_results.id'), nullable=True)
    draw_date = db.Column(db.DateTime, nullable=True)
    matched_numbers = db.Column(db.Integer, default=0)  # Number of correctly predicted main numbers
    matched_bonus = db.Column(db.Boolean, default=False)  # Whether bonus number was correctly predicted
    match_positions = db.Column(db.Text, nullable=True)  # JSON string of positions that matched
    accuracy_score = db.Column(db.Float, default=0.0)  # Overall accuracy of prediction (0.0 to 1.0)
    verification_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    prediction = db.relationship('LotteryPrediction', backref='results')
    actual_draw = db.relationship('LotteryResult', backref='prediction_results')
    
    def __repr__(self):
        return f"<PredictionResult {self.id}: {self.matched_numbers} matches, Score: {self.accuracy_score}>"
    
    def get_match_positions(self):
        """Return match positions as a Python list"""
        if self.match_positions:
            return json.loads(self.match_positions)
        return []
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'prediction_id': self.prediction_id,
            'draw_date': self.draw_date.isoformat() if self.draw_date else None,
            'matched_numbers': self.matched_numbers,
            'matched_bonus': self.matched_bonus,
            'match_positions': self.get_match_positions(),
            'accuracy_score': self.accuracy_score,
            'verification_date': self.verification_date.isoformat()
        }

class ModelTrainingHistory(db.Model):
    """Model for tracking model training history and improvements"""
    __tablename__ = 'model_training_history'
    
    id = db.Column(db.Integer, primary_key=True)
    lottery_type = db.Column(db.String(50), nullable=False)
    model_version = db.Column(db.String(20), nullable=False)
    training_date = db.Column(db.DateTime, default=datetime.utcnow)
    training_data_size = db.Column(db.Integer, nullable=False)  # Number of draws used for training
    accuracy_score = db.Column(db.Float, nullable=False)  # Model accuracy score
    error_rate = db.Column(db.Float, nullable=False)  # Model error rate
    features_used = db.Column(db.Text, nullable=True)  # JSON string of features used in training
    hyperparameters = db.Column(db.Text, nullable=True)  # JSON string of hyperparameters
    notes = db.Column(db.Text, nullable=True)  # Any notes about this training run
    
    def __repr__(self):
        return f"<ModelTrainingHistory {self.id}: {self.lottery_type} v{self.model_version}, Accuracy: {self.accuracy_score}>"
    
    def get_features_list(self):
        """Return features used as a Python list"""
        if self.features_used:
            return json.loads(self.features_used)
        return []
    
    def get_hyperparameters_dict(self):
        """Return hyperparameters as a Python dict"""
        if self.hyperparameters:
            return json.loads(self.hyperparameters)
        return {}
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'lottery_type': self.lottery_type,
            'model_version': self.model_version,
            'training_date': self.training_date.isoformat(),
            'training_data_size': self.training_data_size,
            'accuracy_score': self.accuracy_score,
            'error_rate': self.error_rate,
            'features_used': self.get_features_list(),
            'hyperparameters': self.get_hyperparameters_dict(),
            'notes': self.notes
        }
        
    @classmethod
    def get_records_for_import(cls, import_id):
        """Get all records for a specific import"""
        return cls.query.filter_by(import_id=import_id).all()
        
        
class APIRequestLog(db.Model):
    """Model for tracking API requests to external services like Anthropic"""
    __tablename__ = 'api_request_log'
    
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(50), nullable=False, comment="Name of the external service (e.g., 'anthropic')")
    endpoint = db.Column(db.String(255), nullable=False, comment="The specific API endpoint or method called")
    model = db.Column(db.String(100), nullable=True, comment="Model name used for the request (e.g., 'claude-3-5-sonnet')")
    prompt_tokens = db.Column(db.Integer, nullable=True, comment="Number of tokens in the prompt")
    completion_tokens = db.Column(db.Integer, nullable=True, comment="Number of tokens in the completion/response")
    total_tokens = db.Column(db.Integer, nullable=True, comment="Total tokens used for the request")
    status = db.Column(db.String(20), default='success', comment="Status of the request: success, error")
    duration_ms = db.Column(db.Integer, nullable=True, comment="Duration of the request in milliseconds")
    error_message = db.Column(db.Text, nullable=True, comment="Error message if the request failed")
    request_id = db.Column(db.String(100), nullable=True, comment="Provider's request ID for tracking")
    screenshot_id = db.Column(db.Integer, db.ForeignKey('screenshot.id'), nullable=True)
    lottery_type = db.Column(db.String(50), nullable=True, comment="Related lottery type if applicable")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    screenshot = db.relationship('Screenshot', backref='api_requests')
    
    @classmethod
    def log_request(cls, service, endpoint, model=None, prompt_tokens=None, completion_tokens=None, 
                   status='success', duration_ms=None, error_message=None, request_id=None, 
                   screenshot_id=None, lottery_type=None):
        """Create a log entry for an API request"""
        log_entry = cls(
            service=service,
            endpoint=endpoint,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=((prompt_tokens or 0) + (completion_tokens or 0)) if prompt_tokens or completion_tokens else None,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message,
            request_id=request_id,
            screenshot_id=screenshot_id,
            lottery_type=lottery_type
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    @classmethod
    def get_stats_by_date_range(cls, service=None, start_date=None, end_date=None):
        """Get statistics for API requests in a given date range"""
        from sqlalchemy import func
        
        query = db.session.query(
            func.count(cls.id).label('total_requests'),
            func.sum(cls.total_tokens).label('total_tokens'),
            func.avg(cls.duration_ms).label('avg_duration')
        )
        
        if service:
            query = query.filter(cls.service == service)
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
            
        if end_date:
            query = query.filter(cls.created_at <= end_date)
            
        stats = query.first()
        
        # Format the results into a dictionary
        return {
            'total_requests': stats.total_requests if stats else 0,
            'total_tokens': int(stats.total_tokens) if stats and stats.total_tokens else 0,
            'avg_duration': round(float(stats.avg_duration), 2) if stats and stats.avg_duration else 0
        }
        
# APIRequestLog is already defined elsewhere in this file
# Keeping the model here would cause a duplicate table definition error

# Removed duplicate LotteryResults model - using LotteryResult model above with __tablename__ = 'lottery_results'