#!/usr/bin/env python3
import os
import base64
import json
import logging
from datetime import datetime
from anthropic import Anthropic

# the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY'))

def extract_comprehensive_lottery_data(image_path, lottery_type=None):
    """
    Enhanced AI extraction using Claude Opus with desktop app-level accuracy
    """
    try:
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Comprehensive extraction prompt matching desktop app capabilities
        extraction_prompt = f"""
You are an expert lottery data extraction specialist. Analyze this lottery results screenshot with extreme precision and extract ALL visible information.

CRITICAL REQUIREMENTS:
1. Extract EVERY number, amount, and detail visible
2. Maintain exact formatting for currency amounts (R1,234.56)
3. Capture ALL prize divisions with requirements, winners, and amounts
4. Extract complete financial information (rollover, pool size, sales, next jackpot)
5. Include draw machine, dates, and technical details

EXPECTED OUTPUT FORMAT (JSON):
{{
    "lottery_type": "EXACT name from image",
    "draw_number": "exact draw ID number",
    "draw_date": "YYYY-MM-DD format", 
    "main_numbers": [list of main winning numbers],
    "bonus_numbers": [list of bonus numbers if any],
    "prize_divisions": [
        {{
            "division": "DIV 1",
            "requirement": "exact requirement text",
            "winners": number or null,
            "prize_amount": "exact amount with R formatting"
        }}
    ],
    "financial_info": {{
        "rollover_amount": "exact amount",
        "rollover_number": number,
        "total_pool_size": "exact amount", 
        "total_sales": "exact amount",
        "next_jackpot": "exact amount",
        "draw_machine": "exact machine name",
        "next_draw_date": "YYYY-MM-DD"
    }}
}}

EXTRACTION RULES:
- Use EXACT text and numbers from the image
- Preserve all currency formatting (commas, decimals)
- Include all visible prize divisions even if winners = 0
- Extract rollover numbers and technical details
- Maintain precise number sequences
- Include bonus balls if present

Analyze the image now and provide the complete JSON extraction:
"""

        # Make API call with enhanced parameters
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Latest model
            max_tokens=4000,
            temperature=0.1,  # Low temperature for precision
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": extraction_prompt
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
        
        # Extract and parse response
        response_text = response.content[0].text.strip()
        
        # Find JSON in response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            extracted_data = json.loads(json_str)
            
            logging.info(f"Successfully extracted comprehensive data for {extracted_data.get('lottery_type', 'unknown')}")
            return extracted_data
        else:
            logging.error("No valid JSON found in AI response")
            return None
            
    except Exception as e:
        logging.error(f"Enhanced AI extraction failed: {e}")
        return None

def save_extracted_data_to_database(extracted_data):
    """
    Save comprehensively extracted data to database with all fields
    """
    try:
        from main import app, db, LotteryResult
        
        with app.app_context():
            # Check for existing entry
            existing = LotteryResult.query.filter_by(
                lottery_type=extracted_data['lottery_type'],
                draw_number=extracted_data['draw_number']
            ).first()
            
            if existing:
                print(f"Updating existing {extracted_data['lottery_type']} draw {extracted_data['draw_number']}")
                db.session.delete(existing)
                db.session.commit()
            
            # Create comprehensive new entry
            new_result = LotteryResult()
            new_result.lottery_type = extracted_data['lottery_type']
            new_result.draw_number = extracted_data['draw_number']
            new_result.draw_date = datetime.strptime(extracted_data['draw_date'], '%Y-%m-%d')
            new_result.numbers = json.dumps(extracted_data['main_numbers'])
            
            if extracted_data.get('bonus_numbers'):
                new_result.bonus_numbers = json.dumps(extracted_data['bonus_numbers'])
            
            # Comprehensive divisions data
            if extracted_data.get('prize_divisions'):
                new_result.divisions = json.dumps(extracted_data['prize_divisions'])
            
            # Financial information
            financial = extracted_data.get('financial_info', {})
            new_result.rollover_amount = financial.get('rollover_amount')
            new_result.rollover_number = financial.get('rollover_number')
            new_result.total_pool_size = financial.get('total_pool_size')
            new_result.total_sales = financial.get('total_sales')
            new_result.next_jackpot = financial.get('next_jackpot')
            new_result.draw_machine = financial.get('draw_machine')
            new_result.next_draw_date_str = financial.get('next_draw_date')
            
            # Required fields
            new_result.source_url = "https://www.nationallottery.co.za/"
            new_result.ocr_provider = "claude-3-5-sonnet-20241022"
            new_result.ocr_model = "anthropic-vision"
            new_result.ocr_timestamp = datetime.now()
            
            db.session.add(new_result)
            db.session.commit()
            
            print(f"✓ Successfully saved comprehensive {extracted_data['lottery_type']} data")
            print(f"✓ Draw {extracted_data['draw_number']} with {len(extracted_data.get('prize_divisions', []))} divisions")
            print(f"✓ Financial data: {financial.get('rollover_amount', 'N/A')} rollover")
            
            return True
            
    except Exception as e:
        logging.error(f"Database save failed: {e}")
        return False

if __name__ == "__main__":
    # Test with LOTTO PLUS 1 image
    test_image = "attached_assets/20250606_171942_lotto_plus_1_results.png"
    if os.path.exists(test_image):
        print("Testing enhanced AI extraction on LOTTO PLUS 1...")
        result = extract_comprehensive_lottery_data(test_image)
        if result:
            print("Extraction successful!")
            print(json.dumps(result, indent=2))
        else:
            print("Extraction failed")
    else:
        print(f"Test image not found: {test_image}")