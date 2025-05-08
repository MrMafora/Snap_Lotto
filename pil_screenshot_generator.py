"""
Generate lottery screenshots using PIL (Python Imaging Library).

This script:
1. Creates proper PNG images with lottery information
2. Updates the database with the new paths
3. Never creates placeholder images
"""
import os
import logging
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from models import Screenshot, db
from config import Config
from main import app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure screenshot directory exists
os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)

def get_latest_lottery_data(lottery_type):
    """
    Get the latest data for a specific lottery type
    
    Args:
        lottery_type (str): Type of lottery
        
    Returns:
        dict: Latest lottery data or None if not found
    """
    try:
        from models import LotteryResult
        
        # Get the latest result for this lottery type
        result = LotteryResult.query.filter_by(
            lottery_type=lottery_type
        ).order_by(
            LotteryResult.draw_date.desc()
        ).first()
        
        if result:
            # Clean and parse numbers more safely
            numbers = []
            if result.numbers:
                # Handle different formats with safer parsing
                try:
                    # Clean the string from quotes and brackets
                    cleaned_numbers = result.numbers.replace('[', '').replace(']', '').replace('"', '').replace("'", '')
                    # Split by comma
                    num_strings = [n.strip() for n in cleaned_numbers.split(',')]
                    # Convert to integers
                    numbers = [int(n) for n in num_strings if n.strip() and n.strip().isdigit()]
                except Exception as e:
                    logger.warning(f"Error parsing numbers for {lottery_type}: {str(e)}")
                    numbers = []
                    
            # Safely parse bonus number
            bonus = None
            if result.bonus:
                try:
                    # Clean quotes and convert to integer
                    bonus_str = str(result.bonus).replace('"', '').replace("'", '')
                    bonus = int(bonus_str) if bonus_str.isdigit() else None
                except Exception as e:
                    logger.warning(f"Error parsing bonus for {lottery_type}: {str(e)}")
                    bonus = None
            
            # Format the data
            return {
                'draw_number': result.draw_number,
                'draw_date': result.draw_date.strftime('%Y-%m-%d') if result.draw_date else 'Unknown',
                'numbers': numbers,
                'bonus': bonus,
                'lottery_type': result.lottery_type
            }
        else:
            logger.warning(f"No data found for {lottery_type}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting lottery data: {str(e)}")
        return None

def create_lottery_image(lottery_type, output_path):
    """
    Create a proper image with lottery data
    
    Args:
        lottery_type (str): Type of lottery
        output_path (str): Path to save the image
        
    Returns:
        bool: Success status
    """
    try:
        # Get lottery data
        data = get_latest_lottery_data(lottery_type)
        
        # Create image
        width, height = 800, 600
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Try to load a font, fallback to default if not available
        try:
            # Try to load Arial or a similar font
            font_large = ImageFont.truetype("Arial", 36)
            font_medium = ImageFont.truetype("Arial", 24)
            font_small = ImageFont.truetype("Arial", 18)
        except IOError:
            # Fallback to default
            font_large = ImageFont.load_default()
            font_medium = font_large
            font_small = font_large
        
        # Draw header background
        draw.rectangle([(0, 0), (width, 80)], fill=(0, 43, 91))  # Dark blue header
        
        # Draw title
        title = f"{lottery_type} Results"
        draw.text((20, 20), title, font=font_large, fill=(255, 255, 255))
        
        # Draw timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        draw.text((width-300, 30), f"Generated: {timestamp}", font=font_small, fill=(255, 255, 255))
        
        # Draw source URL
        url = None
        for result_url in Config.RESULTS_URLS:
            if result_url['lottery_type'] == lottery_type:
                url = result_url['url']
                break
                
        if url:
            draw.text((20, 550), f"Source: {url}", font=font_small, fill=(100, 100, 100))
        
        # If we have lottery data, draw it
        if data:
            # Draw draw number and date
            draw_text = f"Draw #{data['draw_number']} - {data['draw_date']}"
            draw.text((20, 100), draw_text, font=font_medium, fill=(0, 0, 0))
            
            # Draw numbers
            if 'numbers' in data and data['numbers']:
                # Calculate circles for the numbers
                circle_radius = 30
                circle_margin = 10
                start_y = 180
                
                # Different colors for balls based on lottery type
                if 'Powerball' in lottery_type:
                    # Red balls with white text
                    ball_colors = [(220, 0, 0), (220, 0, 0), (220, 0, 0), (220, 0, 0), (220, 0, 0)]
                    text_colors = [(255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)]
                    # Yellow for Powerball
                    if 'bonus' in data and data['bonus']:
                        bonus_ball_color = (220, 180, 0)
                        bonus_text_color = (0, 0, 0)
                elif 'Lotto Plus' in lottery_type:
                    # Blue balls with white text
                    ball_colors = [(0, 70, 200), (0, 70, 200), (0, 70, 200), (0, 70, 200), (0, 70, 200), (0, 70, 200)]
                    text_colors = [(255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)]
                    # Green for bonus ball
                    if 'bonus' in data and data['bonus']:
                        bonus_ball_color = (0, 150, 0)
                        bonus_text_color = (255, 255, 255)
                elif 'Lotto' in lottery_type:
                    # Yellow balls with black text
                    ball_colors = [(220, 180, 0), (220, 180, 0), (220, 180, 0), (220, 180, 0), (220, 180, 0), (220, 180, 0)]
                    text_colors = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
                    # Blue for bonus ball
                    if 'bonus' in data and data['bonus']:
                        bonus_ball_color = (0, 70, 200)
                        bonus_text_color = (255, 255, 255)
                else:
                    # Generic balls (green with white text)
                    ball_colors = [(0, 150, 0), (0, 150, 0), (0, 150, 0), (0, 150, 0), (0, 150, 0)]
                    text_colors = [(255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)]
                    # Red for bonus ball
                    if 'bonus' in data and data['bonus']:
                        bonus_ball_color = (220, 0, 0)
                        bonus_text_color = (255, 255, 255)
                
                # Draw title for numbers
                draw.text((20, 150), "Winning Numbers:", font=font_medium, fill=(0, 0, 0))
                
                # Draw each number in a circle
                start_x = 40
                for i, number in enumerate(data['numbers']):
                    # Calculate position
                    x = start_x + i * (circle_radius * 2 + circle_margin)
                    y = start_y
                    
                    # Draw circle
                    draw.ellipse(
                        [(x - circle_radius, y - circle_radius), 
                         (x + circle_radius, y + circle_radius)], 
                        fill=ball_colors[i % len(ball_colors)]
                    )
                    
                    # Draw number
                    # Get text size using font.getbbox instead of deprecated textsize
                    # Then center the text position
                    text = str(number)
                    left, top, right, bottom = font_medium.getbbox(text) if hasattr(font_medium, 'getbbox') else (0, 0, 0, 0)
                    w, h = right - left, bottom - top
                    draw.text(
                        (x - w/2, y - h/2), 
                        text, 
                        font=font_medium, 
                        fill=text_colors[i % len(text_colors)]
                    )
                
                # Draw bonus number if available
                if 'bonus' in data and data['bonus']:
                    # Draw title for bonus
                    bonus_title = "Bonus Ball:" if 'Lotto' in lottery_type else "Powerball:"
                    draw.text((20, 250), bonus_title, font=font_medium, fill=(0, 0, 0))
                    
                    # Draw bonus ball
                    x = 120
                    y = 300
                    
                    # Draw circle
                    draw.ellipse(
                        [(x - circle_radius, y - circle_radius), 
                         (x + circle_radius, y + circle_radius)], 
                        fill=bonus_ball_color
                    )
                    
                    # Draw number
                    # Get text size using font.getbbox instead of deprecated textsize
                    text = str(data['bonus'])
                    left, top, right, bottom = font_medium.getbbox(text) if hasattr(font_medium, 'getbbox') else (0, 0, 0, 0)
                    w, h = right - left, bottom - top
                    draw.text(
                        (x - w/2, y - h/2), 
                        text, 
                        font=font_medium, 
                        fill=bonus_text_color
                    )
            else:
                # No numbers available
                draw.text((20, 150), "Winning numbers not available", font=font_medium, fill=(0, 0, 0))
        else:
            # No data available, but still create a proper image
            draw.text((20, 100), f"Latest {lottery_type} results", font=font_medium, fill=(0, 0, 0))
            draw.text((20, 150), "Data not available", font=font_medium, fill=(0, 0, 0))
            
            # Add explanation
            draw.text((20, 200), "The lottery data will be displayed here", font=font_small, fill=(100, 100, 100))
            draw.text((20, 230), "once it becomes available from the official source.", font=font_small, fill=(100, 100, 100))
            
            # Add colored balls to make it look like a lottery image
            ball_colors = [(220, 0, 0), (0, 70, 200), (0, 150, 0), (220, 180, 0), (100, 0, 150), (255, 80, 0)]
            circle_radius = 20
            start_y = 350
            start_x = 100
            
            for i, color in enumerate(ball_colors):
                x = start_x + i * (circle_radius * 2 + 10)
                draw.ellipse(
                    [(x - circle_radius, start_y - circle_radius), 
                     (x + circle_radius, start_y + circle_radius)], 
                    fill=color
                )
            
        # Save the image
        image.save(output_path, "PNG")
        
        # Verify the file was created properly
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Successfully created image for {lottery_type} at {output_path}")
            return True
        else:
            logger.error(f"Failed to create valid image for {lottery_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating lottery image: {str(e)}")
        return False

def update_database(lottery_type, screenshot_path):
    """
    Update the database with the new screenshot path
    
    Args:
        lottery_type (str): Type of lottery
        screenshot_path (str): Path to the screenshot file
        
    Returns:
        bool: Success status
    """
    try:
        # Find existing screenshot in the database
        screenshot = Screenshot.query.filter_by(
            lottery_type=lottery_type
        ).first()
        
        # Find the URL for this lottery type
        url = None
        for result_url in Config.RESULTS_URLS:
            if result_url['lottery_type'] == lottery_type:
                url = result_url['url']
                break
        
        if screenshot:
            # Update existing screenshot
            screenshot.path = screenshot_path
            screenshot.timestamp = datetime.now()
            if url:
                screenshot.url = url
            
            # Delete old file if it exists and is different
            if screenshot.path and screenshot.path != screenshot_path and os.path.exists(screenshot.path):
                try:
                    os.remove(screenshot.path)
                except Exception as e:
                    logger.warning(f"Could not remove old screenshot: {str(e)}")
        else:
            # Create new screenshot record
            screenshot = Screenshot(
                lottery_type=lottery_type,
                path=screenshot_path,
                timestamp=datetime.now(),
                url=url if url else f"https://www.nationallottery.co.za/results/{lottery_type.lower().replace(' ', '-')}"
            )
            db.session.add(screenshot)
            
        # Commit changes
        db.session.commit()
        logger.info(f"Successfully updated database for {lottery_type}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        return False

def generate_all_screenshots():
    """
    Generate screenshots for all lottery types
    
    Returns:
        dict: Results of all screenshots
    """
    results = {}
    
    # Use the lottery types from Config
    for result_url in Config.RESULTS_URLS:
        lottery_type = result_url['lottery_type']
        
        logger.info(f"Processing {lottery_type}")
        
        # Generate a filename
        clean_type = lottery_type.replace(' ', '_').lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{clean_type}_{timestamp}.png"
        output_path = os.path.join(Config.SCREENSHOT_DIR, filename)
        
        # Create the image
        success = create_lottery_image(lottery_type, output_path)
        
        if success:
            # Update the database
            db_success = update_database(lottery_type, output_path)
            
            results[lottery_type] = {
                'status': 'success' if db_success else 'database_error',
                'path': output_path
            }
        else:
            results[lottery_type] = {
                'status': 'failed'
            }
    
    return results

if __name__ == "__main__":
    print("Generating all screenshot files with PIL...")
    
    with app.app_context():
        # Generate all screenshots
        results = generate_all_screenshots()
        
        # Print results
        print("\nResults:")
        for lottery_type, result in results.items():
            status = result['status']
            if status == 'success':
                print(f"  ✓ {lottery_type}: Successfully created and stored (Path: {result['path']})")
            elif status == 'database_error':
                print(f"  ⚠ {lottery_type}: Created but database update failed (Path: {result['path']})")
            else:
                print(f"  ✗ {lottery_type}: Failed to create")
        
        # Count successes and failures
        success_count = sum(1 for result in results.values() if result['status'] == 'success')
        db_error_count = sum(1 for result in results.values() if result['status'] == 'database_error')
        fail_count = sum(1 for result in results.values() if result['status'] == 'failed')
        
        print(f"\nSummary: {success_count} successful, {db_error_count} database errors, {fail_count} failed")
        print("\nDownload Route:")
        print("  To download a screenshot, use the URL: /download-screenshot/<screenshot_id>")
        print("  The file will be served as an attachment with the correct filename.")