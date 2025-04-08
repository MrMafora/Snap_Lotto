import logging
import json
from datetime import datetime
from models import LotteryResult, Screenshot, db

logger = logging.getLogger(__name__)

# Known correct lottery draw results for verification
KNOWN_CORRECT_DRAWS = {
    "Lotto Plus 1": {
        "2530": {  # April 5, 2025 draw
            "numbers": [4, 9, 18, 20, 38, 39],
            "bonus_numbers": [47]
        },
        "2529": {  # April 2, 2025 draw
            "numbers": [5, 16, 27, 32, 36, 44],
            "bonus_numbers": [51]
        },
        "2528": {  # March 29, 2025 draw
            "numbers": [1, 16, 18, 26, 29, 36],
            "bonus_numbers": [24]
        },
        "2527": {  # March 26, 2025 draw
            "numbers": [1, 16, 19, 24, 31, 44],
            "bonus_numbers": [51]
        },
        "2526": {  # March 22, 2025 draw
            "numbers": [16, 25, 32, 39, 45, 52],
            "bonus_numbers": [40]
        },
        "2525": {  # March 19, 2025 draw
            "numbers": [4, 7, 18, 21, 39, 42],
            "bonus_numbers": [27]
        },
        "2524": {  # March 15, 2025 draw
            "numbers": [3, 26, 33, 38, 39, 41],
            "bonus_numbers": [28]
        },
        "2523": {  # March 12, 2025 draw
            "numbers": [10, 15, 17, 27, 29, 47],
            "bonus_numbers": [31]
        },
        "2522": {  # March 8, 2025 draw
            "numbers": [6, 9, 18, 22, 25, 27],
            "bonus_numbers": [14]
        },
        "2521": {  # March 5, 2025 draw
            "numbers": [33, 36, 38, 40, 46, 49],
            "bonus_numbers": [39]
        }
    }
    # Add more known results as they are verified
}

def aggregate_data(extracted_data, lottery_type, source_url):
    """
    Aggregate and store lottery results extracted from OCR.
    
    Priority data fields processed:
    1. Game Type (lottery_type)
    2. Draw ID (draw_number)
    3. Game Date (draw_date)
    4. Winning Numbers (numbers)
    
    Args:
        extracted_data (dict): The data extracted from OCR
        lottery_type (str): Game Type (e.g., 'Lotto', 'Powerball')
        source_url (str): Source URL of the screenshot
        
    Returns:
        list: List of saved LotteryResult records
    """
    try:
        logger.info(f"Aggregating data for {lottery_type}")
        
        # Validate extracted data
        if not extracted_data or 'results' not in extracted_data:
            logger.error(f"Invalid data format from OCR: {extracted_data}")
            return []
        
        # Get the most recent screenshot for this URL
        screenshot = Screenshot.query.filter_by(
            url=source_url,
            processed=False
        ).order_by(Screenshot.timestamp.desc()).first()
        
        saved_results = []
        total_results = len(extracted_data['results'])
        logger.info(f"Found {total_results} results to process for {lottery_type}")
        
        # Process each result in the extracted data
        for i, result in enumerate(extracted_data['results']):
            try:
                # Parse and validate draw date
                draw_date = None
                if 'draw_date' in result:
                    try:
                        draw_date = datetime.fromisoformat(result['draw_date'])
                    except ValueError:
                        # Try to parse date in different formats if ISO format fails
                        date_formats = ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
                        for fmt in date_formats:
                            try:
                                draw_date = datetime.strptime(result['draw_date'], fmt)
                                break
                            except ValueError:
                                continue
                
                if not draw_date:
                    logger.warning(f"Could not parse draw date: {result.get('draw_date', 'Not provided')}, skipping")
                    continue
                
                # Get draw number
                draw_number = result.get('draw_number', None)
                if not draw_number or draw_number == "Unknown":
                    logger.warning(f"Missing draw number for result #{i+1}, trying to generate one from date")
                    # Try to generate a unique identifier based on date
                    draw_number = f"Unknown-{draw_date.strftime('%Y%m%d')}-{i}"
                
                # Check if this result already exists
                existing_result = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=draw_number
                ).first()
                
                # Convert numbers to JSON strings
                numbers = result.get('numbers', [])
                bonus_numbers = result.get('bonus_numbers', []) if 'bonus_numbers' in result else []
                
                # Check against known correct draws for verification
                if lottery_type in KNOWN_CORRECT_DRAWS and draw_number in KNOWN_CORRECT_DRAWS[lottery_type]:
                    known_data = KNOWN_CORRECT_DRAWS[lottery_type][draw_number]
                    logger.info(f"Found known correct draw data for {lottery_type} draw {draw_number}")
                    
                    # Check similarity with known numbers
                    extracted_set = set(numbers)
                    known_set = set(known_data['numbers'])
                    
                    # If there are significant differences, use the known correct numbers
                    if len(extracted_set.intersection(known_set)) < len(known_set) * 0.8:  # Less than 80% match
                        logger.warning(f"OCR numbers {numbers} don't match known numbers {known_data['numbers']} for {lottery_type} draw {draw_number}")
                        logger.info(f"Using verified numbers instead of OCR numbers for {lottery_type} draw {draw_number}")
                        numbers = known_data['numbers']
                        bonus_numbers = known_data['bonus_numbers']
                    else:
                        logger.info(f"OCR numbers match known numbers for {lottery_type} draw {draw_number}")
                
                # Check if numbers are valid (not all zeros and not empty)
                has_valid_numbers = any(num != 0 for num in numbers) if numbers else False
                has_valid_bonus = any(num != 0 for num in bonus_numbers) if bonus_numbers else False
                
                # Skip saving if all numbers are zeros
                if not has_valid_numbers and len(numbers) > 0 and all(num == 0 for num in numbers):
                    logger.warning(f"Skipping result with all zero numbers: {lottery_type}, draw {draw_number}")
                    continue
                
                numbers_json = json.dumps(numbers)
                bonus_numbers_json = json.dumps(bonus_numbers)
                
                if not existing_result:
                    # Create new lottery result only if we have valid numbers
                    if has_valid_numbers:
                        lottery_result = LotteryResult(
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            numbers=numbers_json,
                            bonus_numbers=bonus_numbers_json,
                            source_url=source_url,
                            screenshot_id=screenshot.id if screenshot else None
                        )
                        
                        db.session.add(lottery_result)
                        saved_results.append(lottery_result)
                        logger.info(f"Added new lottery result for {lottery_type}, draw {draw_number}")
                    else:
                        logger.warning(f"Skipping invalid result for {lottery_type}, draw {draw_number}")
                else:
                    # Check if the new data has better information than the existing one
                    existing_numbers = json.loads(existing_result.numbers)
                    existing_bonus = json.loads(existing_result.bonus_numbers or '[]')
                    
                    # Check if existing data is valid
                    existing_has_valid_numbers = any(num != 0 for num in existing_numbers) if existing_numbers else False
                    existing_has_valid_bonus = any(num != 0 for num in existing_bonus) if existing_bonus else False
                    
                    should_update = False
                    
                    # Update only if new data is better than existing
                    if has_valid_numbers and not existing_has_valid_numbers:
                        existing_result.numbers = numbers_json
                        should_update = True
                        
                    # Update if we have valid bonus numbers and existing doesn't
                    if has_valid_bonus and not existing_has_valid_bonus:
                        existing_result.bonus_numbers = bonus_numbers_json
                        should_update = True
                    
                    if should_update:
                        existing_result.source_url = source_url
                        if screenshot:
                            existing_result.screenshot_id = screenshot.id
                        saved_results.append(existing_result)
                        logger.info(f"Updated existing result for {lottery_type}, draw {draw_number} with better data")
                    else:
                        logger.info(f"Result already exists for {lottery_type}, draw {draw_number} with same or better data")
            
            except Exception as e:
                logger.error(f"Error processing result #{i+1}: {str(e)}")
                continue
        
        # Commit all changes to database in batches to avoid memory issues
        db.session.commit()
        
        # Mark screenshot as processed
        if screenshot:
            screenshot.processed = True
            db.session.commit()
        
        logger.info(f"Successfully aggregated {len(saved_results)} out of {total_results} results for {lottery_type}")
        return saved_results
    
    except Exception as e:
        logger.error(f"Error in aggregate_data: {str(e)}")
        db.session.rollback()
        raise

def get_all_results_by_lottery_type(lottery_type):
    """
    Get all lottery results for a specific lottery type.
    
    Args:
        lottery_type (str): Type of lottery
        
    Returns:
        list: List of LotteryResult objects
    """
    return LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).all()

def get_latest_results():
    """
    Get the latest result for each lottery type.
    
    Returns:
        dict: Dictionary mapping lottery types to their latest results
    """
    lottery_types = db.session.query(LotteryResult.lottery_type).distinct().all()
    latest_results = {}
    
    for lt in lottery_types:
        lottery_type = lt[0]
        result = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
        if result:
            latest_results[lottery_type] = result
    
    return latest_results

def export_results_to_json(lottery_type=None, limit=None):
    """
    Export lottery results to JSON format for API integration.
    
    Args:
        lottery_type (str, optional): Filter by lottery type
        limit (int, optional): Limit number of results
        
    Returns:
        str: JSON string of results
    """
    query = LotteryResult.query
    
    if lottery_type:
        query = query.filter_by(lottery_type=lottery_type)
    
    query = query.order_by(LotteryResult.draw_date.desc())
    
    if limit:
        query = query.limit(limit)
    
    results = query.all()
    
    return json.dumps([result.to_dict() for result in results])

def validate_and_correct_known_draws():
    """
    Validate existing database entries against known correct lottery draws.
    This allows us to manually fix any incorrect OCR readings in the database.
    
    Returns:
        int: Number of corrected draws
    """
    corrected_count = 0
    
    for lottery_type, draws in KNOWN_CORRECT_DRAWS.items():
        for draw_number, known_data in draws.items():
            # Find the draw in the database
            existing = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if existing:
                # Check if the data matches
                existing_numbers = json.loads(existing.numbers)
                existing_bonus = json.loads(existing.bonus_numbers or '[]')
                
                # Compare with known correct data
                if existing_numbers != known_data['numbers'] or existing_bonus != known_data['bonus_numbers']:
                    logger.warning(f"Correcting {lottery_type} draw {draw_number}: "
                                 f"from {existing_numbers}+{existing_bonus} "
                                 f"to {known_data['numbers']}+{known_data['bonus_numbers']}")
                    
                    # Update with correct data
                    existing.numbers = json.dumps(known_data['numbers'])
                    existing.bonus_numbers = json.dumps(known_data['bonus_numbers'])
                    db.session.commit()
                    corrected_count += 1
    
    return corrected_count
