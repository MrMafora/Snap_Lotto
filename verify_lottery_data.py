#!/usr/bin/env python3
"""
Verify and update lottery data from the past week using OpenAI API.
This script checks for recent lottery draws that may be missing from our database
and updates the database with official results.
"""

import os
import sys
import json
from datetime import datetime, timedelta
import logging
from sqlalchemy import desc
from openai import OpenAI

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
logger = logging.getLogger('lottery_data_verifier')

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key is missing. Please set the OPENAI_API_KEY environment variable.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

def normalize_lottery_type(lottery_type):
    """
    Normalize lottery type names for consistency.
    Always use 'Lottery' instead of 'Lotto' except in 'Snap Lotto' app name.
    """
    if not lottery_type:
        return None
    
    # Standardize PowerBall/Powerball case variation
    if "power" in lottery_type.lower():
        if "plus" in lottery_type.lower():
            return "Powerball Plus"
        return "Powerball"
    
    # Replace Lotto with Lottery
    if "lotto" in lottery_type.lower() and "snap" not in lottery_type.lower():
        if "plus 1" in lottery_type.lower():
            return "Lottery Plus 1"
        elif "plus 2" in lottery_type.lower():
            return "Lottery Plus 2"
        elif "daily" in lottery_type.lower():
            return "Daily Lottery"
        else:
            return "Lottery"
    
    return lottery_type

def normalize_numbers(numbers):
    """
    Normalize lottery numbers to strings with leading zeros where needed.
    """
    if isinstance(numbers, list):
        return [str(num).zfill(2) for num in numbers]
    return []

def get_latest_draws():
    """
    Get the latest draw for each lottery type from our database.
    """
    lottery_types = [
        "Lottery",
        "Lottery Plus 1",
        "Lottery Plus 2",
        "Powerball",
        "Powerball Plus",
        "Daily Lottery"
    ]
    
    latest_draws = {}
    
    with app.app_context():
        for lottery_type in lottery_types:
            # Try exact match first
            result = LotteryResult.query.filter_by(
                lottery_type=lottery_type
            ).order_by(
                desc(LotteryResult.draw_date)
            ).first()
            
            # If not found, try case-insensitive for PowerBall variations
            if not result and "Power" in lottery_type:
                result = db.session.query(LotteryResult).filter(
                    db.func.lower(LotteryResult.lottery_type) == db.func.lower(lottery_type)
                ).order_by(
                    LotteryResult.draw_date.desc()
                ).first()
            
            # If still not found, try with Lotto instead of Lottery
            if not result and "Lottery" in lottery_type:
                alt_type = lottery_type.replace("Lottery", "Lotto")
                result = LotteryResult.query.filter_by(
                    lottery_type=alt_type
                ).order_by(
                    desc(LotteryResult.draw_date)
                ).first()
            
            if result:
                draw_info = {
                    "draw_number": result.draw_number,
                    "draw_date": result.draw_date,
                    "numbers": json.loads(result.numbers) if result.numbers else [],
                    "bonus_numbers": json.loads(result.bonus_numbers) if result.bonus_numbers else []
                }
                latest_draws[normalize_lottery_type(lottery_type)] = draw_info
    
    return latest_draws

def query_openai_for_latest_draws():
    """
    Use OpenAI to get the latest lottery draw information.
    """
    today = datetime.now()
    one_week_ago = today - timedelta(days=7)
    
    prompt = f"""
    Please provide the most recent official lottery draw results for South Africa from {one_week_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}.
    Include the following lottery types:
    1. Lottery (known as Lotto)
    2. Lottery Plus 1 (known as Lotto Plus 1)
    3. Lottery Plus 2 (known as Lotto Plus 2)
    4. Powerball
    5. Powerball Plus
    6. Daily Lottery (known as Daily Lotto)
    
    For each lottery type, provide:
    - Draw number
    - Draw date (in YYYY-MM-DD format)
    - Winning numbers (in order, with leading zeros for single digits)
    - Bonus/Powerball number(s) if applicable
    
    Please respond in this exact JSON format:
    {{
        "lottery_types": [
            {{
                "lottery_type": "Lottery",
                "draws": [
                    {{
                        "draw_number": "1234",
                        "draw_date": "2025-05-15",
                        "numbers": ["01", "02", "03", "04", "05", "06"],
                        "bonus_numbers": []
                    }}
                ]
            }},
            ... (repeat for each lottery type)
        ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            messages=[
                {"role": "system", "content": "You are a lottery data verification specialist with access to official South African lottery results."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        response_content = response.choices[0].message.content
        logger.info("Successfully received lottery data from OpenAI")
        return json.loads(response_content)
    except Exception as e:
        logger.error(f"Error querying OpenAI: {e}")
        return None

def update_database_with_new_draws(openai_data, latest_db_draws):
    """
    Update database with any new or missing draws from OpenAI data.
    """
    if not openai_data or 'lottery_types' not in openai_data:
        logger.error("Invalid data format from OpenAI")
        return 0
    
    draw_count = 0
    
    with app.app_context():
        for lottery_type_data in openai_data['lottery_types']:
            lottery_type = normalize_lottery_type(lottery_type_data.get('lottery_type'))
            if not lottery_type:
                continue
                
            for draw in lottery_type_data.get('draws', []):
                draw_number = draw.get('draw_number')
                if not draw_number:
                    continue
                
                # Check if this draw already exists in our db
                existing_draw = LotteryResult.query.filter_by(
                    lottery_type=lottery_type, 
                    draw_number=draw_number
                ).first()
                
                # Also check with alternate lottery type spelling
                if not existing_draw and "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    existing_draw = LotteryResult.query.filter_by(
                        lottery_type=alt_type, 
                        draw_number=draw_number
                    ).first()
                
                # Skip if we already have this draw and it's complete
                if existing_draw and existing_draw.numbers:
                    continue
                
                # Parse draw date
                try:
                    draw_date = datetime.strptime(draw.get('draw_date'), '%Y-%m-%d')
                except (ValueError, TypeError):
                    logger.warning(f"Invalid date format for {lottery_type} draw {draw_number}")
                    continue
                
                # Validate numbers are in correct format
                try:
                    numbers = normalize_numbers(draw.get('numbers', []))
                    bonus_numbers = normalize_numbers(draw.get('bonus_numbers', []))
                    
                    # Validate expected number counts
                    if lottery_type == "Daily Lottery" and len(numbers) != 5:
                        logger.warning(f"Invalid number count for {lottery_type}: {len(numbers)} (expected 5)")
                        continue
                    elif "Powerball" in lottery_type and (len(numbers) != 5 or len(bonus_numbers) != 1):
                        logger.warning(f"Invalid number count for {lottery_type}: {len(numbers)} main, {len(bonus_numbers)} bonus")
                        continue
                    elif "Lottery" in lottery_type and len(numbers) != 6:
                        logger.warning(f"Invalid number count for {lottery_type}: {len(numbers)} (expected 6)")
                        continue
                    
                    if existing_draw:
                        # Update existing draw
                        existing_draw.draw_date = draw_date
                        existing_draw.numbers = json.dumps(numbers)
                        existing_draw.bonus_numbers = json.dumps(bonus_numbers) if bonus_numbers else None
                        existing_draw.ocr_provider = "openai"
                        existing_draw.ocr_model = "gpt-4o"
                        existing_draw.ocr_timestamp = datetime.now()
                        logger.info(f"Updated {lottery_type} draw {draw_number}")
                    else:
                        # Create new draw
                        new_draw = LotteryResult(
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            numbers=json.dumps(numbers),
                            bonus_numbers=json.dumps(bonus_numbers) if bonus_numbers else None,
                            ocr_provider="openai",
                            ocr_model="gpt-4o",
                            ocr_timestamp=datetime.now()
                        )
                        db.session.add(new_draw)
                        logger.info(f"Added new {lottery_type} draw {draw_number}")
                    
                    db.session.commit()
                    draw_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {lottery_type} draw {draw_number}: {e}")
                    db.session.rollback()
    
    return draw_count

def compare_and_validate_draws(openai_data, latest_db_draws):
    """
    Compare OpenAI draw data with our database to find discrepancies.
    """
    if not openai_data or 'lottery_types' not in openai_data:
        logger.error("Invalid data format from OpenAI")
        return
    
    discrepancies = []
    
    for lottery_type_data in openai_data['lottery_types']:
        lottery_type = normalize_lottery_type(lottery_type_data.get('lottery_type'))
        if not lottery_type or lottery_type not in latest_db_draws:
            continue
            
        latest_db_draw = latest_db_draws[lottery_type]
        
        # Find the matching draw in OpenAI data
        for draw in lottery_type_data.get('draws', []):
            if draw.get('draw_number') == latest_db_draw['draw_number']:
                openai_numbers = normalize_numbers(draw.get('numbers', []))
                openai_bonus = normalize_numbers(draw.get('bonus_numbers', []))
                
                db_numbers = normalize_numbers(latest_db_draw['numbers'])
                db_bonus = normalize_numbers(latest_db_draw['bonus_numbers'])
                
                if openai_numbers != db_numbers or openai_bonus != db_bonus:
                    discrepancies.append({
                        'lottery_type': lottery_type,
                        'draw_number': draw.get('draw_number'),
                        'db_numbers': db_numbers,
                        'openai_numbers': openai_numbers,
                        'db_bonus': db_bonus,
                        'openai_bonus': openai_bonus
                    })
    
    return discrepancies

def fix_discrepancies(discrepancies):
    """
    Update database with corrected numbers when discrepancies are found.
    """
    if not discrepancies:
        return 0
    
    fixed_count = 0
    
    with app.app_context():
        for discrepancy in discrepancies:
            lottery_type = discrepancy['lottery_type']
            draw_number = discrepancy['draw_number']
            
            # Find the draw in the database
            draw = LotteryResult.query.filter_by(
                lottery_type=lottery_type, 
                draw_number=draw_number
            ).first()
            
            # Also check with alternate lottery type spelling
            if not draw and "Lottery" in lottery_type:
                alt_type = lottery_type.replace("Lottery", "Lotto")
                draw = LotteryResult.query.filter_by(
                    lottery_type=alt_type, 
                    draw_number=draw_number
                ).first()
            
            if not draw:
                logger.warning(f"Could not find {lottery_type} draw {draw_number} to fix discrepancy")
                continue
            
            # Update with OpenAI's numbers (assuming they're more accurate)
            try:
                draw.numbers = json.dumps(discrepancy['openai_numbers'])
                draw.bonus_numbers = json.dumps(discrepancy['openai_bonus']) if discrepancy['openai_bonus'] else None
                draw.ocr_provider = "openai"
                draw.ocr_model = "gpt-4o"
                draw.ocr_timestamp = datetime.now()
                
                db.session.commit()
                logger.info(f"Fixed discrepancy in {lottery_type} draw {draw_number}")
                fixed_count += 1
                
            except Exception as e:
                logger.error(f"Error fixing {lottery_type} draw {draw_number}: {e}")
                db.session.rollback()
    
    return fixed_count

def fix_daily_lottery_number_format():
    """
    Fix any Daily Lottery numbers that are stored as integers instead of strings with leading zeros.
    """
    with app.app_context():
        # Find draws with integer numbers
        daily_draws = LotteryResult.query.filter(
            LotteryResult.lottery_type.in_(['Daily Lottery', 'Daily Lotto'])
        ).all()
        
        fixed_count = 0
        
        for draw in daily_draws:
            try:
                numbers = json.loads(draw.numbers) if draw.numbers else []
                # Check if any number is an integer or missing leading zeros
                needs_fix = any(isinstance(n, int) or (isinstance(n, str) and len(n) == 1) for n in numbers)
                
                if needs_fix:
                    normalized_numbers = normalize_numbers(numbers)
                    draw.numbers = json.dumps(normalized_numbers)
                    db.session.commit()
                    fixed_count += 1
                    logger.info(f"Fixed number format for Daily Lottery draw {draw.draw_number}")
            except Exception as e:
                logger.error(f"Error fixing number format for draw {draw.draw_number}: {e}")
                db.session.rollback()
        
        return fixed_count

def main():
    """
    Main function to verify and update lottery data.
    """
    logger.info("Starting lottery data verification process")
    
    # Step 1: Get the latest draws from our database
    latest_draws = get_latest_draws()
    logger.info(f"Latest draws in database: {', '.join(latest_draws.keys())}")
    
    # Step 2: Query OpenAI for the latest official lottery results
    openai_data = query_openai_for_latest_draws()
    if not openai_data:
        logger.error("Failed to get data from OpenAI. Aborting.")
        return
    
    # Step 3: Compare and find discrepancies
    discrepancies = compare_and_validate_draws(openai_data, latest_draws)
    if discrepancies:
        logger.info(f"Found {len(discrepancies)} discrepancies between database and official results")
        fixed_discrepancies = fix_discrepancies(discrepancies)
        logger.info(f"Fixed {fixed_discrepancies} discrepancies")
    else:
        logger.info("No discrepancies found between database and official results")
    
    # Step 4: Update database with any new draws
    new_draws = update_database_with_new_draws(openai_data, latest_draws)
    logger.info(f"Added/updated {new_draws} new draws")
    
    # Step 5: Fix number format for Daily Lottery
    fixed_formats = fix_daily_lottery_number_format()
    logger.info(f"Fixed number formats for {fixed_formats} Daily Lottery draws")
    
    logger.info("Lottery data verification complete")

if __name__ == "__main__":
    main()