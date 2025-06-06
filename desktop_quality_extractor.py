#!/usr/bin/env python3
"""
Desktop-Quality Lottery Data Extractor
Matches the accuracy and reliability of desktop Claude apps
"""
import os
import base64
import json
import logging
import time
from datetime import datetime
from anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DesktopQualityExtractor:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY'))
        # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        self.model = "claude-3-5-sonnet-20241022"
        
    def encode_image_optimized(self, image_path):
        """Optimized image encoding with error handling"""
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            logger.info(f"Successfully encoded image: {os.path.basename(image_path)}")
            return image_data
        except Exception as e:
            logger.error(f"Image encoding failed: {e}")
            return None
    
    def create_desktop_quality_prompt(self, lottery_type=None):
        """Create a prompt that matches desktop app conversation quality"""
        return f"""
I need you to analyze this lottery results screenshot with the same precision and accuracy you would use in a desktop conversation. Extract ALL visible information with complete accuracy.

CRITICAL ANALYSIS REQUIREMENTS:
1. Read every number, amount, and text exactly as shown
2. Preserve exact formatting for all currency amounts (R1,234,567.89)
3. Extract complete prize division information including requirements, winners, and amounts
4. Capture all financial data: rollover amounts, pool sizes, sales figures, next jackpot
5. Include technical details: draw machines, dates, draw numbers

EXPECTED JSON OUTPUT:
{{
    "extraction_confidence": "high|medium|low",
    "lottery_type": "exact name from image",
    "draw_number": "exact draw ID",
    "draw_date": "YYYY-MM-DD",
    "main_numbers": [array of main winning numbers],
    "bonus_numbers": [array of bonus numbers if present],
    "prize_divisions": [
        {{
            "division": "DIV 1",
            "requirement": "exact requirement text from image",
            "winners": number_or_null,
            "prize_amount": "exact amount with R formatting"
        }}
    ],
    "financial_details": {{
        "rollover_amount": "exact amount from image",
        "rollover_number": number_if_visible,
        "total_pool_size": "exact amount",
        "total_sales": "exact amount if visible",
        "next_jackpot": "exact amount",
        "draw_machine": "exact machine name if visible",
        "next_draw_date": "YYYY-MM-DD if visible"
    }},
    "technical_info": {{
        "image_quality": "assessment of image clarity",
        "extraction_notes": "any important observations"
    }}
}}

ACCURACY GUIDELINES:
- Use EXACT text and numbers from the image - no approximations
- Maintain precise currency formatting including commas and decimals  
- Include all visible prize divisions even if winners = 0
- Extract rollover information and technical details
- Preserve number sequences exactly as shown
- Include bonus balls and powerball numbers if present

Please analyze this lottery screenshot now and provide the complete, accurate JSON extraction:
"""

    def extract_with_desktop_quality(self, image_path, lottery_type=None, max_retries=3):
        """Extract lottery data with desktop app quality and reliability"""
        
        image_data = self.encode_image_optimized(image_path)
        if not image_data:
            return None
            
        prompt = self.create_desktop_quality_prompt(lottery_type)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Extraction attempt {attempt + 1}/{max_retries} for {os.path.basename(image_path)}")
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.1,  # Low temperature for maximum precision
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
                                        "data": image_data
                                    }
                                }
                            ]
                        }
                    ]
                )
                
                response_text = response.content[0].text.strip()
                
                # Extract JSON from response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    extracted_data = json.loads(json_str)
                    
                    # Validate extraction quality
                    confidence = extracted_data.get('extraction_confidence', 'medium')
                    logger.info(f"Extraction successful with {confidence} confidence")
                    
                    return extracted_data
                else:
                    logger.warning(f"No valid JSON found in response (attempt {attempt + 1})")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed (attempt {attempt + 1}): {e}")
                time.sleep(2)  # Brief delay before retry
                
            except Exception as e:
                logger.error(f"API call failed (attempt {attempt + 1}): {e}")
                time.sleep(5)  # Longer delay for API issues
                
        logger.error(f"All extraction attempts failed for {os.path.basename(image_path)}")
        return None
    
    def save_to_database_comprehensive(self, extracted_data):
        """Save extracted data with comprehensive error handling"""
        try:
            from main import app, db, LotteryResult
            
            with app.app_context():
                # Check for existing entry
                existing = LotteryResult.query.filter_by(
                    lottery_type=extracted_data['lottery_type'],
                    draw_number=extracted_data['draw_number']
                ).first()
                
                if existing:
                    logger.info(f"Updating existing {extracted_data['lottery_type']} draw {extracted_data['draw_number']}")
                    db.session.delete(existing)
                    db.session.commit()
                
                # Create new comprehensive entry
                new_result = LotteryResult()
                new_result.lottery_type = extracted_data['lottery_type']
                new_result.draw_number = extracted_data['draw_number']
                new_result.draw_date = datetime.strptime(extracted_data['draw_date'], '%Y-%m-%d')
                new_result.numbers = json.dumps(extracted_data['main_numbers'])
                
                if extracted_data.get('bonus_numbers'):
                    new_result.bonus_numbers = json.dumps(extracted_data['bonus_numbers'])
                
                # Prize divisions
                if extracted_data.get('prize_divisions'):
                    new_result.divisions = json.dumps(extracted_data['prize_divisions'])
                
                # Financial details
                financial = extracted_data.get('financial_details', {})
                new_result.rollover_amount = financial.get('rollover_amount')
                new_result.rollover_number = financial.get('rollover_number')
                new_result.total_pool_size = financial.get('total_pool_size')
                new_result.total_sales = financial.get('total_sales')
                new_result.next_jackpot = financial.get('next_jackpot')
                new_result.draw_machine = financial.get('draw_machine')
                new_result.next_draw_date_str = financial.get('next_draw_date')
                
                # Technical metadata
                technical = extracted_data.get('technical_info', {})
                new_result.source_url = "https://www.nationallottery.co.za/"
                new_result.ocr_provider = "claude-3-5-sonnet-desktop-quality"
                new_result.ocr_model = "anthropic-vision-enhanced"
                new_result.ocr_timestamp = datetime.now()
                
                db.session.add(new_result)
                db.session.commit()
                
                logger.info(f"✓ Desktop-quality extraction saved: {extracted_data['lottery_type']}")
                logger.info(f"✓ Draw {extracted_data['draw_number']} with {len(extracted_data.get('prize_divisions', []))} divisions")
                logger.info(f"✓ Confidence: {extracted_data.get('extraction_confidence', 'N/A')}")
                
                return True
                
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            return False

def test_desktop_quality_extraction():
    """Test the desktop-quality extractor on available images"""
    extractor = DesktopQualityExtractor()
    
    # Test images in order of priority
    test_images = [
        "attached_assets/20250606_171942_lotto_plus_1_results.png",
        "attached_assets/20250606_171954_lotto_plus_2_results.png", 
        "attached_assets/20250606_172007_powerball.png",
        "attached_assets/20250606_172018_powerball_plus.png",
        "attached_assets/20250606_172030_daily_lotto.png"
    ]
    
    results = []
    
    for image_path in test_images:
        if os.path.exists(image_path):
            logger.info(f"Testing desktop-quality extraction on: {os.path.basename(image_path)}")
            result = extractor.extract_with_desktop_quality(image_path)
            
            if result:
                logger.info(f"✓ Extraction successful for {result.get('lottery_type', 'unknown')}")
                results.append(result)
                
                # Save to database
                if extractor.save_to_database_comprehensive(result):
                    logger.info(f"✓ Data saved to database")
                else:
                    logger.error(f"✗ Database save failed")
            else:
                logger.error(f"✗ Extraction failed for {os.path.basename(image_path)}")
                
    return results

if __name__ == "__main__":
    logger.info("Starting desktop-quality lottery data extraction...")
    results = test_desktop_quality_extraction()
    logger.info(f"Extraction complete. Processed {len(results)} images successfully.")