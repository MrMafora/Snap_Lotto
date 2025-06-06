"""
Process fresh lottery data from the latest screenshots (June 4-6, 2025)
Extract and update database with authentic lottery results
"""

import json
from datetime import datetime
from models import db, LotteryResult

def add_corrected_lotto_data():
    """Add corrected LOTTO data from screenshot - Draw ID 2547"""
    
    # From screenshot: Main Numbers: 12, 34, 08, 52, 36, 24 + 26
    # Current database has incorrect numbers - need to fix
    
    divisions_data = [
        {"division": "DIV 1", "requirement": "SIX CORRECT NUMBERS", "winners": 0, "prize_amount": "R0.00"},
        {"division": "DIV 2", "requirement": "FIVE CORRECT NUMBERS + BONUS BALL", "winners": 0, "prize_amount": "R0.00"},
        {"division": "DIV 3", "requirement": "FIVE CORRECT NUMBERS", "winners": 39, "prize_amount": "R6,883.20"},
        {"division": "DIV 4", "requirement": "FOUR CORRECT NUMBERS + BONUS BALL", "winners": 108, "prize_amount": "R1,972.70"},
        {"division": "DIV 5", "requirement": "FOUR CORRECT NUMBERS", "winners": 2054, "prize_amount": "R173.90"},
        {"division": "DIV 6", "requirement": "THREE CORRECT NUMBERS + BONUS BALL", "winners": 8814, "prize_amount": "R109.80"},
        {"division": "DIV 7", "requirement": "THREE CORRECT NUMBERS", "winners": 11161, "prize_amount": "R50.00"},
        {"division": "DIV 8", "requirement": "TWO CORRECT NUMBERS + BONUS BALL", "winners": 30605, "prize_amount": "R20.00"}
    ]
    
    # Check if record exists and update with correct numbers
    existing = LotteryResult.query.filter_by(lottery_type='LOTTO', draw_number=2547).first()
    if existing:
        # Update with correct numbers from screenshot
        existing.numbers = json.dumps([12, 34, 8, 52, 36, 24])  # Correct numbers from screenshot
        existing.bonus_numbers = json.dumps([26])
        existing.divisions = json.dumps(divisions_data)
        existing.rollover_amount = "R63,481,549.30"
        existing.rollover_number = 26
        existing.total_pool_size = "R67,302,275.10"
        existing.total_sales = "R35,502,615.00"
        existing.next_jackpot = "R67,000,000.00"
        existing.draw_machine = "RNG 1"
        existing.next_draw_date = datetime(2025, 6, 7)
        print(f"Updated LOTTO 2547 with correct numbers: [12, 34, 8, 52, 36, 24] + 26")
    else:
        print("LOTTO 2547 record not found")

def add_corrected_lotto_plus_1_data():
    """Add corrected LOTTO PLUS 1 data from screenshot - Draw ID 2547"""
    
    divisions_data = [
        {"division": "DIV 1", "requirement": "SIX CORRECT NUMBERS", "winners": 0, "prize_amount": "R0.00"},
        {"division": "DIV 2", "requirement": "FIVE CORRECT NUMBERS + BONUS BALL", "winners": 0, "prize_amount": "R0.00"},
        {"division": "DIV 3", "requirement": "FIVE CORRECT NUMBERS", "winners": 30, "prize_amount": "R8,377.20"},
        {"division": "DIV 4", "requirement": "FOUR CORRECT NUMBERS + BONUS BALL", "winners": 75, "prize_amount": "R1,663.00"},
        {"division": "DIV 5", "requirement": "FOUR CORRECT NUMBERS", "winners": 1657, "prize_amount": "R150.60"},
        {"division": "DIV 6", "requirement": "THREE CORRECT NUMBERS + BONUS BALL", "winners": 7460, "prize_amount": "R102.20"},
        {"division": "DIV 7", "requirement": "THREE CORRECT NUMBERS", "winners": 13286, "prize_amount": "R25.00"},
        {"division": "DIV 8", "requirement": "TWO CORRECT NUMBERS + BONUS BALL", "winners": 56976, "prize_amount": "R15.00"}
    ]
    
    existing = LotteryResult.query.filter_by(lottery_type='LOTTO PLUS 1', draw_number=2547).first()
    if existing:
        # Numbers are correct, just update divisions with exact screenshot data
        existing.divisions = json.dumps(divisions_data)
        existing.rollover_amount = "R13,788,244.85"
        existing.rollover_number = 12
        existing.total_pool_size = "R15,674,998.08"
        existing.total_sales = "R6,346,795.00"
        existing.next_jackpot = "R15,000,000.00"
        existing.draw_machine = "RNG 1"
        existing.next_draw_date = datetime(2025, 6, 7)
        print(f"Updated LOTTO PLUS 1 2547 divisions with screenshot data")
    else:
        print("LOTTO PLUS 1 2547 record not found")

def add_corrected_lotto_plus_2_data():
    """Add corrected LOTTO PLUS 2 data from screenshot - Draw ID 2547"""
    
    divisions_data = [
        {"division": "DIV 1", "requirement": "SIX CORRECT NUMBERS", "winners": 0, "prize_amount": "R0.00"},
        {"division": "DIV 2", "requirement": "FIVE CORRECT NUMBERS + BONUS BALL", "winners": 2, "prize_amount": "R67,603.10"},
        {"division": "DIV 3", "requirement": "FIVE CORRECT NUMBERS", "winners": 27, "prize_amount": "R3,338.40"},
        {"division": "DIV 4", "requirement": "FOUR CORRECT NUMBERS + BONUS BALL", "winners": 58, "prize_amount": "R1,928.20"},
        {"division": "DIV 5", "requirement": "FOUR CORRECT NUMBERS", "winners": 1758, "prize_amount": "R127.20"},
        {"division": "DIV 6", "requirement": "THREE CORRECT NUMBERS + BONUS BALL", "winners": 7508, "prize_amount": "R104.10"},
        {"division": "DIV 7", "requirement": "THREE CORRECT NUMBERS", "winners": 13610, "prize_amount": "R25.00"},
        {"division": "DIV 8", "requirement": "TWO CORRECT NUMBERS + BONUS BALL", "winners": 53140, "prize_amount": "R15.00"}
    ]
    
    existing = LotteryResult.query.filter_by(lottery_type='LOTTO PLUS 2', draw_number=2547).first()
    if existing:
        # Numbers are correct, update divisions with exact screenshot data
        existing.divisions = json.dumps(divisions_data)
        existing.rollover_amount = "R8,996,961.23"
        existing.rollover_number = 8
        existing.total_pool_size = "R10,968,714.23"
        existing.total_sales = "R5,713,195.00"
        existing.next_jackpot = "R10,000,000.00"
        existing.draw_machine = "RNG 1"
        existing.next_draw_date = datetime(2025, 6, 7)
        print(f"Updated LOTTO PLUS 2 2547 divisions with screenshot data")
    else:
        print("LOTTO PLUS 2 2547 record not found")

def add_new_powerball_data():
    """Add new PowerBall data from screenshot - Draw ID 1621 (June 3, 2025)"""
    
    divisions_data = [
        {"division": "DIV 1", "requirement": "FIVE CORRECT NUMBERS + POWERBALL", "winners": 0, "prize_amount": "R0.00"},
        {"division": "DIV 2", "requirement": "FIVE CORRECT NUMBERS", "winners": 1, "prize_amount": "R226,644.80"},
        {"division": "DIV 3", "requirement": "FOUR CORRECT NUMBERS + POWERBALL", "winners": 7, "prize_amount": "R20,275.10"},
        {"division": "DIV 4", "requirement": "FOUR CORRECT NUMBERS", "winners": 207, "prize_amount": "R1,162.40"},
        {"division": "DIV 5", "requirement": "THREE CORRECT NUMBERS + POWERBALL", "winners": 461, "prize_amount": "R590.20"},
        {"division": "DIV 6", "requirement": "THREE CORRECT NUMBERS", "winners": 9159, "prize_amount": "R24.80"},
        {"division": "DIV 7", "requirement": "TWO CORRECT NUMBERS + POWERBALL", "winners": 7118, "prize_amount": "R23.90"},
        {"division": "DIV 8", "requirement": "ONE CORRECT NUMBERS + POWERBALL", "winners": 48247, "prize_amount": "R15.00"},
        {"division": "DIV 9", "requirement": "MATCH POWERBALL", "winners": 69876, "prize_amount": "R10.00"}
    ]
    
    # Check if this PowerBall draw exists
    existing = LotteryResult.query.filter_by(lottery_type='PowerBall', draw_number=1621).first()
    if existing:
        existing.numbers = json.dumps([50, 5, 47, 40, 26])
        existing.bonus_numbers = json.dumps([14])
        existing.divisions = json.dumps(divisions_data)
        existing.draw_date = datetime(2025, 6, 3)
        existing.rollover_amount = "R12,127,002.75"
        existing.rollover_number = 1
        existing.total_pool_size = "R14,708,000.65"
        existing.total_sales = "R51,811,285.00"
        existing.next_jackpot = "R16,000,000.00"
        existing.draw_machine = "RNG 1 and 1"
        existing.next_draw_date = datetime(2025, 6, 6)
        print(f"Updated PowerBall 1621 with screenshot data")
    else:
        # Create new record
        new_result = LotteryResult(
            lottery_type='PowerBall',
            draw_number=1621,
            draw_date=datetime(2025, 6, 3),
            numbers=json.dumps([50, 5, 47, 40, 26]),
            bonus_numbers=json.dumps([14]),
            divisions=json.dumps(divisions_data),
            rollover_amount="R12,127,002.75",
            rollover_number=1,
            total_pool_size="R14,708,000.65",
            total_sales="R51,811,285.00",
            next_jackpot="R16,000,000.00",
            draw_machine="RNG 1 and 1",
            next_draw_date=datetime(2025, 6, 6),
            source_url="https://www.nationallottery.co.za/results/powerball",
            ocr_provider="screenshot_manual_entry",
            ocr_model="manual_extraction_june_2025"
        )
        db.session.add(new_result)
        print(f"Added new PowerBall 1621 record")

def add_new_powerball_plus_data():
    """Add new PowerBall Plus data from screenshot - Draw ID 1621 (June 3, 2025)"""
    
    divisions_data = [
        {"division": "DIV 1", "requirement": "FIVE CORRECT NUMBERS + POWERBALL", "winners": 0, "prize_amount": "R0.00"},
        {"division": "DIV 2", "requirement": "FIVE CORRECT NUMBERS", "winners": 0, "prize_amount": "R0.00"},
        {"division": "DIV 3", "requirement": "FOUR CORRECT NUMBERS + POWERBALL", "winners": 2, "prize_amount": "R33,238.20"},
        {"division": "DIV 4", "requirement": "FOUR CORRECT NUMBERS", "winners": 211, "prize_amount": "R514.20"},
        {"division": "DIV 5", "requirement": "THREE CORRECT NUMBERS + POWERBALL", "winners": 431, "prize_amount": "R284.60"},
        {"division": "DIV 6", "requirement": "THREE CORRECT NUMBERS", "winners": 8487, "prize_amount": "R12.00"},
        {"division": "DIV 7", "requirement": "TWO CORRECT NUMBERS + POWERBALL", "winners": 6438, "prize_amount": "R11.90"},
        {"division": "DIV 8", "requirement": "ONE CORRECT NUMBERS + POWERBALL", "winners": 44472, "prize_amount": "R7.50"},
        {"division": "DIV 9", "requirement": "MATCH POWERBALL", "winners": 61209, "prize_amount": "R5.00"}
    ]
    
    # Check if this PowerBall Plus draw exists  
    existing = LotteryResult.query.filter_by(lottery_type='PowerBall Plus', draw_number=1621).first()
    if existing:
        existing.numbers = json.dumps([16, 39, 37, 38, 30])
        existing.bonus_numbers = json.dumps([4])
        existing.divisions = json.dumps(divisions_data)
        existing.draw_date = datetime(2025, 6, 3)
        existing.rollover_amount = "R12,415,992.75"
        existing.rollover_number = 6
        existing.total_pool_size = "R13,563,683.75"
        existing.total_sales = "R5,994,110.00"
        existing.next_jackpot = "R14,000,000.00"
        existing.draw_machine = "RNG 1 and 1"
        existing.next_draw_date = datetime(2025, 6, 6)
        print(f"Updated PowerBall Plus 1621 with screenshot data")
    else:
        # Create new record
        new_result = LotteryResult(
            lottery_type='PowerBall Plus',
            draw_number=1621,
            draw_date=datetime(2025, 6, 3),
            numbers=json.dumps([16, 39, 37, 38, 30]),
            bonus_numbers=json.dumps([4]),
            divisions=json.dumps(divisions_data),
            rollover_amount="R12,415,992.75",
            rollover_number=6,
            total_pool_size="R13,563,683.75",
            total_sales="R5,994,110.00",
            next_jackpot="R14,000,000.00",
            draw_machine="RNG 1 and 1",
            next_draw_date=datetime(2025, 6, 6),
            source_url="https://www.nationallottery.co.za/results/powerball-plus",
            ocr_provider="screenshot_manual_entry",
            ocr_model="manual_extraction_june_2025"
        )
        db.session.add(new_result)
        print(f"Added new PowerBall Plus 1621 record")

def add_new_daily_lotto_data():
    """Add new Daily Lotto data from screenshot - Draw ID 2574 (June 5, 2025)"""
    
    divisions_data = [
        {"division": "DIV 1", "requirement": "FIVE CORRECT NUMBERS", "winners": 414, "prize_amount": "R0.00"},
        {"division": "DIV 2", "requirement": "FOUR CORRECT NUMBERS", "winners": 11575, "prize_amount": "R1,416.70"},
        {"division": "DIV 3", "requirement": "THREE CORRECT NUMBERS", "winners": 108090, "prize_amount": "R19.00"},
        {"division": "DIV 4", "requirement": "TWO CORRECT NUMBERS", "winners": None, "prize_amount": "R5.00"}
    ]
    
    # Check if this Daily Lotto draw exists
    existing = LotteryResult.query.filter_by(lottery_type='Daily Lotto', draw_number=2574).first()
    if existing:
        existing.numbers = json.dumps([7, 27, 35, 22, 15])
        existing.divisions = json.dumps(divisions_data)
        existing.draw_date = datetime(2025, 6, 5)
        existing.total_pool_size = "R1,346,888.80"
        existing.total_sales = "R2,678,082.00"
        existing.draw_machine = "RNG 1"
        existing.next_draw_date = datetime(2025, 6, 6)
        print(f"Updated Daily Lotto 2574 with screenshot data")
    else:
        # Create new record
        new_result = LotteryResult(
            lottery_type='Daily Lotto',
            draw_number=2574,
            draw_date=datetime(2025, 6, 5),
            numbers=json.dumps([7, 27, 35, 22, 15]),
            divisions=json.dumps(divisions_data),
            total_pool_size="R1,346,888.80",
            total_sales="R2,678,082.00",
            draw_machine="RNG 1",
            next_draw_date=datetime(2025, 6, 6),
            source_url="https://www.nationallottery.co.za/results/daily-lotto",
            ocr_provider="screenshot_manual_entry",
            ocr_model="manual_extraction_june_2025"
        )
        db.session.add(new_result)
        print(f"Added new Daily Lotto 2574 record")

def main():
    """Process all fresh lottery data from screenshots"""
    print("Processing fresh lottery data from screenshots...")
    
    try:
        # Update existing records with correct data from screenshots
        add_corrected_lotto_data()
        add_corrected_lotto_plus_1_data() 
        add_corrected_lotto_plus_2_data()
        
        # Add new lottery data
        add_new_powerball_data()
        add_new_powerball_plus_data()
        add_new_daily_lotto_data()
        
        # Commit all changes
        db.session.commit()
        print("✅ All fresh lottery data has been successfully processed and updated")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error processing lottery data: {e}")
        raise

if __name__ == "__main__":
    from app import app
    with app.app_context():
        main()