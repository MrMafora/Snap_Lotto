#!/usr/bin/env python3
"""
Fetch and update lottery data using OpenAI for specific game types and draw IDs.
This script helps manage the draw ID sequence and maintains accurate lottery data.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
import calendar

# Import Flask and database setup
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

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
try:
    from lottery_openai_integration import fetch_lottery_data as fetch_from_openai
except ImportError:
    print("WARNING: OpenAI integration not available, using fallback")
    def fetch_from_openai(lottery_type, draw_id=None):
        """Fallback function if lottery_openai_integration module is not available"""
        return None

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('lottery_data')

# Lottery type configurations
LOTTERY_CONFIG = {
    "Lottery": {
        "latest_id": "2542",  # as of May 17, 2025
        "draw_days": [2, 5],   # Wednesday (2) and Saturday (5)
        "related_games": ["Lottery Plus 1", "Lottery Plus 2"]
    },
    "Lottery Plus 1": {
        "latest_id": "2542",  # as of May 17, 2025
        "draw_days": [2, 5],   # Wednesday (2) and Saturday (5)
        "related_games": ["Lottery", "Lottery Plus 2"]
    },
    "Lottery Plus 2": {
        "latest_id": "2542",  # as of May 17, 2025
        "draw_days": [2, 5],   # Wednesday (2) and Saturday (5)
        "related_games": ["Lottery", "Lottery Plus 1"]
    },
    "Powerball": {
        "latest_id": "1615",  # as of May 14, 2025
        "draw_days": [1, 4],   # Tuesday (1) and Friday (4)
        "related_games": ["Powerball Plus"]
    },
    "Powerball Plus": {
        "latest_id": "1615",  # as of May 14, 2025
        "draw_days": [1, 4],   # Tuesday (1) and Friday (4)
        "related_games": ["Powerball"]
    },
    "Daily Lottery": {
        "latest_id": "2256",  # as of May 16, 2025
        "draw_days": [0, 1, 2, 3, 4, 5, 6],  # Every day of the week
        "related_games": []
    }
}

# URLs for the official lottery websites
LOTTERY_URLS = {
    "Lottery": "https://www.nationallottery.co.za/lotto-history",
    "Lottery Plus 1": "https://www.nationallottery.co.za/lotto-plus-1-history",
    "Lottery Plus 2": "https://www.nationallottery.co.za/lotto-plus-2-history",
    "Powerball": "https://www.nationallottery.co.za/powerball-history",
    "Powerball Plus": "https://www.nationallottery.co.za/powerball-plus-history",
    "Daily Lottery": "https://www.nationallottery.co.za/daily-lotto-history"
}

def get_next_draw_id(lottery_type):
    """
    Get the next draw ID for a specific lottery type.
    
    Args:
        lottery_type (str): The type of lottery
        
    Returns:
        str: The next draw ID
    """
    with app.app_context():
        # Find the latest draw ID in the database
        latest_draw = LotteryResult.query.filter_by(
            lottery_type=lottery_type
        ).order_by(db.desc(LotteryResult.draw_date)).first()
        
        if latest_draw:
            try:
                # Increment the draw ID by 1
                return str(int(latest_draw.draw_number) + 1)
            except ValueError:
                # If the draw ID is not a number, use the config default
                latest_id = LOTTERY_CONFIG[lottery_type]["latest_id"]
                return str(int(latest_id) + 1)
        else:
            # If no draws found, use the config default
            latest_id = LOTTERY_CONFIG[lottery_type]["latest_id"]
            return str(int(latest_id) + 1)

def get_next_draw_date(lottery_type, reference_date=None):
    """
    Calculate the next draw date for a specific lottery type.
    
    Args:
        lottery_type (str): The type of lottery
        reference_date (datetime, optional): Reference date to calculate from
        
    Returns:
        datetime: The next draw date
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    draw_days = LOTTERY_CONFIG[lottery_type]["draw_days"]
    
    # Convert Python's weekday (0 = Monday) to our format (0 = Sunday)
    current_day = (reference_date.weekday() + 1) % 7
    
    # Find the next draw day
    days_ahead = 7
    for day in draw_days:
        days_until = (day - current_day) % 7
        if days_until < days_ahead and days_until > 0:
            days_ahead = days_until
    
    # If today is a draw day and we're checking before the draw time
    if current_day in draw_days and reference_date.hour < 21:  # Assuming draws happen at 9 PM
        days_ahead = 0
    
    next_date = reference_date + timedelta(days=days_ahead)
    # Set time to 9 PM
    next_date = next_date.replace(hour=21, minute=0, second=0, microsecond=0)
    
    return next_date

def fetch_lottery_data_using_openai(lottery_type, draw_id=None, draw_date=None):
    """
    Use OpenAI to fetch lottery data for a specific lottery type and draw ID or date.
    
    Args:
        lottery_type (str): Type of lottery
        draw_id (str, optional): Specific draw ID to fetch
        draw_date (datetime, optional): Specific draw date to fetch
        
    Returns:
        dict: Lottery draw information
    """
    # Use our dedicated lottery OpenAI integration
    return fetch_from_openai(lottery_type, draw_id)

def save_lottery_data(lottery_type, data):
    """
    Save lottery data to the database.
    
    Args:
        lottery_type (str): Type of lottery
        data (dict): Lottery draw data
        
    Returns:
        LotteryResult: The saved lottery result object
    """
    with app.app_context():
        # Check if this draw already exists
        existing = LotteryResult.query.filter_by(
            lottery_type=lottery_type,
            draw_number=data["draw_number"]
        ).first()
        
        if existing:
            logger.info(f"{lottery_type} draw #{data['draw_number']} already exists in database.")
            return existing
        
        # Format the draw date
        if isinstance(data["draw_date"], str):
            try:
                draw_date = datetime.strptime(data["draw_date"], "%Y-%m-%d")
            except ValueError:
                logger.error(f"Could not parse draw date: {data['draw_date']}")
                draw_date = datetime.now()
        else:
            draw_date = data["draw_date"]
        
        # Create a new lottery result
        result = LotteryResult(
            lottery_type=lottery_type,
            draw_number=data["draw_number"],
            draw_date=draw_date,
            numbers=data["numbers"],
            bonus_numbers=data.get("bonus_numbers", []),
            divisions=data.get("divisions", {}),
            ocr_provider="openai",
            ocr_model="gpt-4o",
            source_url=LOTTERY_URLS.get(lottery_type, "")
        )
        
        db.session.add(result)
        db.session.commit()
        
        logger.info(f"Saved {lottery_type} draw #{data['draw_number']} to database.")
        return result

def get_lottery_result(lottery_type, draw_id=None):
    """
    Get lottery result from database or fetch from OpenAI if not found.
    
    Args:
        lottery_type (str): Type of lottery
        draw_id (str, optional): Specific draw ID to get
        
    Returns:
        LotteryResult: The lottery result
    """
    with app.app_context():
        result = None
        
        # Try to get from database first
        if draw_id:
            result = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=draw_id
            ).first()
        else:
            # Get the most recent draw
            result = LotteryResult.query.filter_by(
                lottery_type=lottery_type
            ).order_by(db.desc(LotteryResult.draw_date)).first()
        
        # If not found, try to fetch from OpenAI
        if not result:
            data = fetch_lottery_data_using_openai(lottery_type, draw_id)
            if data:
                result = save_lottery_data(lottery_type, data)
        
        return result

def predict_next_draws(days_ahead=7):
    """
    Predict the next draws for all lottery types for a specific number of days ahead.
    
    Args:
        days_ahead (int): Number of days to predict ahead
        
    Returns:
        dict: Predicted draws by lottery type and date
    """
    predictions = {}
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days_ahead)
    
    for lottery_type, config in LOTTERY_CONFIG.items():
        predictions[lottery_type] = []
        
        # Get the latest draw from database
        with app.app_context():
            latest_draw = LotteryResult.query.filter_by(
                lottery_type=lottery_type
            ).order_by(db.desc(LotteryResult.draw_date)).first()
        
        current_id = latest_draw.draw_number if latest_draw else config["latest_id"]
        
        # Calculate the next draw date from the latest draw
        if latest_draw:
            next_date = get_next_draw_date(lottery_type, latest_draw.draw_date)
        else:
            next_date = get_next_draw_date(lottery_type)
        
        # Predict draws within the date range
        while next_date <= end_date:
            current_id = str(int(current_id) + 1)
            
            predictions[lottery_type].append({
                "draw_number": current_id,
                "draw_date": next_date.strftime("%Y-%m-%d"),
                "day_of_week": calendar.day_name[next_date.weekday()]
            })
            
            next_date = get_next_draw_date(lottery_type, next_date)
    
    return predictions

def update_all_lottery_results():
    """
    Update all lottery results with the latest draws.
    
    Returns:
        dict: Results of the update operation
    """
    results = {}
    
    for lottery_type in LOTTERY_CONFIG.keys():
        try:
            # Get the next draw ID
            next_id = get_next_draw_id(lottery_type)
            
            # Fetch the data using OpenAI
            data = fetch_lottery_data_using_openai(lottery_type, next_id)
            
            if data:
                # Save the data to database
                result = save_lottery_data(lottery_type, data)
                results[lottery_type] = {
                    "success": True,
                    "draw_number": data["draw_number"],
                    "draw_date": data["draw_date"]
                }
            else:
                results[lottery_type] = {
                    "success": False,
                    "error": "Could not fetch data from OpenAI"
                }
        except Exception as e:
            results[lottery_type] = {
                "success": False,
                "error": str(e)
            }
    
    return results

def main():
    """Main function to demonstrate the module functionality."""
    try:
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "predict":
                # Predict future draws
                days = 7
                if len(sys.argv) > 2:
                    try:
                        days = int(sys.argv[2])
                    except ValueError:
                        pass
                
                predictions = predict_next_draws(days)
                print(f"Predicted draws for the next {days} days:")
                for lottery_type, draws in predictions.items():
                    print(f"\n{lottery_type}:")
                    for draw in draws:
                        print(f"  Draw #{draw['draw_number']} on {draw['draw_date']} ({draw['day_of_week']})")
            
            elif command == "fetch":
                # Fetch specific lottery result
                if len(sys.argv) < 3:
                    print("Usage: python fetch_lottery_data.py fetch [lottery_type] [draw_id]")
                    return
                
                lottery_type = sys.argv[2]
                draw_id = None
                if len(sys.argv) > 3:
                    draw_id = sys.argv[3]
                
                result = get_lottery_result(lottery_type, draw_id)
                if result:
                    print(f"\n{result.lottery_type} Draw #{result.draw_number} on {result.draw_date.strftime('%Y-%m-%d')}:")
                    print(f"Numbers: {', '.join(result.numbers)}")
                    if result.bonus_numbers:
                        print(f"Bonus: {', '.join(result.bonus_numbers)}")
                    if result.divisions:
                        print("\nDivision Information:")
                        for div, info in result.divisions.items():
                            print(f"  {div}: {info['match']} - {info['winners']} winners, {info['payout']}")
                else:
                    print(f"Could not find or fetch {lottery_type} draw #{draw_id}")
            
            elif command == "update":
                # Update all lottery results
                results = update_all_lottery_results()
                print("Updated lottery results:")
                for lottery_type, result in results.items():
                    if result["success"]:
                        print(f"  {lottery_type}: Draw #{result['draw_number']} on {result['draw_date']}")
                    else:
                        print(f"  {lottery_type}: Error - {result['error']}")
        
        else:
            # Default: show the next predicted draw for each lottery type
            print("Next predicted draws:")
            for lottery_type in LOTTERY_CONFIG.keys():
                next_id = get_next_draw_id(lottery_type)
                next_date = get_next_draw_date(lottery_type)
                print(f"  {lottery_type}: Draw #{next_id} on {next_date.strftime('%Y-%m-%d')} ({calendar.day_name[next_date.weekday()]})")
    
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()