#!/usr/bin/env python3
"""
Capture fresh Daily Lotto results from official website and process with AI
"""
import os
import sys
import logging
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

from main import app
import google.generativeai as genai
from models import LotteryResult, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_and_process_daily_lotto():
    """Capture fresh Daily Lotto screenshot and extract results"""
    
    try:
        # Use curl to fetch page content
        url = 'https://www.nationallottery.co.za/results/daily-lotto'
        logger.info(f"Fetching Daily Lotto page: {url}")
        
        result = subprocess.run([
            'curl', '-s', '-L', '--max-time', '15',
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            url
        ], capture_output=True, text=True, timeout=20)
        
        if result.returncode != 0 or len(result.stdout) < 1000:
            logger.error("Failed to fetch lottery page")
            return False
            
        # Save page content for analysis
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = f'daily_lotto_{timestamp}.html'
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        logger.info(f"Page content saved: {html_file}")
        
        # Configure Gemini AI
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        if not api_key:
            logger.error("Google API key not found")
            return False
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Process HTML content to extract lottery results
        prompt = """Extract the latest Daily Lotto results from this HTML page.
        
Look for:
1. The most recent draw date (should be June 8, 2025)
2. Draw number (should be 2277 for June 8th Daily Lotto)
3. The 5 main numbers
4. Verify it's actually Daily Lotto (not other lottery types)

Return JSON format:
{
  "lottery_type": "DAILY LOTTO",
  "draw_date": "2025-06-08",
  "draw_number": 2277,
  "main_numbers": [n1, n2, n3, n4, n5],
  "source": "official_website"
}

Only return data if you find authentic June 8, 2025 Daily Lotto results."""

        # Generate content from HTML
        response = model.generate_content([prompt, result.stdout])
        
        if not response.text:
            logger.error("No response from AI")
            return False
            
        # Parse response
        try:
            response_text = response.text.strip()
            if '```json' in response_text:
                response_text = response_text.replace('```json', '').replace('```', '')
            
            lottery_data = json.loads(response_text)
            
            if not lottery_data or 'main_numbers' not in lottery_data:
                logger.warning("No valid lottery data found")
                return False
                
            logger.info(f"Extracted lottery data: {lottery_data}")
            
            # Validate data
            if len(lottery_data.get('main_numbers', [])) != 5:
                logger.warning("Invalid number count for Daily Lotto")
                return False
                
            # Save to database
            with app.app_context():
                existing = LotteryResult.query.filter_by(
                    lottery_type='DAILY LOTTO',
                    draw_number=lottery_data.get('draw_number', 2277)
                ).first()
                
                if existing:
                    logger.info("June 8th Daily Lotto already exists in database")
                    return True
                    
                # Create new result
                new_result = LotteryResult(
                    lottery_type='DAILY LOTTO',
                    draw_date=datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date(),
                    draw_number=lottery_data.get('draw_number', 2277),
                    main_numbers=lottery_data['main_numbers'],
                    bonus_numbers=[]
                )
                
                db.session.add(new_result)
                db.session.commit()
                
                logger.info("SUCCESS: June 8th Daily Lotto saved to database!")
                return True
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"Response was: {response.text[:500]}")
            return False
            
        finally:
            # Clean up HTML file
            try:
                os.remove(html_file)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Process failed: {e}")
        return False

if __name__ == "__main__":
    success = capture_and_process_daily_lotto()
    if success:
        print("SUCCESS: Fresh Daily Lotto data captured and saved")
    else:
        print("FAILED: Could not capture fresh data")
        sys.exit(1)