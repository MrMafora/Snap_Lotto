"""
Database models for the application
"""
from datetime import datetime
import json
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy base
class Base(DeclarativeBase):
    pass

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
    id = db.Column(db.Integer, primary_key=True)
    lottery_type = db.Column(db.String(50), nullable=False, comment="Game Type")
    draw_number = db.Column(db.String(20), nullable=True, comment="Draw ID")
    draw_date = db.Column(db.DateTime, nullable=False, comment="Game Date")
    numbers = db.Column(db.String(255), nullable=False, comment="Winning Numbers (JSON string array)")  # Stored as JSON string
    bonus_numbers = db.Column(db.String(255), nullable=True, comment="Bonus Numbers (JSON string array)")  # Stored as JSON string
    divisions = db.Column(db.Text, nullable=True, comment="Prize Divisions Data (JSON string)")  # Stored as JSON string with division, winners, and prize amount
    source_url = db.Column(db.String(255), nullable=False)
    screenshot_id = db.Column(db.Integer, db.ForeignKey('screenshot.id'), nullable=True)
    ocr_provider = db.Column(db.String(50), nullable=True, comment="OCR Provider (anthropic)")
    ocr_model = db.Column(db.String(100), nullable=True, comment="OCR Model used")
    ocr_timestamp = db.Column(db.DateTime, nullable=True, comment="When OCR was performed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (
        db.UniqueConstraint('lottery_type', 'draw_number', name='uq_lottery_draw'),
    )
    
    def __repr__(self):
        return f"<LotteryResult {self.lottery_type} - {self.draw_number}>"
    
    def get_numbers_list(self):
        """Return numbers as a Python list"""
        return json.loads(self.numbers)
    
    def get_bonus_numbers_list(self):
        """Return bonus numbers as a Python list, or empty list if None"""
        if self.bonus_numbers:
            return json.loads(self.bonus_numbers)
        return []
    
    def get_divisions(self):
        """Return divisions data as a Python dict, or empty dict if None"""
        if self.divisions:
            return json.loads(self.divisions)
        return {}
    
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
            'source_url': self.source_url,
            'ocr_info': {
                'provider': self.ocr_provider,
                'model': self.ocr_model,
                'timestamp': self.ocr_timestamp.isoformat() if self.ocr_timestamp else None
            }
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

class Advertisement(db.Model):
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
            'duration': self.duration,
            'placement': self.placement,
            'active': self.active,
            'priority': self.priority,
            'target_impressions': self.target_impressions,
            'total_impressions': self.total_impressions,
            'total_clicks': self.total_clicks,
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
    
    # Impression details
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    page = db.Column(db.String(100), nullable=True, comment="Page where impression occurred")
    duration_viewed = db.Column(db.Integer, nullable=True, comment="Seconds the ad was viewed")
    was_clicked = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<AdImpression {self.id}: Ad {self.ad_id}>"
        
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
    lottery_result_id = db.Column(db.Integer, db.ForeignKey('lottery_result.id'), nullable=False)
    
    # Relationship to the actual lottery result
    lottery_result = db.relationship('LotteryResult', backref='import_entries')
    
    def __repr__(self):
        return f"<ImportedRecord {self.id}: {self.lottery_type} {self.draw_number}>"
        
    @classmethod
    def get_records_for_import(cls, import_id):
        """Get all records for a specific import"""
        return cls.query.filter_by(import_id=import_id).all()