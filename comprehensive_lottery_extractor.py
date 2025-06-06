"""
Comprehensive lottery data extraction from screenshots with full prize division details
"""
import os
import json
import base64
import anthropic
from datetime import datetime
from models import db, LotteryResult
from main import app

def extract_comprehensive_lottery_data(image_path):
    """Extract complete lottery data including divisions, winners, and financial details"""
    client = anthropic.Anthropic(
        api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY')
    )
    
    # Encode image
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    prompt = """
    Extract ALL lottery data from this image with complete details. Return ONLY valid JSON with this exact structure:

    {
        "lottery_type": "LOTTO",
        "draw_id": 2547,
        "draw_date": "2025-06-04",
        "winning_numbers": {
            "draw_order": [12, 34, 8, 52, 36, 24],
            "numerical_order": [8, 24, 12, 34, 36, 52],
            "bonus_ball": 26
        },
        "prize_divisions": [
            {
                "division": "DIV 1",
                "requirement": "SIX CORRECT NUMBERS",
                "winners": 4,
                "prize_amount": "R0.00"
            },
            {
                "division": "DIV 2", 
                "requirement": "FIVE CORRECT NUMBERS + BONUS BALL",
                "winners": 39,
                "prize_amount": "R0.00"
            },
            {
                "division": "DIV 3",
                "requirement": "FIVE CORRECT NUMBERS", 
                "winners": 108,
                "prize_amount": "R6,883.20"
            }
        ],
        "additional_info": {
            "rollover_amount": "R63,481,569.30",
            "rollover_no": 20,
            "total_pool_size": "R67,302,275.10", 
            "total_sales": "R15,402,610.00",
            "next_jackpot": "R67,000,000.00",
            "draw_machine": "RNG 1",
            "next_draw_date": "2025-06-07"
        }
    }

    CRITICAL REQUIREMENTS:
    1. Extract draw order numbers (left side) NOT numerical order (right side)
    2. Include ALL prize divisions with exact winners and amounts
    3. Capture all financial information (rollover, pool size, sales)
    4. Get exact lottery type name as shown
    5. Extract draw ID number and dates accurately
    6. Include bonus ball if present
    7. Return valid JSON only, no other text
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=3000,
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
    
    try:
        # Extract JSON from response
        content = response.content[0].text.strip()
        if content.startswith('```json'):
            content = content[7:-3]
        elif content.startswith('```'):
            content = content[3:-3]
        
        data = json.loads(content)
        return data
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing AI response: {e}")
        print(f"Raw response: {response.content[0].text}")
        return None

def save_comprehensive_lottery_data(data):
    """Save comprehensive lottery data to database"""
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
            
            # Parse draw date
            draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d')
            
            # Format numbers for PostgreSQL array storage
            main_numbers = '{' + ','.join(map(str, data['winning_numbers']['draw_order'])) + '}'
            bonus_numbers = None
            if 'bonus_ball' in data['winning_numbers'] and data['winning_numbers']['bonus_ball']:
                bonus_numbers = '{' + str(data['winning_numbers']['bonus_ball']) + '}'
            
            # Create new lottery result with comprehensive data
            lottery_result = LotteryResult(
                lottery_type=data['lottery_type'],
                draw_number=data['draw_id'],
                draw_date=draw_date,
                main_numbers=main_numbers,
                bonus_numbers=bonus_numbers,
                divisions=json.dumps(data['prize_divisions']),
                rollover_amount=data['additional_info'].get('rollover_amount'),
                rollover_number=data['additional_info'].get('rollover_no'),
                total_pool_size=data['additional_info'].get('total_pool_size'),
                total_sales=data['additional_info'].get('total_sales'),
                next_jackpot=data['additional_info'].get('next_jackpot'),
                draw_machine=data['additional_info'].get('draw_machine'),
                next_draw_date_str=data['additional_info'].get('next_draw_date')
            )
            
            db.session.add(lottery_result)
            db.session.commit()
            
            print(f"Successfully saved {data['lottery_type']} draw {data['draw_id']}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving lottery data: {e}")
            return False

def process_screenshot_comprehensive(image_path):
    """Process a single screenshot with comprehensive extraction"""
    print(f"Processing {image_path} for comprehensive lottery data...")
    
    data = extract_comprehensive_lottery_data(image_path)
    if data:
        success = save_comprehensive_lottery_data(data)
        if success:
            print(f"Successfully processed {image_path}")
            return True
        else:
            print(f"Failed to save data from {image_path}")
            return False
    else:
        print(f"Failed to extract data from {image_path}")
        return False

def batch_process_screenshots():
    """Process all lottery screenshots with comprehensive extraction"""
    screenshot_dir = "attached_assets"
    processed_count = 0
    
    # Get all lottery screenshot files
    lottery_files = [
        f for f in os.listdir(screenshot_dir) 
        if f.endswith('.png') and any(x in f.lower() for x in ['lotto', 'powerball', 'daily'])
    ]
    
    print(f"Found {len(lottery_files)} lottery screenshots to process")
    
    for filename in lottery_files:
        image_path = os.path.join(screenshot_dir, filename)
        try:
            if process_screenshot_comprehensive(image_path):
                processed_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    print(f"Processed {processed_count} out of {len(lottery_files)} screenshots")
    return processed_count

if __name__ == "__main__":
    # Process specific screenshot or all screenshots
    import sys
    
    if len(sys.argv) > 1:
        # Process specific file
        image_path = sys.argv[1]
        process_screenshot_comprehensive(image_path)
    else:
        # Process all screenshots
        batch_process_screenshots()