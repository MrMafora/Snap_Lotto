import os
import sys
import json
from datetime import datetime, timedelta
import random

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the database models and app
from app import db, app
from models import LotteryResult, Screenshot

# Sample data for the different lottery types
LOTTERY_TYPES = [
    {
        "name": "Lotto",
        "numbers_count": 6,
        "bonus_numbers": True,
        "url": "https://www.nationallottery.co.za/lotto-history"
    },
    {
        "name": "Lotto Plus 1",
        "numbers_count": 6,
        "bonus_numbers": True,
        "url": "https://www.nationallottery.co.za/lotto-plus-1-history"
    },
    {
        "name": "Lotto Plus 2",
        "numbers_count": 6,
        "bonus_numbers": True,
        "url": "https://www.nationallottery.co.za/lotto-plus-2-history"
    },
    {
        "name": "Powerball",
        "numbers_count": 5,
        "bonus_numbers": True,
        "url": "https://www.nationallottery.co.za/powerball-history"
    },
    {
        "name": "Powerball Plus",
        "numbers_count": 5,
        "bonus_numbers": True,
        "url": "https://www.nationallottery.co.za/powerball-plus-history"
    },
    {
        "name": "Daily Lotto",
        "numbers_count": 5,
        "bonus_numbers": False,
        "url": "https://www.nationallottery.co.za/daily-lotto-history"
    }
]

def generate_unique_numbers(count, max_number=49):
    """Generate a list of unique random numbers"""
    return sorted(random.sample(range(1, max_number + 1), count))

def create_sample_data(num_draws_per_type=10):
    """Create sample lottery results for testing"""
    print("Creating sample lottery data...")
    
    with app.app_context():
        # Clear existing data first
        try:
            LotteryResult.query.delete()
            Screenshot.query.delete()
            db.session.commit()
            print("Cleared existing data")
        except Exception as e:
            print(f"Error clearing data: {str(e)}")
            db.session.rollback()
        
        # Base date for the draws (start 60 days ago)
        base_date = datetime.now() - timedelta(days=60)
        
        # Create data for each lottery type
        for lottery_type in LOTTERY_TYPES:
            print(f"Creating data for {lottery_type['name']}...")
            
            # Create a screenshot for this lottery type
            screenshot = Screenshot(
                url=lottery_type['url'],
                lottery_type=lottery_type['name'],
                timestamp=datetime.now(),
                path=f"/screenshots/{lottery_type['name'].lower().replace(' ', '_')}.html",
                processed=True
            )
            db.session.add(screenshot)
            db.session.commit()
            
            # Create multiple draws for this lottery type
            for i in range(num_draws_per_type):
                # Randomize date within the last 60 days with more recent entries
                days_offset = int(i * (60/num_draws_per_type))
                draw_date = base_date + timedelta(days=days_offset)
                
                # Generate the main numbers
                numbers = generate_unique_numbers(lottery_type['numbers_count'])
                
                # Generate bonus number if applicable
                bonus_numbers = None
                if lottery_type['bonus_numbers']:
                    # Make sure bonus number is not in the main numbers
                    possible_bonus = list(set(range(1, 50)) - set(numbers))
                    bonus_numbers = [random.choice(possible_bonus)]
                
                # Create the result record
                result = LotteryResult(
                    lottery_type=lottery_type['name'],
                    draw_number=f"{2000 + i}",
                    draw_date=draw_date,
                    numbers=json.dumps(numbers),
                    bonus_numbers=json.dumps(bonus_numbers) if bonus_numbers else None,
                    source_url=lottery_type['url'],
                    screenshot_id=screenshot.id,
                    created_at=datetime.now()
                )
                db.session.add(result)
            
            # Commit the results for this lottery type
            try:
                db.session.commit()
                print(f"Created {num_draws_per_type} draws for {lottery_type['name']}")
            except Exception as e:
                print(f"Error creating data for {lottery_type['name']}: {str(e)}")
                db.session.rollback()
    
    print("Sample data creation completed!")

if __name__ == "__main__":
    create_sample_data(10)  # Create 10 draws per lottery type