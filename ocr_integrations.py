"""
OCR Integration Module for Multi-Model Lottery Ticket Processing

This module provides integration with Google Gemini and OpenAI models for:
1. OCR processing of lottery ticket images
2. Verification of lottery draw results
3. Consistent formatting and storage of data
"""

import os
import json
import base64
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models
from models import db, LotteryResult, APIRequestLog as ApiRequestLog

class GeminiIntegration:
    """Integration with Google Gemini API for OCR and lottery ticket processing"""
    
    def __init__(self):
        """Initialize the Gemini API client with API key and configuration"""
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-1.5-pro-latest"  # Using the latest model for best results
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        logger.info(f"Gemini Integration initialized. API key available: {bool(self.api_key)}")
        
    def process_lottery_ticket(self, image_path: str) -> Dict[str, Any]:
        """
        Process a lottery ticket image using Gemini Vision capabilities
        
        Args:
            image_path: Path to the lottery ticket image
            
        Returns:
            Dictionary with extracted ticket information
        """
        if not self.api_key:
            logger.error("Gemini API key not available")
            return {"success": False, "error": "Gemini API key not configured"}
        
        try:
            # Read and encode the image
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Define the prompt for lottery ticket processing
            prompt = {
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
                    "topK": 10,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "application/json"
                }
            }
            
            # Make the API request to Gemini
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            response = self._make_request(url, json=prompt)
            
            # Process the response
            extracted_data = self._process_gemini_response(response)
            
            # Log the API request
            self._log_api_request(
                model=self.model,
                endpoint="generateContent",
                prompt_tokens=response.get("promptTokenCount", 0),
                completion_tokens=response.get("completionTokenCount", 0),
                status="success" if extracted_data.get("success") else "error",
                error_message=extracted_data.get("error")
            )
            
            return extracted_data
            
        except Exception as e:
            error_msg = f"Error processing ticket with Gemini: {str(e)}"
            logger.error(error_msg)
            self._log_api_request(
                model=self.model,
                endpoint="generateContent",
                status="error",
                error_message=error_msg
            )
            return {"success": False, "error": error_msg}
    
    def verify_lottery_results(self, lottery_type: str, draw_number: str, draw_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify lottery results using Gemini API
        
        Args:
            lottery_type: Type of lottery game
            draw_number: Draw number to verify
            draw_date: Optional draw date if known
            
        Returns:
            Dictionary with verified lottery results
        """
        if not self.api_key:
            logger.error("Gemini API key not available")
            return {"success": False, "error": "Gemini API key not configured"}
        
        try:
            # Create the prompt for lottery result verification
            date_info = f" from {draw_date}" if draw_date else ""
            prompt = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"Find the official results for South African {lottery_type} draw #{draw_number}{date_info}.\n\n"
                                        f"Search for and provide the following information from the official South African National Lottery website:\n"
                                        f"1. The exact draw date (in YYYY-MM-DD format)\n"
                                        f"2. The winning numbers drawn\n"
                                        f"3. Any bonus or Powerball number\n\n"
                                        f"Return ONLY a JSON object with these fields:\n"
                                        f"lottery_type, draw_number, draw_date, numbers (as string array with leading zeros), bonus_numbers (as string array)"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "topP": 0.8,
                    "topK": 10,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "application/json"
                }
            }
            
            # Make the API request to Gemini
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            response = self._make_request(url, json=prompt)
            
            # Process the response
            verified_data = self._process_gemini_response(response)
            
            # Normalize lottery type for consistency
            if verified_data.get("success"):
                verified_data["lottery_type"] = self._normalize_lottery_type(verified_data.get("lottery_type", lottery_type))
            
            # Log the API request
            self._log_api_request(
                model=self.model,
                endpoint="generateContent",
                prompt_tokens=response.get("promptTokenCount", 0),
                completion_tokens=response.get("completionTokenCount", 0),
                status="success" if verified_data.get("success") else "error",
                error_message=verified_data.get("error"),
                lottery_type=lottery_type
            )
            
            return verified_data
            
        except Exception as e:
            error_msg = f"Error verifying lottery results with Gemini: {str(e)}"
            logger.error(error_msg)
            self._log_api_request(
                model=self.model,
                endpoint="generateContent",
                status="error",
                error_message=error_msg,
                lottery_type=lottery_type
            )
            return {"success": False, "error": error_msg}
    
    def _make_request(self, url: str, json: Dict, retries: int = 0) -> Dict:
        """Make request to Gemini API with retry logic"""
        try:
            start_time = time.time()
            response = requests.post(url, json=json, timeout=30)
            duration_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                # Add duration and token counts for logging
                result["duration_ms"] = duration_ms
                return result
            else:
                if retries < self.max_retries:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** retries)
                    logger.warning(f"Gemini API request failed with status {response.status_code}. Retrying in {delay}s...")
                    time.sleep(delay)
                    return self._make_request(url, json, retries + 1)
                else:
                    error_text = f"Gemini API request failed after {self.max_retries} retries: {response.text}"
                    logger.error(error_text)
                    return {"error": error_text, "status_code": response.status_code}
                    
        except requests.exceptions.RequestException as e:
            if retries < self.max_retries:
                # Exponential backoff
                delay = self.retry_delay * (2 ** retries)
                logger.warning(f"Gemini API request failed with error: {str(e)}. Retrying in {delay}s...")
                time.sleep(delay)
                return self._make_request(url, json, retries + 1)
            else:
                error_text = f"Gemini API request failed after {self.max_retries} retries: {str(e)}"
                logger.error(error_text)
                return {"error": error_text}
    
    def _process_gemini_response(self, response: Dict) -> Dict[str, Any]:
        """Process and validate the response from Gemini API"""
        try:
            # Check for errors in the response
            if "error" in response:
                return {"success": False, "error": response["error"]}
            
            # Extract the JSON content from the response
            if "candidates" in response and response["candidates"]:
                candidate = response["candidates"][0]
                
                if "content" in candidate and candidate["content"]["parts"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            # Try to extract JSON from the text response
                            try:
                                # The response might have ```json wrapping or other text
                                text = part["text"]
                                json_start = text.find("{")
                                json_end = text.rfind("}") + 1
                                
                                if json_start >= 0 and json_end > json_start:
                                    json_text = text[json_start:json_end]
                                    result = json.loads(json_text)
                                    
                                    # Validate the required fields
                                    required_fields = ["lottery_type", "draw_number"]
                                    if all(field in result for field in required_fields):
                                        # Ensure numbers are in the correct format (strings with leading zeros)
                                        if "numbers" in result and isinstance(result["numbers"], list):
                                            result["numbers"] = [str(num).zfill(2) for num in result["numbers"]]
                                        
                                        if "bonus_numbers" in result and isinstance(result["bonus_numbers"], list):
                                            result["bonus_numbers"] = [str(num).zfill(2) for num in result["bonus_numbers"]]
                                        elif "bonus_number" in result:
                                            # Handle case where bonus is provided as a single value
                                            bonus = result.pop("bonus_number")
                                            if bonus:
                                                result["bonus_numbers"] = [str(bonus).zfill(2)]
                                            else:
                                                result["bonus_numbers"] = []
                                        
                                        result["success"] = True
                                        return result
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON from Gemini response: {str(e)}")
                                return {"success": False, "error": f"Invalid JSON format in response: {str(e)}"}
            
            # If we got here, the response didn't contain valid data
            logger.error(f"Unexpected Gemini response format: {response}")
            return {"success": False, "error": "Unable to extract valid data from Gemini response"}
            
        except Exception as e:
            logger.error(f"Error processing Gemini response: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _log_api_request(self, model: str, endpoint: str, prompt_tokens: int = None, 
                        completion_tokens: int = None, status: str = "success", 
                        duration_ms: int = None, error_message: str = None, 
                        request_id: str = None, screenshot_id: int = None, 
                        lottery_type: str = None):
        """Log API request to database"""
        try:
            ApiRequestLog.log_request(
                service="gemini",
                endpoint=endpoint,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                status=status,
                duration_ms=duration_ms,
                error_message=error_message,
                request_id=request_id,
                screenshot_id=screenshot_id,
                lottery_type=lottery_type
            )
        except Exception as e:
            logger.error(f"Failed to log API request: {str(e)}")
    
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


class OpenAIIntegration:
    """Integration with OpenAI API for lottery result verification"""
    
    def __init__(self):
        """Initialize the OpenAI API client with API key and configuration"""
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o"  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        logger.info(f"OpenAI Integration initialized. API key available: {bool(self.api_key)}")
    
    def verify_lottery_results(self, lottery_type: str, draw_number: str, draw_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify lottery results using OpenAI API
        
        Args:
            lottery_type: Type of lottery game
            draw_number: Draw number to verify
            draw_date: Optional draw date if known
            
        Returns:
            Dictionary with verified lottery results
        """
        if not self.api_key:
            logger.error("OpenAI API key not available")
            return {"success": False, "error": "OpenAI API key not configured"}
        
        try:
            # Create the prompt for lottery result verification
            date_info = f" from {draw_date}" if draw_date else ""
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            body = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert on South African lottery results. Your task is to find and provide official lottery results in a structured format."
                    },
                    {
                        "role": "user",
                        "content": f"Find the official results for South African {lottery_type} draw #{draw_number}{date_info}.\n\n"
                                   f"Search for and provide the following information from the official South African National Lottery website:\n"
                                   f"1. The exact draw date (in YYYY-MM-DD format)\n"
                                   f"2. The winning numbers drawn\n"
                                   f"3. Any bonus or Powerball number\n\n"
                                   f"Return ONLY a JSON object with these fields:\n"
                                   f"lottery_type, draw_number, draw_date, numbers (as string array with leading zeros), bonus_numbers (as string array)"
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 2048
            }
            
            # Make the API request to OpenAI
            url = f"{self.base_url}/chat/completions"
            response = self._make_request(url, headers=headers, json=body)
            
            # Process the response
            verified_data = self._process_openai_response(response)
            
            # Normalize lottery type for consistency
            if verified_data.get("success"):
                verified_data["lottery_type"] = self._normalize_lottery_type(verified_data.get("lottery_type", lottery_type))
                verified_data["source"] = "openai"
            
            # Log the API request
            usage = response.get("usage", {})
            self._log_api_request(
                model=self.model,
                endpoint="chat/completions",
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                status="success" if verified_data.get("success") else "error",
                error_message=verified_data.get("error"),
                lottery_type=lottery_type
            )
            
            return verified_data
            
        except Exception as e:
            error_msg = f"Error verifying lottery results with OpenAI: {str(e)}"
            logger.error(error_msg)
            self._log_api_request(
                model=self.model,
                endpoint="chat/completions",
                status="error",
                error_message=error_msg,
                lottery_type=lottery_type
            )
            return {"success": False, "error": error_msg}
    
    def _make_request(self, url: str, headers: Dict, json: Dict, retries: int = 0) -> Dict:
        """Make request to OpenAI API with retry logic"""
        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=json, timeout=30)
            duration_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                # Add duration for logging
                result["duration_ms"] = duration_ms
                return result
            else:
                if retries < self.max_retries:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** retries)
                    logger.warning(f"OpenAI API request failed with status {response.status_code}. Retrying in {delay}s...")
                    time.sleep(delay)
                    return self._make_request(url, headers, json, retries + 1)
                else:
                    error_text = f"OpenAI API request failed after {self.max_retries} retries: {response.text}"
                    logger.error(error_text)
                    return {"error": error_text, "status_code": response.status_code}
                    
        except requests.exceptions.RequestException as e:
            if retries < self.max_retries:
                # Exponential backoff
                delay = self.retry_delay * (2 ** retries)
                logger.warning(f"OpenAI API request failed with error: {str(e)}. Retrying in {delay}s...")
                time.sleep(delay)
                return self._make_request(url, headers, json, retries + 1)
            else:
                error_text = f"OpenAI API request failed after {self.max_retries} retries: {str(e)}"
                logger.error(error_text)
                return {"error": error_text}
    
    def _process_openai_response(self, response: Dict) -> Dict[str, Any]:
        """Process and validate the response from OpenAI API"""
        try:
            # Check for errors in the response
            if "error" in response:
                return {"success": False, "error": response["error"]}
            
            # Extract the JSON content from the response
            if "choices" in response and response["choices"]:
                choice = response["choices"][0]
                
                if "message" in choice and "content" in choice["message"]:
                    # Parse the JSON response (OpenAI should return valid JSON with response_format)
                    try:
                        result = json.loads(choice["message"]["content"])
                        
                        # Validate the required fields
                        required_fields = ["lottery_type", "draw_number"]
                        if all(field in result for field in required_fields):
                            # Ensure numbers are in the correct format (strings with leading zeros)
                            if "numbers" in result and isinstance(result["numbers"], list):
                                result["numbers"] = [str(num).zfill(2) for num in result["numbers"]]
                            
                            if "bonus_numbers" in result and isinstance(result["bonus_numbers"], list):
                                result["bonus_numbers"] = [str(num).zfill(2) for num in result["bonus_numbers"]]
                            elif "bonus_number" in result:
                                # Handle case where bonus is provided as a single value
                                bonus = result.pop("bonus_number")
                                if bonus:
                                    result["bonus_numbers"] = [str(bonus).zfill(2)]
                                else:
                                    result["bonus_numbers"] = []
                            
                            result["success"] = True
                            return result
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON from OpenAI response: {str(e)}")
                        return {"success": False, "error": f"Invalid JSON format in response: {str(e)}"}
            
            # If we got here, the response didn't contain valid data
            logger.error(f"Unexpected OpenAI response format: {response}")
            return {"success": False, "error": "Unable to extract valid data from OpenAI response"}
            
        except Exception as e:
            logger.error(f"Error processing OpenAI response: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _log_api_request(self, model: str, endpoint: str, prompt_tokens: int = None, 
                        completion_tokens: int = None, status: str = "success", 
                        duration_ms: int = None, error_message: str = None, 
                        request_id: str = None, screenshot_id: int = None, 
                        lottery_type: str = None):
        """Log API request to database"""
        try:
            ApiRequestLog.log_request(
                service="openai",
                endpoint=endpoint,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                status=status,
                duration_ms=duration_ms,
                error_message=error_message,
                request_id=request_id,
                screenshot_id=screenshot_id,
                lottery_type=lottery_type
            )
        except Exception as e:
            logger.error(f"Failed to log API request: {str(e)}")
    
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


class EnhancedTicketScanner:
    """
    Enhanced ticket scanner that uses multiple models for lottery ticket processing
    This is the main class that should be used in the application
    """
    
    def __init__(self):
        """Initialize the scanner with primary and fallback integrations"""
        self.gemini = GeminiIntegration()
        self.openai = OpenAIIntegration()
        self.has_gemini = bool(os.environ.get('GEMINI_API_KEY'))
        self.has_openai = bool(os.environ.get('OPENAI_API_KEY'))
        
        logger.info(f"Enhanced Ticket Scanner initialized. Gemini available: {self.has_gemini}, OpenAI available: {self.has_openai}")
    
    def process_ticket(self, image_path: str) -> Dict[str, Any]:
        """
        Process a lottery ticket image, extract information, and check results
        
        Args:
            image_path: Path to ticket image file
            
        Returns:
            Dictionary with ticket information and results
        """
        # Step 1: Extract ticket information from image
        ticket_data = self._extract_ticket_information(image_path)
        if not ticket_data or not ticket_data.get("success"):
            return {"success": False, "error": ticket_data.get("error", "Failed to extract ticket information")}
        
        # Step 2: Check if we have the winning data for this draw
        draw_data = self._check_draw_in_database(ticket_data["lottery_type"], ticket_data["draw_number"])
        
        # Step 3: If we don't have data for this draw, fetch it from external sources
        if not draw_data:
            draw_data = self._fetch_draw_information(
                ticket_data["lottery_type"], 
                ticket_data["draw_number"], 
                ticket_data.get("draw_date")
            )
            
            # Step 4: Save the new draw information to our database
            if draw_data and draw_data.get("success"):
                self._save_draw_to_database(draw_data)
        
        # Step 5: Compare the ticket against the draw results
        if draw_data and draw_data.get("success"):
            comparison_result = self._compare_ticket_to_results(ticket_data, draw_data)
            return {
                "success": True,
                "ticket_data": ticket_data,
                "draw_data": draw_data,
                "comparison": comparison_result
            }
        else:
            return {
                "success": False,
                "ticket_data": ticket_data,
                "error": draw_data.get("error", "Unable to verify ticket against draw results")
            }
    
    def _extract_ticket_information(self, image_path: str) -> Dict[str, Any]:
        """Extract information from a lottery ticket image"""
        # Try Gemini first if available
        if self.has_gemini:
            ticket_data = self.gemini.process_lottery_ticket(image_path)
            if ticket_data and ticket_data.get("success"):
                return ticket_data
        
        # Fallback to manual extraction placeholder
        logger.warning("Falling back to manual extraction - no valid OCR provider available")
        return {"success": False, "error": "No OCR provider available to process ticket"}
    
    def _check_draw_in_database(self, lottery_type: str, draw_number: str) -> Optional[Dict[str, Any]]:
        """Check if the draw information exists in our database"""
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
                "success": True,
                "lottery_type": result.lottery_type,
                "draw_number": result.draw_number,
                "draw_date": result.draw_date.strftime('%Y-%m-%d') if result.draw_date else None,
                "numbers": result.get_numbers_list(),
                "bonus_numbers": result.get_bonus_numbers_list()
            }
            
            return draw_data
            
        except Exception as e:
            logger.error(f"Error checking draw in database: {str(e)}")
            return None
    
    def _fetch_draw_information(self, lottery_type: str, draw_number: str, draw_date: Optional[str] = None) -> Dict[str, Any]:
        """Fetch draw information from external sources when not in our database"""
        # Try Gemini first if available
        if self.has_gemini:
            draw_data = self.gemini.verify_lottery_results(lottery_type, draw_number, draw_date)
            if draw_data and draw_data.get("success"):
                return draw_data
        
        # Try OpenAI as a fallback if available
        if self.has_openai:
            draw_data = self.openai.verify_lottery_results(lottery_type, draw_number, draw_date)
            if draw_data and draw_data.get("success"):
                return draw_data
        
        # If no integrations are available or successful
        logger.error("No available API integrations to verify lottery results")
        return {"success": False, "error": "Unable to verify lottery results - no API integrations available"}
    
    def _save_draw_to_database(self, draw_data: Dict[str, Any]) -> bool:
        """Save newly discovered draw information to the database"""
        try:
            # Check if the draw already exists (double check to prevent race conditions)
            existing = LotteryResult.query.filter_by(
                lottery_type=draw_data["lottery_type"],
                draw_number=draw_data["draw_number"]
            ).first()
            
            if existing:
                logger.info(f"Draw {draw_data['draw_number']} for {draw_data['lottery_type']} already exists in database")
                return True
            
            # Create new database record
            new_draw = LotteryResult()
            new_draw.lottery_type = draw_data["lottery_type"]
            new_draw.draw_number = draw_data["draw_number"]
            
            # Convert date string to datetime
            if draw_data.get("draw_date"):
                try:
                    new_draw.draw_date = datetime.strptime(draw_data["draw_date"], '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Invalid date format for draw date: {draw_data['draw_date']}")
                    new_draw.draw_date = datetime.now()
            else:
                new_draw.draw_date = datetime.now()
            
            # Store numbers as JSON strings
            new_draw.numbers = json.dumps(draw_data["numbers"])
            new_draw.bonus_numbers = json.dumps(draw_data.get("bonus_numbers", []))
            
            # Set source information
            new_draw.source_url = "api_verification"
            new_draw.ocr_provider = draw_data.get("source", "api")
            new_draw.ocr_model = "gemini-1.5-pro" if draw_data.get("source") == "gemini" else "gpt-4o"
            new_draw.ocr_timestamp = datetime.now()
            
            # Save to database
            db.session.add(new_draw)
            db.session.commit()
            
            logger.info(f"Successfully saved draw {draw_data['draw_number']} for {draw_data['lottery_type']} to database")
            return True
            
        except Exception as e:
            logger.error(f"Error saving draw information to database: {str(e)}")
            db.session.rollback()
            return False
    
    def _compare_ticket_to_results(self, ticket_data: Dict[str, Any], draw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare ticket numbers to draw results and calculate winnings"""
        try:
            # Extract the numbers
            ticket_numbers = set(ticket_data.get("player_numbers", []))
            winning_numbers = set(draw_data.get("numbers", []))
            bonus_numbers = set(draw_data.get("bonus_numbers", []))
            
            # Find matching numbers
            matching_numbers = ticket_numbers.intersection(winning_numbers)
            has_bonus = any(num in bonus_numbers for num in ticket_numbers)
            
            # Determine winning status based on lottery type
            lottery_type = draw_data.get("lottery_type", "")
            
            # Calculate prize tier based on lottery type and number of matches
            if "Lottery" in lottery_type:
                result = self._calculate_lottery_prize(len(matching_numbers), has_bonus, lottery_type)
            elif "Powerball" in lottery_type:
                result = self._calculate_powerball_prize(len(matching_numbers), has_bonus, lottery_type)
            elif "Daily Lottery" in lottery_type:
                result = self._calculate_daily_lottery_prize(len(matching_numbers), lottery_type)
            else:
                result = {"prize_tier": "Unknown", "won": False}
            
            # Add matching details to result
            result.update({
                "matching_numbers": list(matching_numbers),
                "bonus_match": has_bonus,
                "draws_checked": 1
            })
            
            logger.info(f"Ticket comparison complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error comparing ticket to results: {str(e)}")
            return {"error": str(e), "won": False, "prize_tier": "Error"}
    
    def _calculate_lottery_prize(self, match_count: int, has_bonus: bool, lottery_type: str) -> Dict[str, Any]:
        """Calculate prize tier for Lottery game types"""
        if match_count == 6:
            return {"prize_tier": "Division 1", "won": True, "description": "Jackpot"}
        elif match_count == 5 and has_bonus:
            return {"prize_tier": "Division 2", "won": True, "description": "5 numbers + bonus"}
        elif match_count == 5:
            return {"prize_tier": "Division 3", "won": True, "description": "5 numbers"}
        elif match_count == 4 and has_bonus:
            return {"prize_tier": "Division 4", "won": True, "description": "4 numbers + bonus"}
        elif match_count == 4:
            return {"prize_tier": "Division 5", "won": True, "description": "4 numbers"}
        elif match_count == 3 and has_bonus:
            return {"prize_tier": "Division 6", "won": True, "description": "3 numbers + bonus"}
        elif match_count == 3:
            return {"prize_tier": "Division 7", "won": True, "description": "3 numbers"}
        elif match_count == 2 and has_bonus:
            return {"prize_tier": "Division 8", "won": True, "description": "2 numbers + bonus"}
        else:
            return {"prize_tier": "No Win", "won": False, "description": "Not a winning ticket"}

    def _calculate_powerball_prize(self, match_count: int, has_powerball: bool, lottery_type: str) -> Dict[str, Any]:
        """Calculate prize tier for Powerball game types"""
        if match_count == 5 and has_powerball:
            return {"prize_tier": "Division 1", "won": True, "description": "Jackpot"}
        elif match_count == 5:
            return {"prize_tier": "Division 2", "won": True, "description": "5 numbers"}
        elif match_count == 4 and has_powerball:
            return {"prize_tier": "Division 3", "won": True, "description": "4 numbers + powerball"}
        elif match_count == 4:
            return {"prize_tier": "Division 4", "won": True, "description": "4 numbers"}
        elif match_count == 3 and has_powerball:
            return {"prize_tier": "Division 5", "won": True, "description": "3 numbers + powerball"}
        elif match_count == 3:
            return {"prize_tier": "Division 6", "won": True, "description": "3 numbers"}
        elif match_count == 2 and has_powerball:
            return {"prize_tier": "Division 7", "won": True, "description": "2 numbers + powerball"}
        elif match_count == 1 and has_powerball:
            return {"prize_tier": "Division 8", "won": True, "description": "1 number + powerball"}
        elif has_powerball:
            return {"prize_tier": "Division 9", "won": True, "description": "Powerball only"}
        else:
            return {"prize_tier": "No Win", "won": False, "description": "Not a winning ticket"}

    def _calculate_daily_lottery_prize(self, match_count: int, lottery_type: str) -> Dict[str, Any]:
        """Calculate prize tier for Daily Lottery game"""
        if match_count == 5:
            return {"prize_tier": "Division 1", "won": True, "description": "Jackpot"}
        elif match_count == 4:
            return {"prize_tier": "Division 2", "won": True, "description": "4 numbers"}
        elif match_count == 3:
            return {"prize_tier": "Division 3", "won": True, "description": "3 numbers"}
        elif match_count == 2:
            return {"prize_tier": "Division 4", "won": True, "description": "2 numbers"}
        else:
            return {"prize_tier": "No Win", "won": False, "description": "Not a winning ticket"}
    
    def _normalize_lottery_type(self, lottery_type: str) -> str:
        """Normalize lottery type names for consistency"""
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


# Helper function to get the scanner instance
def get_scanner():
    """Get a configured ticket scanner instance"""
    return EnhancedTicketScanner()