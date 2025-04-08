from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr

# These models will be bound to the db instance in app.py
class Screenshot:
    """Model for storing screenshot information"""
    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
    lottery_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    path = Column(String(255), nullable=False)
    processed = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Screenshot {self.id}: {self.lottery_type}>"

class LotteryResult:
    """Model for storing lottery results extracted from screenshots"""
    id = Column(Integer, primary_key=True)
    lottery_type = Column(String(50), nullable=False)
    draw_number = Column(String(20), nullable=True)
    draw_date = Column(DateTime, nullable=False)
    numbers = Column(String(255), nullable=False)  # Stored as JSON string
    bonus_numbers = Column(String(255), nullable=True)  # Stored as JSON string
    source_url = Column(String(255), nullable=False)
    screenshot_id = Column(Integer, ForeignKey('screenshot.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @declared_attr
    def __table_args__(cls):
        # Unique constraint to prevent duplicate entries
        return (UniqueConstraint('lottery_type', 'draw_number', name='uq_lottery_draw'),)
    
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

class ScheduleConfig:
    """Model for storing screenshot scheduling configurations"""
    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False, unique=True)
    lottery_type = Column(String(50), nullable=False)
    frequency = Column(String(20), default='daily')  # daily, weekly, etc.
    hour = Column(Integer, default=1)  # Hour of day (0-23)
    minute = Column(Integer, default=0)  # Minute (0-59)
    active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScheduleConfig {self.lottery_type}: {self.frequency} at {self.hour}:{self.minute}>"
