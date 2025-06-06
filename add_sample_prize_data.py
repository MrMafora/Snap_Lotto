"""
Add sample prize division data to demonstrate the functionality
Based on typical South African lottery prize structures
"""
import json
from main import app
from models import db, LotteryResult

def add_lotto_prize_data():
    """Add comprehensive prize division data for LOTTO Draw 2547"""
    with app.app_context():
        lottery_result = LotteryResult.query.filter_by(
            lottery_type='LOTTO',
            draw_number=2547
        ).first()
        
        if lottery_result:
            divisions_data = [
                {
                    "division": 1,
                    "match_type": "6 numbers",
                    "winners": 0,
                    "prize_amount": 0.00,
                    "description": "Match all 6 main numbers"
                },
                {
                    "division": 2, 
                    "match_type": "5 numbers + bonus",
                    "winners": 2,
                    "prize_amount": 89456.70,
                    "description": "Match 5 main numbers plus bonus ball"
                },
                {
                    "division": 3,
                    "match_type": "5 numbers",
                    "winners": 178,
                    "prize_amount": 2645.80,
                    "description": "Match 5 main numbers"
                },
                {
                    "division": 4,
                    "match_type": "4 numbers",
                    "winners": 9876,
                    "prize_amount": 126.50,
                    "description": "Match 4 main numbers"
                },
                {
                    "division": 5,
                    "match_type": "3 numbers + bonus",
                    "winners": 15234,
                    "prize_amount": 56.90,
                    "description": "Match 3 main numbers plus bonus ball"
                },
                {
                    "division": 6,
                    "match_type": "3 numbers",
                    "winners": 234567,
                    "prize_amount": 20.00,
                    "description": "Match 3 main numbers"
                }
            ]
            
            lottery_result.divisions = json.dumps(divisions_data)
            lottery_result.rollover_amount = 15000000.00
            lottery_result.next_jackpot = 18000000.00
            lottery_result.total_pool_size = 25678432.50
            lottery_result.total_sales = 45892156.80
            
            db.session.commit()
            print(f"Added prize data for LOTTO Draw {lottery_result.draw_number}")

def add_powerball_prize_data():
    """Add prize division data for POWERBALL Draw 2547"""
    with app.app_context():
        lottery_result = LotteryResult.query.filter_by(
            lottery_type='POWERBALL',
            draw_number=2547
        ).first()
        
        if lottery_result:
            divisions_data = [
                {
                    "division": 1,
                    "match_type": "5 numbers + Powerball",
                    "winners": 0,
                    "prize_amount": 0.00,
                    "description": "Match all 5 main numbers plus Powerball"
                },
                {
                    "division": 2,
                    "match_type": "5 numbers",
                    "winners": 1,
                    "prize_amount": 156789.40,
                    "description": "Match all 5 main numbers"
                },
                {
                    "division": 3,
                    "match_type": "4 numbers + Powerball",
                    "winners": 23,
                    "prize_amount": 3456.20,
                    "description": "Match 4 main numbers plus Powerball"
                },
                {
                    "division": 4,
                    "match_type": "4 numbers",
                    "winners": 1245,
                    "prize_amount": 234.60,
                    "description": "Match 4 main numbers"
                },
                {
                    "division": 5,
                    "match_type": "3 numbers + Powerball", 
                    "winners": 2567,
                    "prize_amount": 89.30,
                    "description": "Match 3 main numbers plus Powerball"
                },
                {
                    "division": 6,
                    "match_type": "3 numbers",
                    "winners": 45678,
                    "prize_amount": 25.00,
                    "description": "Match 3 main numbers"
                },
                {
                    "division": 7,
                    "match_type": "2 numbers + Powerball",
                    "winners": 67890,
                    "prize_amount": 15.00,
                    "description": "Match 2 main numbers plus Powerball"
                },
                {
                    "division": 8,
                    "match_type": "1 number + Powerball",
                    "winners": 345678,
                    "prize_amount": 10.00,
                    "description": "Match 1 main number plus Powerball"
                },
                {
                    "division": 9,
                    "match_type": "Powerball only",
                    "winners": 567890,
                    "prize_amount": 5.00,
                    "description": "Match Powerball only"
                }
            ]
            
            lottery_result.divisions = json.dumps(divisions_data)
            lottery_result.rollover_amount = 45000000.00
            lottery_result.next_jackpot = 52000000.00
            lottery_result.total_pool_size = 78456321.75
            lottery_result.total_sales = 125678943.20
            
            db.session.commit()
            print(f"Added prize data for POWERBALL Draw {lottery_result.draw_number}")

def add_daily_lotto_prize_data():
    """Add prize division data for DAILY LOTTO Draw 2547"""
    with app.app_context():
        lottery_result = LotteryResult.query.filter_by(
            lottery_type='DAILY LOTTO',
            draw_number=2547
        ).first()
        
        if lottery_result:
            divisions_data = [
                {
                    "division": 1,
                    "match_type": "5 numbers",
                    "winners": 3,
                    "prize_amount": 78934.50,
                    "description": "Match all 5 main numbers"
                },
                {
                    "division": 2,
                    "match_type": "4 numbers",
                    "winners": 234,
                    "prize_amount": 456.80,
                    "description": "Match 4 main numbers"
                },
                {
                    "division": 3,
                    "match_type": "3 numbers",
                    "winners": 5678,
                    "prize_amount": 45.70,
                    "description": "Match 3 main numbers"
                }
            ]
            
            lottery_result.divisions = json.dumps(divisions_data)
            lottery_result.total_pool_size = 1234567.80
            lottery_result.total_sales = 2345678.90
            
            db.session.commit()
            print(f"Added prize data for DAILY LOTTO Draw {lottery_result.draw_number}")

if __name__ == "__main__":
    add_lotto_prize_data()
    add_powerball_prize_data() 
    add_daily_lotto_prize_data()
    print("Prize division data added successfully!")