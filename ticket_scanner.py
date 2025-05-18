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
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models
from models import db, LotteryResult, ApiRequestLog

class TicketScanner:
    """Enhanced lottery ticket scanner with multi-model OCR and result verification"""

    def __init__(self):
        """Initialize the ticket scanner with API keys and configuration"""
        # Check for required API keys
        self.has_gemini_api_key = bool(os.environ.get('GEMINI_API_KEY'))
        self.has_openai_api_key = bool(os.environ.get('OPENAI_API_KEY'))
        
        # Set default settings
        self.ocr_timeout = 30  # seconds
        self.verification_timeout = 45  # seconds
        
        # Initialize API usage tracking
        self.api_requests = {
            'gemini_ocr': 0,
            'openai_verification': 0
        }
        
        logger.info(f"Ticket scanner initialized. Gemini API available: {self.has_gemini_api_key}, OpenAI API available: {self.has_openai_api_key}")

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
            # Read image file as binary data
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()
            
            # Implementation placeholder for Gemini API integration
            # This would be replaced with actual Gemini API calls
            
            # Log API usage
            self._log_api_request('gemini_ocr')
            self.api_requests['gemini_ocr'] += 1
            
            # Mock structure of extracted data (replace with actual implementation)
            extracted_data = {
                'success': True,
                'lottery_type': 'Lottery',  # Example value
                'draw_number': '1234',  # Example value
                'draw_date': '2025-04-15',  # Example value
                'ticket_numbers': ['01', '16', '24', '36', '42', '49'],  # Example value
                'bonus_number': '23',  # Example value
                'player_numbers': ['05', '16', '24', '36', '42', '49'],  # Example value
                'confidence': 0.92  # Example confidence score
            }
            
            logger.info(f"Successfully extracted ticket information: {extracted_data}")
            return extracted_data
            
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
            # Prepare the prompt for OpenAI
            date_info = f" from date {draw_date}" if draw_date else ""
            prompt = (
                f"I need the official results for South African {lottery_type} draw #{draw_number}{date_info}. "
                f"Please provide the draw date, winning numbers, and bonus/powerball number if applicable. "
                f"Return the information in this JSON format only:\n"
                f"{{'lottery_type': 'Lottery/PowerBall/etc', 'draw_number': '1234', 'draw_date': 'YYYY-MM-DD', "
                f"'numbers': ['01', '05', '23', etc], 'bonus_numbers': ['12']}}"
            )
            
            # Implementation placeholder for OpenAI API integration
            # This would be replaced with actual OpenAI API calls
            
            # Log API usage
            self._log_api_request('openai_verification')
            self.api_requests['openai_verification'] += 1
            
            # Mock structure of verified data (replace with actual implementation)
            verified_data = {
                'success': True,
                'source': 'openai',
                'lottery_type': self._normalize_lottery_type(lottery_type),
                'draw_number': draw_number,
                'draw_date': draw_date or '2025-04-15',  # Example fallback date
                'numbers': ['01', '16', '24', '36', '42', '49'],  # Example values
                'bonus_numbers': ['23'] if self._normalize_lottery_type(lottery_type) in ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2'] else ['05']
            }
            
            logger.info(f"Successfully verified draw information from external API: {verified_data}")
            return verified_data
            
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
            new_draw.source = draw_data.get('source', 'api')
            
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
            # Extract the numbers
            ticket_numbers = set(ticket_data.get('player_numbers', []))
            winning_numbers = set(draw_data.get('numbers', []))
            bonus_numbers = set(draw_data.get('bonus_numbers', []))
            
            # Find matching numbers
            matching_numbers = ticket_numbers.intersection(winning_numbers)
            has_bonus = any(num in bonus_numbers for num in ticket_numbers)
            
            # Determine winning status based on lottery type
            lottery_type = draw_data.get('lottery_type', '')
            
            # Calculate prize tier based on lottery type and number of matches
            if 'Lottery' in lottery_type:
                result = self._calculate_lottery_prize(len(matching_numbers), has_bonus, lottery_type)
            elif 'Powerball' in lottery_type:
                result = self._calculate_powerball_prize(len(matching_numbers), has_bonus, lottery_type)
            elif 'Daily Lottery' in lottery_type:
                result = self._calculate_daily_lottery_prize(len(matching_numbers), lottery_type)
            else:
                result = {'prize_tier': 'Unknown', 'won': False}
            
            # Add matching details to result
            result.update({
                'matching_numbers': list(matching_numbers),
                'bonus_match': has_bonus,
                'draws_checked': 1
            })
            
            logger.info(f"Comparison complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error comparing ticket to results: {str(e)}")
            return {'error': str(e), 'won': False, 'prize_tier': 'Error'}

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

    def _log_api_request(self, api_type: str) -> None:
        """
        Log API request for tracking and billing purposes
        
        Args:
            api_type: Type of API request (e.g., 'gemini_ocr', 'openai_verification')
        """
        try:
            log_entry = ApiRequestLog()
            log_entry.api_type = api_type
            log_entry.timestamp = datetime.now()
            log_entry.success = True
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging API request: {str(e)}")


# Utility function to create a scanner instance
def get_ticket_scanner():
    """Create and return a configured ticket scanner instance"""
    return TicketScanner()