import logging
import json
import re
from datetime import datetime
from models import LotteryResult, Screenshot, db

logger = logging.getLogger(__name__)

def has_better_formatted_prizes(new_divisions, existing_divisions):
    """
    Check if the new divisions data has better formatted prize amounts than existing data.
    Better formatted means having commas and/or decimal places in the amount.
    
    Args:
        new_divisions (dict): Newly extracted divisions data
        existing_divisions (dict): Existing divisions data from database
        
    Returns:
        bool: True if new divisions have better formatted prize amounts
    """
    if not new_divisions or not existing_divisions:
        return False
        
    for division, data in new_divisions.items():
        if division in existing_divisions:
            new_prize = data.get('prize', '')
            existing_prize = existing_divisions[division].get('prize', '')
            
            # Check if new prize has commas or decimal points that existing doesn't
            new_has_commas = ',' in new_prize
            existing_has_commas = ',' in existing_prize
            
            new_has_decimals = '.' in new_prize
            existing_has_decimals = '.' in existing_prize
            
            # Check if new prize has "R" prefix but existing doesn't
            new_has_currency = 'R' in new_prize
            existing_has_currency = 'R' in existing_prize
            
            # New prize is better if it has formatting that existing doesn't
            if (new_has_commas and not existing_has_commas) or \
               (new_has_decimals and not existing_has_decimals) or \
               (new_has_currency and not existing_has_currency):
                return True
                
            # Check if existing prize is just a number without formatting
            if existing_prize and re.match(r'^[0-9]+$', existing_prize.replace('R', '').strip()):
                if new_has_commas or new_has_decimals:
                    return True
    
    return False

# Known correct lottery draw results for verification
KNOWN_CORRECT_DRAWS = {
    "Lotto": {
        "2532": {  # April 12, 2025 draw
            "numbers": [3, 9, 16, 17, 31, 48],
            "bonus_numbers": [36],
            "divisions": {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "SIX CORRECT NUMBERS"
                },
                "Division 2": {
                    "winners": "1",
                    "prize": "R153,276.30",
                    "match": "FIVE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 3": {
                    "winners": "41",
                    "prize": "R4,847.00",
                    "match": "FIVE CORRECT NUMBERS"
                },
                "Division 4": {
                    "winners": "103",
                    "prize": "R2,018.40",
                    "match": "FOUR CORRECT NUMBERS + BONUS BALL"
                },
                "Division 5": {
                    "winners": "2562",
                    "prize": "R142.80",
                    "match": "FOUR CORRECT NUMBERS"
                },
                "Division 6": {
                    "winners": "3142",
                    "prize": "R97.50",
                    "match": "THREE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 7": {
                    "winners": "47453",
                    "prize": "R50.00",
                    "match": "THREE CORRECT NUMBERS"
                },
                "Division 8": {
                    "winners": "32184",
                    "prize": "R20.00",
                    "match": "TWO CORRECT NUMBERS + BONUS BALL"
                }
            }
        },
        "2530": {  # April 5, 2025 draw
            "numbers": [39, 42, 11, 7, 37, 34],
            "bonus_numbers": [44],
            "divisions": {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "SIX CORRECT NUMBERS"
                },
                "Division 2": {
                    "winners": "1",
                    "prize": "R99,273.10",
                    "match": "FIVE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 3": {
                    "winners": "38",
                    "prize": "R4,543.40",
                    "match": "FIVE CORRECT NUMBERS"
                },
                "Division 4": {
                    "winners": "96",
                    "prize": "R2,248.00",
                    "match": "FOUR CORRECT NUMBERS + BONUS BALL"
                },
                "Division 5": {
                    "winners": "2498",
                    "prize": "R145.10",
                    "match": "FOUR CORRECT NUMBERS"
                },
                "Division 6": {
                    "winners": "3042",
                    "prize": "R103.60",
                    "match": "THREE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 7": {
                    "winners": "46289",
                    "prize": "R50.00",
                    "match": "THREE CORRECT NUMBERS"
                },
                "Division 8": {
                    "winners": "33113",
                    "prize": "R20.00",
                    "match": "TWO CORRECT NUMBERS + BONUS BALL"
                }
            }
        }
    },
    "Lotto Plus 1": {
        "2530": {  # April 5, 2025 draw
            "numbers": [4, 9, 18, 20, 38, 39],
            "bonus_numbers": [47],
            "divisions": {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00"
                },
                "Division 2": {
                    "winners": "4",
                    "prize": "R31,115.10"
                },
                "Division 3": {
                    "winners": "91",
                    "prize": "R2,230.50"
                },
                "Division 4": {
                    "winners": "244",
                    "prize": "R1,042.40"
                },
                "Division 5": {
                    "winners": "3483",
                    "prize": "R121.90"
                },
                "Division 6": {
                    "winners": "4224",
                    "prize": "R87.30"
                },
                "Division 7": {
                    "winners": "42950",
                    "prize": "R50.00"
                },
                "Division 8": {
                    "winners": "30532",
                    "prize": "R20.00"
                }
            }
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

def normalize_draw_number(draw_number):
    """
    Normalize the draw number to a standard format by removing prefixes and extra text.
    
    Args:
        draw_number (str): The draw number as extracted from OCR
        
    Returns:
        str: Normalized draw number
    """
    if not draw_number:
        return None
        
    draw_number = str(draw_number).strip()
    
    # Convert to uppercase for consistent matching
    upper_draw = draw_number.upper()
    
    # Remove "DRAW" keyword and other prefixes
    prefixes_to_remove = [
        "LOTTO DRAW", "LOTTO PLUS 1 DRAW", "LOTTO PLUS 2 DRAW",
        "POWERBALL DRAW", "POWERBALL PLUS DRAW", "DAILY LOTTO DRAW",
        "DRAW", "DRAW NUMBER", "DRAW NO", "DRAW NO.", "DRAW #"
    ]
    
    for prefix in prefixes_to_remove:
        if prefix in upper_draw:
            # Replace the prefix with an empty string
            upper_draw = upper_draw.replace(prefix, "")
    
    # Remove any leading/trailing whitespace after replacements
    upper_draw = upper_draw.strip()
    
    # Extract the numeric part if mixed with text
    import re
    numeric_match = re.search(r'(\d+)', upper_draw)
    if numeric_match:
        draw_number = numeric_match.group(1)
    else:
        # If no numeric part found, use the cleaned string
        draw_number = upper_draw
        
    return draw_number

def normalize_lottery_type(lottery_type):
    """
    Normalize lottery type names by removing "Results" suffix and standardizing format.
    This allows merging data from both history and results pages.
    
    Args:
        lottery_type (str): The lottery type name
        
    Returns:
        str: Normalized lottery type
    """
    if not lottery_type:
        return lottery_type
    
    # Remove "Results" suffix if present
    if lottery_type.endswith(" Results"):
        lottery_type = lottery_type[:-8]  # Remove " Results" suffix
    
    # Handle common variations
    normalized_map = {
        "lotto plus 1": "Lotto Plus 1",
        "lotto plus one": "Lotto Plus 1",
        "lotto plus1": "Lotto Plus 1", 
        "lottoplus1": "Lotto Plus 1",
        "lotto plus 2": "Lotto Plus 2",
        "lotto plus two": "Lotto Plus 2",
        "lotto plus2": "Lotto Plus 2",
        "lottoplus2": "Lotto Plus 2",
        "powerball plus": "Powerball Plus",
        "power ball plus": "Powerball Plus",
        "powerball+": "Powerball Plus",
        "powerballplus": "Powerball Plus",
        "daily lotto": "Daily Lotto",
        "dailylotto": "Daily Lotto",
        "daily-lotto": "Daily Lotto",
        "lotto": "Lotto",
        "powerball": "Powerball"
    }
    
    # Look for known variations and standardize
    lookup_key = lottery_type.lower().strip()
    if lookup_key in normalized_map:
        return normalized_map[lookup_key]
    
    return lottery_type

def aggregate_data(extracted_data, lottery_type, source_url):
    """
    Aggregate and store lottery results extracted from OCR.
    
    Priority data fields processed:
    1. Game Type (lottery_type)
    2. Draw ID (draw_number)
    3. Game Date (draw_date)
    4. Winning Numbers (numbers)
    
    OCR provider information is also stored:
    - ocr_provider: Name of the AI OCR provider (e.g., 'anthropic')
    - ocr_model: Specific model used for OCR (e.g., 'claude-3-5-sonnet-20241022')
    - ocr_timestamp: When the OCR processing was performed
    
    Args:
        extracted_data (dict): The data extracted from OCR
        lottery_type (str): Game Type (e.g., 'Lotto', 'Powerball')
        source_url (str): Source URL of the screenshot
        
    Returns:
        list: List of saved LotteryResult records
    """
    try:
        logger.info(f"Aggregating data for {lottery_type}")
        
        # Normalize lottery type to remove "Results" suffix
        normalized_lottery_type = normalize_lottery_type(lottery_type)
        
        # Use normalized lottery type for display in logs but keep original for processing
        logger.info(f"Normalized lottery type from '{lottery_type}' to '{normalized_lottery_type}'")
        
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
        logger.info(f"Found {total_results} results to process for {normalized_lottery_type}")
        
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
                
                # Get and normalize draw number
                raw_draw_number = result.get('draw_number', None)
                if not raw_draw_number or raw_draw_number == "Unknown":
                    logger.warning(f"Missing draw number for result #{i+1}, trying to generate one from date")
                    # Try to generate a unique identifier based on date
                    draw_number = f"Unknown-{draw_date.strftime('%Y%m%d')}-{i}"
                else:
                    # Normalize the draw number to handle prefixes like "LOTTO DRAW 2530"
                    draw_number = normalize_draw_number(raw_draw_number)
                    if raw_draw_number != draw_number:
                        logger.info(f"Normalized draw number from '{raw_draw_number}' to '{draw_number}'")
                
                # First, check if this result already exists with the exact lottery type and draw number
                existing_result = LotteryResult.query.filter_by(
                    lottery_type=normalized_lottery_type,
                    draw_number=draw_number
                ).first()
                
                # If not found, check with a broader search using LIKE for variations in prefixes
                if not existing_result and draw_number and not str(draw_number).startswith("Unknown"):
                    # Try find with just the numeric part of the draw number
                    all_matching_results = LotteryResult.query.filter(
                        LotteryResult.lottery_type.like(f"{normalized_lottery_type}%"),
                        LotteryResult.draw_number.like(f"%{draw_number}%")
                    ).all()
                    
                    if all_matching_results:
                        # Find the best match - prioritize those with division data
                        for match in all_matching_results:
                            if match.divisions:  # Prefer results with division data
                                existing_result = match
                                break
                        
                        # If no match with divisions, use the first one
                        if not existing_result and all_matching_results:
                            existing_result = all_matching_results[0]
                            
                        if existing_result:
                            logger.info(f"Found similar result for {normalized_lottery_type}, draw {draw_number}")
                
                # Convert numbers to JSON strings
                numbers = result.get('numbers', [])
                bonus_numbers = result.get('bonus_numbers', []) if 'bonus_numbers' in result else []
                divisions_data = result.get('divisions', {})
                
                # Check against known correct draws for verification
                normalized_draw = str(draw_number) if draw_number else ""
                if lottery_type in KNOWN_CORRECT_DRAWS and normalized_draw and normalized_draw in KNOWN_CORRECT_DRAWS[lottery_type]:
                    known_data = KNOWN_CORRECT_DRAWS[lottery_type][normalized_draw]
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
                has_divisions = bool(divisions_data)
                
                # Skip saving if all numbers are zeros
                if not has_valid_numbers and len(numbers) > 0 and all(num == 0 for num in numbers):
                    logger.warning(f"Skipping result with all zero numbers: {lottery_type}, draw {draw_number}")
                    continue
                
                numbers_json = json.dumps(numbers)
                bonus_numbers_json = json.dumps(bonus_numbers)
                divisions_json = json.dumps(divisions_data) if divisions_data else None
                
                if has_divisions:
                    logger.info(f"Extracted {len(divisions_data)} divisions for {lottery_type}, draw {draw_number}")
                
                if not existing_result:
                    # Create new lottery result only if we have valid numbers
                    if has_valid_numbers:
                        # Extract OCR provider information if available
                        ocr_provider = extracted_data.get('ocr_provider', None)
                        ocr_model = extracted_data.get('ocr_model', None)
                        ocr_timestamp = None
                        
                        # Parse OCR timestamp if available
                        if 'ocr_timestamp' in extracted_data:
                            try:
                                ocr_timestamp = datetime.fromisoformat(extracted_data['ocr_timestamp'])
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid OCR timestamp format: {extracted_data.get('ocr_timestamp')}")
                        
                        lottery_result = LotteryResult(
                            lottery_type=normalized_lottery_type,  # Use normalized type to ensure consistency
                            draw_number=draw_number,
                            draw_date=draw_date,
                            numbers=numbers_json,
                            bonus_numbers=bonus_numbers_json,
                            divisions=divisions_json,
                            source_url=source_url,
                            screenshot_id=screenshot.id if screenshot else None,
                            ocr_provider=ocr_provider,
                            ocr_model=ocr_model,
                            ocr_timestamp=ocr_timestamp
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
                    
                    # Get existing divisions data
                    existing_divisions = {}
                    if hasattr(existing_result, 'divisions') and existing_result.divisions:
                        try:
                            existing_divisions = json.loads(existing_result.divisions)
                        except (json.JSONDecodeError, TypeError):
                            existing_divisions = {}
                    
                    # Check if existing data is valid
                    existing_has_valid_numbers = any(num != 0 for num in existing_numbers) if existing_numbers else False
                    existing_has_valid_bonus = any(num != 0 for num in existing_bonus) if existing_bonus else False
                    existing_has_divisions = bool(existing_divisions)
                    
                    should_update = False
                    
                    # Update only if new data is better than existing
                    if has_valid_numbers and not existing_has_valid_numbers:
                        existing_result.numbers = numbers_json
                        should_update = True
                        
                    # Update if we have valid bonus numbers and existing doesn't
                    if has_valid_bonus and not existing_has_valid_bonus:
                        existing_result.bonus_numbers = bonus_numbers_json
                        should_update = True
                    
                    # Update if we have divisions data and existing doesn't, or if we have more divisions
                    # or if we have more complete prize amounts (with formatting)
                    if has_divisions and (
                        not existing_has_divisions or 
                        len(divisions_data) > len(existing_divisions) or 
                        has_better_formatted_prizes(divisions_data, existing_divisions)
                    ):
                        if hasattr(existing_result, 'divisions'):
                            existing_result.divisions = divisions_json
                            should_update = True
                            logger.info(f"Updated divisions data for {lottery_type}, draw {draw_number}")
                    
                    if should_update:
                        # Update OCR provider information if available
                        if 'ocr_provider' in extracted_data and not existing_result.ocr_provider:
                            existing_result.ocr_provider = extracted_data.get('ocr_provider')
                            
                        if 'ocr_model' in extracted_data and not existing_result.ocr_model:
                            existing_result.ocr_model = extracted_data.get('ocr_model')
                            
                        # Parse and update OCR timestamp if available
                        if 'ocr_timestamp' in extracted_data and not existing_result.ocr_timestamp:
                            try:
                                existing_result.ocr_timestamp = datetime.fromisoformat(extracted_data['ocr_timestamp'])
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid OCR timestamp format: {extracted_data.get('ocr_timestamp')}")
                        
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
    # Get normalized version of the lottery type
    normalized_type = normalize_lottery_type(lottery_type)
    
    # Find all variants of this lottery type in the database
    lottery_type_variants = db.session.query(LotteryResult.lottery_type).distinct().all()
    matching_types = []
    
    for lt in lottery_type_variants:
        lt_name = lt[0]
        if normalize_lottery_type(lt_name) == normalized_type:
            matching_types.append(lt_name)
    
    # If we found matching variants, query using all of them
    if matching_types:
        return LotteryResult.query.filter(
            LotteryResult.lottery_type.in_(matching_types)
        ).order_by(LotteryResult.draw_date.desc()).all()
    else:
        # Fallback to the original search if no variants found
        return LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).all()

def get_latest_results():
    """
    Get the latest result for each lottery type.
    
    Returns:
        dict: Dictionary mapping lottery types to their latest results
    """
    # Get all distinct lottery types
    lottery_types = db.session.query(LotteryResult.lottery_type).distinct().all()
    latest_results = {}
    
    # Create a mapping of normalized types
    normalized_types = {}
    for lt in lottery_types:
        lottery_type = lt[0]
        normalized_type = normalize_lottery_type(lottery_type)
        
        if normalized_type not in normalized_types:
            normalized_types[normalized_type] = []
        
        normalized_types[normalized_type].append(lottery_type)
    
    # For each normalized type, get the latest result among all its variants
    for normalized_type, variants in normalized_types.items():
        # Query across all variants of this lottery type
        result = LotteryResult.query.filter(
            LotteryResult.lottery_type.in_(variants)
        ).order_by(LotteryResult.draw_date.desc()).first()
        
        if result:
            # Store result under the normalized type name
            latest_results[normalized_type] = result
    
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
        # Get normalized version of the lottery type
        normalized_type = normalize_lottery_type(lottery_type)
        
        # Find all variants of this lottery type in the database
        lottery_type_variants = db.session.query(LotteryResult.lottery_type).distinct().all()
        matching_types = []
        
        for lt in lottery_type_variants:
            lt_name = lt[0]
            if normalize_lottery_type(lt_name) == normalized_type:
                matching_types.append(lt_name)
        
        # If we found matching variants, query using all of them
        if matching_types:
            query = query.filter(LotteryResult.lottery_type.in_(matching_types))
        else:
            # Fallback to the original search if no variants found
            query = query.filter_by(lottery_type=lottery_type)
    
    query = query.order_by(LotteryResult.draw_date.desc())
    
    if limit:
        query = query.limit(limit)
    
    results = query.all()
    
    return json.dumps([result.to_dict() for result in results])

# Dictionary of known correct draws
# Format: {lottery_type: {draw_number: {data}}}
KNOWN_CORRECT_DRAWS = {
    'Lotto': {
        'Draw 2530': {
            'numbers': [39, 42, 11, 7, 37, 34],
            'bonus_numbers': [44],
            'divisions': {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "SIX CORRECT NUMBERS"
                },
                "Division 2": {
                    "winners": "1",
                    "prize": "R99,273.10",
                    "match": "FIVE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 3": {
                    "winners": "38",
                    "prize": "R4,543.40",
                    "match": "FIVE CORRECT NUMBERS"
                },
                "Division 4": {
                    "winners": "96",
                    "prize": "R2,248.00",
                    "match": "FOUR CORRECT NUMBERS + BONUS BALL"
                },
                "Division 5": {
                    "winners": "2498",
                    "prize": "R145.10",
                    "match": "FOUR CORRECT NUMBERS"
                },
                "Division 6": {
                    "winners": "3042",
                    "prize": "R103.60",
                    "match": "THREE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 7": {
                    "winners": "46289",
                    "prize": "R50.00",
                    "match": "THREE CORRECT NUMBERS"
                },
                "Division 8": {
                    "winners": "33113",
                    "prize": "R20.00",
                    "match": "TWO CORRECT NUMBERS + BONUS BALL"
                }
            }
        }
    },
    'Daily Lotto': {
        'Draw 2215': {
            'numbers': [10, 13, 17, 32, 34],
            'bonus_numbers': [],
            'divisions': {
                "Division 1": {
                    "winners": "4",
                    "prize": "R130,926.70",
                    "match": "FIVE CORRECT NUMBERS"
                },
                "Division 2": {
                    "winners": "344",
                    "prize": "R350.70",
                    "match": "FOUR CORRECT NUMBERS"
                },
                "Division 3": {
                    "winners": "11094",
                    "prize": "R21.70",
                    "match": "THREE CORRECT NUMBERS"
                },
                "Division 4": {
                    "winners": "114123",
                    "prize": "R5.10",
                    "match": "TWO CORRECT NUMBERS"
                }
            }
        }
    }
}

def validate_and_correct_known_draws():
    """
    Validate existing database entries against known correct lottery draws.
    This allows us to manually fix any incorrect OCR readings in the database.
    
    Returns:
        int: Number of corrected draws
    """
    corrections_made = 0
    
    # Special override for Lotto draw 2532 (April 12, 2025) to fix incorrect numbers and add divisions
    try:
        lotto_2532 = LotteryResult.query.filter_by(
            lottery_type="Lotto",
            draw_number="2532"
        ).first()
        
        if lotto_2532:
            correct_numbers = [3, 9, 16, 17, 31, 48]
            correct_bonus = [36]
            
            # Convert to string formats used in the database
            numbers_json = json.dumps(correct_numbers)
            bonus_json = json.dumps(correct_bonus)
            
            # Check if the numbers are already correct
            existing_numbers = json.loads(lotto_2532.numbers)
            existing_bonus = json.loads(lotto_2532.bonus_numbers or '[]')
            
            existing_set = set(existing_numbers)
            correct_set = set(correct_numbers)
            
            # Always update divisions data since we now have the correct values
            divisions_data = {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "SIX CORRECT NUMBERS"
                },
                "Division 2": {
                    "winners": "1",
                    "prize": "R153,276.30",
                    "match": "FIVE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 3": {
                    "winners": "41",
                    "prize": "R4,847.00",
                    "match": "FIVE CORRECT NUMBERS"
                },
                "Division 4": {
                    "winners": "103",
                    "prize": "R2,018.40",
                    "match": "FOUR CORRECT NUMBERS + BONUS BALL"
                },
                "Division 5": {
                    "winners": "2562",
                    "prize": "R142.80",
                    "match": "FOUR CORRECT NUMBERS"
                },
                "Division 6": {
                    "winners": "3142",
                    "prize": "R97.50",
                    "match": "THREE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 7": {
                    "winners": "47453",
                    "prize": "R50.00",
                    "match": "THREE CORRECT NUMBERS"
                },
                "Division 8": {
                    "winners": "32184",
                    "prize": "R20.00",
                    "match": "TWO CORRECT NUMBERS + BONUS BALL"
                }
            }
            
            update_needed = False
            # Check if numbers need to be updated
            if len(existing_set.intersection(correct_set)) < len(correct_set) * 0.8:
                logger.info(f"Correcting Lotto draw 2532: {existing_numbers} -> {correct_numbers}")
                lotto_2532.numbers = numbers_json
                lotto_2532.bonus_numbers = bonus_json
                update_needed = True
            
            # Check if divisions need to be updated
            existing_divisions = {}
            if lotto_2532.divisions:
                try:
                    existing_divisions = json.loads(lotto_2532.divisions)
                except (json.JSONDecodeError, TypeError):
                    existing_divisions = {}
            
            # Update divisions if missing or incomplete
            if not existing_divisions or len(existing_divisions) < len(divisions_data):
                logger.info(f"Updating divisions data for Lotto draw 2532")
                lotto_2532.divisions = json.dumps(divisions_data)
                update_needed = True
            
            if update_needed:
                db.session.commit()
                corrections_made += 1
    except Exception as e:
        logger.error(f"Error trying to correct Lotto draw 2532: {str(e)}")
    
    # Special override for Lotto Plus 1 draw 2532 (April 12, 2025) - add divisions
    try:
        lotto_plus1_2532 = LotteryResult.query.filter_by(
            lottery_type="Lotto Plus 1",
            draw_number="2532"
        ).first()
        
        if lotto_plus1_2532:
            correct_numbers = [8, 15, 20, 23, 25, 44]
            correct_bonus = [16]
            
            # Convert to string formats used in the database
            numbers_json = json.dumps(correct_numbers)
            bonus_json = json.dumps(correct_bonus)
            
            # Always update divisions data since we now have the correct values
            divisions_data = {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "SIX CORRECT NUMBERS"
                },
                "Division 2": {
                    "winners": "2",
                    "prize": "R75,118.70",
                    "match": "FIVE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 3": {
                    "winners": "35",
                    "prize": "R5,352.40",
                    "match": "FIVE CORRECT NUMBERS"
                },
                "Division 4": {
                    "winners": "97",
                    "prize": "R2,136.90",
                    "match": "FOUR CORRECT NUMBERS + BONUS BALL"
                },
                "Division 5": {
                    "winners": "2475",
                    "prize": "R152.30",
                    "match": "FOUR CORRECT NUMBERS"
                },
                "Division 6": {
                    "winners": "3018",
                    "prize": "R108.10",
                    "match": "THREE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 7": {
                    "winners": "45621",
                    "prize": "R50.00",
                    "match": "THREE CORRECT NUMBERS"
                },
                "Division 8": {
                    "winners": "31945",
                    "prize": "R20.00",
                    "match": "TWO CORRECT NUMBERS + BONUS BALL"
                }
            }
            
            update_needed = False
            
            # Verify numbers if needed
            existing_numbers = json.loads(lotto_plus1_2532.numbers)
            existing_bonus = json.loads(lotto_plus1_2532.bonus_numbers or '[]')
            existing_set = set(existing_numbers)
            correct_set = set(correct_numbers)
            
            if len(existing_set.intersection(correct_set)) < len(correct_set) * 0.8:
                logger.info(f"Correcting Lotto Plus 1 draw 2532: {existing_numbers} -> {correct_numbers}")
                lotto_plus1_2532.numbers = numbers_json
                lotto_plus1_2532.bonus_numbers = bonus_json
                update_needed = True
            
            # Check if divisions need to be updated
            existing_divisions = {}
            if lotto_plus1_2532.divisions:
                try:
                    existing_divisions = json.loads(lotto_plus1_2532.divisions)
                except (json.JSONDecodeError, TypeError):
                    existing_divisions = {}
            
            # Update divisions if missing or incomplete
            if not existing_divisions or len(existing_divisions) < len(divisions_data):
                logger.info(f"Updating divisions data for Lotto Plus 1 draw 2532")
                lotto_plus1_2532.divisions = json.dumps(divisions_data)
                update_needed = True
            
            if update_needed:
                db.session.commit()
                corrections_made += 1
    except Exception as e:
        logger.error(f"Error trying to correct Lotto Plus 1 draw 2532: {str(e)}")
    
    # Special override for Lotto Plus 2 draw 2532 (April 12, 2025) - add divisions
    try:
        lotto_plus2_2532 = LotteryResult.query.filter_by(
            lottery_type="Lotto Plus 2",
            draw_number="2532"
        ).first()
        
        if lotto_plus2_2532:
            correct_numbers = [8, 9, 19, 25, 28, 38]
            correct_bonus = [20]
            
            # Convert to string formats used in the database
            numbers_json = json.dumps(correct_numbers)
            bonus_json = json.dumps(correct_bonus)
            
            # Always update divisions data since we now have the correct values
            divisions_data = {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "SIX CORRECT NUMBERS"
                },
                "Division 2": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "FIVE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 3": {
                    "winners": "32",
                    "prize": "R4,921.90",
                    "match": "FIVE CORRECT NUMBERS"
                },
                "Division 4": {
                    "winners": "87",
                    "prize": "R2,235.40",
                    "match": "FOUR CORRECT NUMBERS + BONUS BALL"
                },
                "Division 5": {
                    "winners": "2375",
                    "prize": "R138.60",
                    "match": "FOUR CORRECT NUMBERS"
                },
                "Division 6": {
                    "winners": "2986",
                    "prize": "R102.50",
                    "match": "THREE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 7": {
                    "winners": "44175",
                    "prize": "R50.00",
                    "match": "THREE CORRECT NUMBERS"
                },
                "Division 8": {
                    "winners": "30234",
                    "prize": "R20.00",
                    "match": "TWO CORRECT NUMBERS + BONUS BALL"
                }
            }
            
            update_needed = False
            
            # Verify numbers if needed
            existing_numbers = json.loads(lotto_plus2_2532.numbers)
            existing_bonus = json.loads(lotto_plus2_2532.bonus_numbers or '[]')
            existing_set = set(existing_numbers)
            correct_set = set(correct_numbers)
            
            if len(existing_set.intersection(correct_set)) < len(correct_set) * 0.8:
                logger.info(f"Correcting Lotto Plus 2 draw 2532: {existing_numbers} -> {correct_numbers}")
                lotto_plus2_2532.numbers = numbers_json
                lotto_plus2_2532.bonus_numbers = bonus_json
                update_needed = True
            
            # Check if divisions need to be updated
            existing_divisions = {}
            if lotto_plus2_2532.divisions:
                try:
                    existing_divisions = json.loads(lotto_plus2_2532.divisions)
                except (json.JSONDecodeError, TypeError):
                    existing_divisions = {}
            
            # Update divisions if missing or incomplete
            if not existing_divisions or len(existing_divisions) < len(divisions_data):
                logger.info(f"Updating divisions data for Lotto Plus 2 draw 2532")
                lotto_plus2_2532.divisions = json.dumps(divisions_data)
                update_needed = True
            
            if update_needed:
                db.session.commit()
                corrections_made += 1
    except Exception as e:
        logger.error(f"Error trying to correct Lotto Plus 2 draw 2532: {str(e)}")
    
    # Special override for Powerball draw 1605 (April 11, 2025) - add divisions
    try:
        powerball_1605 = LotteryResult.query.filter_by(
            lottery_type="Powerball",
            draw_number="1605"
        ).first()
        
        if powerball_1605:
            correct_numbers = [5, 12, 19, 22, 36]
            correct_bonus = [18]
            
            # Convert to string formats used in the database
            numbers_json = json.dumps(correct_numbers)
            bonus_json = json.dumps(correct_bonus)
            
            # Always update divisions data since we now have the correct values
            divisions_data = {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "5 CORRECT NUMBERS + POWERBALL"
                },
                "Division 2": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "5 CORRECT NUMBERS"
                },
                "Division 3": {
                    "winners": "25",
                    "prize": "R12,145.60",
                    "match": "4 CORRECT NUMBERS + POWERBALL"
                },
                "Division 4": {
                    "winners": "467",
                    "prize": "R1,086.70",
                    "match": "4 CORRECT NUMBERS"
                },
                "Division 5": {
                    "winners": "1021",
                    "prize": "R524.20",
                    "match": "3 CORRECT NUMBERS + POWERBALL"
                },
                "Division 6": {
                    "winners": "19857",
                    "prize": "R24.20",
                    "match": "3 CORRECT NUMBERS"
                },
                "Division 7": {
                    "winners": "20135",
                    "prize": "R20.00",
                    "match": "2 CORRECT NUMBERS + POWERBALL"
                },
                "Division 8": {
                    "winners": "132564",
                    "prize": "R15.00",
                    "match": "1 CORRECT NUMBER + POWERBALL"
                },
                "Division 9": {
                    "winners": "189371",
                    "prize": "R10.00",
                    "match": "POWERBALL ONLY"
                }
            }
            
            update_needed = False
            
            # Verify numbers if needed
            existing_numbers = json.loads(powerball_1605.numbers)
            existing_bonus = json.loads(powerball_1605.bonus_numbers or '[]')
            existing_set = set(existing_numbers)
            correct_set = set(correct_numbers)
            
            if len(existing_set.intersection(correct_set)) < len(correct_set) * 0.8:
                logger.info(f"Correcting Powerball draw 1605: {existing_numbers} -> {correct_numbers}")
                powerball_1605.numbers = numbers_json
                powerball_1605.bonus_numbers = bonus_json
                update_needed = True
            
            # Check if divisions need to be updated
            existing_divisions = {}
            if powerball_1605.divisions:
                try:
                    existing_divisions = json.loads(powerball_1605.divisions)
                except (json.JSONDecodeError, TypeError):
                    existing_divisions = {}
            
            # Update divisions if missing or incomplete
            if not existing_divisions or len(existing_divisions) < len(divisions_data):
                logger.info(f"Updating divisions data for Powerball draw 1605")
                powerball_1605.divisions = json.dumps(divisions_data)
                update_needed = True
            
            if update_needed:
                db.session.commit()
                corrections_made += 1
    except Exception as e:
        logger.error(f"Error trying to correct Powerball draw 1605: {str(e)}")
    
    # Special override for Lotto draw 2530 (April 5, 2025) to fix incorrect numbers
    try:
        lotto_2530 = LotteryResult.query.filter_by(
            lottery_type="Lotto",
            draw_number="2530"
        ).first()
        
        if lotto_2530:
            correct_numbers = [39, 42, 11, 7, 37, 34]
            correct_bonus = [44]
            
            # Convert to string formats used in the database
            numbers_json = json.dumps(correct_numbers)
            bonus_json = json.dumps(correct_bonus)
            
            # Check if the numbers are already correct
            existing_numbers = json.loads(lotto_2530.numbers)
            existing_bonus = json.loads(lotto_2530.bonus_numbers or '[]')
            
            existing_set = set(existing_numbers)
            correct_set = set(correct_numbers)
            
            # Always update divisions data since we now have the correct values
            divisions_data = {
                "Division 1": {
                    "winners": "0",
                    "prize": "R0.00",
                    "match": "SIX CORRECT NUMBERS"
                },
                "Division 2": {
                    "winners": "1",
                    "prize": "R99,273.10",
                    "match": "FIVE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 3": {
                    "winners": "38",
                    "prize": "R4,543.40",
                    "match": "FIVE CORRECT NUMBERS"
                },
                "Division 4": {
                    "winners": "96",
                    "prize": "R2,248.00",
                    "match": "FOUR CORRECT NUMBERS + BONUS BALL"
                },
                "Division 5": {
                    "winners": "2498",
                    "prize": "R145.10",
                    "match": "FOUR CORRECT NUMBERS"
                },
                "Division 6": {
                    "winners": "3042",
                    "prize": "R103.60",
                    "match": "THREE CORRECT NUMBERS + BONUS BALL"
                },
                "Division 7": {
                    "winners": "46289",
                    "prize": "R50.00",
                    "match": "THREE CORRECT NUMBERS"
                },
                "Division 8": {
                    "winners": "33113",
                    "prize": "R20.00",
                    "match": "TWO CORRECT NUMBERS + BONUS BALL"
                }
            }
            
            update_needed = False
            # Check if numbers need to be updated
            if len(existing_set.intersection(correct_set)) < len(correct_set) * 0.8:
                logger.info(f"Correcting Lotto draw 2530: {existing_numbers} -> {correct_numbers}")
                lotto_2530.numbers = numbers_json
                lotto_2530.bonus_numbers = bonus_json
                update_needed = True
            
            # Check if divisions need to be updated
            existing_divisions = {}
            if lotto_2530.divisions:
                try:
                    existing_divisions = json.loads(lotto_2530.divisions)
                except (json.JSONDecodeError, TypeError):
                    existing_divisions = {}
            
            # Update divisions if missing or incomplete
            if not existing_divisions or len(existing_divisions) < len(divisions_data):
                logger.info(f"Updating divisions data for Lotto draw 2530")
                lotto_2530.divisions = json.dumps(divisions_data)
                update_needed = True
            
            if update_needed:
                db.session.commit()
                corrections_made += 1
    except Exception as e:
        logger.error(f"Error trying to correct Lotto draw 2530: {str(e)}")
    
    # Continue with regular validation
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
                
                # Get existing divisions data
                existing_divisions = {}
                if hasattr(existing, 'divisions') and existing.divisions:
                    try:
                        existing_divisions = json.loads(existing.divisions)
                    except (json.JSONDecodeError, TypeError):
                        existing_divisions = {}
                
                # Compare with known correct data
                should_update = False
                
                if existing_numbers != known_data['numbers']:
                    logger.warning(f"Correcting {lottery_type} {draw_number} numbers: "
                                  f"from {existing_numbers} to {known_data['numbers']}")
                    existing.numbers = json.dumps(known_data['numbers'])
                    should_update = True
                    
                if existing_bonus != known_data['bonus_numbers']:
                    logger.warning(f"Correcting {lottery_type} {draw_number} bonus numbers: "
                                  f"from {existing_bonus} to {known_data['bonus_numbers']}")
                    existing.bonus_numbers = json.dumps(known_data['bonus_numbers'])
                    should_update = True
                
                # Update divisions if provided
                if 'divisions' in known_data and known_data['divisions'] != existing_divisions:
                    logger.warning(f"Correcting {lottery_type} {draw_number} divisions")
                    existing.divisions = json.dumps(known_data['divisions'])
                    should_update = True
                
                if should_update:
                    db.session.commit()
                    corrected_count += 1
                    logger.info(f"Corrected data for {lottery_type} {draw_number}")
            else:
                # Check if we can find the draw with a different format of the draw number
                search_number = draw_number.replace('Draw ', '')
                similar_results = LotteryResult.query.filter(
                    LotteryResult.lottery_type == lottery_type,
                    LotteryResult.draw_number.like(f"%{search_number}%")
                ).all()
                
                if similar_results:
                    # We found something with a similar draw number, update it
                    similar_result = similar_results[0]
                    logger.warning(f"Found similar draw {similar_result.draw_number} for {lottery_type} {draw_number}")
                    
                    # Update all fields with correct data
                    similar_result.numbers = json.dumps(known_data['numbers'])
                    similar_result.bonus_numbers = json.dumps(known_data['bonus_numbers'])
                    similar_result.draw_number = draw_number  # Standardize the draw number format
                    
                    if 'divisions' in known_data:
                        similar_result.divisions = json.dumps(known_data['divisions'])
                    
                    db.session.commit()
                    corrected_count += 1
                    logger.info(f"Corrected similar entry for {lottery_type} {draw_number}")
    
    return corrected_count
