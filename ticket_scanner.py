"""
Lottery ticket scanner module for processing ticket images and matching against known results.
"""
import os
import base64
import json
import logging
from datetime import datetime
import re

from models import LotteryResult

# Setup logging
logger = logging.getLogger(__name__)

def process_ticket_image(image_data, lottery_type, draw_number=None, file_extension='.jpeg'):
    """
    Process a lottery ticket image to extract all information and check if it's a winner.
    
    Args:
        image_data: The uploaded ticket image data
        lottery_type: Type of lottery (Lottery, Powerball, etc.)
        draw_number: Optional specific draw number to check against
        file_extension: Extension of the uploaded file (e.g., '.jpeg', '.png')
        
    Returns:
        dict: Result of ticket processing including matched numbers and prize info
    """
    # Convert image to base64 for OCR processing
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # We already have the file extension from the parameters
    logger.info(f"Using file extension: {file_extension}")
    
    # Extract ticket information using OCR
    ticket_info = extract_ticket_numbers(image_base64, lottery_type, file_extension)
    
    # Extract details from ticket info
    extracted_game_type = ticket_info.get('game_type')
    extracted_draw_number = ticket_info.get('draw_number')
    extracted_draw_date = ticket_info.get('draw_date')
    plays_powerball_plus = ticket_info.get('plays_powerball_plus', False)
    plays_lottery_plus_1 = ticket_info.get('plays_lottery_plus_1', False) or ticket_info.get('plays_lotto_plus_1', False)
    plays_lottery_plus_2 = ticket_info.get('plays_lottery_plus_2', False) or ticket_info.get('plays_lotto_plus_2', False)
    
    # Get both the raw and processed ticket numbers
    raw_ticket_info = ticket_info.get('raw_selected_numbers', {})
    ticket_numbers = ticket_info.get('selected_numbers', [])
    
    # Make sure the lottery_type is not set to the file extension (fix a common issue)
    if lottery_type and lottery_type.startswith('.'):
        lottery_type = ''
        
    # Use extracted lottery type if available and not manually specified
    if extracted_game_type and extracted_game_type != 'unknown' and (not lottery_type or lottery_type == 'unknown'):
        lottery_type = extracted_game_type
        
    # Use extracted draw number if available and not manually specified
    if extracted_draw_number and extracted_draw_number != 'unknown' and not draw_number:
        draw_number = extracted_draw_number
    
    # Log the extracted information
    logger.info(f"Extracted ticket info - Game: {lottery_type}, Draw: {draw_number}, Date: {extracted_draw_date}, Numbers: {ticket_numbers}, Plays Powerball Plus: {plays_powerball_plus}, Plays Lottery Plus 1: {plays_lottery_plus_1}, Plays Lottery Plus 2: {plays_lottery_plus_2}")
    
    # Get the lottery result to compare against
    lottery_result = get_lottery_result(lottery_type, draw_number)
    
    # Variables to hold additional game results
    powerball_plus_result = None
    lottery_plus_1_result = None
    lottery_plus_2_result = None
    
    # Check for Powerball Plus if applicable
    # Only check if primary game is Powerball and ticket plays Powerball Plus
    # Use case-insensitive comparison for "Powerball" to handle any OCR variations
    if lottery_type.lower() == "powerball" and plays_powerball_plus:
        logger.info("This ticket also plays Powerball Plus - checking both games")
        powerball_plus_result = get_lottery_result("Powerball Plus", draw_number)
    elif lottery_type.lower() == "powerball":
        logger.info("This ticket is Powerball only - NOT checking Powerball Plus")
    
    # Check for Lottery Plus 1 if applicable
    # Only check if primary game is Lottery and ticket plays Lottery Plus 1
    if lottery_type == "Lottery" and plays_lottery_plus_1:
        logger.info("This ticket also plays Lottery Plus 1 - checking both games")
        lottery_plus_1_result = get_lottery_result("Lottery Plus 1", draw_number)
    elif lottery_type == "Lottery":
        logger.info("This ticket doesn't play Lottery Plus 1 or it wasn't detected")
    
    # Check for Lottery Plus 2 if applicable
    # Only check if primary game is Lottery and ticket plays Lottery Plus 2
    if lottery_type == "Lottery" and plays_lottery_plus_2:
        logger.info("This ticket also plays Lottery Plus 2 - checking both games")
        lottery_plus_2_result = get_lottery_result("Lottery Plus 2", draw_number)
    elif lottery_type == "Lottery":
        logger.info("This ticket doesn't play Lottery Plus 2 or it wasn't detected")
    
    if not lottery_result:
        # Enhanced error message with more helpful information
        error_message = f"No results found for {lottery_type}"
        
        if draw_number:
            error_message += f" Draw {draw_number}"
        else:
            error_message += " (latest draw)"
            
        # Check if this is a future draw
        if extracted_draw_date:
            try:
                draw_date = datetime.strptime(extracted_draw_date, '%Y-%m-%d')
                today = datetime.now()
                if draw_date > today:
                    error_message = f"This ticket is for a future draw on {draw_date.strftime('%A, %d %B %Y')}. Results are not available yet."
            except Exception as e:
                logger.error(f"Error parsing draw date: {e}")
        
        # Add suggestion for what to do next
        error_message += ". This might be a recent draw not yet in our database, or the ticket information couldn't be read correctly."
        
        return {
            "error": error_message,
            "ticket_info": {
                "lottery_type": lottery_type,
                "draw_number": draw_number if draw_number else extracted_draw_number,
                "draw_date": extracted_draw_date,
                "ticket_numbers": ticket_numbers,
                "plays_powerball_plus": plays_powerball_plus,
                "plays_lottery_plus_1": plays_lottery_plus_1,
                "plays_lottery_plus_2": plays_lottery_plus_2
            }
        }
    
    # Get winning numbers from the result
    winning_numbers = lottery_result.get_numbers_list()
    winning_numbers = [int(num) for num in winning_numbers]
    
    bonus_numbers = []
    if lottery_result.bonus_numbers:
        bonus_numbers = lottery_result.get_bonus_numbers_list()
        bonus_numbers = [int(num) for num in bonus_numbers]
    
    # Initialize variables for best matching row
    best_row_matches = []
    best_row_bonus_matches = []
    rows_with_matches = []
    
    # If we have raw ticket info (multiple rows), analyze each row separately
    if raw_ticket_info and isinstance(raw_ticket_info, dict) and len(raw_ticket_info) > 0:
        # Process each row separately
        for row_name, numbers in raw_ticket_info.items():
            row_matches = [num for num in numbers if num in winning_numbers]
            row_bonus_matches = [num for num in numbers if num in bonus_numbers]
            
            # Track row with matches
            if row_matches or row_bonus_matches:
                row_data = {
                    "row": row_name,
                    "numbers": numbers,
                    "matched_numbers": row_matches,
                    "matched_bonus": row_bonus_matches,
                    "total_matched": len(row_matches) + len(row_bonus_matches),
                    "game_type": lottery_type  # This identifies which game the matches belong to
                }
                rows_with_matches.append(row_data)
                
                # Keep track of best row (most matches)
                if len(row_matches) + len(row_bonus_matches) > len(best_row_matches) + len(best_row_bonus_matches):
                    best_row_matches = row_matches
                    best_row_bonus_matches = row_bonus_matches
        
        # If we found rows with matches, use the best row for prize determination
        if best_row_matches or best_row_bonus_matches:
            matched_numbers = best_row_matches
            matched_bonus = best_row_bonus_matches
        else:
            # No matches in any row
            matched_numbers = []
            matched_bonus = []
    else:
        # For single row tickets, check the flattened list
        matched_numbers = [num for num in ticket_numbers if num in winning_numbers]
        matched_bonus = [num for num in ticket_numbers if num in bonus_numbers]
    
    # Get prize information based on matches
    prize_info = get_prize_info(lottery_type, matched_numbers, matched_bonus, lottery_result)
    
    # Format draw date for display
    formatted_date = lottery_result.draw_date.strftime("%A, %d %B %Y")
    
    # Initialize result structure
    result = {
        "lottery_type": lottery_type,
        "draw_number": lottery_result.draw_number,
        "draw_date": formatted_date,
        "ticket_info": {
            "detected_game_type": extracted_game_type,
            "detected_draw_number": extracted_draw_number,
            "detected_draw_date": extracted_draw_date,
            "selected_numbers": ticket_numbers,
            "plays_powerball_plus": plays_powerball_plus,
            "plays_lottery_plus_1": plays_lottery_plus_1,
            "plays_lottery_plus_2": plays_lottery_plus_2
        },
        "ticket_numbers": ticket_numbers,
        "winning_numbers": winning_numbers,
        "bonus_numbers": bonus_numbers,
        "matched_numbers": matched_numbers,
        "matched_bonus": matched_bonus,
        "total_matched": len(matched_numbers) + len(matched_bonus),
        "has_prize": bool(prize_info),
        "prize_info": prize_info if prize_info else {}
    }
    
    # Include raw selected numbers data if available
    if raw_ticket_info:
        result["ticket_info"]["raw_selected_numbers"] = raw_ticket_info
    
    # Add rows with matches if we have them
    if rows_with_matches:
        result["rows_with_matches"] = rows_with_matches
    
    # If this ticket also plays additional games, check against those results
    
    # For Powerball Plus results
    if powerball_plus_result:
        # Get Powerball Plus winning numbers
        pp_winning_numbers = powerball_plus_result.get_numbers_list()
        pp_winning_numbers = [int(num) for num in pp_winning_numbers]
        
        pp_bonus_numbers = []
        if powerball_plus_result.bonus_numbers:
            pp_bonus_numbers = powerball_plus_result.get_bonus_numbers_list()
            pp_bonus_numbers = [int(num) for num in pp_bonus_numbers]
        
        # Initialize best matches for Powerball Plus
        pp_best_matches = []
        pp_best_bonus_matches = []
        pp_rows_with_matches = []
        
        # Check each row separately for Powerball Plus matches
        if raw_ticket_info and isinstance(raw_ticket_info, dict) and len(raw_ticket_info) > 0:
            for row_name, numbers in raw_ticket_info.items():
                row_matches = [num for num in numbers if num in pp_winning_numbers]
                row_bonus_matches = [num for num in numbers if num in pp_bonus_numbers]
                
                if row_matches or row_bonus_matches:
                    pp_rows_with_matches.append({
                        "row": row_name,
                        "numbers": numbers,
                        "matched_numbers": row_matches,
                        "matched_bonus": row_bonus_matches,
                        "total_matched": len(row_matches) + len(row_bonus_matches),
                        "game_type": "Powerball Plus"  # Add game type for clarity
                    })
                    
                    # Track best matches
                    if len(row_matches) + len(row_bonus_matches) > len(pp_best_matches) + len(pp_best_bonus_matches):
                        pp_best_matches = row_matches
                        pp_best_bonus_matches = row_bonus_matches
            
            # Use best row matches if any found
            if pp_best_matches or pp_best_bonus_matches:
                pp_matched_numbers = pp_best_matches
                pp_matched_bonus = pp_best_bonus_matches
            else:
                # No matches in any row
                pp_matched_numbers = []
                pp_matched_bonus = []
        else:
            # For single row tickets
            pp_matched_numbers = [num for num in ticket_numbers if num in pp_winning_numbers]
            pp_matched_bonus = [num for num in ticket_numbers if num in pp_bonus_numbers]
        
        # Check for prize in Powerball Plus
        pp_prize_info = get_prize_info("Powerball Plus", pp_matched_numbers, pp_matched_bonus, powerball_plus_result)
        
        # Include Powerball Plus results in our response
        pp_result_data = {
            "lottery_type": "Powerball Plus",
            "draw_number": powerball_plus_result.draw_number,
            "draw_date": powerball_plus_result.draw_date.strftime("%A, %d %B %Y"),
            "winning_numbers": pp_winning_numbers,
            "bonus_numbers": pp_bonus_numbers,
            "matched_numbers": pp_matched_numbers,
            "matched_bonus": pp_matched_bonus,
            "total_matched": len(pp_matched_numbers) + len(pp_matched_bonus),
            "has_prize": bool(pp_prize_info),
            "prize_info": pp_prize_info if pp_prize_info else {}
        }
        
        # Add rows with matches for Powerball Plus if available
        if pp_rows_with_matches:
            pp_result_data["rows_with_matches"] = pp_rows_with_matches
            
        result["powerball_plus_results"] = pp_result_data
        
        # If Powerball Plus has a prize but the main game doesn't, mark overall ticket as winning
        if bool(pp_prize_info) and not bool(prize_info):
            result["has_prize"] = True
    
    # For Lottery Plus 1 results
    if lottery_plus_1_result:
        # Get Lottery Plus 1 winning numbers
        lp1_winning_numbers = lottery_plus_1_result.get_numbers_list()
        lp1_winning_numbers = [int(num) for num in lp1_winning_numbers]
        
        lp1_bonus_numbers = []
        if lottery_plus_1_result.bonus_numbers:
            lp1_bonus_numbers = lottery_plus_1_result.get_bonus_numbers_list()
            lp1_bonus_numbers = [int(num) for num in lp1_bonus_numbers]
        
        # Initialize best matches for Lottery Plus 1
        lp1_best_matches = []
        lp1_best_bonus_matches = []
        lp1_rows_with_matches = []
        
        # Check each row separately for Lottery Plus 1 matches
        if raw_ticket_info and isinstance(raw_ticket_info, dict) and len(raw_ticket_info) > 0:
            for row_name, numbers in raw_ticket_info.items():
                row_matches = [num for num in numbers if num in lp1_winning_numbers]
                row_bonus_matches = [num for num in numbers if num in lp1_bonus_numbers]
                
                if row_matches or row_bonus_matches:
                    lp1_rows_with_matches.append({
                        "row": row_name,
                        "numbers": numbers,
                        "matched_numbers": row_matches,
                        "matched_bonus": row_bonus_matches,
                        "total_matched": len(row_matches) + len(row_bonus_matches),
                        "game_type": "Lottery Plus 1"  # Add game type for clarity
                    })
                    
                    # Track best matches
                    if len(row_matches) + len(row_bonus_matches) > len(lp1_best_matches) + len(lp1_best_bonus_matches):
                        lp1_best_matches = row_matches
                        lp1_best_bonus_matches = row_bonus_matches
            
            # Use best row matches if any found
            if lp1_best_matches or lp1_best_bonus_matches:
                lp1_matched_numbers = lp1_best_matches
                lp1_matched_bonus = lp1_best_bonus_matches
            else:
                # No matches in any row
                lp1_matched_numbers = []
                lp1_matched_bonus = []
        else:
            # For single row tickets
            lp1_matched_numbers = [num for num in ticket_numbers if num in lp1_winning_numbers]
            lp1_matched_bonus = [num for num in ticket_numbers if num in lp1_bonus_numbers]
        
        # Check for prize in Lottery Plus 1
        lp1_prize_info = get_prize_info("Lottery Plus 1", lp1_matched_numbers, lp1_matched_bonus, lottery_plus_1_result)
        
        # Include Lottery Plus 1 results in our response
        lp1_result_data = {
            "lottery_type": "Lottery Plus 1",
            "draw_number": lottery_plus_1_result.draw_number,
            "draw_date": lottery_plus_1_result.draw_date.strftime("%A, %d %B %Y"),
            "winning_numbers": lp1_winning_numbers,
            "bonus_numbers": lp1_bonus_numbers,
            "matched_numbers": lp1_matched_numbers,
            "matched_bonus": lp1_matched_bonus,
            "total_matched": len(lp1_matched_numbers) + len(lp1_matched_bonus),
            "has_prize": bool(lp1_prize_info),
            "prize_info": lp1_prize_info if lp1_prize_info else {}
        }
        
        # Add rows with matches for Lottery Plus 1 if available
        if lp1_rows_with_matches:
            lp1_result_data["rows_with_matches"] = lp1_rows_with_matches
            
        result["lottery_plus_1_results"] = lp1_result_data
        
        # If Lottery Plus 1 has a prize but the main game doesn't, mark overall ticket as winning
        if bool(lp1_prize_info) and not bool(prize_info):
            result["has_prize"] = True
    
    # For Lottery Plus 2 results
    if lottery_plus_2_result:
        # Get Lottery Plus 2 winning numbers
        lp2_winning_numbers = lottery_plus_2_result.get_numbers_list()
        lp2_winning_numbers = [int(num) for num in lp2_winning_numbers]
        
        lp2_bonus_numbers = []
        if lottery_plus_2_result.bonus_numbers:
            lp2_bonus_numbers = lottery_plus_2_result.get_bonus_numbers_list()
            lp2_bonus_numbers = [int(num) for num in lp2_bonus_numbers]
        
        # Initialize best matches for Lottery Plus 2
        lp2_best_matches = []
        lp2_best_bonus_matches = []
        lp2_rows_with_matches = []
        
        # Check each row separately for Lottery Plus 2 matches
        if raw_ticket_info and isinstance(raw_ticket_info, dict) and len(raw_ticket_info) > 0:
            for row_name, numbers in raw_ticket_info.items():
                row_matches = [num for num in numbers if num in lp2_winning_numbers]
                row_bonus_matches = [num for num in numbers if num in lp2_bonus_numbers]
                
                if row_matches or row_bonus_matches:
                    lp2_rows_with_matches.append({
                        "row": row_name,
                        "numbers": numbers,
                        "matched_numbers": row_matches,
                        "matched_bonus": row_bonus_matches,
                        "total_matched": len(row_matches) + len(row_bonus_matches),
                        "game_type": "Lottery Plus 2"  # Add game type for clarity
                    })
                    
                    # Track best matches
                    if len(row_matches) + len(row_bonus_matches) > len(lp2_best_matches) + len(lp2_best_bonus_matches):
                        lp2_best_matches = row_matches
                        lp2_best_bonus_matches = row_bonus_matches
            
            # Use best row matches if any found
            if lp2_best_matches or lp2_best_bonus_matches:
                lp2_matched_numbers = lp2_best_matches
                lp2_matched_bonus = lp2_best_bonus_matches
            else:
                # No matches in any row
                lp2_matched_numbers = []
                lp2_matched_bonus = []
        else:
            # For single row tickets
            lp2_matched_numbers = [num for num in ticket_numbers if num in lp2_winning_numbers]
            lp2_matched_bonus = [num for num in ticket_numbers if num in lp2_bonus_numbers]
        
        # Check for prize in Lottery Plus 2
        lp2_prize_info = get_prize_info("Lottery Plus 2", lp2_matched_numbers, lp2_matched_bonus, lottery_plus_2_result)
        
        # Include Lottery Plus 2 results in our response
        lp2_result_data = {
            "lottery_type": "Lottery Plus 2",
            "draw_number": lottery_plus_2_result.draw_number,
            "draw_date": lottery_plus_2_result.draw_date.strftime("%A, %d %B %Y"),
            "winning_numbers": lp2_winning_numbers,
            "bonus_numbers": lp2_bonus_numbers,
            "matched_numbers": lp2_matched_numbers,
            "matched_bonus": lp2_matched_bonus,
            "total_matched": len(lp2_matched_numbers) + len(lp2_matched_bonus),
            "has_prize": bool(lp2_prize_info),
            "prize_info": lp2_prize_info if lp2_prize_info else {}
        }
        
        # Add rows with matches for Lottery Plus 2 if available
        if lp2_rows_with_matches:
            lp2_result_data["rows_with_matches"] = lp2_rows_with_matches
            
        result["lottery_plus_2_results"] = lp2_result_data
        
        # If Lottery Plus 2 has a prize but no other game has a prize, mark overall ticket as winning
        # First check if we have a Lottery Plus 1 result with a prize
        lp1_has_prize = False
        if lottery_plus_1_result and result.get("lottery_plus_1_results", {}).get("has_prize", False):
            lp1_has_prize = True
                
        # Now check if Lottery Plus 2 has a prize but no other game does
        if bool(lp2_prize_info) and not (bool(prize_info) or lp1_has_prize):
            result["has_prize"] = True
        
    return result

def extract_ticket_numbers(image_base64, lottery_type, file_extension='.jpeg'):
    """
    Extract ticket numbers and information from an image using OCR.
    
    Args:
        image_base64: Base64-encoded image data
        lottery_type: Type of lottery for context (empty string if auto-detect)
        file_extension: Extension of the uploaded file (e.g., '.jpeg', '.png')
        
    Returns:
        dict: Extracted ticket information including numbers, draw date, and draw number
    """
    try:
        # For now, we'll use anthropic for OCR as it's already set up in the system
        from ocr_processor import process_with_anthropic
        
        # Create a prompt specifically for lottery ticket information extraction
        system_prompt = """
        You are a specialized South African lottery ticket scanner. Your job is to extract all key information from 
        a lottery ticket image including:
        
        1. Game type (which lottery game: Lottery, Lottery Plus 1, Lottery Plus 2, Powerball, Powerball Plus, Daily Lottery)
        2. Draw date (in YYYY-MM-DD format if possible)
        3. Draw number (ID number of the specific draw) - CRITICAL: Extract the exact draw number as printed on the ticket
        4. Selected numbers (the player's chosen numbers on the ticket)
        5. IMPORTANT: Check if the ticket has any of these indications:
           - "POWERBALL PLUS: YES" - means the ticket is valid for both Powerball and Powerball Plus draws
           - "LOTTERY PLUS 1: YES" or "LOTTO PLUS 1: YES" - means the ticket is valid for both Lottery and Lottery Plus 1 draws
           - "LOTTERY PLUS 2: YES" or "LOTTO PLUS 2: YES" - means the ticket is valid for both Lottery and Lottery Plus 2 draws
        
        CRITICAL REQUIREMENT: If the ticket has MULTIPLE ROWS or SETS of numbers (e.g., A01-F01 or multiple games),
        you MUST extract ALL ROWS and ALL NUMBERS from the ticket. Do not just extract the first row.
        
        Important notes:
        - South African lottery tickets typically display game type, draw date and draw number clearly
        - For Powerball tickets, the draw number is EXTREMELY IMPORTANT - look for text like "Draw: 1603" or just "1603"
        - Powerball tickets may say "PowerBall" or "Power Ball" - treat these as the same game type
        - Focus on the player's selected numbers (usually circled, marked, or otherwise highlighted)
        - For Lottery/Lottery Plus tickets, look for 6 selected numbers per row
        - For Powerball/Powerball Plus tickets, look for 5 main numbers + 1 Powerball number per row
        - For Daily Lottery tickets, look for 5 selected numbers per row
        - CAREFULLY check for additional game participation (POWERBALL PLUS, LOTTERY PLUS 1, LOTTERY PLUS 2)
        - Return all information in a structured JSON format with no additional text or explanations
        - If you can't determine certain fields with confidence, use "unknown" as the value
        
        Return the data in this JSON format:
        {
            "game_type": "The detected game type (e.g., Lottery, Powerball)",
            "draw_date": "Draw date in YYYY-MM-DD format if possible",
            "draw_number": "Draw ID number as shown on ticket",
            "plays_powerball_plus": true/false,
            "plays_lottery_plus_1": true/false,
            "plays_lottery_plus_2": true/false,
            "selected_numbers": {
                "A01": [first set of numbers],
                "B01": [second set of numbers],
                ...additional rows as needed
            }
        }
        
        Alternatively, you can use this format for the selected numbers if row labels are not visible:
        "selected_numbers": [
            [first row numbers],
            [second row numbers],
            ...additional rows as needed
        ]
        
        Do not include any explanatory text outside the JSON structure. Return ONLY the JSON.
        """
        
        # Log that we're processing a ticket
        logger.info(f"Processing {lottery_type} ticket with OCR")
        
        # Determine image format from file extension
        image_format = 'jpeg'  # Default to JPEG
        if file_extension.lower() == '.png':
            image_format = 'png'
        elif file_extension.lower() in ['.jpg', '.jpeg']:
            image_format = 'jpeg'
        elif file_extension.lower() == '.webp':
            image_format = 'webp'
            
        logger.info(f"Using image format {image_format} for ticket scanning")
        
        # Process the image with the correct format
        response = process_with_anthropic(image_base64, lottery_type, system_prompt, image_format)
        
        # Extract the text content
        raw_response = response.get('raw_response', '')
        
        # Try to parse the response as JSON
        try:
            # Clean up the response to handle different formats
            cleaned_response = raw_response.strip()
            
            # If response is wrapped in code blocks, extract just the content
            if '```' in cleaned_response:
                match = re.search(r'```(?:json)?(.*?)```', cleaned_response, re.DOTALL)
                if match:
                    cleaned_response = match.group(1).strip()
            
            # Try to extract just the JSON portion (Claude sometimes adds explanations after JSON)
            try:
                # Find where the JSON starts (first {)
                json_start = cleaned_response.find('{')
                if json_start >= 0:
                    # Find the matching closing } by counting braces
                    brace_count = 0
                    json_end = -1
                    in_quotes = False
                    escape_next = False
                    
                    for i, char in enumerate(cleaned_response[json_start:]):
                        pos = json_start + i
                        
                        # Handle string quotes and escaping
                        if char == '\\' and not escape_next:
                            escape_next = True
                            continue
                        
                        if char == '"' and not escape_next:
                            in_quotes = not in_quotes
                        
                        escape_next = False
                        
                        # Only count braces when not in quotes
                        if not in_quotes:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = pos
                                    break
                    
                    if json_end > json_start:
                        # Extract just the valid JSON portion
                        json_str = cleaned_response[json_start:json_end+1]
                        
                        # Remove leading zeros from numbers in JSON strings (like "08" -> "8")
                        # This fixes JSON parsing errors for numbers with leading zeros
                        json_str = re.sub(r'([^0-9"])0+([1-9][0-9]*)', r'\1\2', json_str)
                        
                        logger.info(f"Extracted clean JSON: {json_str}")
                        ticket_info = json.loads(json_str)
                    else:
                        # Remove leading zeros from numbers in JSON strings (like "08" -> "8")
                        cleaned_response = re.sub(r'([^0-9"])0+([1-9][0-9]*)', r'\1\2', cleaned_response)
                        
                        # Fallback to regular parsing
                        ticket_info = json.loads(cleaned_response)
                else:
                    # Remove leading zeros from numbers in JSON strings (like "08" -> "8")
                    cleaned_response = re.sub(r'([^0-9"])0+([1-9][0-9]*)', r'\1\2', cleaned_response)

                    # No JSON found, try original
                    ticket_info = json.loads(cleaned_response)
            except Exception:
                # If sophisticated parsing fails, try regular parsing
                logger.warning("JSON extraction failed, trying direct parsing")
                
                # Remove leading zeros from numbers in JSON strings (like "08" -> "8")
                cleaned_response = re.sub(r'([^0-9"])0+([1-9][0-9]*)', r'\1\2', cleaned_response)
                
                ticket_info = json.loads(cleaned_response)
            
            # Handle selected numbers which could be in various formats
            selected_numbers = []
            
            if 'selected_numbers' in ticket_info:
                # Check if it's a dictionary directly with row names (A06, B06, etc.)
                if isinstance(ticket_info['selected_numbers'], dict):
                    logger.warning("Found dictionary with row names for selected numbers")
                    ticket_info['raw_selected_numbers'] = {}
                    for row_name, numbers in ticket_info['selected_numbers'].items():
                        if isinstance(numbers, list):
                            row_numbers = [int(num) for num in numbers if isinstance(num, (int, str, float))]
                            ticket_info['raw_selected_numbers'][row_name] = row_numbers
                            selected_numbers.extend(row_numbers)
                # Case 1: Simple list of numbers
                elif isinstance(ticket_info['selected_numbers'], list):
                    # Check if we're dealing with a simple list of integers
                    if all(isinstance(x, (int, str, float)) for x in ticket_info['selected_numbers']):
                        selected_numbers = [int(num) for num in ticket_info['selected_numbers']]
                    # Case 2: Nested array of arrays (multiple rows of numbers)
                    elif isinstance(ticket_info['selected_numbers'], list) and len(ticket_info['selected_numbers']) > 0 and isinstance(ticket_info['selected_numbers'][0], list):
                        logger.warning("Found nested arrays of numbers, flattening all rows")
                        # Store original rows for reference
                        ticket_info['raw_selected_numbers'] = {}
                        for i, row in enumerate(ticket_info['selected_numbers']):
                            if isinstance(row, list):
                                row_name = f"Row {i+1}"
                                row_numbers = [int(num) for num in row if isinstance(num, (int, str, float))]
                                ticket_info['raw_selected_numbers'][row_name] = row_numbers
                                selected_numbers.extend(row_numbers)
                    # Case 3: Complex structure with lines/rows
                    elif isinstance(ticket_info['selected_numbers'], list) and len(ticket_info['selected_numbers']) > 0:
                        for item in ticket_info['selected_numbers']:
                            if isinstance(item, dict):
                                # Extract numbers from all fields in the dict
                                for key, value in item.items():
                                    if isinstance(value, list):
                                        selected_numbers.extend([int(num) for num in value if isinstance(num, (int, str, float))])
                
                # If we still don't have numbers, try to find any integers in the JSON
                if not selected_numbers:
                    logger.warning("Complex number structure found, extracting all numbers")
                    # Extract all integers from the ticket_info recursively
                    def extract_all_numbers(obj):
                        numbers = []
                        if isinstance(obj, dict):
                            for value in obj.values():
                                numbers.extend(extract_all_numbers(value))
                        elif isinstance(obj, list):
                            for item in obj:
                                numbers.extend(extract_all_numbers(item))
                        elif isinstance(obj, (int, float)) or (isinstance(obj, str) and obj.isdigit()):
                            numbers.append(int(obj))
                        return numbers
                    
                    all_numbers = extract_all_numbers(ticket_info)
                    # Filter to reasonable lottery numbers (1-50)
                    selected_numbers = [num for num in all_numbers if 1 <= num <= 50]
            
            # Update the ticket info with our processed numbers
            ticket_info['selected_numbers'] = selected_numbers if selected_numbers else []
            
            # Make sure we have a game type
            if not ticket_info.get('game_type') or ticket_info.get('game_type') == 'unknown':
                # Extract game type from Claude response if possible
                game_type_match = re.search(r'(lottery|powerball|daily\s*lottery)(?:\s*plus\s*[12])?', 
                                          raw_response, re.IGNORECASE)
                if game_type_match:
                    extracted_type = game_type_match.group(0).strip()
                    # Standardize the format
                    if "powerball" in extracted_type.lower():
                        if "plus" in extracted_type.lower():
                            ticket_info['game_type'] = "Powerball Plus"
                        else:
                            ticket_info['game_type'] = "Powerball"
                    elif "daily" in extracted_type.lower():
                        ticket_info['game_type'] = "Daily Lottery"
                    elif "lottery" in extracted_type.lower() or "lotto" in extracted_type.lower():
                        if "plus 1" in extracted_type.lower():
                            ticket_info['game_type'] = "Lottery Plus 1"
                        elif "plus 2" in extracted_type.lower():
                            ticket_info['game_type'] = "Lottery Plus 2"
                        else:
                            ticket_info['game_type'] = "Lottery"
            
            # If we have game type but the user already specified it, prioritize user selection
            if lottery_type and lottery_type != "unknown":
                ticket_info['game_type'] = lottery_type
            
            logger.info(f"Successfully extracted ticket info: {ticket_info}")
            return ticket_info
            
        except json.JSONDecodeError:
            # If parsing fails, try to extract data using regex
            logger.warning(f"Failed to parse OCR response as JSON. Trying regex extraction.")
            
            # Extract numbers
            number_pattern = r'\d+'
            numbers = re.findall(number_pattern, raw_response)
            ticket_numbers = [int(num) for num in numbers if 1 <= int(num) <= 50]
            
            # Limit to appropriate number of selections based on lottery type
            if 'Lottery' in lottery_type and 'Powerball' not in lottery_type:
                ticket_numbers = ticket_numbers[:6]
            elif 'Powerball' in lottery_type:
                ticket_numbers = ticket_numbers[:6]  # 5 main + 1 powerball
            elif 'Daily' in lottery_type:
                ticket_numbers = ticket_numbers[:5]
            
            # Try to extract draw number
            draw_match = re.search(r'draw\s*(?:number|no|#)?\s*[:#]?\s*(\d+)', raw_response, re.IGNORECASE)
            draw_number = draw_match.group(1) if draw_match else "unknown"
            
            # Try to extract date
            date_match = re.search(r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})', raw_response)
            draw_date = date_match.group(1) if date_match else "unknown"
            
            # Try to extract game type if not provided
            extracted_game_type = lottery_type
            if not lottery_type or lottery_type == "unknown":
                game_type_match = re.search(r'(lottery|powerball|daily\s*lottery)(?:\s*plus\s*[12])?', 
                                         raw_response, re.IGNORECASE)
                if game_type_match:
                    extracted_type = game_type_match.group(0).strip()
                    # Standardize the format
                    if "powerball" in extracted_type.lower():
                        if "plus" in extracted_type.lower():
                            extracted_game_type = "Powerball Plus"
                        else:
                            extracted_game_type = "Powerball"
                    elif "daily" in extracted_type.lower():
                        extracted_game_type = "Daily Lottery"
                    elif "lottery" in extracted_type.lower():
                        if "plus 1" in extracted_type.lower():
                            extracted_game_type = "Lottery Plus 1"
                        elif "plus 2" in extracted_type.lower():
                            extracted_game_type = "Lottery Plus 2"
                        else:
                            extracted_game_type = "Lottery"
            
            ticket_info = {
                'game_type': extracted_game_type,
                'draw_date': draw_date,
                'draw_number': draw_number,
                'selected_numbers': ticket_numbers
            }
            
            logger.info(f"Extracted ticket info using regex: {ticket_info}")
            return ticket_info
            
    except Exception as e:
        logger.error(f"Error extracting ticket info: {str(e)}")
        # For debugging, return basic structure with placeholder data
        return {
            'game_type': lottery_type,
            'draw_date': "unknown",
            'draw_number': "unknown",
            'selected_numbers': [5, 10, 15, 20, 25, 30]
        }

def get_lottery_result(lottery_type, draw_number=None):
    """
    Get the lottery result to check against.
    
    Args:
        lottery_type: Type of lottery
        draw_number: Optional specific draw number
        
    Returns:
        LotteryResult: The lottery result object or None if not found
    """
    # Import models here to avoid circular imports
    from models import LotteryResult, db
    import re
    
    # Normalize lottery type
    normalized_lottery_type = lottery_type.strip()
    
    # Handle common variations
    if normalized_lottery_type.lower() in ['powerball', 'power ball']:
        normalized_lottery_type = 'Powerball'
    elif normalized_lottery_type.lower() in ['powerball plus', 'power ball plus']:
        normalized_lottery_type = 'Powerball Plus'
    
    query = LotteryResult.query.filter_by(lottery_type=normalized_lottery_type)
    
    if draw_number:
        # Clean the draw number - remove any non-digit characters
        if isinstance(draw_number, str):
            clean_draw_number = re.sub(r'\D', '', draw_number)
        else:
            clean_draw_number = str(draw_number)
            
        # Log what we're searching for
        logger.info(f"Searching for {normalized_lottery_type} draw {clean_draw_number}")
        
        # Try to find the exact match first
        result = query.filter_by(draw_number=clean_draw_number).first()
        if result:
            logger.info(f"Found exact match for {normalized_lottery_type} draw {clean_draw_number}")
            return result
            
        # If not found, try partial match
        result = query.filter(LotteryResult.draw_number.like(f"%{clean_draw_number}%")).first()
        if result:
            logger.info(f"Found partial match for {normalized_lottery_type} draw {clean_draw_number} -> {result.draw_number}")
            return result
            
        # No match found
        logger.warning(f"No match found for {normalized_lottery_type} draw {clean_draw_number}")
        return None
    else:
        # Get the latest result for this lottery type
        result = query.order_by(LotteryResult.draw_date.desc()).first()
        if result:
            logger.info(f"Using latest {normalized_lottery_type} draw: {result.draw_number}")
        else:
            logger.warning(f"No results found for {normalized_lottery_type}")
        return result

def get_prize_info(lottery_type, matched_numbers, matched_bonus, lottery_result):
    """
    Determine if the ticket won a prize based on matched numbers.
    
    Args:
        lottery_type: Type of lottery
        matched_numbers: List of matched main numbers
        matched_bonus: List of matched bonus numbers
        lottery_result: The lottery result object
        
    Returns:
        dict: Prize information or None if no prize
    """
    # Get divisions data from lottery result
    divisions = lottery_result.get_divisions()
    if not divisions:
        return None
        
    # Count total matches
    match_count = len(matched_numbers)
    bonus_match = len(matched_bonus) > 0
    
    # Determine division based on matches
    division = None
    match_type = ""
    
    if "Lottery" in lottery_type and "Powerball" not in lottery_type:
        # Lottery/Lottery Plus prize structure
        if match_count == 6:
            division = "Division 1"
            match_type = "SIX CORRECT NUMBERS"
        elif match_count == 5 and bonus_match:
            division = "Division 2"
            match_type = "FIVE CORRECT NUMBERS + BONUS BALL"
        elif match_count == 5:
            division = "Division 3"
            match_type = "FIVE CORRECT NUMBERS"
        elif match_count == 4 and bonus_match:
            division = "Division 4"
            match_type = "FOUR CORRECT NUMBERS + BONUS BALL"
        elif match_count == 4:
            division = "Division 5"
            match_type = "FOUR CORRECT NUMBERS"
        elif match_count == 3 and bonus_match:
            division = "Division 6"
            match_type = "THREE CORRECT NUMBERS + BONUS BALL"
        elif match_count == 3:
            division = "Division 7"
            match_type = "THREE CORRECT NUMBERS"
        elif match_count == 2 and bonus_match:
            division = "Division 8"
            match_type = "TWO CORRECT NUMBERS + BONUS BALL"
    
    elif "Powerball" in lottery_type:
        # Powerball/Powerball Plus structure
        # Assuming last number in selection is the Powerball
        if match_count == 5 and bonus_match:
            division = "Division 1"
            match_type = "FIVE CORRECT NUMBERS + POWERBALL"
        elif match_count == 5:
            division = "Division 2"
            match_type = "FIVE CORRECT NUMBERS"
        elif match_count == 4 and bonus_match:
            division = "Division 3"
            match_type = "FOUR CORRECT NUMBERS + POWERBALL"
        elif match_count == 4:
            division = "Division 4"
            match_type = "FOUR CORRECT NUMBERS"
        elif match_count == 3 and bonus_match:
            division = "Division 5"
            match_type = "THREE CORRECT NUMBERS + POWERBALL"
        elif match_count == 3:
            division = "Division 6"
            match_type = "THREE CORRECT NUMBERS"
        elif match_count == 2 and bonus_match:
            division = "Division 7"
            match_type = "TWO CORRECT NUMBERS + POWERBALL"
        elif match_count == 1 and bonus_match:
            division = "Division 8"
            match_type = "ONE CORRECT NUMBER + POWERBALL"
        elif bonus_match:
            division = "Division 9"
            match_type = "MATCH POWERBALL ONLY"
    
    elif "Daily Lottery" in lottery_type:
        # Daily Lottery structure
        if match_count == 5:
            division = "Division 1"
            match_type = "FIVE CORRECT NUMBERS"
        elif match_count == 4:
            division = "Division 2"
            match_type = "FOUR CORRECT NUMBERS"
        elif match_count == 3:
            division = "Division 3"
            match_type = "THREE CORRECT NUMBERS"
        elif match_count == 2:
            division = "Division 4"
            match_type = "TWO CORRECT NUMBERS"
    
    # If a division is found and exists in the result's divisions data
    if division and division in divisions:
        prize_data = divisions[division]
        
        return {
            "division": division,
            "match_type": match_type,
            "prize_amount": prize_data.get("prize", "R0.00"),
            "winners": prize_data.get("winners", "0")
        }
    
    # For Powerball, we want to return a prize even if division data is missing
    # This ensures players who match 3 or fewer numbers still see they've won
    if division and "Powerball" in lottery_type:
        # Fallback prize information for common Powerball divisions
        fallback_prizes = {
            "Division 1": "Jackpot",
            "Division 2": "Share of Prize Pool",
            "Division 3": "Approx. R10,000",
            "Division 4": "Approx. R1,000",
            "Division 5": "Approx. R500",
            "Division 6": "Approx. R100",
            "Division 7": "Approx. R50",
            "Division 8": "Approx. R20",
            "Division 9": "Approx. R15"
        }
        
        if division in fallback_prizes:
            return {
                "division": division,
                "match_type": match_type,
                "prize_amount": fallback_prizes[division],
                "winners": "N/A",
                "note": "Exact prize amount unavailable - showing estimate"
            }
            
    # No prize found
    return None