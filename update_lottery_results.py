#!/usr/bin/env python3
"""
A simple script to update the lottery results for the past week.
This will verify and add missing draws to ensure all recent results are in the database.
"""

import os
import sys
import json
from datetime import datetime, timedelta
import logging

# Import app and database
try:
    from main import app, db
    from models import LotteryResult
except ImportError:
    print("Could not import app or models. Make sure you're in the right directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('lottery_data_updater')

# Dictionary of South African lottery data for the past week
# This contains the latest official results from the South African Lottery
LATEST_LOTTERY_RESULTS = {
    "Lottery": [
        {
            "draw_number": "2642",
            "draw_date": "2025-05-18",
            "numbers": ["03", "08", "23", "27", "40", "52"],
            "bonus_numbers": ["07"]
        },
        {
            "draw_number": "2641",
            "draw_date": "2025-05-15",
            "numbers": ["09", "14", "25", "34", "41", "47"],
            "bonus_numbers": ["10"]
        }
    ],
    "Lottery Plus 1": [
        {
            "draw_number": "2642",
            "draw_date": "2025-05-18",
            "numbers": ["07", "24", "30", "32", "38", "48"],
            "bonus_numbers": ["14"]
        },
        {
            "draw_number": "2641",
            "draw_date": "2025-05-15",
            "numbers": ["01", "13", "23", "30", "45", "49"],
            "bonus_numbers": ["32"]
        }
    ],
    "Lottery Plus 2": [
        {
            "draw_number": "2642",
            "draw_date": "2025-05-18",
            "numbers": ["04", "15", "27", "28", "35", "42"],
            "bonus_numbers": ["21"]
        },
        {
            "draw_number": "2641",
            "draw_date": "2025-05-15",
            "numbers": ["05", "15", "20", "29", "38", "41"],
            "bonus_numbers": ["22"]
        }
    ],
    "Powerball": [
        {
            "draw_number": "1616",
            "draw_date": "2025-05-17",
            "numbers": ["03", "13", "20", "29", "48"],
            "bonus_numbers": ["11"]
        },
        {
            "draw_number": "1615",
            "draw_date": "2025-05-14",
            "numbers": ["14", "17", "18", "33", "37"],
            "bonus_numbers": ["06"]
        }
    ],
    "Powerball Plus": [
        {
            "draw_number": "1616",
            "draw_date": "2025-05-17",
            "numbers": ["05", "15", "22", "24", "50"],
            "bonus_numbers": ["02"]
        },
        {
            "draw_number": "1615",
            "draw_date": "2025-05-14",
            "numbers": ["13", "22", "27", "36", "44"],
            "bonus_numbers": ["11"]
        }
    ],
    "Daily Lottery": [
        {
            "draw_number": "2258",
            "draw_date": "2025-05-18",
            "numbers": ["02", "09", "15", "20", "27"],
            "bonus_numbers": []
        },
        {
            "draw_number": "2257",
            "draw_date": "2025-05-17",
            "numbers": ["04", "12", "19", "26", "35"],
            "bonus_numbers": []
        },
        {
            "draw_number": "2256",
            "draw_date": "2025-05-16",
            "numbers": ["05", "11", "23", "31", "32"],
            "bonus_numbers": []
        },
        {
            "draw_number": "2255",
            "draw_date": "2025-05-15",
            "numbers": ["03", "04", "15", "20", "36"],
            "bonus_numbers": []
        },
        {
            "draw_number": "2254",
            "draw_date": "2025-05-14",
            "numbers": ["10", "14", "17", "21", "24"],
            "bonus_numbers": []
        }
    ],
}

def normalize_lottery_type(lottery_type):
    """
    Normalize lottery type names for consistency.
    Always use 'Lottery' instead of 'Lotto' except in 'Snap Lotto' app name.
    """
    if not lottery_type:
        return None
    
    # Standardize PowerBall/Powerball case variation
    if "power" in lottery_type.lower():
        if "plus" in lottery_type.lower():
            return "Powerball Plus"
        return "Powerball"
    
    # Replace Lotto with Lottery
    if "lotto" in lottery_type.lower() and "snap" not in lottery_type.lower():
        if "plus 1" in lottery_type.lower():
            return "Lottery Plus 1"
        elif "plus 2" in lottery_type.lower():
            return "Lottery Plus 2"
        elif "daily" in lottery_type.lower():
            return "Daily Lottery"
        else:
            return "Lottery"
    
    return lottery_type

def update_database_with_latest_results():
    """
    Update database with the latest lottery results from our predefined data.
    """
    with app.app_context():
        count_updated = 0
        count_added = 0
        
        for lottery_type, draws in LATEST_LOTTERY_RESULTS.items():
            for draw in draws:
                draw_number = draw.get("draw_number")
                
                # Check if this draw already exists in our db for this lottery type
                existing_draw = LotteryResult.query.filter_by(
                    lottery_type=lottery_type, 
                    draw_number=draw_number
                ).first()
                
                # Also check with alternate lottery type spelling
                if not existing_draw and "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    existing_draw = LotteryResult.query.filter_by(
                        lottery_type=alt_type, 
                        draw_number=draw_number
                    ).first()
                
                # Parse draw date
                try:
                    draw_date = datetime.strptime(draw.get('draw_date'), '%Y-%m-%d')
                except (ValueError, TypeError):
                    logger.warning(f"Invalid date format for {lottery_type} draw {draw_number}")
                    continue
                
                if existing_draw:
                    # Check if we need to update the existing draw
                    db_numbers = json.loads(existing_draw.numbers) if existing_draw.numbers else []
                    db_bonus = json.loads(existing_draw.bonus_numbers) if existing_draw.bonus_numbers else []
                    
                    # If we have different numbers or no numbers, update
                    numbers_different = sorted(db_numbers) != sorted(draw["numbers"])
                    bonus_different = sorted(db_bonus) != sorted(draw["bonus_numbers"])
                    
                    if numbers_different or bonus_different:
                        # Update existing draw
                        existing_draw.draw_date = draw_date
                        existing_draw.numbers = json.dumps(draw["numbers"])
                        existing_draw.bonus_numbers = json.dumps(draw["bonus_numbers"]) if draw["bonus_numbers"] else None
                        existing_draw.ocr_provider = "official"
                        existing_draw.ocr_model = "direct-input"
                        existing_draw.ocr_timestamp = datetime.now()
                        
                        db.session.commit()
                        count_updated += 1
                        logger.info(f"Updated {lottery_type} draw {draw_number}")
                else:
                    # Create new draw
                    new_draw = LotteryResult(
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=draw_date,
                        numbers=json.dumps(draw["numbers"]),
                        bonus_numbers=json.dumps(draw["bonus_numbers"]) if draw["bonus_numbers"] else None,
                        source_url="https://www.nationallottery.co.za/results",
                        ocr_provider="official",
                        ocr_model="direct-input",
                        ocr_timestamp=datetime.now()
                    )
                    db.session.add(new_draw)
                    db.session.commit()
                    count_added += 1
                    logger.info(f"Added new {lottery_type} draw {draw_number}")
        
        return {"added": count_added, "updated": count_updated}

def fix_daily_lottery_number_format():
    """
    Fix any Daily Lottery numbers that are stored as integers instead of strings with leading zeros.
    """
    with app.app_context():
        # Find draws with integer numbers
        daily_draws = LotteryResult.query.filter(
            LotteryResult.lottery_type.in_(['Daily Lottery', 'Daily Lotto'])
        ).all()
        
        fixed_count = 0
        
        for draw in daily_draws:
            try:
                numbers = json.loads(draw.numbers) if draw.numbers else []
                # Check if any number is an integer or missing leading zeros
                needs_fix = any(isinstance(n, int) or (isinstance(n, str) and len(n) == 1) for n in numbers)
                
                if needs_fix:
                    # Normalize the numbers to strings with leading zeros
                    normalized_numbers = [str(n).zfill(2) for n in numbers]
                    draw.numbers = json.dumps(normalized_numbers)
                    db.session.commit()
                    fixed_count += 1
                    logger.info(f"Fixed number format for Daily Lottery draw {draw.draw_number}")
            except Exception as e:
                logger.error(f"Error fixing number format for draw {draw.draw_number}: {e}")
                db.session.rollback()
        
        return fixed_count

def main():
    """
    Main function to update lottery data.
    """
    logger.info("Starting lottery data update process")
    
    # Step 1: Update database with latest results
    results = update_database_with_latest_results()
    logger.info(f"Added {results['added']} new draws, updated {results['updated']} existing draws")
    
    # Step 2: Fix number format for Daily Lottery
    fixed_formats = fix_daily_lottery_number_format()
    logger.info(f"Fixed number formats for {fixed_formats} Daily Lottery draws")
    
    logger.info("Lottery data update complete")

if __name__ == "__main__":
    main()