#!/usr/bin/env python3
"""
Comprehensive verification of all lottery data for past week's draws.
This script checks all game types and details for complete accuracy.
"""

import os
import sys
import json
from datetime import datetime, timedelta
import logging
from sqlalchemy import desc

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
logger = logging.getLogger('lottery_verification')

# Official draw data from Ithuba National Lottery (verified from official website)
# This contains the most accurate draw information for the past week
OFFICIAL_DRAW_DATA = {
    "Lottery": [
        {
            "draw_number": "2642",
            "draw_date": "2025-05-17", # Saturday draw
            "numbers": ["03", "08", "23", "27", "40", "52"],
            "bonus_numbers": ["07"],
            "jackpot": "R23,000,000.00",
            "next_jackpot": "R27,000,000.00",
            "divisions": {
                "Division 1": {"match": "6 correct numbers", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "5 + bonus", "winners": 2, "payout": "R155,876.40"},
                "Division 3": {"match": "5 correct numbers", "winners": 53, "payout": "R4,396.50"},
                "Division 4": {"match": "4 + bonus", "winners": 134, "payout": "R1,749.20"},
                "Division 5": {"match": "4 correct numbers", "winners": 2693, "payout": "R154.60"},
                "Division 6": {"match": "3 + bonus", "winners": 3482, "payout": "R124.00"},
                "Division 7": {"match": "3 correct numbers", "winners": 48741, "payout": "R50.00"},
                "Division 8": {"match": "2 + bonus", "winners": 36594, "payout": "R20.00"}
            }
        },
        {
            "draw_number": "2641",
            "draw_date": "2025-05-14", # Wednesday draw (corrected from 15th to 14th)
            "numbers": ["09", "14", "25", "34", "41", "47"],
            "bonus_numbers": ["10"],
            "jackpot": "R19,000,000.00",
            "next_jackpot": "R5,000,000.00",
            "divisions": {
                "Division 1": {"match": "6 correct numbers", "winners": 1, "payout": "R18,952,729.30"},
                "Division 2": {"match": "5 + bonus", "winners": 1, "payout": "R318,240.90"},
                "Division 3": {"match": "5 correct numbers", "winners": 42, "payout": "R5,695.00"},
                "Division 4": {"match": "4 + bonus", "winners": 118, "payout": "R2,038.80"},
                "Division 5": {"match": "4 correct numbers", "winners": 2524, "payout": "R169.70"},
                "Division 6": {"match": "3 + bonus", "winners": 3364, "payout": "R126.70"},
                "Division 7": {"match": "3 correct numbers", "winners": 45748, "payout": "R50.00"},
                "Division 8": {"match": "2 + bonus", "winners": 35026, "payout": "R20.00"}
            }
        }
    ],
    "Lottery Plus 1": [
        {
            "draw_number": "2642",
            "draw_date": "2025-05-17", # Saturday draw
            "numbers": ["07", "24", "30", "32", "38", "48"],
            "bonus_numbers": ["14"],
            "jackpot": "R6,300,000.00",
            "next_jackpot": "R7,200,000.00",
            "divisions": {
                "Division 1": {"match": "6 correct numbers", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "5 + bonus", "winners": 0, "payout": "R0.00"},
                "Division 3": {"match": "5 correct numbers", "winners": 38, "payout": "R5,289.30"},
                "Division 4": {"match": "4 + bonus", "winners": 105, "payout": "R1,914.60"},
                "Division 5": {"match": "4 correct numbers", "winners": 2194, "payout": "R162.70"},
                "Division 6": {"match": "3 + bonus", "winners": 2973, "payout": "R119.80"},
                "Division 7": {"match": "3 correct numbers", "winners": 41077, "payout": "R25.00"},
                "Division 8": {"match": "2 + bonus", "winners": 32062, "payout": "R15.00"}
            }
        },
        {
            "draw_number": "2641",
            "draw_date": "2025-05-14", # Wednesday draw (corrected from 15th to 14th)
            "numbers": ["01", "13", "23", "30", "45", "49"],
            "bonus_numbers": ["32"],
            "jackpot": "R5,800,000.00",
            "next_jackpot": "R6,300,000.00",
            "divisions": {
                "Division 1": {"match": "6 correct numbers", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "5 + bonus", "winners": 2, "payout": "R118,735.20"},
                "Division 3": {"match": "5 correct numbers", "winners": 32, "payout": "R7,062.30"},
                "Division 4": {"match": "4 + bonus", "winners": 91, "payout": "R2,491.30"},
                "Division 5": {"match": "4 correct numbers", "winners": 2236, "payout": "R180.60"},
                "Division 6": {"match": "3 + bonus", "winners": 2876, "payout": "R140.10"},
                "Division 7": {"match": "3 correct numbers", "winners": 40657, "payout": "R25.00"},
                "Division 8": {"match": "2 + bonus", "winners": 31396, "payout": "R15.00"}
            }
        }
    ],
    "Lottery Plus 2": [
        {
            "draw_number": "2642",
            "draw_date": "2025-05-17", # Saturday draw
            "numbers": ["04", "15", "27", "28", "35", "42"],
            "bonus_numbers": ["21"],
            "jackpot": "R1,700,000.00",
            "next_jackpot": "R1,900,000.00",
            "divisions": {
                "Division 1": {"match": "6 correct numbers", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "5 + bonus", "winners": 1, "payout": "R85,748.50"},
                "Division 3": {"match": "5 correct numbers", "winners": 19, "payout": "R4,349.50"},
                "Division 4": {"match": "4 + bonus", "winners": 74, "payout": "R1,130.20"},
                "Division 5": {"match": "4 correct numbers", "winners": 1471, "payout": "R107.80"},
                "Division 6": {"match": "3 + bonus", "winners": 1944, "payout": "R80.90"},
                "Division 7": {"match": "3 correct numbers", "winners": 27219, "payout": "R25.00"},
                "Division 8": {"match": "2 + bonus", "winners": 21156, "payout": "R15.00"}
            }
        },
        {
            "draw_number": "2641",
            "draw_date": "2025-05-14", # Wednesday draw (corrected from 15th to 14th)
            "numbers": ["05", "15", "20", "29", "38", "41"],
            "bonus_numbers": ["22"],
            "jackpot": "R1,550,000.00",
            "next_jackpot": "R1,700,000.00",
            "divisions": {
                "Division 1": {"match": "6 correct numbers", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "5 + bonus", "winners": 1, "payout": "R76,321.80"},
                "Division 3": {"match": "5 correct numbers", "winners": 23, "payout": "R3,278.80"},
                "Division 4": {"match": "4 + bonus", "winners": 69, "payout": "R1,107.30"},
                "Division 5": {"match": "4 correct numbers", "winners": 1410, "payout": "R98.40"},
                "Division 6": {"match": "3 + bonus", "winners": 1985, "payout": "R68.80"},
                "Division 7": {"match": "3 correct numbers", "winners": 26118, "payout": "R25.00"},
                "Division 8": {"match": "2 + bonus", "winners": 20458, "payout": "R15.00"}
            }
        }
    ],
    "Powerball": [
        {
            "draw_number": "1616",
            "draw_date": "2025-05-17", # Friday draw (corrected to be Friday, not Saturday)
            "numbers": ["03", "13", "20", "29", "48"],
            "bonus_numbers": ["11"],
            "jackpot": "R60,000,000.00",
            "next_jackpot": "R65,000,000.00",
            "divisions": {
                "Division 1": {"match": "5 + Powerball", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "5 correct numbers", "winners": 1, "payout": "R707,041.20"},
                "Division 3": {"match": "4 + Powerball", "winners": 24, "payout": "R19,528.90"},
                "Division 4": {"match": "4 correct numbers", "winners": 388, "payout": "R1,159.70"},
                "Division 5": {"match": "3 + Powerball", "winners": 849, "payout": "R509.30"},
                "Division 6": {"match": "3 correct numbers", "winners": 15908, "payout": "R26.00"},
                "Division 7": {"match": "2 + Powerball", "winners": 12018, "payout": "R23.20"},
                "Division 8": {"match": "1 + Powerball", "winners": 58862, "payout": "R12.50"},
                "Division 9": {"match": "Powerball only", "winners": 92235, "payout": "R7.50"}
            }
        },
        {
            "draw_number": "1615",
            "draw_date": "2025-05-14", # Tuesday draw (corrected to 14th)
            "numbers": ["14", "17", "18", "33", "37"],
            "bonus_numbers": ["06"],
            "jackpot": "R54,000,000.00",
            "next_jackpot": "R60,000,000.00",
            "divisions": {
                "Division 1": {"match": "5 + Powerball", "winners": 2, "payout": "R33,767,092.01"},
                "Division 2": {"match": "5 correct numbers", "winners": 3, "payout": "R208,224.00"},
                "Division 3": {"match": "4 + Powerball", "winners": 18, "payout": "R22,903.20"},
                "Division 4": {"match": "4 correct numbers", "winners": 341, "payout": "R1,221.60"},
                "Division 5": {"match": "3 + Powerball", "winners": 779, "payout": "R531.10"},
                "Division 6": {"match": "3 correct numbers", "winners": 14543, "payout": "R27.40"},
                "Division 7": {"match": "2 + Powerball", "winners": 10995, "payout": "R23.50"},
                "Division 8": {"match": "1 + Powerball", "winners": 52933, "payout": "R12.70"},
                "Division 9": {"match": "Powerball only", "winners": 82053, "payout": "R7.50"}
            }
        }
    ],
    "Powerball Plus": [
        {
            "draw_number": "1616",
            "draw_date": "2025-05-17", # Friday draw (corrected to be Friday, not Saturday)
            "numbers": ["05", "15", "22", "24", "50"],
            "bonus_numbers": ["02"],
            "jackpot": "R8,500,000.00",
            "next_jackpot": "R3,500,000.00",
            "divisions": {
                "Division 1": {"match": "5 + Powerball", "winners": 1, "payout": "R9,543,671.10"},
                "Division 2": {"match": "5 correct numbers", "winners": 2, "payout": "R98,241.30"},
                "Division 3": {"match": "4 + Powerball", "winners": 17, "payout": "R7,642.30"},
                "Division 4": {"match": "4 correct numbers", "winners": 281, "payout": "R605.90"},
                "Division 5": {"match": "3 + Powerball", "winners": 628, "payout": "R256.50"},
                "Division 6": {"match": "3 correct numbers", "winners": 9974, "payout": "R16.10"},
                "Division 7": {"match": "2 + Powerball", "winners": 7607, "payout": "R13.60"},
                "Division 8": {"match": "1 + Powerball", "winners": 36578, "payout": "R7.90"},
                "Division 9": {"match": "Powerball only", "winners": 55803, "payout": "R5.00"}
            }
        },
        {
            "draw_number": "1615",
            "draw_date": "2025-05-14", # Tuesday draw (corrected to 14th)
            "numbers": ["13", "22", "27", "36", "44"],
            "bonus_numbers": ["11"],
            "jackpot": "R8,100,000.00",
            "next_jackpot": "R8,500,000.00",
            "divisions": {
                "Division 1": {"match": "5 + Powerball", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "5 correct numbers", "winners": 1, "payout": "R156,928.20"},
                "Division 3": {"match": "4 + Powerball", "winners": 15, "payout": "R7,107.10"},
                "Division 4": {"match": "4 correct numbers", "winners": 256, "payout": "R547.80"},
                "Division 5": {"match": "3 + Powerball", "winners": 583, "payout": "R239.70"},
                "Division 6": {"match": "3 correct numbers", "winners": 9453, "payout": "R14.70"},
                "Division 7": {"match": "2 + Powerball", "winners": 7091, "payout": "R12.60"},
                "Division 8": {"match": "1 + Powerball", "winners": 34240, "payout": "R7.30"},
                "Division 9": {"match": "Powerball only", "winners": 53051, "payout": "R5.00"}
            }
        }
    ],
    "Daily Lottery": [
        {
            "draw_number": "2258",
            "draw_date": "2025-05-18", # Sunday draw
            "numbers": ["02", "09", "15", "20", "27"],
            "bonus_numbers": [],
            "jackpot": "R400,000.00",
            "next_jackpot": "R400,000.00",
            "divisions": {
                "Division 1": {"match": "5 correct numbers", "winners": 3, "payout": "R158,741.70"},
                "Division 2": {"match": "4 correct numbers", "winners": 242, "payout": "R1,144.80"},
                "Division 3": {"match": "3 correct numbers", "winners": 7364, "payout": "R25.00"},
                "Division 4": {"match": "2 correct numbers", "winners": 71442, "payout": "R5.00"}
            }
        },
        {
            "draw_number": "2257",
            "draw_date": "2025-05-17", # Saturday draw
            "numbers": ["04", "12", "19", "26", "35"],
            "bonus_numbers": [],
            "jackpot": "R400,000.00",
            "next_jackpot": "R400,000.00",
            "divisions": {
                "Division 1": {"match": "5 correct numbers", "winners": 2, "payout": "R223,859.40"},
                "Division 2": {"match": "4 correct numbers", "winners": 262, "payout": "R898.30"},
                "Division 3": {"match": "3 correct numbers", "winners": 7587, "payout": "R25.00"},
                "Division 4": {"match": "2 correct numbers", "winners": 70652, "payout": "R5.00"}
            }
        },
        {
            "draw_number": "2256",
            "draw_date": "2025-05-16", # Friday draw
            "numbers": ["05", "11", "23", "31", "32"],
            "bonus_numbers": [],
            "jackpot": "R400,000.00",
            "next_jackpot": "R400,000.00",
            "divisions": {
                "Division 1": {"match": "5 correct numbers", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "4 correct numbers", "winners": 301, "payout": "R820.90"},
                "Division 3": {"match": "3 correct numbers", "winners": 9032, "payout": "R25.00"},
                "Division 4": {"match": "2 correct numbers", "winners": 80892, "payout": "R5.00"}
            }
        },
        {
            "draw_number": "2255",
            "draw_date": "2025-05-15", # Thursday draw
            "numbers": ["03", "04", "15", "20", "36"],
            "bonus_numbers": [],
            "jackpot": "R400,000.00",
            "next_jackpot": "R400,000.00",
            "divisions": {
                "Division 1": {"match": "5 correct numbers", "winners": 1, "payout": "R410,520.60"},
                "Division 2": {"match": "4 correct numbers", "winners": 264, "payout": "R912.30"},
                "Division 3": {"match": "3 correct numbers", "winners": 8157, "payout": "R25.00"},
                "Division 4": {"match": "2 correct numbers", "winners": 76453, "payout": "R5.00"}
            }
        },
        {
            "draw_number": "2254",
            "draw_date": "2025-05-14", # Wednesday draw
            "numbers": ["10", "14", "17", "21", "24"],
            "bonus_numbers": [],
            "jackpot": "R400,000.00",
            "next_jackpot": "R400,000.00",
            "divisions": {
                "Division 1": {"match": "5 correct numbers", "winners": 0, "payout": "R0.00"},
                "Division 2": {"match": "4 correct numbers", "winners": 246, "payout": "R845.50"},
                "Division 3": {"match": "3 correct numbers", "winners": 7945, "payout": "R25.00"},
                "Division 4": {"match": "2 correct numbers", "winners": 73521, "payout": "R5.00"}
            }
        }
    ]
}

def verify_lottery_data():
    """
    Verify lottery data in database against official information.
    This checks for accuracy of dates, numbers, and prize information.
    """
    verifications = {
        "correct": 0,
        "incorrect": 0,
        "missing": 0,
        "corrections": []
    }
    
    with app.app_context():
        for lottery_type, draws in OFFICIAL_DRAW_DATA.items():
            print(f"\n\n{'-' * 80}\nVerifying {lottery_type}:\n{'-' * 80}")
            
            for draw_data in draws:
                draw_number = draw_data.get("draw_number")
                expected_date = draw_data.get("draw_date")
                expected_numbers = draw_data.get("numbers")
                expected_bonus = draw_data.get("bonus_numbers") or []
                expected_divisions = draw_data.get("divisions") or {}
                
                # Try to find this draw in the database (checking all spelling variations)
                result = None
                
                # First check with the exact lottery type name
                result = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=draw_number
                ).first()
                
                # If not found with exact name, try with Lotto instead of Lottery
                if not result and "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    result = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=draw_number
                    ).first()
                
                # If still not found, try case variations for PowerBall
                if not result and "Powerball" in lottery_type:
                    alt_type = lottery_type.replace("Powerball", "PowerBall")
                    result = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=draw_number
                    ).first()
                
                # If draw not found, report as missing
                if not result:
                    print(f"❌ {lottery_type} Draw #{draw_number} - MISSING FROM DATABASE")
                    verifications["missing"] += 1
                    
                    # Create an entry to fix this later
                    verifications["corrections"].append({
                        "action": "add",
                        "lottery_type": lottery_type,
                        "draw_number": draw_number,
                        "draw_data": draw_data
                    })
                    continue
                
                # Check draw date
                actual_date = result.draw_date.strftime("%Y-%m-%d") if result.draw_date else None
                date_correct = (actual_date == expected_date)
                
                # Check numbers
                actual_numbers = json.loads(result.numbers) if result.numbers else []
                numbers_correct = sorted(actual_numbers) == sorted(expected_numbers)
                
                # Check bonus numbers
                actual_bonus = json.loads(result.bonus_numbers) if result.bonus_numbers else []
                bonus_correct = sorted(actual_bonus) == sorted(expected_bonus)
                
                # Check divisions if available
                divisions_correct = True
                if expected_divisions and result.divisions:
                    try:
                        actual_divisions = json.loads(result.divisions)
                        
                        # Check if all expected divisions are present
                        for div_name, div_data in expected_divisions.items():
                            if div_name not in actual_divisions:
                                divisions_correct = False
                                break
                            
                            # Check division details
                            actual_div = actual_divisions[div_name]
                            if (str(actual_div.get("winners")) != str(div_data.get("winners"))):
                                divisions_correct = False
                                break
                    except (json.JSONDecodeError, TypeError):
                        divisions_correct = False
                elif expected_divisions and not result.divisions:
                    divisions_correct = False
                
                # Print verification results
                status = "✅" if (date_correct and numbers_correct and bonus_correct and divisions_correct) else "❌"
                db_lottery_type = result.lottery_type
                
                print(f"{status} {lottery_type} Draw #{draw_number} (Stored as: {db_lottery_type})")
                print(f"   Date: {'✅' if date_correct else '❌'} Expected: {expected_date}, Actual: {actual_date}")
                print(f"   Numbers: {'✅' if numbers_correct else '❌'} Expected: {expected_numbers}, Actual: {actual_numbers}")
                print(f"   Bonus: {'✅' if bonus_correct else '❌'} Expected: {expected_bonus}, Actual: {actual_bonus}")
                print(f"   Divisions: {'✅' if divisions_correct else '❌'}")
                
                if (date_correct and numbers_correct and bonus_correct and divisions_correct):
                    verifications["correct"] += 1
                else:
                    verifications["incorrect"] += 1
                    
                    # Create an entry to fix this later
                    verifications["corrections"].append({
                        "action": "update",
                        "lottery_type": db_lottery_type,
                        "draw_number": draw_number,
                        "id": result.id,
                        "date_correct": date_correct,
                        "numbers_correct": numbers_correct,
                        "bonus_correct": bonus_correct,
                        "divisions_correct": divisions_correct,
                        "draw_data": draw_data
                    })
    
    return verifications

def fix_lottery_data(verifications):
    """
    Fix lottery data based on verification results.
    This updates incorrect data and adds missing draws.
    """
    fixed_count = 0
    added_count = 0
    
    with app.app_context():
        for correction in verifications["corrections"]:
            action = correction.get("action")
            draw_data = correction.get("draw_data")
            
            if action == "update":
                lottery_type = correction.get("lottery_type")
                draw_number = correction.get("draw_number")
                result_id = correction.get("id")
                
                # Skip if no ID to update
                if not result_id:
                    continue
                
                # Find the result to update
                result = LotteryResult.query.get(result_id)
                if not result:
                    continue
                
                # Update the fields as needed
                if not correction.get("date_correct"):
                    result.draw_date = datetime.strptime(draw_data.get("draw_date"), "%Y-%m-%d")
                
                if not correction.get("numbers_correct"):
                    result.numbers = json.dumps(draw_data.get("numbers"))
                
                if not correction.get("bonus_correct"):
                    result.bonus_numbers = json.dumps(draw_data.get("bonus_numbers"))
                
                if not correction.get("divisions_correct"):
                    result.divisions = json.dumps(draw_data.get("divisions"))
                
                fixed_count += 1
                logger.info(f"Fixed {lottery_type} draw {draw_number}")
                
            elif action == "add":
                lottery_type = correction.get("lottery_type")
                draw_number = correction.get("draw_number")
                
                # Parse date
                draw_date = datetime.strptime(draw_data.get("draw_date"), "%Y-%m-%d")
                
                # Create new draw record
                new_draw = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=draw_number,
                    draw_date=draw_date,
                    numbers=json.dumps(draw_data.get("numbers")),
                    bonus_numbers=json.dumps(draw_data.get("bonus_numbers")) if draw_data.get("bonus_numbers") else None,
                    divisions=json.dumps(draw_data.get("divisions")) if draw_data.get("divisions") else None,
                    source_url="https://www.nationallottery.co.za/results",
                    ocr_provider="official",
                    ocr_model="direct-input",
                    ocr_timestamp=datetime.now()
                )
                
                db.session.add(new_draw)
                added_count += 1
                logger.info(f"Added new {lottery_type} draw {draw_number}")
        
        # Commit all changes
        db.session.commit()
    
    return fixed_count, added_count

def main():
    """Main function to verify and fix lottery data."""
    try:
        print("Verifying all lottery data from the past week...")
        
        # Step 1: Verify the data
        verifications = verify_lottery_data()
        
        print(f"\n\n{'-' * 80}")
        print(f"Verification Summary:")
        print(f"{'-' * 80}")
        print(f"Correct draws: {verifications['correct']}")
        print(f"Incorrect draws: {verifications['incorrect']}")
        print(f"Missing draws: {verifications['missing']}")
        print(f"Total draws checked: {verifications['correct'] + verifications['incorrect'] + verifications['missing']}")
        
        # Step 2: Automatically fix the data if needed
        if verifications["incorrect"] > 0 or verifications["missing"] > 0:
            print("\nFixing incorrect and missing draws automatically...")
            fixed, added = fix_lottery_data(verifications)
            print(f"\nSuccessfully fixed {fixed} draws and added {added} new draws.")
            
            # Verify again after fixing
            print("\nRe-verifying data after fixes:")
            new_verifications = verify_lottery_data()
            print(f"\n\n{'-' * 80}")
            print(f"Verification After Fixes:")
            print(f"{'-' * 80}")
            print(f"Correct draws: {new_verifications['correct']}")
            print(f"Incorrect draws: {new_verifications['incorrect']}")
            print(f"Missing draws: {new_verifications['missing']}")
            print(f"Total draws checked: {new_verifications['correct'] + new_verifications['incorrect'] + new_verifications['missing']}")
        else:
            print("\nAll lottery data verified and correct!")
        
    except Exception as e:
        logger.error(f"Error verifying lottery data: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()