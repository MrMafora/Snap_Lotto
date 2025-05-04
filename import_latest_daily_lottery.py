#!/usr/bin/env python3
"""
Import missing Daily Lottery draws from spreadsheet text data
"""
import json
import os
import sys
from datetime import datetime

# Application context is required for database queries
from main import app
from models import LotteryResult, db

# The missing Daily Lottery draws we need to add
MISSING_DRAWS = [
    {
        "lottery_type": "Daily Lottery",
        "draw_number": "2240",
        "draw_date": "2025-05-02",
        "numbers": [7, 10, 29, 31, 35],
        "divisions_data": {
            "Division 1": {"description": "5 Correct Numbers", "winners": 1, "prize": "R437,418.80"},
            "Division 2": {"description": "4 Correct Numbers", "winners": 348, "prize": "R348.60"},
            "Division 3": {"description": "3 Correct Numbers", "winners": 10154, "prize": "R25.00"},
            "Division 4": {"description": "2 Correct Numbers", "winners": 91279, "prize": "R5.00"},
        }
    },
    {
        "lottery_type": "Daily Lottery",
        "draw_number": "2241",
        "draw_date": "2025-05-03",
        "numbers": [2, 6, 18, 23, 24],
        "divisions_data": {
            "Division 1": {"description": "5 Correct Numbers", "winners": 2, "prize": "R221,744.50"},
            "Division 2": {"description": "4 Correct Numbers", "winners": 378, "prize": "R322.90"},
            "Division 3": {"description": "3 Correct Numbers", "winners": 9871, "prize": "R25.00"},
            "Division 4": {"description": "2 Correct Numbers", "winners": 92587, "prize": "R5.00"},
        }
    }
]

def import_latest_daily_lottery():
    """
    Import missing Daily Lottery draws from data
    """
    with app.app_context():
        print('--- Importing Latest Daily Lottery Draws ---')
        
        imported_count = 0
        for draw_data in MISSING_DRAWS:
            # Check if draw already exists
            existing_draw = LotteryResult.query.filter_by(
                lottery_type=draw_data["lottery_type"],
                draw_number=draw_data["draw_number"]
            ).first()
            
            if existing_draw:
                print(f"Draw #{draw_data['draw_number']} already exists - skipping")
                continue
            
            # Prepare draw date as datetime
            draw_date = datetime.strptime(draw_data["draw_date"], "%Y-%m-%d")
            
            # Format numbers as JSON string (correct format for database)
            numbers_json = json.dumps(draw_data["numbers"])
            
            # Create new LotteryResult record
            new_draw = LotteryResult(
                lottery_type=draw_data["lottery_type"],
                draw_number=draw_data["draw_number"],
                draw_date=draw_date,
                numbers=numbers_json,
                source_url="https://www.nationallottery.co.za/daily-lotto-history",
                divisions=json.dumps(draw_data["divisions_data"]),
                created_at=datetime.now(),
                ocr_provider="manual_import",
                ocr_model="manual_entry",
                ocr_timestamp=datetime.now()
            )
            
            # Add to database
            db.session.add(new_draw)
            imported_count += 1
            
        if imported_count > 0:
            db.session.commit()
            print(f"Successfully imported {imported_count} missing Daily Lottery draws")
        else:
            print("No new draws were imported")
            
        print('--- Import Completed ---')
        
        # Verify the latest draws are now in the database
        latest_draws = LotteryResult.query.filter_by(
            lottery_type='Daily Lottery'
        ).order_by(
            LotteryResult.draw_number.desc()
        ).limit(5).all()
        
        if latest_draws:
            print(f'Latest draws in database: {[r.draw_number for r in latest_draws]}')
            latest_draw = latest_draws[0]
            print(f'Most recent: #{latest_draw.draw_number} ({latest_draw.draw_date})')

if __name__ == '__main__':
    import_latest_daily_lottery()