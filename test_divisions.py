import sys
import json
from main import app
from models import LotteryResult

def inspect_divisions():
    with app.app_context():
        # Check each lottery type
        lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 'Powerball', 'Powerball Plus', 'Daily Lotto']
        
        for lottery_type in lottery_types:
            print(f"\n======= {lottery_type} =======")
            
            # Get the most recent result
            result = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
            
            if not result:
                print(f"No {lottery_type} results found")
                continue
                
            print(f"Found result: {result}")
            
            # Check divisions data
            divisions = result.get_divisions()
            print(f"Divisions type: {type(divisions)}")
            print(f"Divisions data: {json.dumps(divisions, indent=2)}")
            
            # Check for price formatting
            if divisions:
                for div, data in divisions.items():
                    print(f"Division: {div}")
                    prize = data.get('prize')
                    prize_type = type(prize)
                    print(f"  Prize: {prize} (Type: {prize_type})")
                    
                    # Try to convert to float if not already
                    if prize and not isinstance(prize, float):
                        try:
                            float_prize = float(prize)
                            print(f"  Float conversion: {float_prize}")
                        except (ValueError, TypeError):
                            print(f"  Cannot convert to float: {prize}")

if __name__ == "__main__":
    inspect_divisions()