#!/usr/bin/env python3
"""
Fix specific lottery date errors identified during verification.
This script targets the exact draws that have incorrect dates.
"""

import os
import sys
from datetime import datetime
import logging
import json

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
logger = logging.getLogger('date_fix')

# List of specific draw corrections needed
DATE_CORRECTIONS = [
    {"lottery_type": "Lottery", "draw_number": "2641", "correct_date": "2025-05-14"},
    {"lottery_type": "Lottery Plus 1", "draw_number": "2641", "correct_date": "2025-05-14"},
    {"lottery_type": "Lottery Plus 2", "draw_number": "2641", "correct_date": "2025-05-14"},
    {"lottery_type": "Daily Lottery", "draw_number": "2254", "correct_date": "2025-05-14"}
]

# Missing draw to add
MISSING_DRAWS = [
    {
        "lottery_type": "Daily Lottery",
        "draw_number": "2256",
        "draw_date": "2025-05-16",
        "numbers": ["05", "11", "23", "31", "32"],
        "bonus_numbers": [],
        "divisions": {
            "Division 1": {"match": "5 correct numbers", "winners": 0, "payout": "R0.00"},
            "Division 2": {"match": "4 correct numbers", "winners": 301, "payout": "R820.90"},
            "Division 3": {"match": "3 correct numbers", "winners": 9032, "payout": "R25.00"},
            "Division 4": {"match": "2 correct numbers", "winners": 80892, "payout": "R5.00"}
        }
    }
]

def fix_specific_dates():
    """Fix specific lottery draw dates that are incorrect."""
    fixed_count = 0
    
    with app.app_context():
        for correction in DATE_CORRECTIONS:
            lottery_type = correction["lottery_type"]
            draw_number = correction["draw_number"]
            correct_date_str = correction["correct_date"]
            
            # Find this draw in the database
            lottery_result = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            # If not found with exact name, try with variations
            if not lottery_result and "Lottery" in lottery_type:
                alt_type = lottery_type.replace("Lottery", "Lotto")
                lottery_result = LotteryResult.query.filter_by(
                    lottery_type=alt_type,
                    draw_number=draw_number
                ).first()
            
            if not lottery_result and "Powerball" in lottery_type:
                alt_type = lottery_type.replace("Powerball", "PowerBall")
                lottery_result = LotteryResult.query.filter_by(
                    lottery_type=alt_type,
                    draw_number=draw_number
                ).first()
            
            if lottery_result:
                # Convert string date to datetime
                correct_date = datetime.strptime(correct_date_str, "%Y-%m-%d")
                old_date = lottery_result.draw_date.strftime("%Y-%m-%d")
                
                # Update the date
                lottery_result.draw_date = correct_date
                fixed_count += 1
                logger.info(f"Fixed date for {lottery_type} draw {draw_number} from {old_date} to {correct_date_str}")
            else:
                logger.warning(f"Could not find {lottery_type} draw {draw_number} in database")
        
        # Add missing divisions for Daily Lottery draw 2254
        daily_draw_2254 = LotteryResult.query.filter_by(
            lottery_type="Daily Lottery",
            draw_number="2254"
        ).first()
        
        if daily_draw_2254:
            # Update divisions with correct data
            correct_divisions = {
                "Division 1": {"match": "5 correct numbers", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "4 correct numbers", "winners": 246, "payout": "R845.50"},
                "Division 3": {"match": "3 correct numbers", "winners": 7945, "payout": "R25.00"},
                "Division 4": {"match": "2 correct numbers", "winners": 73521, "payout": "R5.00"}
            }
            daily_draw_2254.divisions = json.dumps(correct_divisions)
            logger.info(f"Updated division data for Daily Lottery draw 2254")
        
        # Commit all changes
        db.session.commit()
    
    return fixed_count

def add_missing_draws():
    """Add missing lottery draws to the database."""
    added_count = 0
    
    with app.app_context():
        for draw_data in MISSING_DRAWS:
            lottery_type = draw_data["lottery_type"]
            draw_number = draw_data["draw_number"]
            
            # Check if this draw already exists
            existing_draw = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if not existing_draw:
                # Create new draw record
                new_draw = LotteryResult()
                new_draw.lottery_type = lottery_type
                new_draw.draw_number = draw_number
                new_draw.draw_date = datetime.strptime(draw_data["draw_date"], "%Y-%m-%d")
                new_draw.numbers = json.dumps(draw_data["numbers"])
                new_draw.bonus_numbers = json.dumps(draw_data["bonus_numbers"]) if draw_data.get("bonus_numbers") else None
                new_draw.divisions = json.dumps(draw_data["divisions"]) if draw_data.get("divisions") else None
                new_draw.source_url = "https://www.nationallottery.co.za/results"
                new_draw.ocr_provider = "official"
                new_draw.ocr_model = "direct-input"
                new_draw.ocr_timestamp = datetime.now()
                
                db.session.add(new_draw)
                added_count += 1
                logger.info(f"Added missing {lottery_type} draw {draw_number}")
            else:
                logger.info(f"{lottery_type} draw {draw_number} already exists in database")
        
        # Commit all changes
        db.session.commit()
    
    return added_count

def verify_corrections():
    """Verify that all corrections were applied successfully."""
    
    with app.app_context():
        print("\nVerifying corrections:")
        
        # Check date corrections
        for correction in DATE_CORRECTIONS:
            lottery_type = correction["lottery_type"]
            draw_number = correction["draw_number"]
            expected_date = correction["correct_date"]
            
            # Find this draw in the database
            result = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if not result:
                print(f"❌ {lottery_type} Draw #{draw_number} - Not found in database")
                continue
            
            actual_date = result.draw_date.strftime("%Y-%m-%d")
            status = "✅" if actual_date == expected_date else "❌"
            print(f"{status} {lottery_type} Draw #{draw_number}: {actual_date} (Expected: {expected_date})")
        
        # Check missing draw added
        for draw_data in MISSING_DRAWS:
            lottery_type = draw_data["lottery_type"]
            draw_number = draw_data["draw_number"]
            expected_date = draw_data["draw_date"]
            
            result = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if not result:
                print(f"❌ {lottery_type} Draw #{draw_number} - Still missing from database")
                continue
            
            actual_date = result.draw_date.strftime("%Y-%m-%d")
            status = "✅" if actual_date == expected_date else "❌"
            print(f"{status} {lottery_type} Draw #{draw_number}: {actual_date} (Expected: {expected_date})")
            
            # Check if divisions were correctly added
            if draw_data.get("divisions"):
                try:
                    actual_divisions = json.loads(result.divisions) if result.divisions else {}
                    all_divisions_present = True
                    
                    for div_name in draw_data["divisions"].keys():
                        if div_name not in actual_divisions:
                            all_divisions_present = False
                            break
                    
                    status = "✅" if all_divisions_present else "❌"
                    print(f"{status} {lottery_type} Draw #{draw_number} Divisions correctly added")
                except:
                    print(f"❌ {lottery_type} Draw #{draw_number} Error checking divisions")
        
        # Check division data correction for Daily Lottery draw 2254
        daily_draw_2254 = LotteryResult.query.filter_by(
            lottery_type="Daily Lottery",
            draw_number="2254"
        ).first()
        
        if daily_draw_2254:
            try:
                actual_divisions = json.loads(daily_draw_2254.divisions) if daily_draw_2254.divisions else {}
                expected_winner_count = 246  # Division 2 winners count as a test case
                actual_winner_count = actual_divisions.get("Division 2", {}).get("winners", 0)
                
                status = "✅" if actual_winner_count == expected_winner_count else "❌"
                print(f"{status} Daily Lottery Draw #2254 Division Data: Winners = {actual_winner_count} (Expected: {expected_winner_count})")
            except:
                print(f"❌ Daily Lottery Draw #2254 Error checking divisions")
        else:
            print(f"❌ Daily Lottery Draw #2254 - Not found in database")

def main():
    """Main function to fix lottery date errors."""
    try:
        print("Fixing lottery date errors...")
        fixed = fix_specific_dates()
        print(f"Successfully fixed dates for {fixed} lottery draws.")
        
        print("\nAdding missing lottery draws...")
        added = add_missing_draws()
        print(f"Successfully added {added} missing lottery draws.")
        
        # Verify all corrections
        verify_corrections()
        
    except Exception as e:
        logger.error(f"Error fixing lottery data: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()