"""
Enhanced Lottery Data Extraction System

This script enhances the extraction system to work with the new PNG-only format
and ensures proper extraction of lottery data from the National Lottery website.
"""
from main import app
from models import Screenshot, ScheduleConfig, PendingExtraction, db
import requests
from bs4 import BeautifulSoup
import logging
import os
from datetime import datetime
import anthropic
import base64
import json
import re
from PIL import Image
import io

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("enhanced_extraction")

# Initialize Anthropic client
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def get_lottery_data_directly(url, lottery_type):
    """
    Get lottery data directly from the website using requests and BeautifulSoup
    
    Args:
        url (str): URL to fetch data from
        lottery_type (str): Type of lottery (e.g., "Daily Lotto")
        
    Returns:
        dict: Extracted lottery data
    """
    logger.info(f"Fetching data directly from {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch URL {url}: HTTP status {response.status_code}")
            return None
            
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract data based on lottery type
        extracted_data = {
            "lottery_type": lottery_type,
            "source_url": url,
            "extraction_timestamp": datetime.now().isoformat(),
            "draw_data": []
        }
        
        # Different extraction logic for different lottery types
        if lottery_type in ["Daily Lotto", "Daily Lotto Results"]:
            # Find the main results container
            results_container = soup.find('div', class_='resultsHeader')
            if not results_container:
                logger.warning(f"Results container not found for {lottery_type}")
                
            # Find the most recent draw date and number
            draw_date_element = soup.find('div', class_='resultsDrawDate')
            draw_number_element = soup.find('div', class_='resultsDrawID')
            
            if draw_date_element and draw_number_element:
                draw_date_text = draw_date_element.text.strip()
                draw_number_text = draw_number_element.text.strip()
                
                # Extract draw number
                draw_number = re.search(r'Draw: (\d+)', draw_number_text)
                if draw_number:
                    draw_number = draw_number.group(1)
                
                # Extract winning numbers
                winning_numbers = []
                ball_elements = soup.find_all('div', class_='resultsNewBallContainer')
                for ball in ball_elements:
                    if ball.text.strip().isdigit():
                        winning_numbers.append(ball.text.strip())
                
                if winning_numbers:
                    extracted_data["draw_data"].append({
                        "draw_number": draw_number,
                        "draw_date": draw_date_text,
                        "winning_numbers": winning_numbers,
                        "bonus_ball": None  # Daily Lotto doesn't have a bonus ball
                    })
        
        elif lottery_type in ["PowerBall", "PowerBall Results", "Powerball", "Powerball Results"]:
            # Find PowerBall specific elements
            results_container = soup.find('div', class_='resultsHeader')
            
            # Find the most recent draw date and number
            draw_date_element = soup.find('div', class_='resultsDrawDate')
            draw_number_element = soup.find('div', class_='resultsDrawID')
            
            if draw_date_element and draw_number_element:
                draw_date_text = draw_date_element.text.strip()
                draw_number_text = draw_number_element.text.strip()
                
                # Extract draw number
                draw_number = re.search(r'Draw: (\d+)', draw_number_text)
                if draw_number:
                    draw_number = draw_number.group(1)
                
                # Extract main winning numbers
                winning_numbers = []
                main_balls = soup.find_all('div', class_='resultsBallContainer')
                for ball in main_balls:
                    if ball.text.strip().isdigit():
                        winning_numbers.append(ball.text.strip())
                
                # Extract PowerBall (bonus)
                powerball = None
                powerball_element = soup.find('div', class_='powerballContainer')
                if powerball_element:
                    powerball = powerball_element.text.strip()
                
                if winning_numbers:
                    extracted_data["draw_data"].append({
                        "draw_number": draw_number,
                        "draw_date": draw_date_text,
                        "winning_numbers": winning_numbers,
                        "bonus_ball": powerball
                    })
                    
        # Similar logic for other lottery types...
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error fetching from {url}: {str(e)}")
        return None

def extract_with_anthropic(screenshot_path, lottery_type):
    """
    Extract lottery data from a screenshot using Anthropic API
    
    Args:
        screenshot_path (str): Path to the screenshot image
        lottery_type (str): Type of lottery
        
    Returns:
        dict: Extracted lottery data or None if extraction failed
    """
    logger.info(f"Extracting data from {screenshot_path} using Anthropic API")
    
    try:
        # Read image file
        with open(screenshot_path, 'rb') as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        # Prepare message for Claude
        prompt = f"""
        Extract lottery results from this image of {lottery_type}. 
        Look for:
        1. Draw number
        2. Draw date
        3. Winning numbers (in order)
        4. Bonus ball (if applicable)
        
        Return the data in this JSON format:
        {{
          "lottery_type": "{lottery_type}",
          "draw_data": [
            {{
              "draw_number": "XXXX",
              "draw_date": "YYYY-MM-DD",
              "winning_numbers": ["X", "X", "X", "X", "X", "X"],
              "bonus_ball": "X"  // Set to null for Daily Lotto which has no bonus ball
            }}
          ]
        }}
        
        Only include what you can see clearly in the image. If any information is unclear or missing, set the corresponding fields to null.
        """
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Using the latest Claude model
            max_tokens=2000,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_base64}}
                ]}
            ]
        )
        
        # Extract JSON from the response
        response_text = response.content[0].text
        
        # Try to extract JSON if it's embedded in text
        try:
            # Look for JSON pattern
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                json_str = json_match.group(1)
                extracted_data = json.loads(json_str)
                logger.info(f"Successfully extracted data using Anthropic API")
                return extracted_data
            else:
                logger.warning("No JSON found in Anthropic response")
                return None
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from Anthropic response")
            return None
            
    except Exception as e:
        logger.error(f"Error using Anthropic API: {str(e)}")
        return None

def save_pending_extraction(extracted_data):
    """
    Save extracted data as a pending extraction for review
    
    Args:
        extracted_data (dict): Extracted lottery data
        
    Returns:
        int: ID of the created pending extraction or None if failed
    """
    with app.app_context():
        try:
            # Convert to JSON
            json_data = json.dumps(extracted_data)
            
            # Get draw number if available
            draw_number = None
            draw_data = extracted_data.get('draw_data', [])
            if draw_data and len(draw_data) > 0:
                draw_number = draw_data[0].get('draw_number')
            
            # Create a new pending extraction
            pending = PendingExtraction(
                lottery_type=extracted_data.get('lottery_type', 'Unknown'),
                draw_number=draw_number,
                raw_data=json_data,
                reviewed=False,
                approved=None,
                extraction_date=datetime.now()
            )
            
            db.session.add(pending)
            db.session.commit()
            
            logger.info(f"Created pending extraction with ID {pending.id}")
            return pending.id
            
        except Exception as e:
            logger.error(f"Error saving pending extraction: {str(e)}")
            return None

def process_lottery_type(lottery_type):
    """
    Process a specific lottery type: capture screenshot, extract data, save for review
    
    Args:
        lottery_type (str): Type of lottery to process
        
    Returns:
        bool: Success status
    """
    with app.app_context():
        # Get config for this lottery type
        config = ScheduleConfig.query.filter_by(lottery_type=lottery_type).first()
        if not config:
            logger.error(f"No configuration found for {lottery_type}")
            return False
        
        url = config.url
        
        # First try to get data directly from the website
        extracted_data = get_lottery_data_directly(url, lottery_type)
        
        if not extracted_data or not extracted_data.get('draw_data'):
            # If direct extraction failed, try using the screenshot with Anthropic
            screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
            if not screenshot or not screenshot.path:
                logger.error(f"No screenshot found for {lottery_type}")
                return False
            
            # Extract data using Anthropic
            if os.path.exists(screenshot.path):
                extracted_data = extract_with_anthropic(screenshot.path, lottery_type)
            else:
                logger.error(f"Screenshot file not found: {screenshot.path}")
                return False
        
        if not extracted_data:
            logger.error(f"Failed to extract data for {lottery_type}")
            return False
        
        # Save as pending extraction
        pending_id = save_pending_extraction(extracted_data)
        return pending_id is not None

def run_enhanced_extraction():
    """
    Run the enhanced extraction process for all lottery types
    
    Returns:
        list: List of lottery types with successful extraction
    """
    successful = []
    
    # Process Daily Lotto
    if process_lottery_type("Daily Lotto"):
        successful.append("Daily Lotto")
    
    # Process Daily Lotto Results
    if process_lottery_type("Daily Lotto Results"):
        successful.append("Daily Lotto Results")
    
    # Process PowerBall (can add other lottery types as needed)
    if process_lottery_type("PowerBall"):
        successful.append("PowerBall")
    
    if process_lottery_type("PowerBall Results"):
        successful.append("PowerBall Results")
    
    return successful

if __name__ == "__main__":
    if ANTHROPIC_API_KEY:
        successful = run_enhanced_extraction()
        logger.info(f"Successfully extracted data for: {successful}")
        print(f"Successfully extracted data for: {successful}")
    else:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        print("ANTHROPIC_API_KEY not found in environment variables")