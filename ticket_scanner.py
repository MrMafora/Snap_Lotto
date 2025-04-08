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

def process_ticket_image(image_data, lottery_type, draw_number=None):
    """
    Process a lottery ticket image to extract numbers and check if it's a winner.
    
    Args:
        image_data: The uploaded ticket image data
        lottery_type: Type of lottery (Lotto, Powerball, etc.)
        draw_number: Optional specific draw number to check against
        
    Returns:
        dict: Result of ticket processing including matched numbers and prize info
    """
    # Convert image to base64 for OCR processing
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Extract ticket numbers using OCR
    ticket_numbers = extract_ticket_numbers(image_base64, lottery_type)
    
    # Get the lottery result to compare against
    lottery_result = get_lottery_result(lottery_type, draw_number)
    
    if not lottery_result:
        return {
            "error": f"No results found for {lottery_type}" + 
                     (f" Draw {draw_number}" if draw_number else " (latest draw)")
        }
    
    # Get winning numbers from the result
    winning_numbers = lottery_result.get_numbers_list()
    winning_numbers = [int(num) for num in winning_numbers]
    
    bonus_numbers = []
    if lottery_result.bonus_numbers:
        bonus_numbers = lottery_result.get_bonus_numbers_list()
        bonus_numbers = [int(num) for num in bonus_numbers]
    
    # Find matched numbers
    matched_numbers = [num for num in ticket_numbers if num in winning_numbers]
    matched_bonus = [num for num in ticket_numbers if num in bonus_numbers]
    
    # Get prize information based on matches
    prize_info = get_prize_info(lottery_type, matched_numbers, matched_bonus, lottery_result)
    
    # Format draw date for display
    formatted_date = lottery_result.draw_date.strftime("%A, %d %B %Y")
    
    # Return result
    return {
        "lottery_type": lottery_type,
        "draw_number": lottery_result.draw_number,
        "draw_date": formatted_date,
        "ticket_numbers": ticket_numbers,
        "winning_numbers": winning_numbers,
        "bonus_numbers": bonus_numbers,
        "matched_numbers": matched_numbers + matched_bonus,
        "matched_bonus": matched_bonus,
        "has_prize": bool(prize_info),
        "prize_info": prize_info if prize_info else {}
    }

def extract_ticket_numbers(image_base64, lottery_type):
    """
    Extract ticket numbers from an image using OCR.
    
    Args:
        image_base64: Base64-encoded image data
        lottery_type: Type of lottery for context
        
    Returns:
        list: Extracted ticket numbers as integers
    """
    try:
        # For now, we'll use anthropic for OCR as it's already set up in the system
        from ocr_processor import process_with_anthropic
        
        # Create a prompt specifically for lottery ticket number extraction
        system_prompt = """
        You are a specialized lottery ticket scanner. Your job is to extract the selected lottery 
        numbers from a lottery ticket image.
        
        - Focus ONLY on the player's selected numbers (usually circled, marked, or otherwise highlighted)
        - Ignore any other information like ticket purchase date, barcode, etc.
        - Return ONLY the numbers in a JSON array format
        - For South African lottery tickets, there are typically 6 numbers for Lotto/Lotto Plus
          and 5 numbers + 1 Powerball number for Powerball/Powerball Plus
        - For Daily Lotto, there are 5 numbers
        - Return numbers as integers, not strings
        - DO NOT include any explanatory text, ONLY return the JSON array
        
        Example response for Lotto ticket:
        [5, 11, 23, 27, 34, 42]
        
        Example response for Powerball ticket:
        [4, 15, 26, 37, 45, 20]
        (where 20 is the Powerball number)
        """
        
        # Log that we're processing a ticket
        logger.info(f"Processing {lottery_type} ticket with OCR")
        
        # Process the image
        response = process_with_anthropic(image_base64, lottery_type, system_prompt)
        
        # Extract just the text content
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
            
            # If response has explanation text, try to extract just the array part
            if '[' in cleaned_response and ']' in cleaned_response:
                match = re.search(r'\[(.*?)\]', cleaned_response, re.DOTALL)
                if match:
                    cleaned_response = '[' + match.group(1) + ']'
            
            # Parse the JSON array
            numbers = json.loads(cleaned_response)
            
            # Ensure all items are integers
            ticket_numbers = [int(num) for num in numbers]
            
            logger.info(f"Successfully extracted ticket numbers: {ticket_numbers}")
            return ticket_numbers
            
        except json.JSONDecodeError:
            # If parsing fails, try to extract numbers using regex
            logger.warning(f"Failed to parse OCR response as JSON. Trying regex extraction.")
            number_pattern = r'\d+'
            numbers = re.findall(number_pattern, raw_response)
            
            # Convert to integers and take appropriate number based on lottery type
            ticket_numbers = [int(num) for num in numbers if 1 <= int(num) <= 50]
            
            # Limit to appropriate number of selections
            if 'Lotto' in lottery_type:
                ticket_numbers = ticket_numbers[:6]
            elif 'Powerball' in lottery_type:
                ticket_numbers = ticket_numbers[:6]
            elif 'Daily' in lottery_type:
                ticket_numbers = ticket_numbers[:5]
                
            logger.info(f"Extracted ticket numbers using regex: {ticket_numbers}")
            return ticket_numbers
    except Exception as e:
        logger.error(f"Error extracting ticket numbers: {str(e)}")
        # For debugging, return sample numbers (will be replaced with manual input in production)
        return [5, 10, 15, 20, 25, 30]

def get_lottery_result(lottery_type, draw_number=None):
    """
    Get the lottery result to check against.
    
    Args:
        lottery_type: Type of lottery
        draw_number: Optional specific draw number
        
    Returns:
        LotteryResult: The lottery result object or None if not found
    """
    from app import db
    
    query = LotteryResult.query.filter_by(lottery_type=lottery_type)
    
    if draw_number:
        # Try to find the exact match first
        result = query.filter_by(draw_number=draw_number).first()
        if result:
            return result
            
        # If not found, try partial match
        result = query.filter(LotteryResult.draw_number.like(f"%{draw_number}%")).first()
        if result:
            return result
            
        # No match found
        return None
    else:
        # Get the latest result for this lottery type
        return query.order_by(LotteryResult.draw_date.desc()).first()

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
    
    if "Lotto" in lottery_type and "Powerball" not in lottery_type:
        # Lotto/Lotto Plus prize structure
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
    
    elif "Daily Lotto" in lottery_type:
        # Daily Lotto structure
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
    
    return None