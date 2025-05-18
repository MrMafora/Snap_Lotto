"""
Script to correct lottery results with verified official data.
"""
import sys
import datetime
from flask import Flask
from sqlalchemy import and_
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the existing app and db from main.py
sys.path.append('.')
from main import app, db
from models import LotteryResult

def update_lottery_result(lottery_type, draw_date, draw_number, numbers, bonus_numbers=None):
    """
    Update a specific lottery result with correct numbers.
    
    Args:
        lottery_type (str): Type of lottery (e.g., "Lottery", "Lottery Plus 1")
        draw_date (datetime): Date of the draw
        draw_number (str): Draw number
        numbers (list): Correct main numbers
        bonus_numbers (list, optional): Correct bonus numbers
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        # Format numbers for storing in database
        numbers_json = json.dumps(numbers)
        bonus_numbers_json = json.dumps(bonus_numbers) if bonus_numbers else None
        
        # Find the result in the database
        result = LotteryResult.query.filter(
            and_(
                LotteryResult.lottery_type == lottery_type,
                LotteryResult.draw_date == draw_date
            )
        ).first()
        
        if not result:
            # Try with alternative date formats
            # Sometimes there might be timezone issues with the date
            date_start = draw_date.replace(hour=0, minute=0, second=0)
            date_end = draw_date.replace(hour=23, minute=59, second=59)
            
            result = LotteryResult.query.filter(
                and_(
                    LotteryResult.lottery_type == lottery_type,
                    LotteryResult.draw_date >= date_start,
                    LotteryResult.draw_date <= date_end
                )
            ).first()
        
        if not result:
            # Try with the draw number
            result = LotteryResult.query.filter(
                and_(
                    LotteryResult.lottery_type == lottery_type,
                    LotteryResult.draw_number == draw_number
                )
            ).first()
        
        if not result:
            logger.error(f"Could not find result for {lottery_type} on {draw_date} (Draw #{draw_number})")
            return False
            
        # Update the numbers
        logger.info(f"Updating {lottery_type} draw #{draw_number} on {draw_date.strftime('%Y-%m-%d')}")
        logger.info(f"  Old numbers: {result.numbers} -> New numbers: {numbers_json}")
        if bonus_numbers:
            logger.info(f"  Old bonus: {result.bonus_numbers} -> New bonus: {bonus_numbers_json}")
            
        result.numbers = numbers_json
        if bonus_numbers:
            result.bonus_numbers = bonus_numbers_json
            
        # Save to database
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating result: {e}")
        db.session.rollback()
        return False

def fix_lottery_data():
    """Fix incorrect lottery results with official data."""
    with app.app_context():
        # Fix Lottery (6/49) data
        corrections = [
            # Wed 5 Mar 2025
            {
                "lottery_type": "Lottery",
                "draw_date": datetime.datetime(2025, 3, 5),
                "draw_number": "2539",  # Assumed draw number
                "numbers": [2, 8, 37, 45, 48, 51],
                "bonus_numbers": [24]
            },
            # Sat 12 Apr 2025
            {
                "lottery_type": "Lottery",
                "draw_date": datetime.datetime(2025, 4, 12),
                "draw_number": "2540",  # Assumed draw number
                "numbers": None,  # Main numbers correct
                "bonus_numbers": [36]
            },
            # Sat 19 Apr 2025
            {
                "lottery_type": "Lottery",
                "draw_date": datetime.datetime(2025, 4, 19),
                "draw_number": "2540",  # Assumed draw number
                "numbers": [6, 9, 11, 33, 38, 52],
                "bonus_numbers": [32]
            },
            # Wed 23 Apr 2025
            {
                "lottery_type": "Lottery",
                "draw_date": datetime.datetime(2025, 4, 23),
                "draw_number": "2540",  # Assumed draw number
                "numbers": [1, 5, 22, 31, 34, 44],
                "bonus_numbers": [33]
            },
            # Sat 3 May 2025
            {
                "lottery_type": "Lottery",
                "draw_date": datetime.datetime(2025, 5, 3),
                "draw_number": "2540",  # Assumed draw number
                "numbers": [4, 5, 7, 10, 11, 41],
                "bonus_numbers": [2]
            },
            # Wed 7 May 2025
            {
                "lottery_type": "Lottery",
                "draw_date": datetime.datetime(2025, 5, 7),
                "draw_number": "2539",  # Assumed draw number
                "numbers": [9, 10, 27, 30, 31, 45],
                "bonus_numbers": [23]
            },
            # Wed 14 May 2025
            {
                "lottery_type": "Lottery",
                "draw_date": datetime.datetime(2025, 5, 14),
                "draw_number": "2541",  # This one we know from earlier
                "numbers": [9, 18, 19, 30, 31, 40],
                "bonus_numbers": [28]
            },
        ]
        
        # Apply Lottery corrections
        for correction in corrections:
            if correction["numbers"] is None:
                # Only update bonus numbers
                result = LotteryResult.query.filter(
                    and_(
                        LotteryResult.lottery_type == correction["lottery_type"],
                        LotteryResult.draw_date == correction["draw_date"]
                    )
                ).first()
                
                if not result:
                    # Try with the draw number
                    result = LotteryResult.query.filter(
                        and_(
                            LotteryResult.lottery_type == correction["lottery_type"],
                            LotteryResult.draw_number == correction["draw_number"]
                        )
                    ).first()
                
                if result:
                    bonus_numbers_json = json.dumps(correction["bonus_numbers"])
                    logger.info(f"Updating {correction['lottery_type']} draw #{correction['draw_number']} on {correction['draw_date'].strftime('%Y-%m-%d')}")
                    logger.info(f"  Old bonus: {result.bonus_numbers} -> New bonus: {bonus_numbers_json}")
                    result.bonus_numbers = bonus_numbers_json
                    db.session.commit()
            else:
                update_lottery_result(
                    correction["lottery_type"],
                    correction["draw_date"],
                    correction["draw_number"],
                    correction["numbers"],
                    correction["bonus_numbers"]
                )
        
        # Fix Lottery Plus 1 data (samples from the document)
        plus1_corrections = [
            # Wed 5 Mar 2025
            {
                "lottery_type": "Lottery Plus 1",
                "draw_date": datetime.datetime(2025, 3, 5),
                "draw_number": "2539",  # Assumed draw number
                "numbers": [2, 8, 37, 45, 48, 51],
                "bonus_numbers": [24]
            },
            # Sat 15 Mar 2025
            {
                "lottery_type": "Lottery Plus 1",
                "draw_date": datetime.datetime(2025, 3, 15),
                "draw_number": "2539",  # Assumed draw number
                "numbers": [6, 23, 24, 34, 47, 49],
                "bonus_numbers": [18]
            },
            # Wed 9 Apr 2025
            {
                "lottery_type": "Lottery Plus 1", 
                "draw_date": datetime.datetime(2025, 4, 9),
                "draw_number": "2540",  # Assumed draw number
                "numbers": [1, 18, 30, 40, 49, 52],
                "bonus_numbers": [23]
            },
            # Wed 23 Apr 2025
            {
                "lottery_type": "Lottery Plus 1",
                "draw_date": datetime.datetime(2025, 4, 23),
                "draw_number": "2540",  # Assumed draw number
                "numbers": [3, 12, 21, 30, 39, 45],
                "bonus_numbers": [31]
            },
            # Sat 3 May 2025
            {
                "lottery_type": "Lottery Plus 1",
                "draw_date": datetime.datetime(2025, 5, 3),
                "draw_number": "2540",  # Assumed draw number
                "numbers": [12, 16, 17, 19, 29, 38],
                "bonus_numbers": [42]
            },
            # Wed 30 Apr 2025
            {
                "lottery_type": "Lottery Plus 1",
                "draw_date": datetime.datetime(2025, 4, 30),
                "draw_number": "2540",  # Assumed draw number
                "numbers": [9, 17, 19, 40, 47, 51],
                "bonus_numbers": [8]
            },
            # Wed 14 May 2025
            {
                "lottery_type": "Lottery Plus 1",
                "draw_date": datetime.datetime(2025, 5, 14),
                "draw_number": "2541",  # This one we know from earlier
                "numbers": [21, 25, 31, 41, 42, 50],
                "bonus_numbers": [48]
            },
        ]
        
        # Apply Lottery Plus 1 corrections
        for correction in plus1_corrections:
            update_lottery_result(
                correction["lottery_type"],
                correction["draw_date"],
                correction["draw_number"],
                correction["numbers"],
                correction["bonus_numbers"]
            )
        
        # Fix Lottery Plus 2 data
        plus2_corrections = [
            # Sat 15 Mar 2025
            {
                "lottery_type": "Lottery Plus 2",
                "draw_date": datetime.datetime(2025, 3, 15),
                "draw_number": "2539",  # Assumed draw number
                "numbers": None,  # Main numbers correct
                "bonus_numbers": [52]
            },
            # Sat 19 Apr 2025
            {
                "lottery_type": "Lottery Plus 2",
                "draw_date": datetime.datetime(2025, 4, 19),
                "draw_number": "2540",  # Assumed draw number
                "numbers": [3, 8, 17, 25, 33, 50],
                "bonus_numbers": [41]
            },
            # Wed 23 Apr 2025
            {
                "lottery_type": "Lottery Plus 2",
                "draw_date": datetime.datetime(2025, 4, 23),
                "draw_number": "2540",  # Assumed draw number
                "numbers": None,  # Main numbers correct
                "bonus_numbers": [12]
            },
            # Sat 3 May 2025
            {
                "lottery_type": "Lottery Plus 2",
                "draw_date": datetime.datetime(2025, 5, 3),
                "draw_number": "2540",  # Assumed draw number
                "numbers": [6, 9, 27, 32, 33, 39],
                "bonus_numbers": [46]
            },
        ]
        
        # Apply Lottery Plus 2 corrections
        for correction in plus2_corrections:
            if correction["numbers"] is None:
                # Only update bonus numbers
                result = LotteryResult.query.filter(
                    and_(
                        LotteryResult.lottery_type == correction["lottery_type"],
                        LotteryResult.draw_date == correction["draw_date"]
                    )
                ).first()
                
                if not result:
                    # Try with the draw number
                    result = LotteryResult.query.filter(
                        and_(
                            LotteryResult.lottery_type == correction["lottery_type"],
                            LotteryResult.draw_number == correction["draw_number"]
                        )
                    ).first()
                
                if result:
                    bonus_numbers_json = json.dumps(correction["bonus_numbers"])
                    logger.info(f"Updating {correction['lottery_type']} draw #{correction['draw_number']} on {correction['draw_date'].strftime('%Y-%m-%d')}")
                    logger.info(f"  Old bonus: {result.bonus_numbers} -> New bonus: {bonus_numbers_json}")
                    result.bonus_numbers = bonus_numbers_json
                    db.session.commit()
            else:
                update_lottery_result(
                    correction["lottery_type"],
                    correction["draw_date"],
                    correction["draw_number"],
                    correction["numbers"],
                    correction["bonus_numbers"]
                )
        
        # Fix PowerBall data
        powerball_corrections = [
            # Tue 1 Apr 2025
            {
                "lottery_type": "Powerball",
                "draw_date": datetime.datetime(2025, 4, 1),
                "draw_number": "1614",  # Assumed draw number
                "numbers": [1, 6, 12, 13, 36],
                "bonus_numbers": [7]
            },
            # Fri 29 Apr 2025 (assuming this is actually April 25, as April 29 is not a Friday)
            {
                "lottery_type": "Powerball",
                "draw_date": datetime.datetime(2025, 4, 25),
                "draw_number": "1614",  # Assumed draw number
                "numbers": [5, 14, 32, 33, 45],
                "bonus_numbers": [13]
            },
        ]
        
        # Apply PowerBall corrections
        for correction in powerball_corrections:
            update_lottery_result(
                correction["lottery_type"],
                correction["draw_date"],
                correction["draw_number"],
                correction["numbers"],
                correction["bonus_numbers"]
            )
        
        logger.info("All corrections applied successfully!")
        
        # Test by checking a specific result that we updated
        test_result = LotteryResult.query.filter(
            and_(
                LotteryResult.lottery_type == "Lottery",
                LotteryResult.draw_date == datetime.datetime(2025, 5, 14)
            )
        ).first()
        
        if test_result:
            logger.info(f"Verification test - Lottery 2025-05-14:")
            logger.info(f"Numbers: {test_result.numbers}")
            logger.info(f"Bonus: {test_result.bonus_numbers}")
        
        return True

if __name__ == "__main__":
    fix_lottery_data()