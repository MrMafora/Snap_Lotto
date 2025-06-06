"""
Manual entry tool for comprehensive lottery data based on screenshot analysis
This tool allows manual input of detailed lottery information when AI extraction times out
"""
import json
from datetime import datetime
from models import db, LotteryResult
from main import app

def create_june_6_lotto_entry():
    """Create comprehensive entry for June 6, 2025 LOTTO results based on screenshot"""
    
    # Data extracted from the June 6, 2025 LOTTO screenshot
    lotto_data = {
        "lottery_type": "LOTTO",
        "draw_id": 2547,
        "draw_date": "2025-06-04", 
        "main_numbers": [32, 34, 8, 52, 36, 24],  # Draw order from left side
        "bonus_number": 26,
        "prize_divisions": [
            {
                "division": "DIV 1",
                "requirement": "SIX CORRECT NUMBERS", 
                "winners": 0,
                "prize_amount": "R0.00"
            },
            {
                "division": "DIV 2",
                "requirement": "FIVE CORRECT NUMBERS + BONUS BALL",
                "winners": 5, 
                "prize_amount": "R0.00"
            },
            {
                "division": "DIV 3", 
                "requirement": "FIVE CORRECT NUMBERS",
                "winners": 108,
                "prize_amount": "R6,883.20"
            },
            {
                "division": "DIV 4",
                "requirement": "FOUR CORRECT NUMBERS + BONUS BALL", 
                "winners": 2054,
                "prize_amount": "R1,972.70"
            },
            {
                "division": "DIV 5",
                "requirement": "FOUR CORRECT NUMBERS",
                "winners": 8814, 
                "prize_amount": "R173.90"
            },
            {
                "division": "DIV 6",
                "requirement": "THREE CORRECT NUMBERS + BONUS BALL",
                "winners": 11161,
                "prize_amount": "R109.80"
            },
            {
                "division": "DIV 7", 
                "requirement": "THREE CORRECT NUMBERS",
                "winners": 30605,
                "prize_amount": "R50.00"
            },
            {
                "division": "DIV 8",
                "requirement": "TWO CORRECT NUMBERS + BONUS BALL", 
                "winners": None,  # Not shown
                "prize_amount": "R20.00"
            }
        ],
        "financial_info": {
            "rollover_amount": "R63,481,569.30",
            "rollover_no": 20,
            "total_pool_size": "R67,302,275.10", 
            "total_sales": "R15,402,610.00",
            "next_jackpot": "R67,000,000.00",
            "draw_machine": "RNG 1",
            "next_draw_date": "2025-06-07"
        }
    }
    
    return lotto_data

def save_comprehensive_lotto_data(data):
    """Save comprehensive LOTTO data to database"""
    
    with app.app_context():
        try:
            # Check if this draw already exists
            existing = LotteryResult.query.filter_by(
                lottery_type=data['lottery_type'],
                draw_number=data['draw_id']
            ).first()
            
            if existing:
                print(f"Draw {data['draw_id']} for {data['lottery_type']} already exists")
                return False
            
            # Parse date
            draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d')
            
            # Format numbers for existing database schema (using 'numbers' field)
            numbers_str = json.dumps(data['main_numbers'])
            
            # Format bonus number 
            bonus_numbers = None
            if data.get('bonus_number'):
                bonus_numbers = json.dumps([data['bonus_number']])
            
            # Create lottery result with comprehensive data
            lottery_result = LotteryResult(
                lottery_type=data['lottery_type'],
                draw_number=data['draw_id'],
                draw_date=draw_date,
                numbers=numbers_str,
                bonus_numbers=bonus_numbers,
                divisions=json.dumps(data['prize_divisions']),
                rollover_amount=data['financial_info']['rollover_amount'],
                rollover_number=data['financial_info']['rollover_no'],
                total_pool_size=data['financial_info']['total_pool_size'],
                total_sales=data['financial_info']['total_sales'],
                next_jackpot=data['financial_info']['next_jackpot'],
                draw_machine=data['financial_info']['draw_machine'],
                next_draw_date_str=data['financial_info']['next_draw_date'],
                source_url="https://www.nationallottery.co.za"
            )
            
            db.session.add(lottery_result)
            db.session.commit()
            
            print(f"Successfully saved {data['lottery_type']} draw {data['draw_id']} with {len(data['prize_divisions'])} divisions")
            print(f"Main numbers: {data['main_numbers']}")
            print(f"Rollover amount: {data['financial_info']['rollover_amount']}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving comprehensive lottery data: {e}")
            return False

def add_june_6_comprehensive_data():
    """Add the comprehensive June 6, 2025 LOTTO data to database"""
    print("Adding comprehensive June 6, 2025 LOTTO data...")
    
    data = create_june_6_lotto_entry()
    success = save_comprehensive_lotto_data(data)
    
    if success:
        print("Successfully added comprehensive LOTTO data with all prize divisions")
    else:
        print("Failed to add comprehensive LOTTO data")
    
    return success

if __name__ == "__main__":
    add_june_6_comprehensive_data()