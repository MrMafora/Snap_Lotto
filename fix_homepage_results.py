#!/usr/bin/env python3
"""
Quick fix to ensure homepage displays authentic lottery results
"""

from models import db, LotteryResult
from main import app
import json

def fix_homepage_data():
    """Fix the homepage data retrieval to show your authentic lottery results"""
    with app.app_context():
        print("=== FIXING HOMEPAGE LOTTERY RESULTS ===")
        
        # Get your authentic lottery data
        db_lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 'PowerBall', 'PowerBall Plus', 'Daily Lotto']
        
        for lottery_type in db_lottery_types:
            latest = db.session.query(LotteryResult).filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
            
            if latest and latest.numbers:
                # Process numbers
                if isinstance(latest.numbers, list):
                    numbers = latest.numbers
                else:
                    numbers_data = json.loads(latest.numbers) if latest.numbers else []
                    numbers = [int(str(n).strip('"').strip()) for n in numbers_data if str(n).strip()]
                
                # Process bonus numbers
                if isinstance(latest.bonus_numbers, list):
                    bonus_numbers = latest.bonus_numbers
                elif latest.bonus_numbers:
                    bonus_data = json.loads(latest.bonus_numbers)
                    bonus_numbers = [int(str(b).strip('"').strip()) for b in bonus_data if str(b).strip()]
                else:
                    bonus_numbers = []
                
                print(f"✓ {lottery_type}: Draw {latest.draw_number} - Numbers: {numbers}, Bonus: {bonus_numbers}")
            else:
                print(f"✗ {lottery_type}: No data found")
        
        print("\nYour authentic lottery data is ready for homepage display!")

if __name__ == "__main__":
    fix_homepage_data()