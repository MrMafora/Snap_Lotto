from datetime import datetime
from app import db
import json

class Screenshot(db.Model):
    """Model for storing screenshot information"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    lottery_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    path = db.Column(db.String(255), nullable=False)
    processed = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<Screenshot {self.id}: {self.lottery_type}>"

class LotteryResult(db.Model):
    """Model for storing lottery results extracted from screenshots"""
    id = db.Column(db.Integer, primary_key=True)
    lottery_type = db.Column(db.String(50), nullable=False)
    draw_number = db.Column(db.String(20), nullable=True)
    draw_date = db.Column(db.DateTime, nullable=False)
    numbers = db.Column(db.String(255), nullable=False)  # Stored as JSON string
    bonus_numbers = db.Column(db.String(255), nullable=True)  # Stored as JSON string
    source_url = db.Column(db.String(255), nullable=False)
    screenshot_id = db.Column(db.Integer, db.ForeignKey('screenshot.id'), nullable=True)
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
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'lottery_type': self.lottery_type,
            'draw_number': self.draw_number,
            'draw_date': self.draw_date.isoformat() if self.draw_date else None,
            'numbers': self.get_numbers_list(),
            'bonus_numbers': self.get_bonus_numbers_list(),
            'source_url': self.source_url
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
