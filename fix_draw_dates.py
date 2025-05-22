#!/usr/bin/env python3
"""
Fix lottery draw dates to match official Ithuba information.
This script corrects any date discrepancies in our database.
"""

import os
import sys
from datetime import datetime
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
logger = logging.getLogger('date_corrector')

# Correct dates for lottery draws based on official Ithuba information
CORRECT_DATES = {
    "Lottery": {
        "2642": "2025-05-17", # Saturday draw
        "2641": "2025-05-15"  # Wednesday draw
    },
    "Lottery Plus 1": {
        "2642": "2025-05-17", # Saturday draw
        "2641": "2025-05-15"  # Wednesday draw
    },
    "Lottery Plus 2": {
        "2642": "2025-05-17", # Saturday draw
        "2641": "2025-05-15"  # Wednesday draw
    },
    "Powerball": {
        "1616": "2025-05-17", # Friday draw
        "1615": "2025-05-14"  # Tuesday draw
    },
    "Powerball Plus": {
        "1616": "2025-05-17", # Friday draw
        "1615": "2025-05-14"  # Tuesday draw
    },
    "Daily Lottery": {
        "2258": "2025-05-18", # Sunday draw
        "2257": "2025-05-17", # Saturday draw
        "2256": "2025-05-16", # Friday draw
        "2255": "2025-05-15"  # Thursday draw
    }
}

def fix_draw_dates():
    """
    Update lottery results with correct draw dates.
    """
    fixed_count = 0
    
    with app.app_context():
        for lottery_type, draws in CORRECT_DATES.items():
            for draw_number, correct_date_str in draws.items():
                # Find this draw in the database
                lottery_result = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=draw_number
                ).first()
                
                # If not found with exact name, try with Lotto instead of Lottery
                if not lottery_result and "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    lottery_result = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=draw_number
                    ).first()
                
                # If still not found, try PowerBall variation
                if not lottery_result and "Powerball" in lottery_type:
                    alt_type = lottery_type.replace("Powerball", "PowerBall")
                    lottery_result = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=draw_number
                    ).first()
                
                if lottery_result:
                    # Convert string date to datetime
                    correct_date = datetime.strptime(correct_date_str, "%Y-%m-%d")
                    
                    # Check if date needs correction
                    if lottery_result.draw_date.date() != correct_date.date():
                        old_date = lottery_result.draw_date.strftime("%Y-%m-%d")
                        lottery_result.draw_date = correct_date
                        fixed_count += 1
                        logger.info(f"Fixed date for {lottery_type} draw {draw_number} from {old_date} to {correct_date_str}")
                    else:
                        logger.info(f"Date already correct for {lottery_type} draw {draw_number}: {correct_date_str}")
                else:
                    logger.warning(f"Could not find {lottery_type} draw {draw_number} in database")
        
        # Commit all changes
        db.session.commit()
    
    return fixed_count

def main():
    """Main function to fix draw dates."""
    try:
        print("Fixing lottery draw dates...")
        fixed = fix_draw_dates()
        print(f"Successfully fixed dates for {fixed} lottery draws.")
        
        # Now let's verify our fixes
        with app.app_context():
            print("\nVerifying fixed dates:")
            for lottery_type, draws in CORRECT_DATES.items():
                for draw_number, expected_date in draws.items():
                    # Find this draw in the database (try all variations)
                    draw = None
                    
                    # Try with exact lottery type
                    draw = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                    
                    # If not found, try with Lotto instead of Lottery
                    if not draw and "Lottery" in lottery_type:
                        alt_type = lottery_type.replace("Lottery", "Lotto")
                        draw = LotteryResult.query.filter_by(
                            lottery_type=alt_type,
                            draw_number=draw_number
                        ).first()
                    
                    # If still not found, try PowerBall variation
                    if not draw and "Powerball" in lottery_type:
                        alt_type = lottery_type.replace("Powerball", "PowerBall")
                        draw = LotteryResult.query.filter_by(
                            lottery_type=alt_type,
                            draw_number=draw_number
                        ).first()
                    
                    if draw:
                        actual_date = draw.draw_date.strftime("%Y-%m-%d")
                        status = "✓" if actual_date == expected_date else "✗"
                        print(f"{status} {lottery_type} Draw #{draw_number}: {actual_date} (Expected: {expected_date})")
                    else:
                        print(f"- {lottery_type} Draw #{draw_number}: Not found in database")
        
    except Exception as e:
        logger.error(f"Error fixing draw dates: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()