import logging
import json
from datetime import datetime
from db_models import LotteryResult, Screenshot
from app import db

logger = logging.getLogger(__name__)

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
        
        # Process each result in the extracted data
        for result in extracted_data['results']:
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
                    logger.warning(f"Could not parse draw date: {result.get('draw_date', 'Not provided')}")
                    continue
                
                # Get draw number
                draw_number = result.get('draw_number', None)
                
                # Check if this result already exists
                existing_result = None
                if draw_number:
                    existing_result = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                
                # Convert numbers to JSON strings
                numbers = result.get('numbers', [])
                bonus_numbers = result.get('bonus_numbers', []) if 'bonus_numbers' in result else []
                
                # Check if numbers are not all zeros
                has_valid_numbers = any(num != 0 for num in numbers)
                has_valid_bonus = any(num != 0 for num in bonus_numbers)
                
                numbers_json = json.dumps(numbers)
                bonus_numbers_json = json.dumps(bonus_numbers)
                
                if not existing_result:
                    # Create new lottery result
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
                    # Check if the new data has better information than the existing one
                    existing_numbers = json.loads(existing_result.numbers)
                    existing_bonus = json.loads(existing_result.bonus_numbers or '[]')
                    
                    existing_has_zeros = any(num == 0 for num in existing_numbers)
                    existing_bonus_has_zeros = any(num == 0 for num in existing_bonus)
                    
                    should_update = False
                    
                    # Update if we have valid numbers and existing data has zeros
                    if has_valid_numbers and existing_has_zeros:
                        existing_result.numbers = numbers_json
                        should_update = True
                        
                    # Update if we have valid bonus numbers and existing data has zeros
                    if has_valid_bonus and existing_bonus_has_zeros:
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
                logger.error(f"Error processing result: {str(e)}")
                continue
        
        # Commit all changes to database
        db.session.commit()
        
        # Mark screenshot as processed
        if screenshot:
            screenshot.processed = True
            db.session.commit()
        
        logger.info(f"Successfully aggregated {len(saved_results)} results for {lottery_type}")
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
