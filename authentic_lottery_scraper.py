#!/usr/bin/env python3
"""
Authentic SA National Lottery Data Scraper
Extracts real lottery results from official website using trafilatura
"""

import os
import sys
import logging
import time
import random
from datetime import datetime
import trafilatura
import requests
from config import Config
import re
from urllib.parse import urljoin, urlparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticLotteryScraper:
    def __init__(self):
        self.base_url = "https://www.nationallottery.co.za"
        self.results_urls = [
            {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
            {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
            {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
            {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
            {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
            {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
        ]
        
        # Human-like headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-ZA,en;q=0.9,af;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache'
        }

    def extract_lottery_numbers(self, text_content, lottery_type):
        """
        Extract authentic lottery numbers from cleaned text content
        
        Args:
            text_content: Cleaned text from trafilatura
            lottery_type: Type of lottery game
            
        Returns:
            Dictionary with extracted lottery data
        """
        try:
            lottery_data = {
                'lottery_type': lottery_type,
                'main_numbers': [],
                'bonus_numbers': [],
                'draw_date': None,
                'draw_number': None,
                'prize_divisions': []
            }
            
            # Clean the text for better parsing
            text = text_content.lower().replace('\n', ' ').replace('\t', ' ')
            
            # Extract draw date patterns
            date_patterns = [
                r'draw\s+date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    lottery_data['draw_date'] = match.group(1)
                    break
            
            # Extract draw number
            draw_patterns = [
                r'draw\s+number[:\s]*(\d+)',
                r'draw[:\s]*(\d+)',
                r'number[:\s]*(\d+)'
            ]
            
            for pattern in draw_patterns:
                match = re.search(pattern, text)
                if match:
                    lottery_data['draw_number'] = match.group(1)
                    break
            
            # Extract winning numbers based on lottery type
            if lottery_type.lower() in ['lotto', 'lotto plus 1', 'lotto plus 2']:
                # Look for 6 main numbers (1-52)
                number_patterns = [
                    r'winning\s+numbers[:\s]*(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)',
                    r'numbers[:\s]*(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)',
                    r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)'
                ]
                
                for pattern in number_patterns:
                    match = re.search(pattern, text)
                    if match:
                        numbers = [int(n) for n in match.groups() if 1 <= int(n) <= 52]
                        if len(numbers) == 6:
                            lottery_data['main_numbers'] = sorted(numbers)
                            break
                            
            elif lottery_type.lower() in ['powerball', 'powerball plus']:
                # Look for 5 main numbers + 1 powerball
                powerball_patterns = [
                    r'(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+powerball[:\s]*(\d+)',
                    r'main[:\s]*(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]*bonus[:\s]*(\d+)',
                    r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,?\s*(\d+)'
                ]
                
                for pattern in powerball_patterns:
                    match = re.search(pattern, text)
                    if match:
                        groups = match.groups()
                        if len(groups) >= 6:
                            main_nums = [int(n) for n in groups[:5] if 1 <= int(n) <= 50]
                            bonus_num = int(groups[5]) if 1 <= int(groups[5]) <= 20 else None
                            
                            if len(main_nums) == 5 and bonus_num:
                                lottery_data['main_numbers'] = sorted(main_nums)
                                lottery_data['bonus_numbers'] = [bonus_num]
                                break
                                
            elif lottery_type.lower() == 'daily lotto':
                # Look for 5 main numbers (1-36)
                daily_patterns = [
                    r'winning\s+numbers[:\s]*(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)',
                    r'numbers[:\s]*(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)',
                    r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)'
                ]
                
                for pattern in daily_patterns:
                    match = re.search(pattern, text)
                    if match:
                        numbers = [int(n) for n in match.groups() if 1 <= int(n) <= 36]
                        if len(numbers) == 5:
                            lottery_data['main_numbers'] = sorted(numbers)
                            break
            
            # Extract prize information if available
            prize_patterns = [
                r'division\s+1[:\s]*r?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
                r'jackpot[:\s]*r?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
                r'first\s+prize[:\s]*r?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
            ]
            
            for pattern in prize_patterns:
                match = re.search(pattern, text)
                if match:
                    prize_amount = match.group(1).replace(',', '')
                    lottery_data['prize_divisions'].append({
                        'division': 1,
                        'amount': f"R{prize_amount}"
                    })
                    break
            
            return lottery_data
            
        except Exception as e:
            logger.error(f"Failed to extract lottery numbers: {str(e)}")
            return None

    def scrape_lottery_page(self, url, lottery_type, retries=3):
        """
        Scrape authentic lottery data from official website
        
        Args:
            url: Lottery results URL
            lottery_type: Type of lottery
            retries: Number of retry attempts
            
        Returns:
            Dictionary with lottery data or None if failed
        """
        for attempt in range(retries):
            try:
                logger.info(f"Scraping {lottery_type} from {url} (attempt {attempt + 1})")
                
                # Add delay to appear more human-like
                if attempt > 0:
                    delay = random.uniform(5, 15)
                    logger.info(f"Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
                
                # Create session with headers
                session = requests.Session()
                session.headers.update(self.headers)
                
                # Fetch the URL content with custom session
                response = session.get(url, timeout=30)
                response.raise_for_status()
                
                downloaded = response.text
                
                if not downloaded:
                    logger.warning(f"Failed to download content from {url}")
                    continue
                
                # Extract clean text content
                text_content = trafilatura.extract(downloaded)
                
                if not text_content:
                    logger.warning(f"No text content extracted from {url}")
                    continue
                
                logger.info(f"Extracted {len(text_content)} characters of text content")
                
                # Extract lottery data from text
                lottery_data = self.extract_lottery_numbers(text_content, lottery_type)
                
                if lottery_data and lottery_data.get('main_numbers'):
                    logger.info(f"Successfully extracted {lottery_type} numbers: {lottery_data['main_numbers']}")
                    return lottery_data
                else:
                    logger.warning(f"Could not extract valid lottery numbers from {lottery_type} page")
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {lottery_type}: {str(e)}")
                
        logger.error(f"All attempts failed for {lottery_type}")
        return None

    def scrape_all_lottery_results(self):
        """
        Scrape authentic results from all lottery pages
        
        Returns:
            List of lottery data dictionaries
        """
        results = []
        
        logger.info("=== STARTING AUTHENTIC LOTTERY DATA SCRAPING ===")
        
        for i, url_config in enumerate(self.results_urls):
            url = url_config['url']
            lottery_type = url_config['lottery_type']
            
            # Human-like delay between requests
            if i > 0:
                delay = random.uniform(3, 8)
                logger.info(f"Waiting {delay:.1f} seconds before next scrape...")
                time.sleep(delay)
            
            # Scrape lottery data
            lottery_data = self.scrape_lottery_page(url, lottery_type)
            
            if lottery_data:
                results.append(lottery_data)
            
        logger.info(f"=== SCRAPING COMPLETED: {len(results)} lottery results extracted ===")
        return results

def run_authentic_scraping():
    """Run authentic lottery data scraping"""
    try:
        scraper = AuthenticLotteryScraper()
        return scraper.scrape_all_lottery_results()
    except Exception as e:
        logger.error(f"Failed to run authentic scraping: {str(e)}")
        return []

if __name__ == "__main__":
    results = run_authentic_scraping()
    for result in results:
        if result:
            print(f"{result['lottery_type']}: {result.get('main_numbers', [])} {result.get('bonus_numbers', [])}")