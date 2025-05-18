#!/usr/bin/env python3
"""
Verify the official draw IDs for South African lottery draws.
This script compares our database against officially published information.
"""

import os
import sys
import json
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
logger = logging.getLogger('draw_id_verification')

# Dictionary to hold our database information
DATABASE_INFO = {}

def get_latest_draw_numbers():
    """Get the latest draw numbers from our database for each lottery type."""
    
    with app.app_context():
        # Get the latest draws for each lottery type
        lottery_types = [
            "Lottery", 
            "Lottery Plus 1", 
            "Lottery Plus 2", 
            "Powerball", 
            "Powerball Plus", 
            "Daily Lottery"
        ]
        
        # Try alternate spellings too
        alternate_lottery_types = [
            "Lotto", 
            "Lotto Plus 1", 
            "Lotto Plus 2", 
            "PowerBall", 
            "PowerBall Plus", 
            "Daily Lotto"
        ]
        
        all_types = lottery_types + alternate_lottery_types
        
        for lottery_type in all_types:
            latest_draw = LotteryResult.query.filter_by(
                lottery_type=lottery_type
            ).order_by(db.desc(LotteryResult.draw_date)).first()
            
            if latest_draw:
                if lottery_type in DATABASE_INFO:
                    # If we already have this, check which is newer
                    existing_date = DATABASE_INFO[lottery_type]["date"]
                    new_date = latest_draw.draw_date
                    
                    if new_date > existing_date:
                        DATABASE_INFO[lottery_type] = {
                            "draw_number": latest_draw.draw_number,
                            "date": latest_draw.draw_date,
                            "numbers": json.loads(latest_draw.numbers) if latest_draw.numbers else []
                        }
                else:
                    DATABASE_INFO[lottery_type] = {
                        "draw_number": latest_draw.draw_number,
                        "date": latest_draw.draw_date,
                        "numbers": json.loads(latest_draw.numbers) if latest_draw.numbers else []
                    }
        
        # Now normalize the lottery types to standard terms
        normalized_info = {}
        for lottery_type, info in DATABASE_INFO.items():
            # Normalize to standard terms
            if lottery_type == "Lotto":
                normalized_type = "Lottery"
            elif lottery_type == "Lotto Plus 1":
                normalized_type = "Lottery Plus 1"
            elif lottery_type == "Lotto Plus 2":
                normalized_type = "Lottery Plus 2"
            elif lottery_type == "PowerBall":
                normalized_type = "Powerball"
            elif lottery_type == "PowerBall Plus":
                normalized_type = "Powerball Plus"
            elif lottery_type == "Daily Lotto":
                normalized_type = "Daily Lottery"
            else:
                normalized_type = lottery_type
            
            # Only add if not already present or if newer
            if normalized_type not in normalized_info or info["date"] > normalized_info[normalized_type]["date"]:
                normalized_info[normalized_type] = info
                
        return normalized_info

def verify_lottery_draws():
    """Verify lottery draws against official information."""
    
    # Official information from the South African National Lottery website
    # These are the actual draw IDs as published on the official website
    OFFICIAL_DRAW_IDS = {
        "Lottery": {
            "latest_draw": "2542", # Official as of May 18, 2025
            "draw_day": "Wednesday and Saturday"
        },
        "Lottery Plus 1": {
            "latest_draw": "2542", # Official as of May 18, 2025
            "draw_day": "Wednesday and Saturday"
        },
        "Lottery Plus 2": {
            "latest_draw": "2542", # Official as of May 18, 2025
            "draw_day": "Wednesday and Saturday"
        },
        "Powerball": {
            "latest_draw": "1616", # Official as of May 18, 2025
            "draw_day": "Tuesday and Friday"
        },
        "Powerball Plus": {
            "latest_draw": "1616", # Official as of May 18, 2025
            "draw_day": "Tuesday and Friday"
        },
        "Daily Lottery": {
            "latest_draw": "2258", # Official as of May 18, 2025
            "draw_day": "Every day"
        }
    }
    
    # Get our database information
    db_info = get_latest_draw_numbers()
    
    print("\nVerifying lottery draw IDs against official information:")
    print("-" * 80)
    
    for lottery_type, official_info in OFFICIAL_DRAW_IDS.items():
        official_draw_id = official_info["latest_draw"]
        draw_days = official_info["draw_day"]
        
        if lottery_type in db_info:
            db_draw_id = db_info[lottery_type]["draw_number"]
            db_date = db_info[lottery_type]["date"].strftime("%Y-%m-%d")
            db_numbers = db_info[lottery_type]["numbers"]
            
            status = "✅" if official_draw_id == db_draw_id else "❌"
            print(f"{status} {lottery_type}: Draw #{db_draw_id} (Official ID: #{official_draw_id})")
            print(f"    Date: {db_date}")
            print(f"    Numbers: {', '.join(db_numbers)}")
            print(f"    Draw Days: {draw_days}")
            
            if official_draw_id != db_draw_id:
                print(f"    DISCREPANCY: Our database shows #{db_draw_id} but official latest is #{official_draw_id}")
        else:
            print(f"❌ {lottery_type}: Not found in database (Official ID: #{official_draw_id})")
    
    print("\nVerification complete.")

def main():
    """Main function to verify lottery draw IDs."""
    try:
        print("Verifying lottery draw IDs against official information...")
        verify_lottery_draws()
        
    except Exception as e:
        logger.error(f"Error verifying lottery draw IDs: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()