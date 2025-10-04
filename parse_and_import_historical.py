#!/usr/bin/env python3
"""
Parse fetched HTML data and import lottery results into the database
"""

import json
import re
import psycopg2
import logging
import os
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_lottery_result(html_content, lottery_type, url):
    """
    Parse lottery result from HTML content
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract draw date from URL (format: DD-MONTH-YYYY)
        date_match = re.search(r'(\d{1,2})-(january|february|march|april|may|june|july|august|september|october|november|december)-(\d{4})', url.lower())
        if not date_match:
            logger.warning(f"Could not extract date from URL: {url}")
            return None
        
        day, month_name, year = date_match.groups()
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        month = month_map[month_name.lower()]
        draw_date = f"{year}-{month:02d}-{int(day):02d}"
        
        # Extract winning numbers (look for number balls or number lists)
        numbers = []
        bonus_numbers = []
        
        # Look for number elements with various class patterns
        number_elements = soup.find_all(class_=re.compile(r'ball|number|winning', re.I))
        
        for elem in number_elements:
            text = elem.get_text(strip=True)
            # Extract numbers from text
            if text.isdigit() and 1 <= int(text) <= 60:
                num = int(text)
                if num not in numbers and len(numbers) < 7:  # Max 6 main + 1 bonus
                    numbers.append(num)
        
        # Try alternative: look for text patterns like "Winning Numbers: 1, 2, 3, 4, 5, 6"
        text_content = soup.get_text()
        number_pattern = re.findall(r'\b([1-9]|[1-5][0-9]|60)\b', text_content)
        
        if not numbers and number_pattern:
            # Get first 6-7 numbers found
            for num_str in number_pattern[:8]:
                num = int(num_str)
                if 1 <= num <= 60 and num not in numbers:
                    numbers.append(num)
        
        # Extract draw number/ID
        draw_number = None
        draw_id_match = re.search(r'draw[:\s#]*(\d+)', text_content, re.I)
        if draw_id_match:
            draw_number = int(draw_id_match.group(1))
        
        # For LOTTO types: 6 main numbers + 1 bonus
        # For POWERBALL: 5 main + 1 powerball
        # For DAILY LOTTO: 5 numbers, no bonus
        
        if lottery_type == 'DAILY LOTTO':
            main_numbers = sorted(numbers[:5]) if len(numbers) >= 5 else sorted(numbers)
            bonus_numbers = []
        elif 'POWERBALL' in lottery_type:
            main_numbers = sorted(numbers[:5]) if len(numbers) >= 5 else sorted(numbers[:5])
            bonus_numbers = numbers[5:6] if len(numbers) > 5 else []
        else:  # LOTTO types
            main_numbers = sorted(numbers[:6]) if len(numbers) >= 6 else sorted(numbers[:6])
            bonus_numbers = numbers[6:7] if len(numbers) > 6 else []
        
        if not main_numbers:
            logger.warning(f"No numbers found for {lottery_type} on {draw_date}")
            return None
        
        result = {
            'lottery_type': lottery_type,
            'draw_number': draw_number,
            'draw_date': draw_date,
            'main_numbers': main_numbers,
            'bonus_numbers': bonus_numbers
        }
        
        logger.info(f"Parsed {lottery_type} {draw_date}: {main_numbers} + {bonus_numbers}")
        return result
        
    except Exception as e:
        logger.error(f"Error parsing lottery result: {e}")
        return None

def import_to_database(results):
    """
    Import parsed results to PostgreSQL database
    """
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()
        
        imported = 0
        skipped = 0
        
        for result in results:
            if not result:
                continue
            
            # Check if already exists
            cur.execute("""
                SELECT COUNT(*) FROM lottery_results 
                WHERE lottery_type = %s AND draw_date = %s
            """, (result['lottery_type'], result['draw_date']))
            
            if cur.fetchone()[0] > 0:
                logger.info(f"Skipping {result['lottery_type']} {result['draw_date']} - already exists")
                skipped += 1
                continue
            
            # Insert new result
            cur.execute("""
                INSERT INTO lottery_results 
                (lottery_type, draw_number, draw_date, numbers, bonus_numbers, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                result['lottery_type'],
                result['draw_number'],
                result['draw_date'],
                json.dumps(result['main_numbers']),
                json.dumps(result['bonus_numbers']) if result['bonus_numbers'] else None
            ))
            
            logger.info(f"✅ Imported {result['lottery_type']} {result['draw_date']}")
            imported += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Import complete: {imported} new results, {skipped} skipped")
        logger.info(f"{'='*60}")
        
        return imported, skipped
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        return 0, 0

def main():
    """
    Main function to parse and import historical data
    """
    logger.info("Starting historical data import")
    logger.info("="*60)
    
    # Load the fetched HTML data
    json_file = 'recent_draws_20251003_203257.json'
    
    if not os.path.exists(json_file):
        logger.error(f"Data file not found: {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_results = []
    
    # Parse each lottery type's draws
    for lottery_type, draws in data.items():
        logger.info(f"\nProcessing {lottery_type}...")
        
        for draw in draws:
            result = parse_lottery_result(draw['html'], lottery_type, draw['url'])
            if result:
                all_results.append(result)
    
    logger.info(f"\nParsed {len(all_results)} results total")
    
    # Import to database
    imported, skipped = import_to_database(all_results)
    
    print(f"\n{'='*60}")
    print(f"DATABASE IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Total parsed:    {len(all_results)}")
    print(f"Newly imported:  {imported}")
    print(f"Already existed: {skipped}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
