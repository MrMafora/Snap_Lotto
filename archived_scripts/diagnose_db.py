"""
Database diagnostic script to check for lottery results data
and troubleshoot analysis issues.
"""
import os
import sys
from datetime import datetime, timedelta
import json
import random

# Add Flask app context
from main import app, db
from models import LotteryResult, User

def check_lottery_data():
    """Check if we have lottery results in the database"""
    with app.app_context():
        # Count lottery results by type
        results = {}
        for lottery_type in ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 
                           'Powerball', 'Powerball Plus', 'Daily Lotto']:
            count = LotteryResult.query.filter_by(lottery_type=lottery_type).count()
            results[lottery_type] = count
        
        total = sum(results.values())
        
        print(f"Total lottery results: {total}")
        for lottery_type, count in results.items():
            print(f"  {lottery_type}: {count} results")
        
        # If no data, return False
        return total > 0

def import_sample_data():
    """Import sample lottery data for testing"""
    with app.app_context():
        # Only import if we have less than 10 results
        if LotteryResult.query.count() >= 10:
            print("Database already has data, skipping sample import")
            return

        lottery_types = ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 
                       'Powerball', 'Powerball Plus', 'Daily Lotto']
        
        # Create sample data for each lottery type
        for lottery_type in lottery_types:
            print(f"Creating sample data for {lottery_type}...")
            
            # Determine number of balls and range based on lottery type
            if lottery_type in ['Powerball', 'Powerball Plus']:
                num_balls = 5
                bonus_balls = 1
                number_range = 50
                bonus_range = 20
            elif lottery_type == 'Daily Lotto':
                num_balls = 5
                bonus_balls = 0
                number_range = 36
                bonus_range = 0
            else:  # Lotto types
                num_balls = 6
                bonus_balls = 0
                number_range = 52
                bonus_range = 0
            
            # Create 10 results for each lottery type
            for i in range(10):
                # Generate random draw date within the last year
                days_ago = random.randint(1, 365)
                draw_date = datetime.now() - timedelta(days=days_ago)
                
                # Generate random unique numbers
                numbers = random.sample(range(1, number_range + 1), num_balls)
                
                # Generate bonus ball if needed
                bonus_numbers = []
                if bonus_balls > 0:
                    bonus_numbers = random.sample(range(1, bonus_range + 1), bonus_balls)
                
                # Create mock divisions data (winners and payouts)
                divisions = {}
                for div in range(1, 4):  # 3 prize divisions
                    divisions[str(div)] = {
                        "winners": random.randint(0, 100),
                        "payout": f"R{random.randint(1000, 1000000):,}"
                    }
                
                # Create lottery result
                result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=f"{i+1000}",
                    draw_date=draw_date,
                    numbers=numbers,
                    bonus_numbers=bonus_numbers,
                    divisions=divisions,
                    jackpot=f"R{random.randint(1000000, 10000000):,}",
                    total_sales=f"R{random.randint(5000000, 20000000):,}"
                )
                
                db.session.add(result)
            
            # Commit after each lottery type
            db.session.commit()
            print(f"Added 10 sample results for {lottery_type}")

def diagnose_pattern_analysis():
    """Test pattern analysis function with direct call"""
    from lottery_analysis import LotteryAnalyzer
    
    with app.app_context():
        print("Diagnosing pattern analysis issue...")
        analyzer = LotteryAnalyzer(db)
        
        # Try each lottery type
        for lottery_type in ['Lotto', 'Powerball', 'Daily Lotto']:
            print(f"\nTesting pattern analysis for {lottery_type}...")
            try:
                result = analyzer.analyze_patterns(lottery_type, days=365)
                if "error" in result:
                    print(f"Error in pattern analysis: {result['error']}")
                else:
                    print(f"Pattern analysis successful for {lottery_type}")
                    
                    # Check for data in each lottery type result
                    if lottery_type in result:
                        if "error" in result[lottery_type]:
                            print(f"  Error for {lottery_type}: {result[lottery_type]['error']}")
                        else:
                            print(f"  Analysis data available for {lottery_type}")
            except Exception as e:
                print(f"Exception in pattern analysis for {lottery_type}: {str(e)}")
    
    print("\nPattern analysis diagnosis complete.")

if __name__ == "__main__":
    # Check if we have data
    has_data = check_lottery_data()
    
    # If no data, import sample data
    if not has_data:
        print("\nNo lottery data found. Importing sample data...")
        import_sample_data()
        print("Sample data import complete\n")
        
        # Check again after import
        has_data = check_lottery_data()
    
    # Diagnose pattern analysis
    if has_data:
        diagnose_pattern_analysis()
    else:
        print("Still no data available. Unable to diagnose pattern analysis.")