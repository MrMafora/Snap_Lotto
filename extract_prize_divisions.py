"""
Extract comprehensive lottery prize division data from screenshots using Google Gemini 2.5 Pro
This script extracts detailed prize breakdowns including divisions, winners, and amounts
"""
import os
import json
import base64
import logging
from datetime import datetime
from main import app
from models import db, LotteryResult
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrizeDivisionExtractor:
    """Extract comprehensive prize division data from lottery screenshots"""
    
    def __init__(self):
        """Initialize Gemini client"""
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY_SNAP_LOTTERY environment variable must be set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
    def encode_image(self, image_path):
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def create_extraction_prompt(self):
        """Create comprehensive prompt for prize division extraction"""
        return """
Extract comprehensive lottery prize division data from this screenshot. Analyze every visible detail and return a complete JSON structure.

Required JSON format:
{
    "lottery_type": "LOTTO|LOTTO PLUS 1|LOTTO PLUS 2|POWERBALL|POWERBALL PLUS|DAILY LOTTO",
    "draw_number": 2547,
    "draw_date": "2025-06-04",
    "main_numbers": [8, 24, 32, 34, 36, 52],
    "bonus_numbers": [26],
    "divisions": [
        {
            "division": 1,
            "match_type": "6 numbers",
            "winners": 0,
            "prize_amount": 0.00,
            "description": "Match all 6 main numbers"
        },
        {
            "division": 2,
            "match_type": "5 numbers + bonus",
            "winners": 2,
            "prize_amount": 45678.90,
            "description": "Match 5 main numbers plus bonus ball"
        }
    ],
    "rollover_amount": 15000000.00,
    "next_jackpot": 18000000.00,
    "total_pool_size": 25000000.00,
    "total_sales": 35000000.00,
    "total_winners": 1234,
    "total_prize_pool": 12500000.00
}

CRITICAL EXTRACTION RULES:
1. Extract ALL visible prize divisions with exact winner counts and prize amounts
2. Include rollover amounts, next jackpot estimates, and pool sizes if visible
3. Capture total winners and total prize pool information
4. For divisions with 0 winners, set prize_amount to 0.00
5. All monetary amounts should be numeric (not strings)
6. Use exact lottery type names as shown in the image
7. Extract draw number and date precisely as displayed
8. Include bonus numbers array even if empty []

Return ONLY the JSON object, no additional text or explanations.
"""

    def extract_prize_data(self, image_path):
        """Extract comprehensive prize division data from lottery screenshot"""
        try:
            # Encode image
            base64_image = self.encode_image(image_path)
            
            # Create prompt
            prompt = self.create_extraction_prompt()
            
            # Prepare image for Gemini
            image_data = {
                'mime_type': 'image/png',
                'data': base64_image
            }
            
            logger.info(f"Extracting prize data from: {image_path}")
            
            # Generate content with Gemini
            response = self.model.generate_content([prompt, image_data])
            
            if not response or not response.text:
                logger.error("No response from Gemini API")
                return None
                
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
                
            extracted_data = json.loads(response_text)
            logger.info(f"Successfully extracted prize data for {extracted_data.get('lottery_type')} Draw {extracted_data.get('draw_number')}")
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return None
        except Exception as e:
            logger.error(f"Error extracting prize data from {image_path}: {e}")
            return None
    
    def save_prize_data(self, extracted_data):
        """Save extracted prize division data to database"""
        try:
            # Find existing lottery result
            lottery_result = LotteryResult.query.filter_by(
                lottery_type=extracted_data['lottery_type'],
                draw_number=extracted_data['draw_number']
            ).first()
            
            if not lottery_result:
                logger.warning(f"No existing lottery result found for {extracted_data['lottery_type']} Draw {extracted_data['draw_number']}")
                return False
            
            # Update with prize division data
            lottery_result.divisions = json.dumps(extracted_data.get('divisions', []))
            lottery_result.rollover_amount = extracted_data.get('rollover_amount')
            lottery_result.next_jackpot = extracted_data.get('next_jackpot') 
            lottery_result.total_pool_size = extracted_data.get('total_pool_size')
            lottery_result.total_sales = extracted_data.get('total_sales')
            
            db.session.commit()
            logger.info(f"Successfully saved prize data for {extracted_data['lottery_type']} Draw {extracted_data['draw_number']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving prize data: {e}")
            db.session.rollback()
            return False
    
    def process_image(self, image_path):
        """Process a single lottery screenshot for prize division data"""
        extracted_data = self.extract_prize_data(image_path)
        if extracted_data:
            return self.save_prize_data(extracted_data)
        return False

def extract_all_prize_divisions():
    """Extract prize divisions from all available lottery screenshots"""
    extractor = PrizeDivisionExtractor()
    
    # Define image files with complete prize division data
    image_files = [
        'attached_assets/20250606_171929_lotto.png',
        'attached_assets/20250606_171942_lotto_plus_1_results.png', 
        'attached_assets/20250606_171954_lotto_plus_2_results.png',
        'attached_assets/20250606_172007_powerball.png',
        'attached_assets/20250606_172018_powerball_plus.png',
        'attached_assets/20250606_172030_daily_lotto.png'
    ]
    
    successful_extractions = 0
    
    with app.app_context():
        for image_file in image_files:
            if os.path.exists(image_file):
                logger.info(f"Processing {image_file}")
                if extractor.process_image(image_file):
                    successful_extractions += 1
                else:
                    logger.error(f"Failed to process {image_file}")
            else:
                logger.warning(f"Image file not found: {image_file}")
    
    logger.info(f"Successfully extracted prize divisions from {successful_extractions}/{len(image_files)} images")
    return successful_extractions

if __name__ == "__main__":
    extract_all_prize_divisions()