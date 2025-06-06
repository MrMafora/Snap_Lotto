"""
Quick extraction test for fresh screenshots
"""
import os
import base64
import json
import logging
from datetime import datetime
from anthropic import Anthropic
from main import app, db
from models import LotteryResult

#the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
def quick_extract(image_path):
    """Fast extraction for testing"""
    try:
        client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY'))
        
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extract lottery data from this image. Return JSON with: lottery_type, draw_number, draw_date, main_numbers, bonus_number (if exists)"
                    }
                ]
            }]
        )
        
        # Handle response content properly
        response_text = response.content[0].text
        print(f"Raw response: {response_text}")
        
        # Find JSON in response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = response_text[start:end]
            result = json.loads(json_str)
        else:
            print("No valid JSON found in response")
            return None
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    with app.app_context():
        # Test with Daily Lotto
        result = quick_extract('screenshots/20250606_172030_daily_lotto.png')
        if result:
            print(f"Extracted: {result}")
            
            # Save to database
            lottery_result = LotteryResult(
                lottery_type=result['lottery_type'],
                draw_number=str(result['draw_number']),
                draw_date=datetime.fromisoformat(result['draw_date']) if result.get('draw_date') else datetime.now(),
                numbers=json.dumps(result['main_numbers']),
                bonus_numbers=json.dumps([result['bonus_number']]) if result.get('bonus_number') else None,
                source_url='quick_extract',
                ocr_provider='anthropic',
                ocr_model='claude-3-5-sonnet-20241022'
            )
            
            db.session.add(lottery_result)
            db.session.commit()
            print("Saved to database")
        else:
            print("No data extracted")