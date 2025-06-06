"""
Enhanced lottery data processor that extracts comprehensive information
including prize divisions, winners, and financial details
"""
import os
import json
import base64
import anthropic
from datetime import datetime
from models import db, LotteryResult
from main import app

def extract_lottery_with_divisions(image_path):
    """Extract lottery data with full prize division breakdown"""
    client = anthropic.Anthropic(
        api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY')
    )
    
    # Encode image
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    prompt = """Extract lottery data from this South African lottery results page. Focus on the LOTTO results section.

Return JSON with this structure:
{
    "lottery_type": "LOTTO", 
    "draw_id": 2547,
    "draw_date": "2025-06-04",
    "main_numbers": [32, 34, 8, 52, 36],
    "bonus_number": 24,
    "divisions": [
        {"div": "DIV 1", "requirement": "SIX CORRECT NUMBERS", "winners": 0, "prize": "R0.00"},
        {"div": "DIV 2", "requirement": "FIVE CORRECT NUMBERS + BONUS BALL", "winners": 5, "prize": "R6,883.20"}
    ],
    "rollover_amount": "R63,481,569.30",
    "total_pool_size": "R67,302,275.10",
    "next_jackpot": "R67,000,000.00"
}

CRITICAL: Use the numbers from the DRAW ORDER (left side), NOT numerical order (right side).
Extract ALL visible prize divisions with exact winner counts and prize amounts."""
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            timeout=20,
            messages=[{
                "role": "user", 
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png", 
                            "data": base64_image
                        }
                    }
                ]
            }]
        )
        
        content = response.content[0].text.strip()
        if content.startswith('```json'):
            content = content[7:-3]
        elif content.startswith('```'):
            content = content[3:-3]
        
        return json.loads(content)
        
    except Exception as e:
        print(f"Extraction error: {e}")
        return None

def save_enhanced_lottery_data(data):
    """Save enhanced lottery data with division information"""
    if not data:
        return False
        
    with app.app_context():
        try:
            # Check if this draw already exists
            existing = LotteryResult.query.filter_by(
                lottery_type=data['lottery_type'],
                draw_number=data['draw_id']
            ).first()
            
            if existing:
                print(f"Draw {data['draw_id']} for {data['lottery_type']} already exists")
                return False
            
            # Parse date
            draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d')
            
            # Format numbers for PostgreSQL array
            main_numbers = '{' + ','.join(map(str, data['main_numbers'])) + '}'
            bonus_numbers = None
            if 'bonus_number' in data and data['bonus_number']:
                bonus_numbers = '{' + str(data['bonus_number']) + '}'
            
            # Create lottery result
            lottery_result = LotteryResult(
                lottery_type=data['lottery_type'],
                draw_number=data['draw_id'],
                draw_date=draw_date,
                main_numbers=main_numbers,
                bonus_numbers=bonus_numbers,
                divisions=json.dumps(data.get('divisions', [])),
                rollover_amount=data.get('rollover_amount'),
                total_pool_size=data.get('total_pool_size'),
                next_jackpot=data.get('next_jackpot'),
                source_url="https://www.nationallottery.co.za"
            )
            
            db.session.add(lottery_result)
            db.session.commit()
            
            print(f"Successfully saved {data['lottery_type']} draw {data['draw_id']} with {len(data.get('divisions', []))} divisions")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Save error: {e}")
            return False

def process_june_6_lotto():
    """Process the June 6, 2025 LOTTO screenshot specifically"""
    image_path = "attached_assets/20250606_171929_lotto.png"
    
    print(f"Processing June 6, 2025 LOTTO results from {image_path}")
    
    data = extract_lottery_with_divisions(image_path)
    if data:
        print(f"Extracted: {data['lottery_type']} Draw {data['draw_id']}")
        print(f"Numbers: {data['main_numbers']}")
        print(f"Divisions: {len(data.get('divisions', []))}")
        
        success = save_enhanced_lottery_data(data)
        return success
    else:
        print("Failed to extract data")
        return False

if __name__ == "__main__":
    process_june_6_lotto()