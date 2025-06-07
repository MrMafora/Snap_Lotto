"""
Extract complete prize division data from latest authentic screenshots
Process all lottery types with comprehensive prize breakdown information
"""
import os
import base64
import json
import google.generativeai as genai
from datetime import datetime
from app import app
from models import db, LotteryResult

class CompletePrizeExtractor:
    """Extract complete prize division data from authentic lottery screenshots"""
    
    def __init__(self):
        """Initialize Gemini client"""
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY', '')
        if not api_key:
            raise ValueError("Google API key not found")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("✓ Gemini 2.0 Flash initialized for complete prize extraction")
    
    def encode_image(self, image_path):
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def create_comprehensive_prompt(self):
        """Create comprehensive prompt for complete prize division extraction"""
        return """
        Extract complete lottery information from this South African lottery screenshot including:

        1. BASIC INFORMATION:
        - Lottery type (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2, POWERBALL, POWERBALL PLUS, DAILY LOTTO)
        - Draw number
        - Draw date
        - Winning numbers (main numbers)
        - Bonus/PowerBall number (if applicable)

        2. COMPLETE PRIZE DIVISIONS:
        - All division levels (Division 1, Division 2, etc.)
        - Match requirements for each division
        - Number of winners in each division
        - Prize amount per winner for each division
        - Total prize pool information

        3. ADDITIONAL DETAILS:
        - Next jackpot amount (if shown)
        - Rollover information
        - Draw machine used
        - Next draw date

        Return ONLY valid JSON in this exact format:
        {
            "lottery_type": "string",
            "draw_number": number,
            "draw_date": "YYYY-MM-DD",
            "main_numbers": [number, number, ...],
            "bonus_numbers": [number] or [],
            "divisions": [
                {
                    "division": "DIV 1",
                    "match": "match description",
                    "winners": number,
                    "prize_per_winner": "R formatted amount"
                }
            ],
            "next_jackpot": "R amount or null",
            "rollover_amount": "R amount or null",
            "total_pool_size": "R amount or null",
            "draw_machine": "machine name or null",
            "next_draw_date": "YYYY-MM-DD or null"
        }

        Extract ALL prize divisions shown in the image. Be precise with amounts and numbers.
        """
    
    def extract_complete_data(self, image_path):
        """Extract complete lottery data including all prize divisions"""
        try:
            print(f"Processing {image_path} for complete prize data...")
            
            # Encode image
            image_base64 = self.encode_image(image_path)
            
            # Create prompt
            prompt = self.create_comprehensive_prompt()
            
            # Process with Gemini
            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": image_base64}
            ])
            
            # Parse response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            data = json.loads(response_text)
            print(f"✓ Extracted complete data for {data['lottery_type']} Draw #{data['draw_number']}")
            return data
            
        except Exception as e:
            print(f"❌ Error extracting from {image_path}: {e}")
            return None
    
    def clean_currency_value(self, value):
        """Clean currency values for database storage"""
        if not value or value == "null":
            return None
        # Remove 'R' prefix and commas, keep only numbers and decimal point
        cleaned = str(value).replace('R', '').replace(',', '').strip()
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
    
    def save_complete_data(self, extracted_data):
        """Save complete lottery data with prize divisions to database"""
        try:
            lottery_type = extracted_data['lottery_type']
            draw_number = extracted_data['draw_number']
            
            # Clean currency values for database storage
            next_jackpot = self.clean_currency_value(extracted_data.get('next_jackpot'))
            rollover_amount = self.clean_currency_value(extracted_data.get('rollover_amount'))
            total_pool_size = self.clean_currency_value(extracted_data.get('total_pool_size'))
            
            # Check if record exists
            existing = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if existing:
                print(f"Updating existing {lottery_type} Draw #{draw_number} with complete prize data")
                # Update existing record with complete data
                existing.numbers = json.dumps(extracted_data['main_numbers'])
                existing.bonus_numbers = json.dumps(extracted_data['bonus_numbers'])
                existing.divisions = json.dumps(extracted_data['divisions'])
                existing.next_jackpot = extracted_data.get('next_jackpot')  # Keep as string for display
                existing.rollover_amount = extracted_data.get('rollover_amount')  # Keep as string for display
                existing.total_pool_size = extracted_data.get('total_pool_size')  # Keep as string for display
                existing.draw_machine = extracted_data.get('draw_machine')
                existing.next_draw_date_str = extracted_data.get('next_draw_date')
                existing.ocr_provider = 'google_gemini_2.0_flash'
                existing.ocr_model = 'gemini-2.0-flash-exp'
                existing.ocr_timestamp = datetime.now()
            else:
                print(f"Creating new {lottery_type} Draw #{draw_number} with complete prize data")
                # Create new record
                new_result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=draw_number,
                    draw_date=datetime.strptime(extracted_data['draw_date'], '%Y-%m-%d'),
                    numbers=json.dumps(extracted_data['main_numbers']),
                    bonus_numbers=json.dumps(extracted_data['bonus_numbers']),
                    divisions=json.dumps(extracted_data['divisions']),
                    next_jackpot=extracted_data.get('next_jackpot'),
                    rollover_amount=extracted_data.get('rollover_amount'),
                    total_pool_size=extracted_data.get('total_pool_size'),
                    draw_machine=extracted_data.get('draw_machine'),
                    next_draw_date_str=extracted_data.get('next_draw_date'),
                    ocr_provider='google_gemini_2.0_flash',
                    ocr_model='gemini-2.0-flash-exp',
                    ocr_timestamp=datetime.now(),
                    created_at=datetime.now()
                )
                db.session.add(new_result)
            
            db.session.commit()
            print(f"✓ Saved complete data for {lottery_type} Draw #{draw_number}")
            
        except Exception as e:
            print(f"❌ Error saving {lottery_type} data: {e}")
            db.session.rollback()
    
    def process_all_latest_screenshots(self):
        """Process all latest screenshots for complete prize data"""
        screenshot_dir = 'screenshots'
        processed_count = 0
        
        # Get all latest screenshot files
        screenshot_files = [
            f for f in os.listdir(screenshot_dir) 
            if f.endswith('.png') and '20250607' in f
        ]
        
        print(f"Found {len(screenshot_files)} latest screenshots to process")
        
        for filename in sorted(screenshot_files):
            image_path = os.path.join(screenshot_dir, filename)
            print(f"\n=== Processing {filename} ===")
            
            # Extract complete data
            extracted_data = self.extract_complete_data(image_path)
            
            if extracted_data:
                # Save to database
                self.save_complete_data(extracted_data)
                processed_count += 1
            
        print(f"\n✓ Successfully processed {processed_count} screenshots with complete prize data")
        return processed_count

def main():
    """Extract complete prize data from all latest authentic screenshots"""
    print("=== COMPLETE PRIZE DATA EXTRACTION ===")
    print("Processing latest authentic lottery screenshots with Gemini 2.0 Flash")
    
    try:
        with app.app_context():
            extractor = CompletePrizeExtractor()
            processed_count = extractor.process_all_latest_screenshots()
            
            print(f"\n🎯 COMPLETE: Processed {processed_count} authentic lottery screenshots")
            print("All lottery types now have complete prize division data")
        
    except Exception as e:
        print(f"❌ EXTRACTION FAILED: {e}")

if __name__ == "__main__":
    main()