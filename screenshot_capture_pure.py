"""
Pure Python Screenshot Alternative - No Browser Dependencies
Uses requests + BeautifulSoup to fetch lottery data for AI processing
"""

import os
import time
import logging
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from models import Screenshot, db

# Configure logging
logger = logging.getLogger(__name__)

# South African Lottery URLs
LOTTERY_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
}


def fetch_lottery_content_pure(lottery_type, url, output_dir='screenshots'):
    """
    Pure Python approach: Fetch lottery content and save as HTML for AI processing
    This avoids browser dependency issues while still getting authentic data
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') 
    unique_id = int(time.time() * 1000000) % 1000000
    filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}_content_{unique_id}.html"
    filepath = os.path.join(output_dir, filename)
    
    try:
        logger.info(f"Starting PURE PYTHON fetch: {lottery_type} from {url}")
        
        # Create session with realistic headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        
        # Fetch the page content with proper encoding handling
        logger.info(f"Fetching content from {url}...")
        response = session.get(url, timeout=30, stream=True)
        response.raw.decode_content = True  # Handle gzip encoding properly
        response.raise_for_status()
        
        # Force UTF-8 encoding
        response.encoding = 'utf-8'
        
        # Parse with BeautifulSoup and clean up
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract key content sections (lottery results, prize divisions, etc.)
        content_html = extract_lottery_content(soup, lottery_type)
        
        # Save cleaned HTML content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content_html)
        
        file_size = os.path.getsize(filepath)
        logger.info(f"✓ PURE PYTHON SUCCESS: {filepath} ({file_size:,} bytes)")
        
        # Save to database
        screenshot = Screenshot(
            lottery_type=lottery_type,
            filename=filename,
            file_path=filepath,
            file_size=file_size,
            capture_method='PURE_PYTHON',
            capture_timestamp=datetime.now(),
            url=url
        )
        db.session.add(screenshot)
        db.session.commit()
        logger.info(f"Saved to database: Screenshot ID {screenshot.id}")
        
        return {
            'success': True,
            'lottery_type': lottery_type,
            'filepath': filepath,
            'file_size': file_size,
            'method': 'PURE_PYTHON'
        }
        
    except Exception as e:
        logger.error(f"Pure Python fetch error for {lottery_type}: {e}")
        return {
            'success': False,
            'lottery_type': lottery_type,
            'error': str(e)
        }


def extract_lottery_content(soup, lottery_type):
    """
    Extract and structure lottery content for AI processing
    Returns clean HTML with all necessary lottery information
    """
    try:
        # Create structured HTML template
        content_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>South African {lottery_type} Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .lottery-header {{ background: #2c5aa0; color: white; padding: 10px; }}
        .lottery-results {{ margin: 20px 0; }}
        .winning-numbers {{ font-size: 18px; font-weight: bold; margin: 10px 0; }}
        .prize-divisions {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .prize-divisions th, .prize-divisions td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .financial-info {{ background: #f5f5f5; padding: 15px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="lottery-header">
        <h1>PHANDA PUSHA PLAY - South African National Lottery</h1>
        <h2>{lottery_type} Results</h2>
    </div>
    <div class="lottery-results">
"""
        
        # Extract winning numbers
        numbers_section = soup.find_all('div', class_=['results-numbers', 'winning-numbers', 'lottery-balls'])
        if numbers_section:
            content_html += '<div class="winning-numbers">Winning Numbers: '
            # Try to find number elements
            for section in numbers_section:
                numbers = section.find_all(['span', 'div'], class_=['ball', 'number', 'lottery-ball'])
                if numbers:
                    for num in numbers:
                        content_html += f'<span class="number-ball">{num.get_text().strip()}</span> '
            content_html += '</div>'
        
        # Extract prize divisions table
        tables = soup.find_all('table')
        for table in tables:
            # Look for prize division tables
            headers = table.find_all('th')
            if headers and any('prize' in header.get_text().lower() or 'division' in header.get_text().lower() for header in headers):
                content_html += str(table)
                break
        
        # Extract financial information
        financial_sections = soup.find_all('div', class_=['financial-info', 'jackpot-info', 'rollover'])
        for section in financial_sections:
            content_html += f'<div class="financial-info">{section}</div>'
        
        # Extract draw information
        draw_info = soup.find_all('div', class_=['draw-info', 'draw-details'])
        for info in draw_info:
            content_html += f'<div class="draw-info">{info}</div>'
        
        # Add all text content as fallback
        if not any(['winning-numbers' in content_html, 'prize-divisions' in content_html]):
            # Extract all visible text if structured data not found
            visible_text = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in visible_text.split('\n') if line.strip()]
            
            content_html += '<div class="extracted-content">'
            for line in lines[:100]:  # Limit to first 100 lines
                if any(keyword in line.lower() for keyword in ['lotto', 'powerball', 'daily', 'draw', 'number', 'prize', 'jackpot']):
                    content_html += f'<p>{line}</p>'
            content_html += '</div>'
        
        content_html += """
    </div>
</body>
</html>
"""
        
        return content_html
        
    except Exception as e:
        logger.error(f"Content extraction error: {e}")
        # Return basic HTML with raw content as fallback
        return f"""
<!DOCTYPE html>
<html><head><title>{lottery_type} Results</title></head>
<body>
<h1>{lottery_type} Results</h1>
<div>{soup}</div>
</body></html>
"""


def capture_all_lottery_screenshots_pure():
    """
    Pure Python version: Capture all 6 lottery types using requests
    """
    results = {
        'successful': [],
        'failed': [],
        'total_success': 0,
        'total_failed': 0
    }
    
    logger.info("Starting PURE PYTHON capture for all 6 lottery types...")
    
    for lottery_type, url in LOTTERY_URLS.items():
        logger.info(f"Capturing {lottery_type}...")
        result = fetch_lottery_content_pure(lottery_type, url)
        
        if result['success']:
            results['successful'].append(result)
            results['total_success'] += 1
        else:
            results['failed'].append(result)
            results['total_failed'] += 1
    
    logger.info(f"Pure Python capture complete: {results['total_success']}/6 successful")
    return results


def test_pure_method():
    """Test the pure Python method"""
    logger.info("Testing PURE PYTHON method...")
    result = fetch_lottery_content_pure('LOTTO', LOTTERY_URLS['LOTTO'])
    if result['success']:
        logger.info("✓ PURE PYTHON TEST SUCCESS")
        return True
    else:
        logger.error("❌ PURE PYTHON TEST FAILED")
        return False