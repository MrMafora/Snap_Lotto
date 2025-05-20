"""
Enhanced Lottery Ticket Scanner

This module implements an advanced lottery ticket scanning system that:
1. Uses Google Gemini 2.5 Pro for OCR to extract ticket information
2. Checks the extracted data against our database
3. Falls back to OpenAI for missing draw information
4. Saves new draw data to improve the system over time
"""

import os
import json
import logging
import requests
import base64
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models
from models import db, LotteryResult, APIRequestLog

# Note: We'll import GeminiIntegration in scan_ticket to avoid circular imports

class TicketScanner:
    """Enhanced lottery ticket scanner with multi-model OCR and result verification"""

    def __init__(self):
        """Initialize the ticket scanner with API keys and configuration"""
        # Check for required API keys
        self.has_gemini_api_key = bool(os.environ.get('GEMINI_API_KEY'))
        self.has_openai_api_key = bool(os.environ.get('OPENAI_API_KEY'))
        self.has_anthropic_api_key = bool(os.environ.get('Lotto_scape_ANTHROPIC_KEY'))
        
        # Set default settings
        self.ocr_timeout = 30  # seconds
        self.verification_timeout = 45  # seconds
        
        # Initialize API usage tracking
        self.api_requests = {
            'anthropic_ocr': 0,
            'gemini_ocr': 0,
            'openai_verification': 0
        }
        
        logger.info(f"Ticket scanner initialized. Claude Vision available: {self.has_anthropic_api_key}, Gemini API available: {self.has_gemini_api_key}, OpenAI API available: {self.has_openai_api_key}")

    def scan_ticket(self, image_path: str) -> Dict[str, Any]:
        """
        Process a lottery ticket image and extract all relevant information
        
        Args:
            image_path: Path to the ticket image file
        
        Returns:
            Dictionary containing extracted ticket information
        """
        logger.info(f"Processing ticket image: {image_path}")
        
        # Step 1: Extract ticket information using OCR
        # Try with Claude Vision first if available
        if self.has_anthropic_api_key:
            logger.info("Attempting to extract ticket information with Claude Vision")
            ticket_data = self._extract_ticket_information_with_anthropic(image_path)
            if ticket_data and ticket_data.get('success'):
                logger.info("Successfully extracted ticket information with Claude Vision")
            else:
                logger.warning("Claude Vision extraction failed, falling back to Gemini")
                ticket_data = self._extract_ticket_information(image_path)
        else:
            logger.info("Using Gemini for ticket extraction")
            ticket_data = self._extract_ticket_information(image_path)
        
        if not ticket_data or not ticket_data.get('success'):
            logger.error("Failed to extract ticket information")
            return {'success': False, 'error': 'Failed to extract ticket information from image'}
        
        # Step 2: Check if we have the winning data for this draw
        draw_data = self._check_draw_in_database(ticket_data['lottery_type'], ticket_data['draw_number'])
        
        # Step 3: If we don't have data for this draw, fetch it
        if not draw_data:
            logger.info(f"Draw {ticket_data['draw_number']} for {ticket_data['lottery_type']} not found in database, fetching...")
            draw_data = self._fetch_draw_information(ticket_data['lottery_type'], ticket_data['draw_number'], ticket_data.get('draw_date'))
            
            # Step 4: Save the new draw information to our database
            if draw_data and draw_data.get('success'):
                self._save_draw_to_database(draw_data)
        
        # Step 5: Compare the ticket against the draw results
        if draw_data and draw_data.get('success'):
            comparison_result = self._compare_ticket_to_results(ticket_data, draw_data)
            return {
                'success': True,
                'ticket_data': ticket_data,
                'draw_data': draw_data,
                'comparison': comparison_result
            }
        else:
            logger.error(f"Unable to verify ticket against draw results")
            return {
                'success': False,
                'ticket_data': ticket_data,
                'error': 'Unable to verify ticket against official draw results'
            }

    def _extract_ticket_information(self, image_path: str) -> Dict[str, Any]:
        """
        Use Google Gemini 2.5 Pro OCR to extract information from ticket image
        
        Args:
            image_path: Path to the ticket image file
        
        Returns:
            Dictionary with extracted ticket details
        """
        # Check if we have the required API key
        if not self.has_gemini_api_key:
            logger.error("Gemini API key not available for OCR processing")
            return {'success': False, 'error': 'OCR service unavailable'}
        
        try:
            # Read and encode the image for API request
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Log API usage
            self._log_api_request('gemini_ocr')
            self.api_requests['gemini_ocr'] += 1
            
            # Construct the API request URL
            api_key = os.environ.get('GEMINI_API_KEY')
            model = "gemini-1.5-pro-latest"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            # Create the request payload with the analyze prompt
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": "Analyze this South African lottery ticket and extract the following information:\n"
                                        "1. Lottery Type (e.g., Lottery, Powerball, Daily Lottery)\n"
                                        "2. Draw Number\n"
                                        "3. Draw Date\n"
                                        "4. Ticket Numbers (the player's selected numbers)\n"
                                        "5. Any bonus or Powerball number\n\n"
                                        "Return ONLY a JSON object with these fields: "
                                        "lottery_type, draw_number, draw_date (YYYY-MM-DD format), "
                                        "player_numbers (as string array with leading zeros where necessary), "
                                        "bonus_number (if applicable)."
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "topP": 0.8,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "application/json"
                }
            }
            
            # Make API request
            response = requests.post(url, json=payload, timeout=30)
            
            # Process the response
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract text from response
                if "candidates" in response_data and response_data["candidates"]:
                    candidate = response_data["candidates"][0]
                    
                    if "content" in candidate and candidate["content"]["parts"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                text = part["text"]
                                
                                # Extract JSON from the response text
                                try:
                                    # Handle markdown code blocks if present
                                    if "```json" in text:
                                        json_start = text.find("```json") + 7
                                        json_end = text.find("```", json_start)
                                        json_str = text[json_start:json_end].strip()
                                    elif "```" in text:
                                        json_start = text.find("```") + 3
                                        json_end = text.find("```", json_start)
                                        json_str = text[json_start:json_end].strip()
                                    else:
                                        json_str = text
                                    
                                    # Parse the JSON
                                    result = json.loads(json_str)
                                    
                                    # Add success flag if not present
                                    result['success'] = True
                                    
                                    # Ensure numbers are properly formatted with leading zeros
                                    if 'player_numbers' in result:
                                        result['player_numbers'] = [str(num).zfill(2) for num in result['player_numbers']]
                                    
                                    # Convert bonus_number to bonus_numbers list if needed
                                    if 'bonus_number' in result and 'bonus_numbers' not in result:
                                        bonus = result.pop('bonus_number', None)
                                        if bonus:
                                            result['bonus_numbers'] = [str(bonus).zfill(2)]
                                        else:
                                            result['bonus_numbers'] = []
                                    
                                    logger.info(f"Successfully extracted ticket information: {result}")
                                    return result
                                except json.JSONDecodeError as e:
                                    error_msg = f"Failed to parse JSON from Gemini response: {str(e)}"
                                    logger.error(error_msg)
                                    return {'success': False, 'error': error_msg}
            
            # If we got here, the API request failed or the response format was unexpected
            error_msg = f"Failed to extract data from Gemini API response: {response.text if response.status_code == 200 else f'Status {response.status_code}'}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
        except Exception as e:
            logger.error(f"Error extracting ticket information: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _check_draw_in_database(self, lottery_type: str, draw_number: str) -> Optional[Dict[str, Any]]:
        """
        Check if the draw information exists in our database
        
        Args:
            lottery_type: Type of lottery game
            draw_number: Draw number identifier
        
        Returns:
            Draw data if found, None otherwise
        """
        try:
            # Normalize lottery type for consistent database lookup
            normalized_type = self._normalize_lottery_type(lottery_type)
            
            # Query database for this draw
            result = LotteryResult.query.filter_by(
                lottery_type=normalized_type,
                draw_number=draw_number
            ).first()
            
            if not result:
                logger.info(f"Draw {draw_number} for {normalized_type} not found in database")
                return None
            
            logger.info(f"Found draw {draw_number} for {normalized_type} in database")
            
            # Convert database record to dictionary
            draw_data = {
                'success': True,
                'lottery_type': result.lottery_type,
                'draw_number': result.draw_number,
                'draw_date': result.draw_date.strftime('%Y-%m-%d') if result.draw_date else None,
                'numbers': json.loads(result.numbers) if result.numbers else [],
                'bonus_numbers': json.loads(result.bonus_numbers) if result.bonus_numbers else []
            }
            
            return draw_data
            
        except Exception as e:
            logger.error(f"Error checking draw in database: {str(e)}")
            return None

    def _fetch_draw_information(self, lottery_type: str, draw_number: str, draw_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Use OpenAI to fetch official draw information when not in our database
        
        Args:
            lottery_type: Type of lottery game
            draw_number: Draw number identifier
            draw_date: Optional draw date if known
        
        Returns:
            Dictionary with draw information
        """
        # Check if we have the required API key
        if not self.has_openai_api_key:
            logger.error("OpenAI API key not available for draw verification")
            return {'success': False, 'error': 'Verification service unavailable'}
        
        try:
            # Prepare the OpenAI API request
            api_key = os.environ.get('OPENAI_API_KEY')
            
            # Create the prompt for OpenAI
            date_info = f" from date {draw_date}" if draw_date else ""
            user_prompt = (
                f"I need the official results for South African {lottery_type} draw #{draw_number}{date_info}. "
                f"Please provide the draw date, winning numbers, and bonus/powerball number if applicable. "
                f"Return the information in this JSON format only:\n"
                f"{{'lottery_type': 'Lottery/PowerBall/etc', 'draw_number': '1234', 'draw_date': 'YYYY-MM-DD', "
                f"'numbers': ['01', '05', '23', etc], 'bonus_numbers': ['12']}}"
            )
            
            # Import OpenAI library
            import openai
            from openai import OpenAI
            
            # Create OpenAI client and make request
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",  # Use the most capable model for accurate results
                messages=[
                    {"role": "system", "content": "You are a specialized lottery information retrieval system that provides accurate and official South African lottery draw results. Always format numbers with leading zeros where needed (e.g., '01' instead of '1')."},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=500
            )
            
            # Log API usage
            self._log_api_request('openai_verification')
            self.api_requests['openai_verification'] += 1
            
            # Process the response
            if response and response.choices and response.choices[0].message:
                # Get the response content
                result_text = response.choices[0].message.content
                
                try:
                    # Parse the JSON response - ensure we have a valid string
                    if result_text and isinstance(result_text, str):
                        verified_data = json.loads(result_text)
                    else:
                        logger.error(f"Invalid response format from OpenAI: {result_text}")
                        return {'success': False, 'error': "Invalid response format from verification service"}
                    
                    # Add success flag and source
                    verified_data['success'] = True
                    verified_data['source'] = 'openai'
                    
                    # Normalize the lottery type
                    verified_data['lottery_type'] = self._normalize_lottery_type(verified_data.get('lottery_type', lottery_type))
                    
                    # Ensure numbers are properly formatted as strings with leading zeros
                    if 'numbers' in verified_data:
                        verified_data['numbers'] = [str(num).zfill(2) for num in verified_data['numbers']]
                    
                    if 'bonus_numbers' in verified_data:
                        verified_data['bonus_numbers'] = [str(num).zfill(2) for num in verified_data['bonus_numbers']]
                    
                    logger.info(f"Successfully verified draw information from OpenAI API: {verified_data}")
                    return verified_data
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing OpenAI response: {str(e)}, Response: {result_text}")
                    return {'success': False, 'error': f"Invalid response format from verification service"}
            
            # If we get here, something went wrong with the API call
            logger.error(f"Unexpected response format from OpenAI API")
            return {'success': False, 'error': "Failed to verify draw information"}
            
        except Exception as e:
            logger.error(f"Error fetching draw information: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _save_draw_to_database(self, draw_data: Dict[str, Any]) -> bool:
        """
        Save newly discovered draw information to the database
        
        Args:
            draw_data: Dictionary with draw information
        
        Returns:
            Success flag
        """
        try:
            # Create new database record
            new_draw = LotteryResult()
            new_draw.lottery_type = draw_data['lottery_type']
            new_draw.draw_number = draw_data['draw_number']
            
            # Convert date string to datetime
            if draw_data.get('draw_date'):
                try:
                    new_draw.draw_date = datetime.strptime(draw_data['draw_date'], '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Invalid date format for draw date: {draw_data['draw_date']}")
                    new_draw.draw_date = datetime.now()
            else:
                new_draw.draw_date = datetime.now()
            
            # Store numbers as JSON strings
            new_draw.numbers = json.dumps(draw_data['numbers'])
            new_draw.bonus_numbers = json.dumps(draw_data.get('bonus_numbers', []))
            
            # Add source information
            new_draw.source_url = 'api_verification'
            new_draw.ocr_provider = draw_data.get('source', 'api')
            
            # Save to database
            db.session.add(new_draw)
            db.session.commit()
            
            logger.info(f"Successfully saved draw {draw_data['draw_number']} for {draw_data['lottery_type']} to database")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error saving draw information: {str(e)}")
            db.session.rollback()
            return False
        except Exception as e:
            logger.error(f"Error saving draw information: {str(e)}")
            db.session.rollback()
            return False

    def _compare_ticket_to_results(self, ticket_data: Dict[str, Any], draw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare ticket numbers to draw results and calculate winnings
        
        Args:
            ticket_data: Extracted ticket information
            draw_data: Official draw information
        
        Returns:
            Comparison results with winning status
        """
        try:
            # Get normalized lottery type
            lottery_type = self._normalize_lottery_type(
                ticket_data.get('lottery_type', draw_data.get('lottery_type', ''))
            )
            
            # Handle player numbers (ensure proper formatting)
            player_numbers = []
            if 'player_numbers' in ticket_data and ticket_data['player_numbers']:
                player_numbers = ticket_data['player_numbers']
            elif 'ticket_numbers' in ticket_data and ticket_data['ticket_numbers']:
                player_numbers = ticket_data['ticket_numbers']
                
            # Standardize number formats (with leading zeros)
            player_numbers = [str(num).zfill(2) for num in player_numbers]
            
            # Handle winning numbers from draw data
            winning_numbers = [str(num).zfill(2) for num in draw_data.get('numbers', [])]
            
            # Handle bonus/powerball numbers
            player_bonus = None
            if 'bonus_number' in ticket_data and ticket_data['bonus_number']:
                player_bonus = str(ticket_data['bonus_number']).zfill(2)
                
            winning_bonus = [str(num).zfill(2) for num in draw_data.get('bonus_numbers', [])]
            
            # Convert to sets for intersection operations
            player_numbers_set = set(player_numbers)
            winning_numbers_set = set(winning_numbers)
            
            # Find matching numbers
            matching_numbers = player_numbers_set.intersection(winning_numbers_set)
            has_bonus = (player_bonus in winning_bonus) if player_bonus and winning_bonus else False
            
            # Calculate prize tier based on lottery type and number of matches
            if 'Lottery' in lottery_type:
                result = self._calculate_lottery_prize(len(matching_numbers), has_bonus, lottery_type)
            elif 'Powerball' in lottery_type:
                result = self._calculate_powerball_prize(len(matching_numbers), has_bonus, lottery_type)
            elif 'Daily Lottery' in lottery_type:
                result = self._calculate_daily_lottery_prize(len(matching_numbers), lottery_type)
            else:
                result = {'prize_tier': 'Unknown', 'won': False}
            
            # Build comprehensive result data
            result.update({
                'success': True,
                'lottery_type': lottery_type,
                'draw_number': draw_data.get('draw_number', 'Unknown'),
                'draw_date': draw_data.get('draw_date', 'Unknown'),
                'ticket_numbers': player_numbers,
                'winning_numbers': winning_numbers,
                'matching_numbers': list(matching_numbers),
                'match_count': len(matching_numbers),
                'bonus_match': has_bonus,
                'bonus_number': player_bonus,
                'winning_bonus': winning_bonus[0] if winning_bonus else None,
                'draws_checked': 1
            })
            
            logger.info(f"Ticket comparison complete for {lottery_type}: {len(matching_numbers)} matches, bonus match: {has_bonus}")
            return result
            
        except Exception as e:
            logger.error(f"Error comparing ticket to results: {str(e)}")
            return {
                'success': False,
                'error': f"Error processing result comparison: {str(e)}",
                'won': False, 
                'prize_tier': 'Error'
            }

    def _calculate_lottery_prize(self, match_count: int, has_bonus: bool, lottery_type: str) -> Dict[str, Any]:
        """Calculate prize tier for Lottery game types"""
        if match_count == 6:
            return {'prize_tier': 'Division 1', 'won': True, 'description': 'Jackpot'}
        elif match_count == 5 and has_bonus:
            return {'prize_tier': 'Division 2', 'won': True, 'description': '5 numbers + bonus'}
        elif match_count == 5:
            return {'prize_tier': 'Division 3', 'won': True, 'description': '5 numbers'}
        elif match_count == 4 and has_bonus:
            return {'prize_tier': 'Division 4', 'won': True, 'description': '4 numbers + bonus'}
        elif match_count == 4:
            return {'prize_tier': 'Division 5', 'won': True, 'description': '4 numbers'}
        elif match_count == 3 and has_bonus:
            return {'prize_tier': 'Division 6', 'won': True, 'description': '3 numbers + bonus'}
        elif match_count == 3:
            return {'prize_tier': 'Division 7', 'won': True, 'description': '3 numbers'}
        elif match_count == 2 and has_bonus:
            return {'prize_tier': 'Division 8', 'won': True, 'description': '2 numbers + bonus'}
        else:
            return {'prize_tier': 'No Win', 'won': False, 'description': 'Not a winning ticket'}

    def _calculate_powerball_prize(self, match_count: int, has_powerball: bool, lottery_type: str) -> Dict[str, Any]:
        """Calculate prize tier for Powerball game types"""
        if match_count == 5 and has_powerball:
            return {'prize_tier': 'Division 1', 'won': True, 'description': 'Jackpot'}
        elif match_count == 5:
            return {'prize_tier': 'Division 2', 'won': True, 'description': '5 numbers'}
        elif match_count == 4 and has_powerball:
            return {'prize_tier': 'Division 3', 'won': True, 'description': '4 numbers + powerball'}
        elif match_count == 4:
            return {'prize_tier': 'Division 4', 'won': True, 'description': '4 numbers'}
        elif match_count == 3 and has_powerball:
            return {'prize_tier': 'Division 5', 'won': True, 'description': '3 numbers + powerball'}
        elif match_count == 3:
            return {'prize_tier': 'Division 6', 'won': True, 'description': '3 numbers'}
        elif match_count == 2 and has_powerball:
            return {'prize_tier': 'Division 7', 'won': True, 'description': '2 numbers + powerball'}
        elif match_count == 1 and has_powerball:
            return {'prize_tier': 'Division 8', 'won': True, 'description': '1 number + powerball'}
        elif has_powerball:
            return {'prize_tier': 'Division 9', 'won': True, 'description': 'Powerball only'}
        else:
            return {'prize_tier': 'No Win', 'won': False, 'description': 'Not a winning ticket'}

    def _calculate_daily_lottery_prize(self, match_count: int, lottery_type: str) -> Dict[str, Any]:
        """Calculate prize tier for Daily Lottery game"""
        if match_count == 5:
            return {'prize_tier': 'Division 1', 'won': True, 'description': 'Jackpot'}
        elif match_count == 4:
            return {'prize_tier': 'Division 2', 'won': True, 'description': '4 numbers'}
        elif match_count == 3:
            return {'prize_tier': 'Division 3', 'won': True, 'description': '3 numbers'}
        elif match_count == 2:
            return {'prize_tier': 'Division 4', 'won': True, 'description': '2 numbers'}
        else:
            return {'prize_tier': 'No Win', 'won': False, 'description': 'Not a winning ticket'}

    def _normalize_lottery_type(self, lottery_type: str) -> str:
        """
        Normalize lottery type names for consistent database handling
        
        Args:
            lottery_type: Raw lottery type string
        
        Returns:
            Normalized lottery type
        """
        if not lottery_type:
            return ""
            
        # Remove "Results" suffix if present
        cleaned = lottery_type.replace(" Results", "").strip()
        
        # Standardize common variations
        if "lotto" in cleaned.lower() and "plus" not in cleaned.lower() and "daily" not in cleaned.lower():
            return "Lottery"
        elif "lotto plus 1" in cleaned.lower():
            return "Lottery Plus 1"
        elif "lotto plus 2" in cleaned.lower():
            return "Lottery Plus 2"
        elif "powerball plus" in cleaned.lower():
            return "Powerball Plus"
        elif "powerball" in cleaned.lower():
            return "Powerball"
        elif "daily lotto" in cleaned.lower():
            return "Daily Lottery"
        
        return cleaned

    def _extract_ticket_information_with_anthropic(self, image_path: str) -> Dict[str, Any]:
        """
        Use Anthropic Claude Vision to extract information from lottery ticket image
        
        Args:
            image_path: Path to the ticket image file
            
        Returns:
            Dictionary with extracted ticket details
        """
        # Check if Anthropic API key is available
        if not self.has_anthropic_api_key:
            logger.error("Anthropic API key not available for Claude Vision processing")
            return {'success': False, 'error': 'Claude Vision service unavailable'}
            
        try:
            # Import necessary functions from ocr_processor
            from ocr_processor import get_anthropic_client
            import base64
            from datetime import datetime
            
            # Log API usage
            self._log_api_request('anthropic_ocr')
            self.api_requests['anthropic_ocr'] += 1
            
            # Read and encode the image
            with open(image_path, 'rb') as img_file:
                base64_content = base64.b64encode(img_file.read()).decode('utf-8')
                
            # Get Anthropic client
            client = get_anthropic_client()
            if not client:
                logger.error("Failed to initialize Claude client")
                return {'success': False, 'error': 'Claude Vision client initialization failed'}
                
            # System prompt for ticket analysis
            system_prompt = """You are an expert in analyzing South African lottery tickets.
Extract the following information with high precision:
1. Lottery Type (e.g., Lottery, Powerball, Daily Lottery)
2. Draw Number (the numeric identifier of the draw)
3. Draw Date (in YYYY-MM-DD format)
4. Numbers selected by the player (the main numbers on the ticket)
5. Any bonus or Powerball numbers (if applicable)

Important naming conventions:
- Always use "Lottery" instead of "Lotto"
- "Powerball" is one word (not Power-ball or Power Ball)
- For Lottery Plus games, use "Lottery Plus 1" and "Lottery Plus 2"
- For Daily Lottery, ensure it's "Daily Lottery" not "Daily Lotto"

Return only a clean JSON object with these fields:
{
  "lottery_type": "string", 
  "draw_number": "string", 
  "draw_date": "YYYY-MM-DD",
  "player_numbers": ["01", "02", ...],
  "bonus_numbers": ["01"] or []
}

Ensure all numbers use 2-digit format with leading zeros (e.g., "01" not "1").
For Daily Lottery, bonus_numbers should be an empty array.
"""
            
            # Process with Claude Vision
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_content
                                }
                            },
                            {
                                "type": "text",
                                "text": "Analyze this South African lottery ticket and extract the key information as JSON."
                            }
                        ]
                    }
                ]
            )
            
            # Extract the response content
            content = response.content[0].text if response and response.content else ""
            
            # Parse the JSON from the response
            try:
                # Extract JSON if enclosed in code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                else:
                    # If no code blocks, try to parse the whole text
                    json_str = content
                
                # Parse the JSON
                result = json.loads(json_str)
                
                # Add success flag
                result['success'] = True
                
                # Standardize the format of player numbers
                if 'player_numbers' in result:
                    result['player_numbers'] = [str(num).zfill(2) for num in result['player_numbers']]
                else:
                    result['player_numbers'] = []
                
                # Standardize the format of bonus numbers
                if 'bonus_number' in result and 'bonus_numbers' not in result:
                    bonus = result.pop('bonus_number', None)
                    if bonus:
                        result['bonus_numbers'] = [str(bonus).zfill(2)]
                    else:
                        result['bonus_numbers'] = []
                elif 'bonus_numbers' not in result:
                    result['bonus_numbers'] = []
                else:
                    result['bonus_numbers'] = [str(num).zfill(2) for num in result['bonus_numbers']]
                
                # Normalize lottery type
                if 'lottery_type' in result:
                    result['lottery_type'] = self._normalize_lottery_type(result['lottery_type'])
                
                logger.info(f"Successfully extracted ticket information with Claude Vision: {result}")
                return result
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON from Claude response: {str(e)}"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f"Error extracting ticket information with Claude Vision: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def _log_api_request(self, api_type: str) -> None:
        """
        Log API request for tracking and billing purposes
        
        Args:
            api_type: Type of API request (e.g., 'gemini_ocr', 'openai_verification', 'anthropic_ocr')
        """
        try:
            # Determine service based on api_type
            service = None
            if api_type == 'anthropic_ocr':
                service = 'anthropic'
            elif api_type == 'gemini_ocr':
                service = 'google_gemini'
            elif api_type == 'openai_verification':
                service = 'openai'
            else:
                service = api_type.split('_')[0]
                
            # Use the existing APIRequestLog.log_request method
            APIRequestLog.log_request(
                service=service,
                endpoint=api_type.split('_')[1] if '_' in api_type else api_type,  # 'ocr' or 'verification'
                status='success'
            )
            
        except Exception as e:
            logger.error(f"Error logging API request: {str(e)}")


# Utility function to create a scanner instance
def get_ticket_scanner():
    """Create and return a configured ticket scanner instance"""
    return TicketScanner()


# Process ticket image function used by main.py
def process_ticket_image(image_data, lottery_type='', draw_number=None, file_extension='.jpeg'):
    """
    Process a ticket image from binary data
    
    Args:
        image_data: Binary image data
        lottery_type: Optional lottery type if known
        draw_number: Optional draw number if known
        file_extension: File extension for the image
        
    Returns:
        Dictionary with processing results
    """
    import os
    import tempfile
    
    logger.info("Processing ticket image via process_ticket_image function")
    
    # Save the image data to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
    temp_file_path = temp_file.name
    
    try:
        # Write image data to the temporary file
        with open(temp_file_path, 'wb') as f:
            f.write(image_data)
        
        # Create a scanner instance
        scanner = TicketScanner()
        
        # Process the ticket image
        logger.info(f"Scanning ticket at path: {temp_file_path}")
        result = scanner.scan_ticket(temp_file_path)
        
        # Log the result summary
        if result and result.get('success', False):
            logger.info(f"Ticket scan successful: {result.get('lottery_type', 'Unknown')}, Draw #{result.get('draw_number', 'Unknown')}")
            if 'comparison' in result and result['comparison'].get('match_count', 0) > 0:
                logger.info(f"Match found! {result['comparison'].get('match_count', 0)} numbers matched, prize tier: {result['comparison'].get('prize_tier', 'Unknown')}")
        else:
            logger.error(f"Ticket scan failed: {result.get('error', 'Unknown error')}")
        
        return result
    except Exception as e:
        logger.error(f"Error processing ticket image: {str(e)}")
        return {
            'success': False,
            'error': f"Error processing ticket: {str(e)}"
        }
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except Exception as cleanup_error:
            logger.warning(f"Error cleaning up temporary file: {str(cleanup_error)}")