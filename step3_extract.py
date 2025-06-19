#!/usr/bin/env python3
"""
Step 3: Extract Lottery Data from Captured Content
Processes authentic lottery content captured from SA National Lottery URLs
"""

import os
import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_lottery_data_from_html(filepath, lottery_type):
    """Extract lottery numbers and draw information from captured HTML content"""
    try:
        logger.info(f"Processing {lottery_type} content from {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract lottery numbers using various patterns
        lottery_data = {
            'lottery_type': lottery_type,
            'main_numbers': [],
            'bonus_numbers': [],
            'draw_date': None,
            'draw_number': None,
            'jackpot_amount': None,
            'next_draw_date': None
        }
        
        # Look for number patterns in the HTML
        # Pattern 1: Look for ball numbers in spans or divs
        ball_elements = soup.find_all(['span', 'div'], class_=re.compile(r'ball|number|result'))
        for element in ball_elements:
            text = element.get_text().strip()
            if text.isdigit() and 1 <= int(text) <= 60:
                lottery_data['main_numbers'].append(int(text))
        
        # Pattern 2: Look for JSON data in script tags
        script_tags = soup.find_all('script')
        for script in script_tags:
            script_content = script.get_text()
            
            # Look for draw dates
            date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', script_content)
            if date_matches and not lottery_data['draw_date']:
                lottery_data['draw_date'] = date_matches[0]
            
            # Look for number arrays
            number_arrays = re.findall(r'\[(\d+(?:,\s*\d+)*)\]', script_content)
            for array in number_arrays:
                numbers = [int(n.strip()) for n in array.split(',')]
                if len(numbers) >= 5 and all(1 <= n <= 60 for n in numbers):
                    if not lottery_data['main_numbers']:
                        lottery_data['main_numbers'] = numbers[:6]  # Take first 6 for main numbers
                    elif len(numbers) == 1 and not lottery_data['bonus_numbers']:
                        lottery_data['bonus_numbers'] = numbers  # Single number for bonus
        
        # Pattern 3: Look for prize amounts
        amount_pattern = r'R(\d+(?:,\d+)*(?:\.\d+)?)\s*Million'
        amount_matches = re.findall(amount_pattern, html_content)
        if amount_matches:
            lottery_data['jackpot_amount'] = f"R{amount_matches[0]} Million"
        
        # Pattern 4: Extract from text content
        text_content = soup.get_text()
        
        # Look for "Last Draw" dates
        last_draw_pattern = r'Last Draw:\s*(\d{1,2}\s+\w+\s+\d{4})'
        last_draw_match = re.search(last_draw_pattern, text_content)
        if last_draw_match and not lottery_data['draw_date']:
            lottery_data['draw_date'] = last_draw_match.group(1)
        
        # Look for "Next Draw" dates
        next_draw_pattern = r'Next Draw:\s*(\d{1,2}\s+\w+,?\s+\d{4})'
        next_draw_match = re.search(next_draw_pattern, text_content)
        if next_draw_match:
            lottery_data['next_draw_date'] = next_draw_match.group(1)
        
        # Remove duplicates and sort main numbers
        if lottery_data['main_numbers']:
            lottery_data['main_numbers'] = sorted(list(set(lottery_data['main_numbers'])))
        
        if lottery_data['bonus_numbers']:
            lottery_data['bonus_numbers'] = sorted(list(set(lottery_data['bonus_numbers'])))
        
        logger.info(f"Extracted data for {lottery_type}: {lottery_data}")
        return lottery_data
        
    except Exception as e:
        logger.error(f"Error extracting data from {filepath}: {str(e)}")
        return None

def process_captured_content():
    """Process all captured HTML content files"""
    logger.info("=== STEP 3: LOTTERY DATA EXTRACTION STARTED ===")
    
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    if not os.path.exists(screenshot_dir):
        logger.error("Screenshots directory not found")
        return []
    
    # Find all HTML content files
    html_files = [f for f in os.listdir(screenshot_dir) if f.endswith('_content.html')]
    
    if not html_files:
        logger.warning("No HTML content files found for processing")
        return []
    
    extracted_data = []
    
    for html_file in html_files:
        filepath = os.path.join(screenshot_dir, html_file)
        
        # Determine lottery type from filename
        if 'lotto_plus_1' in html_file:
            lottery_type = 'Lotto Plus 1'
        elif 'lotto_plus_2' in html_file:
            lottery_type = 'Lotto Plus 2'
        elif 'lotto' in html_file and 'plus' not in html_file:
            lottery_type = 'Lotto'
        elif 'powerball_plus' in html_file:
            lottery_type = 'Powerball Plus'
        elif 'powerball' in html_file:
            lottery_type = 'Powerball'
        elif 'daily_lotto' in html_file:
            lottery_type = 'Daily Lotto'
        else:
            lottery_type = 'Unknown'
        
        # Extract lottery data
        data = extract_lottery_data_from_html(filepath, lottery_type)
        if data:
            extracted_data.append(data)
    
    logger.info("=== STEP 3: LOTTERY DATA EXTRACTION COMPLETED ===")
    logger.info(f"Successfully extracted data from {len(extracted_data)} files")
    
    # Save extracted data to JSON file
    output_file = os.path.join(screenshot_dir, f"extracted_lottery_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Extracted data saved to: {output_file}")
    
    return extracted_data

if __name__ == "__main__":
    results = process_captured_content()
    print(f"Extracted lottery data from {len(results)} files")