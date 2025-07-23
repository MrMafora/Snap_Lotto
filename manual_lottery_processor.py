#!/usr/bin/env python3
"""
Manual Lottery Image Processor - User uploads images for AI processing
This bypasses website blocking by allowing direct image uploads
"""

import os
import json
import logging
from datetime import datetime
from google import genai
from google.genai import types
import psycopg2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManualLotteryProcessor:
    """Process user-uploaded lottery ticket images with AI"""
    
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        
    def process_lottery_image(self, image_path, expected_lottery_type=None):
        """Process a lottery image and extract all lottery data"""
        
        if not self.client:
            return {"error": "Gemini API key not available"}
        
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}
        
        # Enhanced prompt for SA National Lottery ticket scanning
        prompt = f"""
        You are analyzing a South African National Lottery PLAYER'S TICKET (not results page).
        This image shows a TICKET that a player purchased with their SELECTED NUMBERS.
        
        CRITICAL: You must extract the PLAYER'S CHOSEN NUMBERS from their ticket.
        Look for:
        - Numbers that the player selected/marked on their ticket
        - Base game type: LOTTO, POWERBALL, or DAILY LOTTO
        - Additional games: Check if player included LOTTO PLUS 1, LOTTO PLUS 2, or POWERBALL PLUS
        - Draw number and date information
        - Any marked/selected bonus numbers
        
        The PLAYER'S NUMBERS are typically displayed as:
        - Grid of numbered boxes with some numbers marked/selected
        - Printed confirmation numbers on the ticket
        - Quick pick or manual selection numbers
        
        IGNORE any winning numbers or results - focus ONLY on what the player selected.
        
        Extract ALL information and return in this EXACT JSON format:
        {{
            "lottery_type": "LOTTO",
            "included_games": ["LOTTO", "LOTTO PLUS 1", "LOTTO PLUS 2"],
            "draw_number": 2556,
            "draw_date": "2025-07-05",
            "main_numbers": [[4, 9, 12, 14, 29, 1], [7, 15, 23, 31, 42, 49]],
            "bonus_numbers": [23],
            "prize_divisions": [
                {{
                    "division": "DIV 1",
                    "match_description": "SIX CORRECT NUMBERS",
                    "winners": 0,
                    "prize_amount": "0.00"
                }},
                {{
                    "division": "DIV 2", 
                    "match_description": "FIVE CORRECT NUMBERS + BONUS BALL",
                    "winners": 2,
                    "prize_amount": "R7,631.30"
                }}
            ],
            "financial_info": {{
                "rollover_amount": "R5,753,261.36",
                "rollover_number": "2",
                "total_pool_size": "R9,621,635.16", 
                "total_sales": "R15,670,660.00",
                "next_jackpot": "R8,000,000.00",
                "draw_machine": "RNG 2",
                "next_draw_date": "2025-07-09"
            }},
            "confidence": 98
        }}

        CRITICAL EXTRACTION RULES FOR TICKET SCANNING:
        1. lottery_type: Base game type - one of: LOTTO, POWERBALL, DAILY LOTTO
        2. included_games: Array of ALL games the player selected:
           - For LOTTO tickets: Can include ["LOTTO", "LOTTO PLUS 1", "LOTTO PLUS 2"]  
           - For POWERBALL tickets: Can include ["POWERBALL", "POWERBALL PLUS"]
           - For DAILY LOTTO tickets: Only ["DAILY LOTTO"]
        3. main_numbers: Extract ALL LINES of player's numbers as array of arrays [[line1], [line2], [line3]]
        4. IMPORTANT: Look for marked/selected numbers on the player's ticket, NOT winning results
        5. The player's numbers are what they chose to play with, shown on their purchased ticket
        3. bonus_numbers: Extract bonus/powerball numbers as integers [23] or [7] for PowerBall
        4. prize_divisions: Extract ALL divisions visible (8 for LOTTO, 9 for PowerBall, 4 for Daily Lotto)
        5. Financial amounts: Include currency symbol and commas "R5,753,261.36"
        6. Dates: Use YYYY-MM-DD format
        7. Extract EVERY piece of visible lottery data - numbers, prizes, financial info
        8. Return ONLY valid JSON, no additional text
        """
        
        try:
            # Read image file
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Process with Gemini 2.5 Pro
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                    prompt
                ],
            )
            
            if response.text:
                # Clean and parse JSON response
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                extracted_data = json.loads(response_text)
                
                logger.info(f"Successfully processed image: {image_path}")
                logger.info(f"Found {len(extracted_data.get('extractions', []))} lottery extractions")
                
                return extracted_data
            else:
                return {"error": "Empty response from Gemini AI"}
                
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {"error": str(e)}
    
    def save_extractions_to_database(self, extractions_data):
        """Save extracted lottery data to database"""
        
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                return {"error": "Database URL not available"}
            
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            saved_records = []
            
            # Handle single extraction format (new format)
            if 'lottery_type' in extractions_data and 'extractions' not in extractions_data:
                extractions = [extractions_data]
            else:
                extractions = extractions_data.get('extractions', [])
            
            # Process each extraction
            for extraction in extractions:
                
                insert_query = """
                INSERT INTO lottery_results (
                    lottery_type, draw_number, draw_date, main_numbers, bonus_numbers,
                    next_jackpot, prize_divisions, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """
                
                values = (
                    extraction.get('lottery_type'),
                    extraction.get('draw_number'),
                    extraction.get('draw_date'),
                    json.dumps(extraction.get('main_numbers', [])),
                    json.dumps(extraction.get('bonus_numbers', [])),
                    str(extraction.get('next_jackpot', '')),
                    json.dumps(extraction.get('prize_divisions', [])),
                    datetime.now()
                )
                
                cursor.execute(insert_query, values)
                new_id = cursor.fetchone()[0]
                
                saved_records.append({
                    'id': new_id,
                    'lottery_type': extraction.get('lottery_type'),
                    'draw_date': extraction.get('draw_date')
                })
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(saved_records)} lottery records to database")
            return {"success": True, "saved_records": saved_records}
            
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            return {"error": str(e)}

def process_uploaded_image(image_path):
    """Main function to process an uploaded lottery image"""
    
    print(f"Processing lottery image: {image_path}")
    print("=" * 50)
    
    processor = ManualLotteryProcessor()
    
    # Process image with AI
    print("Step 1: AI Extraction...")
    result = processor.process_lottery_image(image_path)
    
    if 'error' in result:
        print(f"❌ AI extraction failed: {result['error']}")
        return False
    
    # Display results 
    print("Step 2: Results Preview...")
    lottery_type = result.get('lottery_type')
    confidence = result.get('confidence', 0)
    
    print(f"✅ Extraction successful! Confidence: {confidence}%")
    print(f"🎯 Lottery Type: {lottery_type}")
    print(f"📅 Draw: #{result.get('draw_number')} on {result.get('draw_date')}")
    print(f"🔢 Main Numbers: {result.get('main_numbers')}")
    print(f"⭐ Bonus Numbers: {result.get('bonus_numbers')}")
    
    # Display prize divisions
    divisions = result.get('prize_divisions', [])
    if divisions:
        print(f"\n🏆 Prize Divisions ({len(divisions)} total):")
        for div in divisions[:3]:  # Show first 3 divisions
            winners = div.get('winners', 0)
            prize = div.get('prize_amount', '0.00')
            print(f"  {div.get('division')}: {winners} winners - {prize}")
        if len(divisions) > 3:
            print(f"  ... and {len(divisions) - 3} more divisions")
    
    # Display financial info
    financial = result.get('financial_info', {})
    if financial:
        print(f"\n💰 Financial Information:")
        if financial.get('next_jackpot'):
            print(f"  Next Jackpot: {financial.get('next_jackpot')}")
        if financial.get('rollover_amount'):
            print(f"  Rollover: {financial.get('rollover_amount')}")
        if financial.get('total_sales'):
            print(f"  Total Sales: {financial.get('total_sales')}")
    
    # Save to database
    print("\nStep 3: Saving to database...")
    save_result = processor.save_extractions_to_database(result)
    
    if save_result.get('success'):
        saved_records = save_result.get('saved_records', [])
        print(f"✅ Saved {len(saved_records)} records to database")
        for record in saved_records:
            print(f"  - {record['lottery_type']} (ID: {record['id']})")
        return True
    else:
        print(f"❌ Database save failed: {save_result.get('error')}")
        return False

if __name__ == "__main__":
    # Test with test_capture.png which contains real lottery data
    test_image = "screenshots/test_capture.png"
    
    if os.path.exists(test_image):
        print("🧪 Testing Manual Lottery Image Processor")
        print("Using test_capture.png with real lottery data")
        print("=" * 60)
        
        success = process_uploaded_image(test_image)
        
        if success:
            print("\n🎉 Manual lottery processor working perfectly!")
            print("Users can now upload lottery images for AI processing")
        else:
            print("\n⚠️ Manual processor needs attention")
    else:
        print(f"❌ Test image not found: {test_image}")
        print("Place a lottery ticket image in screenshots/ folder and run again")