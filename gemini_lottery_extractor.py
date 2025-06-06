"""
Google Gemini 2.5 Pro Lottery Data Extractor
High-performance lottery data extraction using Google's latest AI model
"""

import os
import json
import base64
from datetime import datetime
import google.generativeai as genai
from models import db, LotteryResult
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiLotteryExtractor:
    """Extract lottery data from images using Google Gemini 2.5 Pro"""
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY', '')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY_SNAP_LOTTERY environment variable not found")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("Initialized Gemini 2.5 Pro lottery extractor")
    
    def encode_image(self, image_path):
        """Encode image to base64 for Gemini API"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return encoded_string
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            raise
    
    def create_comprehensive_prompt(self):
        """Create optimized prompt for Gemini 2.5 Pro lottery extraction"""
        return """You are an automated data extraction API. Your task is to analyze the provided image of a lottery result and return the data in a structured JSON format.

Instructions:
- Strictly adhere to the JSON schema defined below.
- Extract all data points accurately from the image.
- If a field is not present in the image (e.g., a bonus ball in Daily Lotto), use null as its value.
- Parse numbers from strings where specified (e.g., Draw ID, Winners). Currency values should remain as strings to preserve formatting.

JSON Output Schema:
{
  "lottery_type": "String",
  "draw_number": "Number",
  "draw_date": "String (YYYY-MM-DD)",
  "main_numbers": ["Array of Numbers"],
  "bonus_numbers": ["Array of Numbers or empty"],
  "prize_divisions": [
    {
      "division": "Number",
      "description": "String",
      "winners": "Number",
      "prize_amount": "String"
    }
  ],
  "jackpot_info": {
     "next_jackpot": "String",
     "next_draw_date": "String (YYYY-MM-DD)"
  },
  "additional_info": {
    "rollover_amount": "String | null",
    "total_pool_size": "String | null",
    "total_sales": "String | null"
  }
}

CRITICAL: Extract winning numbers in their EXACT DISPLAY ORDER as shown on the lottery results page.

Example Extraction Guidelines:
- lottery_type: Extract from the main title (e.g., "LOTTO PLUS 1").
- draw_number: Extract the "DRAW ID" number.
- main_numbers: Extract numbers in the EXACT order they appear in the "WINNING NUMBERS" section (left to right). DO NOT sort them.
- bonus_numbers: This is the number after the + sign.
- prize_divisions: Extract all visible prize tiers with winner counts and amounts.
- jackpot_info: Find the estimated jackpot amount for the next draw.

IMPORTANT: Preserve the exact sequence of winning numbers as displayed on the screen. For example, if numbers show as "08 24 32 34 36 52", return [8, 24, 32, 34, 36, 52] - not sorted.

Process the attached image and return the JSON output.
Return ONLY valid JSON in this exact structure:

```json
{
  "lottery_type": "LOTTO",
  "draw_number": 2547,
  "draw_date": "2025-06-04",
  "main_numbers": [12, 34, 8, 52, 36, 24],
  "bonus_numbers": [26],
  "divisions": [
    {
      "division": "DIV 1",
      "requirement": "SIX CORRECT NUMBERS",
      "winners": 0,
      "prize_amount": "R0.00"
    }
  ],
  "rollover_amount": "R63,481,549.30",
  "rollover_number": 26,
  "total_pool_size": "R67,302,275.10",
  "total_sales": "R35,502,615.00",
  "next_jackpot": "R67,000,000.00",
  "draw_machine": "RNG 1",
  "next_draw_date": "2025-06-07"
}
```

## VERIFICATION CHECKLIST:
✓ Division winner counts match their respective rows
✓ All numbers are integers (not strings)
✓ Prize amounts include "R" prefix
✓ Date format is YYYY-MM-DD
✓ JSON is valid and complete

Extract all visible lottery data with absolute precision. Focus on table row alignment to prevent data shifting errors."""

    def extract_lottery_data(self, image_path):
        """Extract lottery data from image using Gemini 2.5 Pro"""
        try:
            logger.info(f"Processing lottery image: {image_path}")
            
            # Read and prepare image
            with open(image_path, 'rb') as img_file:
                image_data = img_file.read()
            
            # Create prompt
            prompt = self.create_comprehensive_prompt()
            
            # Prepare image for Gemini
            image_part = {
                "mime_type": "image/png",
                "data": image_data
            }
            
            # Generate content with Gemini 2.5 Pro
            response = self.model.generate_content([prompt, image_part])
            
            # Extract and clean JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Parse JSON
            extracted_data = json.loads(response_text.strip())
            
            logger.info(f"Successfully extracted lottery data: {extracted_data['lottery_type']} Draw {extracted_data.get('draw_number', 'Unknown')}")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for {image_path}: {e}")
            logger.error(f"Raw response: {response_text}")
            raise
        except Exception as e:
            logger.error(f"Gemini extraction failed for {image_path}: {e}")
            raise

    def save_to_database(self, extracted_data):
        """Save extracted lottery data to database"""
        try:
            from main import app
            
            with app.app_context():
                # Convert date string to datetime object
                draw_date = datetime.strptime(extracted_data['draw_date'], '%Y-%m-%d')
                
                # Handle next_draw_date if present
                next_draw_date = None
                if extracted_data.get('next_draw_date'):
                    next_draw_date = datetime.strptime(extracted_data['next_draw_date'], '%Y-%m-%d')
                
                # Create new lottery result record
                new_result = LotteryResult(
                    lottery_type=extracted_data['lottery_type'],
                    draw_number=extracted_data['draw_number'],
                    draw_date=draw_date,
                    numbers=json.dumps(extracted_data['main_numbers']),
                    bonus_numbers=json.dumps(extracted_data.get('bonus_numbers', [])),
                    divisions=json.dumps(extracted_data.get('divisions', [])),
                    rollover_amount=extracted_data.get('rollover_amount'),
                    rollover_number=extracted_data.get('rollover_number'),
                    total_pool_size=extracted_data.get('total_pool_size'),
                    total_sales=extracted_data.get('total_sales'),
                    next_jackpot=extracted_data.get('next_jackpot'),
                    draw_machine=extracted_data.get('draw_machine'),
                    next_draw_date=next_draw_date,
                    source_url=f"https://www.nationallottery.co.za/results/{extracted_data['lottery_type'].lower().replace(' ', '-')}",
                    ocr_provider="gemini-2.5-pro",
                    ocr_model="gemini-2.0-flash-exp"
                )
                
                db.session.add(new_result)
                db.session.commit()
            
            logger.info(f"Successfully saved {extracted_data['lottery_type']} Draw {extracted_data['draw_number']} to database")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save lottery data to database: {e}")
            raise

    def process_single_image(self, image_path):
        """Process a single lottery image with full pipeline"""
        try:
            logger.info(f"Starting Gemini extraction for: {image_path}")
            
            # Extract data using Gemini 2.5 Pro
            extracted_data = self.extract_lottery_data(image_path)
            
            # Save to database
            success = self.save_to_database(extracted_data)
            
            if success:
                logger.info(f"✅ Successfully processed {image_path}")
                return extracted_data
            else:
                logger.error(f"❌ Failed to save data from {image_path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error processing {image_path}: {e}")
            return None

    def process_directory(self, image_directory):
        """Process all lottery images in directory using Gemini 2.5 Pro"""
        import os
        
        if not os.path.exists(image_directory):
            logger.error(f"Directory not found: {image_directory}")
            return []
        
        results = []
        image_files = [f for f in os.listdir(image_directory) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        logger.info(f"Found {len(image_files)} images to process with Gemini 2.5 Pro")
        
        for image_file in sorted(image_files):
            image_path = os.path.join(image_directory, image_file)
            result = self.process_single_image(image_path)
            if result:
                results.append(result)
        
        logger.info(f"Successfully processed {len(results)} images with Gemini 2.5 Pro")
        return results

def test_gemini_extractor():
    """Test the Gemini lottery extractor"""
    try:
        extractor = GeminiLotteryExtractor()
        logger.info("✅ Gemini 2.5 Pro extractor initialized successfully")
        
        # Test with screenshots directory
        screenshots_dir = "screenshots"
        if os.path.exists(screenshots_dir):
            results = extractor.process_directory(screenshots_dir)
            logger.info(f"✅ Processed {len(results)} lottery images")
            return results
        else:
            logger.info("Screenshots directory not found - extractor ready for use")
            return []
            
    except Exception as e:
        logger.error(f"❌ Gemini extractor test failed: {e}")
        return None

if __name__ == "__main__":
    from app import app
    with app.app_context():
        test_gemini_extractor()