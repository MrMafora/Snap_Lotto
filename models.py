"""
Database models for the South African Lottery Scanner
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

class LotteryResult(db.Model):
    """Model for storing lottery results"""
    __tablename__ = 'lottery_results'
    
    id = db.Column(db.Integer, primary_key=True)
    lottery_type = db.Column(db.String(50), nullable=False)
    draw_number = db.Column(db.Integer, nullable=False)
    draw_date = db.Column(db.Date, nullable=False)
    main_numbers = db.Column(db.String(200))  # Main winning numbers as text/JSON
    bonus_numbers = db.Column(db.String(100))  # Bonus numbers as text/JSON
    divisions = db.Column(db.JSON)  # Prize divisions data
    rollover_amount = db.Column(db.Float)
    next_jackpot = db.Column(db.Float)
    total_pool_size = db.Column(db.Float)
    total_sales = db.Column(db.Float)
    draw_machine = db.Column(db.String(50))
    next_draw_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for better performance
    __table_args__ = (
        db.Index('idx_lottery_type_draw_date', 'lottery_type', 'draw_date'),
        db.Index('idx_lottery_type_draw_number', 'lottery_type', 'draw_number'),
        db.Index('idx_draw_date', 'draw_date'),
        db.Index('idx_lottery_type', 'lottery_type'),
    )

class ExtractionReview(db.Model):
    """Model for tracking image extraction reviews"""
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(255), nullable=False)
    lottery_type = db.Column(db.String(50), nullable=False)
    extracted_data = db.Column(db.JSON, nullable=False)
    confidence_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reviewer_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class HealthCheck(db.Model):
    """Model for system health monitoring"""
    id = db.Column(db.Integer, primary_key=True)
    check_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pass, fail, warning
    details = db.Column(db.JSON)
    response_time = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Alert(db.Model):
    """Model for system alerts"""
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='info')  # info, warning, error, critical
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

class SystemLog(db.Model):
    """Model for system logging"""
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class APIKey(db.Model):
    """Model for API key management"""
    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permissions = db.Column(db.JSON, default=list)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

class PredictionModel(db.Model):
    """Model for storing prediction models"""
    id = db.Column(db.Integer, primary_key=True)
    lottery_type = db.Column(db.String(50), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)
    model_data = db.Column(db.JSON, nullable=False)
    accuracy_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserPreference(db.Model):
    """Model for user preferences"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    preference_key = db.Column(db.String(50), nullable=False)
    preference_value = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'preference_key'),
    )

class Screenshot(db.Model):
    """Model for storing screenshot information"""
    id = db.Column(db.Integer, primary_key=True)
    lottery_type = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(500), nullable=False)  # Source URL
    filename = db.Column(db.String(255), nullable=False)  # Screenshot filename
    file_path = db.Column(db.String(500), nullable=False)  # Full file path
    file_size = db.Column(db.Integer)  # File size in bytes
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, archived, failed
    capture_method = db.Column(db.String(50), default='selenium')  # selenium, playwright, etc.
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    __table_args__ = (
        db.Index('idx_lottery_type_timestamp', 'lottery_type', 'timestamp'),
        db.Index('idx_status', 'status'),
    )

class LotteryPrediction(db.Model):
    """Model for storing AI-generated lottery predictions"""
    __tablename__ = 'lottery_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    game_type = db.Column(db.String(50), nullable=False)
    predicted_numbers = db.Column(db.String(200), nullable=False)  # JSON string of predicted numbers
    bonus_numbers = db.Column(db.String(100))  # JSON string of bonus numbers
    confidence_score = db.Column(db.Float, nullable=False)
    prediction_method = db.Column(db.String(100), default='Phase 2 ML')
    reasoning = db.Column(db.Text)
    target_draw_date = db.Column(db.Date, nullable=False)
    linked_draw_id = db.Column(db.Integer)  # Draw number this prediction is for
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)
    validation_status = db.Column(db.String(20), default='pending')  # pending, validated, invalid
    accuracy_score = db.Column(db.Float)
    main_number_matches = db.Column(db.Integer, default=0)
    bonus_number_matches = db.Column(db.Integer, default=0)
    accuracy_percentage = db.Column(db.Float)
    prize_tier = db.Column(db.String(50))
    matched_main_numbers = db.Column(db.String(200))  # JSON string
    matched_bonus_numbers = db.Column(db.String(100))  # JSON string
    
    __table_args__ = (
        db.Index('idx_game_type_target_date', 'game_type', 'target_draw_date'),
        db.Index('idx_validation_status', 'validation_status'),
        db.Index('idx_target_draw_date', 'target_draw_date'),
    )