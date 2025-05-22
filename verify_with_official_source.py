#!/usr/bin/env python3
"""
Verify lottery draw data against the official South African National Lottery website.
This script reaches out to the official source to get the most accurate information.
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import trafilatura

# Import app and database
try:
    from main import app, db
    from models import LotteryResult
except ImportError:
    print("Could not import app or models. Make sure you're in the right directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('official_verification')

# Official URLs for latest results
OFFICIAL_URLS = {
    "Lottery": "https://www.nationallottery.co.za/lotto-history",
    "Lottery Plus 1": "https://www.nationallottery.co.za/lotto-plus-1-history",
    "Lottery Plus 2": "https://www.nationallottery.co.za/lotto-plus-2-history",
    "Powerball": "https://www.nationallottery.co.za/powerball-history",
    "Powerball Plus": "https://www.nationallottery.co.za/powerball-plus-history",
    "Daily Lottery": "https://www.nationallottery.co.za/daily-lotto-history"
}

# Alternative URLs for the latest results
LATEST_RESULT_URLS = {
    "Lottery": "https://www.nationallottery.co.za/results/lotto",
    "Lottery Plus 1": "https://www.nationallottery.co.za/results/lotto-plus-1-results",
    "Lottery Plus 2": "https://www.nationallottery.co.za/results/lotto-plus-2-results",
    "Powerball": "https://www.nationallottery.co.za/results/powerball",
    "Powerball Plus": "https://www.nationallottery.co.za/results/powerball-plus",
    "Daily Lottery": "https://www.nationallottery.co.za/results/daily-lotto"
}

def get_website_text(url):
    """
    Retrieves and extracts the main text content from a webpage.
    
    Args:
        url (str): The URL of the webpage to fetch
        
    Returns:
        str: The extracted text content
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            return text
        return None
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None

def get_webpage_content(url):
    """
    Fetch webpage content using requests and BeautifulSoup.
    
    Args:
        url (str): The URL to fetch
        
    Returns:
        BeautifulSoup: Parsed HTML content
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None

def extract_draw_info_using_openai(content, lottery_type):
    """
    Use OpenAI to extract structured draw information from webpage content.
    
    Args:
        content (str): Text content from the website
        lottery_type (str): Type of lottery
        
    Returns:
        dict: Structured draw information
    """
    try:
        from ocr_integrations import query_openai
        
        prompt = f"""
        You are helping to extract lottery draw information from the South African National Lottery website.
        The text content is from the {lottery_type} results page.
        
        Please extract:
        1. The latest draw number (just the number, no text)
        2. The draw date (in YYYY-MM-DD format)
        3. The winning numbers (as an array of strings)
        4. The bonus or powerball number(s) if applicable (as an array of strings)
        
        Return the information in JSON format with these keys:
        {{
            "draw_number": "the draw number as a string",
            "draw_date": "the date in YYYY-MM-DD format",
            "winning_numbers": ["the", "winning", "numbers", "as", "strings"],
            "bonus_numbers": ["bonus", "or", "powerball", "numbers"]
        }}
        
        The text content is:
        {content[:4000]}  # Limit to avoid token limits
        """
        
        response = query_openai(prompt)
        
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            import re
            json_match = re.search(r'({[\s\S]*})', response)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                return data
            else:
                logger.warning(f"Could not find JSON in OpenAI response for {lottery_type}")
                return None
        except Exception as json_err:
            logger.error(f"Error parsing JSON from OpenAI response for {lottery_type}: {json_err}")
            return None
            
    except Exception as e:
        logger.error(f"Error querying OpenAI for {lottery_type}: {e}")
        return None

def verify_with_official_sources():
    """
    Verify lottery data against official sources.
    """
    print("Verifying lottery draw data with official South African National Lottery sources...")
    print("-" * 80)
    
    official_data = {}
    
    # Try each URL to get official information
    for lottery_type, url in OFFICIAL_URLS.items():
        print(f"\nChecking {lottery_type}:")
        
        # First try with trafilatura for text extraction
        text_content = get_website_text(url)
        if text_content:
            # Use OpenAI to extract structured data
            draw_info = extract_draw_info_using_openai(text_content, lottery_type)
            
            if draw_info and "draw_number" in draw_info:
                official_data[lottery_type] = draw_info
                print(f"  Official Draw #{draw_info['draw_number']} on {draw_info.get('draw_date', 'unknown date')}")
                print(f"  Numbers: {', '.join(draw_info.get('winning_numbers', []))}")
                if "bonus_numbers" in draw_info and draw_info["bonus_numbers"]:
                    print(f"  Bonus: {', '.join(draw_info.get('bonus_numbers', []))}")
            else:
                print(f"  Could not extract draw information from {url}")
                
                # Try alternate URL
                alt_url = LATEST_RESULT_URLS.get(lottery_type)
                if alt_url:
                    print(f"  Trying alternate URL: {alt_url}")
                    alt_text = get_website_text(alt_url)
                    if alt_text:
                        alt_draw_info = extract_draw_info_using_openai(alt_text, lottery_type)
                        if alt_draw_info and "draw_number" in alt_draw_info:
                            official_data[lottery_type] = alt_draw_info
                            print(f"  Official Draw #{alt_draw_info['draw_number']} on {alt_draw_info.get('draw_date', 'unknown date')}")
                            print(f"  Numbers: {', '.join(alt_draw_info.get('winning_numbers', []))}")
                            if "bonus_numbers" in alt_draw_info and alt_draw_info["bonus_numbers"]:
                                print(f"  Bonus: {', '.join(alt_draw_info.get('bonus_numbers', []))}")
                        else:
                            print(f"  Could not extract draw information from alternate URL")
                    else:
                        print(f"  Could not get content from alternate URL")
        else:
            print(f"  Could not get content from {url}")
        
        # Sleep to avoid rate limiting
        time.sleep(2)
    
    return official_data

def compare_database_with_official(official_data):
    """
    Compare database records with official data.
    
    Args:
        official_data (dict): Official data from the lottery website
    """
    print("\n\nComparing database with official draw data:")
    print("-" * 80)
    
    corrections_needed = []
    
    with app.app_context():
        for lottery_type, draw_info in official_data.items():
            official_draw_number = draw_info.get("draw_number")
            if not official_draw_number:
                continue
                
            # Query database for this lottery type
            latest_draw = LotteryResult.query.filter_by(
                lottery_type=lottery_type
            ).order_by(db.desc(LotteryResult.draw_date)).first()
            
            # Also check variations in naming
            if not latest_draw and "Lottery" in lottery_type:
                alt_type = lottery_type.replace("Lottery", "Lotto")
                latest_draw = LotteryResult.query.filter_by(
                    lottery_type=alt_type
                ).order_by(db.desc(LotteryResult.draw_date)).first()
            
            if latest_draw:
                db_draw_number = latest_draw.draw_number
                db_date = latest_draw.draw_date.strftime("%Y-%m-%d") if latest_draw.draw_date else "unknown"
                
                # Compare draw numbers
                if db_draw_number != official_draw_number:
                    print(f"❌ {lottery_type}: Database shows #{db_draw_number}, Official shows #{official_draw_number}")
                    corrections_needed.append({
                        "lottery_type": lottery_type,
                        "db_draw_number": db_draw_number,
                        "official_draw_number": official_draw_number,
                        "db_id": latest_draw.id
                    })
                else:
                    print(f"✅ {lottery_type}: Database and official both show #{db_draw_number}")
                
                # Log additional info
                print(f"   Database date: {db_date}")
                official_date = draw_info.get("draw_date", "unknown")
                print(f"   Official date: {official_date}")
            else:
                print(f"❓ {lottery_type}: No records found in database to compare")
    
    return corrections_needed

def main():
    """Main function to verify lottery data with official sources."""
    try:
        # Get official data from the lottery website
        official_data = verify_with_official_sources()
        
        # Compare with our database
        if official_data:
            corrections = compare_database_with_official(official_data)
            
            if corrections:
                print("\n\nCorrections needed:")
                print("-" * 80)
                for correction in corrections:
                    lottery_type = correction.get("lottery_type")
                    db_number = correction.get("db_draw_number")
                    official_number = correction.get("official_draw_number")
                    print(f"{lottery_type}: Change #{db_number} to #{official_number}")
                
                print("\nUse the following correct draw numbers to update your database:")
                for lottery_type, draw_info in official_data.items():
                    print(f"{lottery_type}: #{draw_info.get('draw_number', 'unknown')}")
            else:
                print("\nAll draw numbers match official data!")
        else:
            print("\nCould not retrieve official data for verification.")
        
    except Exception as e:
        logger.error(f"Error verifying with official sources: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()