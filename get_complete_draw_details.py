#!/usr/bin/env python3
"""
Get complete details of lottery draws, including divisions and prize amounts.
This script extracts all information we have about the latest lottery draws.
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
logger = logging.getLogger('lottery_details')

def format_currency(amount):
    """Format monetary amount with commas and currency symbol"""
    if not amount:
        return "No data"
    
    try:
        # Convert to float and format
        numeric_amount = float(str(amount).replace(',', '').replace('R', '').strip())
        return f"R{numeric_amount:,.2f}"
    except:
        # Return original if we can't parse it
        return amount

def get_latest_draws(limit=3):
    """
    Get the latest draws for each lottery type with complete details.
    
    Args:
        limit (int): Number of recent draws to fetch per lottery type
        
    Returns:
        dict: Latest draws organized by lottery type
    """
    lottery_types = [
        "Lottery",
        "Lottery Plus 1",
        "Lottery Plus 2",
        "Powerball",
        "Powerball Plus",
        "Daily Lottery"
    ]
    
    # Also check alternate spellings
    alt_lottery_types = [
        "Lotto",
        "Lotto Plus 1",
        "Lotto Plus 2",
        "PowerBall",
        "PowerBall PLUS",
        "Daily Lotto"
    ]
    
    all_lottery_types = lottery_types + alt_lottery_types
    results = {}
    
    with app.app_context():
        for lottery_type in lottery_types:
            # Get latest draws for this type
            draws = db.session.query(LotteryResult).filter(
                LotteryResult.lottery_type.in_([lottery_type, lottery_type.replace("Lottery", "Lotto")])
            ).order_by(
                desc(LotteryResult.draw_date)
            ).limit(limit).all()
            
            if draws:
                type_results = []
                for draw in draws:
                    # Extract divisions data
                    divisions = []
                    if draw.divisions:
                        try:
                            divisions_data = json.loads(draw.divisions)
                            for div_name, div_data in divisions_data.items():
                                if isinstance(div_data, dict):
                                    division = {
                                        "name": div_name,
                                        "winners": div_data.get("winners", "No data"),
                                        "payout": format_currency(div_data.get("payout", "No data")),
                                        "match": div_data.get("match", "No data")
                                    }
                                    divisions.append(division)
                        except (json.JSONDecodeError, AttributeError, TypeError) as e:
                            logger.warning(f"Error parsing divisions for {lottery_type} draw {draw.draw_number}: {e}")
                    
                    # Parse numbers
                    numbers = []
                    bonus_numbers = []
                    try:
                        if draw.numbers:
                            numbers = json.loads(draw.numbers)
                        if draw.bonus_numbers:
                            bonus_numbers = json.loads(draw.bonus_numbers)
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.warning(f"Error parsing numbers for {lottery_type} draw {draw.draw_number}: {e}")
                    
                    # Format date
                    formatted_date = draw.draw_date.strftime("%Y-%m-%d") if draw.draw_date else "Unknown"
                    
                    # Add draw details
                    draw_details = {
                        "draw_id": draw.draw_number,
                        "date": formatted_date,
                        "numbers": numbers,
                        "bonus_numbers": bonus_numbers,
                        "divisions": divisions,
                        "source_url": draw.source_url,
                        "total_winners": sum(int(d.get("winners", 0)) for d in divisions if isinstance(d.get("winners"), (int, str)) and str(d.get("winners")).isdigit())
                    }
                    type_results.append(draw_details)
                
                results[lottery_type] = type_results
    
    return results

def print_draw_details(draws_by_type):
    """
    Print formatted draw details.
    
    Args:
        draws_by_type (dict): Draw details organized by lottery type
    """
    for lottery_type, draws in draws_by_type.items():
        print(f"\n{'=' * 80}")
        print(f"  {lottery_type.upper()} - LATEST DRAW RESULTS")
        print(f"{'=' * 80}")
        
        for i, draw in enumerate(draws):
            draw_date = draw.get("date", "Unknown")
            draw_id = draw.get("draw_id", "Unknown")
            numbers = draw.get("numbers", [])
            bonus_numbers = draw.get("bonus_numbers", [])
            divisions = draw.get("divisions", [])
            total_winners = draw.get("total_winners", 0)
            
            # Convert all number elements to strings if they're not already
            numbers = [str(n) for n in numbers]
            bonus_numbers = [str(n) for n in bonus_numbers]
            
            print(f"\nDraw #{draw_id} - {draw_date}")
            print(f"Numbers: {' '.join(numbers)}")
            
            if bonus_numbers:
                if "powerball" in lottery_type.lower():
                    print(f"Powerball: {' '.join(bonus_numbers)}")
                else:
                    print(f"Bonus: {' '.join(bonus_numbers)}")
            
            print(f"Total Winners: {total_winners}")
            
            if divisions:
                print("\nDivision Details:")
                print(f"{'Division':<10} {'Match':<20} {'Winners':<10} {'Prize'}")
                print("-" * 65)
                
                for div in divisions:
                    div_name = div.get("name", "")
                    div_match = div.get("match", "No data")
                    div_winners = div.get("winners", "No data")
                    div_payout = div.get("payout", "No data")
                    
                    print(f"{div_name:<10} {div_match:<20} {div_winners:<10} {div_payout}")
            else:
                print("\nNo detailed division information available.")
            
            print("-" * 80)

def main():
    """Main function to get and display lottery draw details."""
    try:
        print("Gathering complete lottery draw details...")
        draws = get_latest_draws(limit=2)
        print_draw_details(draws)
        print("\nDraw details retrieved successfully.")
    except Exception as e:
        logger.error(f"Error retrieving draw details: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()