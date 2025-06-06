"""
Extract authentic lottery data from the real screenshot using Anthropic AI
"""
import os
import json
import base64
import anthropic
from models import db, LotteryResult
from main import app

def extract_from_image(image_path):
    """Extract lottery data from image using Anthropic AI"""
    client = anthropic.Anthropic(
        api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY')
    )
    
    # Encode image
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    prompt = """
    Extract lottery data from this image. Return ONLY valid JSON with this structure:
    [
        {
            "lottery_type": "Lotto Plus 1",
            "draw_number": 2545,
            "draw_date": "2025-05-28",
            "main_numbers": [14, 18, 32, 27, 41],
            "bonus_numbers": [45, 15]
        }
    ]
    
    Extract ALL lottery games visible in the image. For each game, get:
    - Exact lottery type name
    - Draw number 
    - Draw date (YYYY-MM-DD format)
    - Main numbers as array
    - Bonus numbers as array (if any)
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
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
        data = json.loads(response.content[0].text)
        return data
    except:
        print("Raw response:", response.content[0].text)
        return None

def update_database(lottery_data):
    """Update database with extracted lottery data"""
    with app.app_context():
        # Clear existing test data
        LotteryResult.query.delete()
        
        for game in lottery_data:
            result = LotteryResult(
                lottery_type=game['lottery_type'],
                draw_number=game['draw_number'],
                draw_date=game['draw_date'],
                main_numbers='{' + ','.join(map(str, game['main_numbers'])) + '}',
                bonus_numbers='{' + ','.join(map(str, game['bonus_numbers'])) + '}' if game['bonus_numbers'] else '{}'
            )
            db.session.add(result)
        
        db.session.commit()
        print(f"Updated database with {len(lottery_data)} authentic lottery results")

if __name__ == "__main__":
    # Extract from the real lottery screenshot
    data = extract_from_image("attached_assets/IMG_8477.png")
    if data:
        update_database(data)
        print("Authentic lottery data extracted and saved to database")
    else:
        print("Failed to extract data")