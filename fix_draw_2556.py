#!/usr/bin/env python3
"""
Fix draw 2556 by properly saving the approved extraction to lottery_results table
"""
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, ExtractionReview, LotteryResult
from main import app

def fix_draw_2556():
    """Process the approved extraction for draw 2556"""
    with app.app_context():
        # Find the extraction review for draw 2556
        extraction = ExtractionReview.query.filter_by(id=3, extracted_draw_number=2556).first()
        
        if not extraction:
            print("ERROR: Could not find extraction review for draw 2556")
            return False
        
        print(f"Found extraction: {extraction.lottery_type} Draw {extraction.extracted_draw_number}")
        print(f"Status: {extraction.status}")
        print(f"Numbers: {extraction.extracted_numbers}")
        print(f"Bonus: {extraction.extracted_bonus_numbers}")
        
        # Check if it already exists in lottery_results
        existing = LotteryResult.query.filter_by(
            lottery_type='LOTTO',
            draw_number=2556
        ).first()
        
        if existing:
            print(f"Draw 2556 already exists in lottery_results with ID {existing.id}")
            return True
        
        # Create the lottery result using the approve method
        try:
            lottery_result = extraction.approve('admin', 'Manual fix for draw 2556')
            print(f"Successfully created lottery result with ID {lottery_result.id}")
            print(f"Lottery Type: {lottery_result.lottery_type}")
            print(f"Draw Number: {lottery_result.draw_number}")
            print(f"Draw Date: {lottery_result.draw_date}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to create lottery result: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = fix_draw_2556()
    sys.exit(0 if success else 1)