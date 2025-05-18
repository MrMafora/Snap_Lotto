#!/usr/bin/env python3
"""
Script to clean up invalid screenshot database records

This script removes screenshot records that have missing file paths
to prevent errors when viewing screenshots.
"""
import os
import sys
from flask import Flask
from models import db, Screenshot
from config import Config

def create_app():
    """Create Flask application instance with database connection"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def cleanup_invalid_screenshots(app):
    """
    Remove screenshot records with missing file paths
    
    Args:
        app: Flask application instance
        
    Returns:
        int: Number of records deleted
    """
    with app.app_context():
        # Get all screenshots with missing paths
        invalid_screenshots = Screenshot.query.filter(
            Screenshot.path.is_(None)
        ).all()
        
        if not invalid_screenshots:
            print("No invalid screenshots found.")
            return 0
        
        print(f"Found {len(invalid_screenshots)} screenshots with missing paths:")
        for ss in invalid_screenshots:
            print(f"ID: {ss.id}, Type: {ss.lottery_type}")
        
        # Confirm deletion
        confirmation = input("Delete these records? (y/n): ")
        if confirmation.lower() != 'y':
            print("Operation cancelled.")
            return 0
        
        # Delete invalid screenshots
        for ss in invalid_screenshots:
            db.session.delete(ss)
        
        db.session.commit()
        print(f"Deleted {len(invalid_screenshots)} invalid screenshot records.")
        return len(invalid_screenshots)

if __name__ == "__main__":
    app = create_app()
    cleanup_invalid_screenshots(app)