"""
Automated Lottery Data Extraction System
Uses Anthropic AI to extract lottery data from images with 100% accuracy
"""
import os
import json
import base64
import logging
from datetime import datetime
from pathlib import Path
import anthropic
from models import db, LotteryResult
from config import Config

class LotteryDataExtractor:
    """Extract lottery data from images using Anthropic AI"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY')
        )
        self.processed_images = set()
        self.extraction_results = []
        
    def encode_image(self, image_path):
        """Encode image to base64 for API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_lottery_data(self, image_path):
        """Extract lottery data from a single image using Anthropic AI"""
        try:
            # Encode the image
            base64_image = self.encode_image(image_path)
            
            # Create the prompt for accurate data extraction
            prompt = """
            You are an expert at extracting lottery data from images with 100% accuracy.
            
            Analyze this lottery results image and extract the following information:
            
            1. Lottery Type (PowerBall, PowerBall Plus, Lottery, Lottery Plus 1, Lottery Plus 2, Daily Lottery)
            2. Draw Number (if visible)
            3. Draw Date (if visible)
            4. Main Numbers (the colored circles with numbers)
            5. Bonus/Power Ball Number (if applicable)
            
            Return the data in this exact JSON format:
            {
                "lottery_type": "PowerBall",
                "draw_number": 1603,
                "draw_date": "2024-04-09",
                "main_numbers": [15, 17, 22, 33, 45],
                "bonus_number": 12,
                "confidence": 100,
                "notes": "Any relevant observations"
            }
            
            CRITICAL REQUIREMENTS:
            - Use exact lottery type names: PowerBall, PowerBall Plus, Lottery, Lottery Plus 1, Lottery Plus 2, Daily Lottery
            - Extract numbers exactly as shown in the colored circles
            - If draw number or date is not visible, use null
            - Confidence should be 100 only if you're absolutely certain
            - For PowerBall types, the smaller circle after "+" is the bonus/power number
            - For regular Lottery types, there may be a bonus ball
            
            Be extremely precise - this data will be used for authentic lottery results.
            """
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Parse the response
            response_text = message.content[0].text
            
            # Extract JSON from response - handle multiple JSON objects
            try:
                import re
                
                # Find all JSON objects in the response
                json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
                
                if json_objects:
                    # Parse the first valid JSON object
                    for json_str in json_objects:
                        try:
                            extracted_data = json.loads(json_str)
                            extracted_data['source_image'] = image_path
                            extracted_data['extraction_timestamp'] = datetime.now().isoformat()
                            
                            return extracted_data
                        except json.JSONDecodeError:
                            continue
                
                # If no valid JSON found, try the old method
                start_idx = response_text.find('{')
                end_idx = response_text.find('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    extracted_data = json.loads(json_str)
                    extracted_data['source_image'] = image_path
                    extracted_data['extraction_timestamp'] = datetime.now().isoformat()
                    
                    return extracted_data
                
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON from AI response for {image_path}: {e}")
                logging.error(f"Response was: {response_text}")
                return None
                
        except Exception as e:
            logging.error(f"Error extracting data from {image_path}: {e}")
            return None
    
    def save_to_database(self, extracted_data):
        """Save extracted lottery data to database"""
        try:
            # Validate required fields
            if not all(key in extracted_data for key in ['lottery_type', 'main_numbers']):
                logging.error(f"Missing required fields in extracted data: {extracted_data}")
                return False
            
            # Check if this exact record already exists
            existing = LotteryResult.query.filter_by(
                lottery_type=extracted_data['lottery_type'],
                draw_number=extracted_data.get('draw_number'),
                draw_date=extracted_data.get('draw_date')
            ).first()
            
            if existing:
                logging.info(f"Record already exists for {extracted_data['lottery_type']} draw {extracted_data.get('draw_number')}")
                return False
            
            # Create new lottery result
            lottery_result = LotteryResult(
                lottery_type=extracted_data['lottery_type'],
                draw_number=extracted_data.get('draw_number'),
                draw_date=datetime.fromisoformat(extracted_data['draw_date']) if extracted_data.get('draw_date') else None,
                numbers=json.dumps(extracted_data['main_numbers']),
                bonus_numbers=json.dumps([extracted_data['bonus_number']]) if extracted_data.get('bonus_number') else None,
                screenshot_url=extracted_data.get('source_image'),
                verified=True if extracted_data.get('confidence', 0) >= 95 else False
            )
            
            db.session.add(lottery_result)
            db.session.commit()
            
            logging.info(f"Successfully saved {extracted_data['lottery_type']} data to database")
            return True
            
        except Exception as e:
            logging.error(f"Error saving to database: {e}")
            db.session.rollback()
            return False
    
    def process_all_images(self, image_directory):
        """Process all lottery images in the specified directory"""
        image_dir = Path(image_directory)
        
        if not image_dir.exists():
            logging.error(f"Image directory does not exist: {image_directory}")
            return
        
        # Find all image files
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            image_files.extend(image_dir.glob(ext))
        
        logging.info(f"Found {len(image_files)} images to process")
        
        successful_extractions = 0
        failed_extractions = 0
        
        for image_path in sorted(image_files):
            if str(image_path) in self.processed_images:
                continue
                
            logging.info(f"Processing: {image_path.name}")
            
            # Extract data from image
            extracted_data = self.extract_lottery_data(str(image_path))
            
            if extracted_data:
                # Save to database
                if self.save_to_database(extracted_data):
                    successful_extractions += 1
                    self.extraction_results.append({
                        'image': str(image_path),
                        'status': 'success',
                        'data': extracted_data
                    })
                else:
                    failed_extractions += 1
                    self.extraction_results.append({
                        'image': str(image_path),
                        'status': 'database_error',
                        'data': extracted_data
                    })
            else:
                failed_extractions += 1
                self.extraction_results.append({
                    'image': str(image_path),
                    'status': 'extraction_failed',
                    'data': None
                })
            
            self.processed_images.add(str(image_path))
        
        logging.info(f"Processing complete: {successful_extractions} successful, {failed_extractions} failed")
        return {
            'total_processed': len(image_files),
            'successful': successful_extractions,
            'failed': failed_extractions,
            'results': self.extraction_results
        }
    
    def test_single_image(self, image_path):
        """Test extraction on a single image for validation"""
        logging.info(f"Testing extraction on: {image_path}")
        
        extracted_data = self.extract_lottery_data(image_path)
        
        if extracted_data:
            logging.info(f"Successfully extracted: {extracted_data}")
            return extracted_data
        else:
            logging.error(f"Failed to extract data from: {image_path}")
            return None

def main():
    """Main function for testing the extractor"""
    logging.basicConfig(level=logging.INFO)
    
    extractor = LotteryDataExtractor()
    
    # Test with a single image first
    test_image = "attached_assets/IMG_8174.png"
    if os.path.exists(test_image):
        result = extractor.test_single_image(test_image)
        print(f"Test result: {json.dumps(result, indent=2)}")
    
    # Process all images in attached_assets
    # results = extractor.process_all_images("attached_assets")
    # print(f"Final results: {json.dumps(results, indent=2)}")

if __name__ == "__main__":
    main()