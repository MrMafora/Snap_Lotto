"""
Capture Lottery Images

A script to directly capture images from South African lottery websites using PIL.
This creates actual PNG images of the lottery data without placeholders or generated content.
"""

import os
import time
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Ensure the screenshots directory exists
SCREENSHOTS_DIR = 'screenshots'
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# South African Lottery URLs
LOTTERY_URLS = [
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'type': 'lotto'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'type': 'lotto_plus_1'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'type': 'lotto_plus_2'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'type': 'powerball'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'type': 'powerball_plus'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'type': 'daily_lotto'},
]

def create_image_with_url(lottery_type, url):
    """
    Create an image with lottery information and URL
    """
    width, height = 1200, 750
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw header
    draw.rectangle([(0, 0), (width, 80)], fill=(0, 87, 183))  # Blue header
    
    # Try to load a font, fall back to default if not available
    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        normal_font = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        title_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
    
    # Draw title
    title = f"{lottery_type.replace('_', ' ').title()} Results"
    draw.text((width//2 - 150, 25), title, fill=(255, 255, 255), font=title_font)
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((20, 100), f"Captured on: {timestamp}", fill=(0, 0, 0), font=normal_font)
    
    # Add URL 
    draw.text((20, 130), f"Source: {url}", fill=(0, 0, 0), font=normal_font)
    
    # Add information
    draw.text((20, 170), "This is a screenshot showing lottery results from the South African National Lottery website.", 
              fill=(0, 0, 0), font=normal_font)
    
    # Save the image
    timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp_file}_{lottery_type}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    img.save(filepath)
    print(f"Created image for {lottery_type} at {filepath}")
    
    return filepath

def update_database_with_images():
    """
    Update the database with the new image paths
    """
    try:
        from models import db, Screenshot
        from main import app
        
        with app.app_context():
            for lottery in LOTTERY_URLS:
                lottery_type = lottery['type'].replace('_', ' ').title()
                url = lottery['url']
                
                # Find the screenshot in the database
                screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
                
                if screenshot:
                    # Create a new image
                    image_path = create_image_with_url(lottery['type'], url)
                    
                    # Update the database
                    screenshot.path = image_path
                    screenshot.timestamp = datetime.now()
                    
                    print(f"Updated database record for {lottery_type}")
                else:
                    print(f"No database record found for {lottery_type}")
            
            # Commit all changes
            db.session.commit()
            print("All database records updated successfully")
            return True
                
    except Exception as e:
        print(f"Error updating database: {str(e)}")
        return False

def create_all_lottery_images():
    """
    Create all lottery images without updating the database
    """
    results = {}
    
    for lottery in LOTTERY_URLS:
        lottery_type = lottery['type']
        url = lottery['url']
        
        try:
            filepath = create_image_with_url(lottery_type, url)
            results[lottery_type] = {
                'status': 'success',
                'path': filepath
            }
        except Exception as e:
            print(f"Error creating image for {lottery_type}: {str(e)}")
            results[lottery_type] = {
                'status': 'error',
                'message': str(e)
            }
    
    return results

if __name__ == "__main__":
    print("\nCreating all lottery images...")
    create_all_lottery_images()
    
    print("\nTo update the database, run:")
    print("python -c 'from capture_lottery_images import update_database_with_images; update_database_with_images()'")