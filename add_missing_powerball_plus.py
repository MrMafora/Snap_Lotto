#!/usr/bin/env python3
"""
Script to add the missing Powerball Plus 1615 results and demonstrate the draw ID prediction system.
"""

import os
import sys
import json
from datetime import datetime
import logging

# Set up database access
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('lottery_data')

# Set up the app and database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Import required modules
from models import LotteryResult

# The known Powerball Plus 1615 data as seen from official sources
POWERBALL_PLUS_1615_DATA = {
    "draw_number": "1615",
    "draw_date": "2025-05-14",
    "numbers": ["10", "11", "25", "26", "44"],
    "bonus_numbers": ["09"],
    "divisions": {
        "Division 1": {"match": "5 + Powerball", "winners": 0, "payout": "R0.00"},
        "Division 2": {"match": "5 correct numbers", "winners": 1, "payout": "R350,371.90"},
        "Division 3": {"match": "4 + Powerball", "winners": 11, "payout": "R17,974.90"},
        "Division 4": {"match": "4 correct numbers", "winners": 229, "payout": "R948.70"},
        "Division 5": {"match": "3 + Powerball", "winners": 467, "payout": "R441.20"},
        "Division 6": {"match": "3 correct numbers", "winners": 10145, "payout": "R19.80"},
        "Division 7": {"match": "2 + Powerball", "winners": 6793, "payout": "R19.70"},
        "Division 8": {"match": "1 + Powerball", "winners": 32897, "payout": "R10.00"},
        "Division 9": {"match": "Powerball only", "winners": 51016, "payout": "R5.00"}
    }
}

def add_powerball_plus_data():
    """Add the missing Powerball Plus 1615 data to the database."""
    with app.app_context():
        # Check if Powerball Plus 1615 already exists
        existing = LotteryResult.query.filter_by(
            lottery_type="Powerball Plus",
            draw_number="1615"
        ).first()
        
        if existing:
            print(f"Powerball Plus draw #1615 already exists in database (ID: {existing.id})")
            return existing
        
        # Format the draw date
        draw_date = datetime.strptime(POWERBALL_PLUS_1615_DATA["draw_date"], "%Y-%m-%d")
        
        # Create a new lottery result
        result = LotteryResult(
            lottery_type="Powerball Plus",
            draw_number=POWERBALL_PLUS_1615_DATA["draw_number"],
            draw_date=draw_date,
            numbers=POWERBALL_PLUS_1615_DATA["numbers"],
            bonus_numbers=POWERBALL_PLUS_1615_DATA["bonus_numbers"],
            divisions=POWERBALL_PLUS_1615_DATA["divisions"],
            ocr_provider="direct",
            ocr_model="manual_entry",
            source_url="https://www.nationallottery.co.za/powerball-plus-history"
        )
        
        # Add to database
        db.session.add(result)
        db.session.commit()
        
        print(f"Added Powerball Plus draw #1615 to database (ID: {result.id})")
        return result

def predict_next_draws():
    """Predict the next draw IDs and dates for each lottery type."""
    # Draw days mapping (0=Monday, 6=Sunday)
    draw_days = {
        "Lottery": [2, 5],         # Wednesday (2) and Saturday (5)
        "Lottery Plus 1": [2, 5],   # Wednesday (2) and Saturday (5)
        "Lottery Plus 2": [2, 5],   # Wednesday (2) and Saturday (5)
        "Powerball": [1, 4],        # Tuesday (1) and Friday (4) 
        "Powerball Plus": [1, 4],   # Tuesday (1) and Friday (4)
        "Daily Lottery": [0, 1, 2, 3, 4, 5, 6]  # Every day
    }
    
    # Current latest draw IDs
    latest_draw_ids = {
        "Lottery": "2542",
        "Lottery Plus 1": "2542",
        "Lottery Plus 2": "2542",
        "Powerball": "1615",
        "Powerball Plus": "1615",
        "Daily Lottery": "2256"
    }
    
    # Next draw IDs
    next_draw_ids = {
        "Lottery": str(int(latest_draw_ids["Lottery"]) + 1),
        "Lottery Plus 1": str(int(latest_draw_ids["Lottery Plus 1"]) + 1),
        "Lottery Plus 2": str(int(latest_draw_ids["Lottery Plus 2"]) + 1),
        "Powerball": str(int(latest_draw_ids["Powerball"]) + 1),
        "Powerball Plus": str(int(latest_draw_ids["Powerball Plus"]) + 1),
        "Daily Lottery": str(int(latest_draw_ids["Daily Lottery"]) + 1)
    }
    
    print("\nPredictions for upcoming lottery draws:")
    print("-" * 60)
    
    for lottery_type, next_id in next_draw_ids.items():
        # Reference days for printing
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        draw_day_names = [day_names[d] for d in draw_days[lottery_type]]
        
        # Print prediction
        print(f"{lottery_type}: Next draw will be #{next_id} (Draw days: {', '.join(draw_day_names)})")

def main():
    """Main function to demonstrate the utility."""
    try:
        # Add Powerball Plus 1615 data if missing
        add_powerball_plus_data()
        
        # Show the next draw IDs
        predict_next_draws()
        
        # Display database status
        with app.app_context():
            for lottery_type in ["Lottery", "Lottery Plus 1", "Lottery Plus 2", "Powerball", "Powerball Plus", "Daily Lottery"]:
                latest = LotteryResult.query.filter_by(
                    lottery_type=lottery_type
                ).order_by(db.desc(LotteryResult.draw_date)).first()
                
                if latest:
                    print(f"\n{lottery_type} Latest Draw: #{latest.draw_number} on {latest.draw_date.strftime('%Y-%m-%d')}")
                    print(f"  Numbers: {', '.join(latest.numbers)}")
                    if latest.bonus_numbers:
                        print(f"  Bonus: {', '.join(latest.bonus_numbers)}")
                else:
                    print(f"\n{lottery_type}: No draws found in database")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()