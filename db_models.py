from datetime import datetime
import json
from app import db

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
    lottery_type = db.Column(db.String(50), nullable=False, comment="Game Type")
    draw_number = db.Column(db.String(20), nullable=True, comment="Draw ID")
    draw_date = db.Column(db.DateTime, nullable=False, comment="Game Date")
    numbers = db.Column(db.String(255), nullable=False, comment="Winning Numbers (JSON string array)")  # Stored as JSON string
    bonus_numbers = db.Column(db.String(255), nullable=True, comment="Bonus Numbers (JSON string array)")  # Stored as JSON string
    divisions = db.Column(db.Text, nullable=True, comment="Prize Divisions Data (JSON string)")  # Stored as JSON string with division, winners, and prize amount
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