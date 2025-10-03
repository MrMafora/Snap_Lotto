#!/usr/bin/env python3
"""
Scrape historical lottery data from za.national-lottery.com
This will fetch the last 10 draws for each lottery type and save them to the database
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
import os
import sys
from datetime import datetime
import psycopg2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_historical_results(lottery_type_url, lottery_type_name):
    """
    Fetch historical results from the za.national-lottery.com website
    """
    try:
        logger.info(f"Fetching {lottery_type_name} historical results from: {lottery_type_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(lottery_type_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find draw result links or tables containing results
        # The structure varies, but typically there are links to individual draws
        draw_links = []
        
        # Try to find links that contain '/results/' in them
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/results/' in href and lottery_type_name.lower().replace(' ', '-') in href.lower():
                full_url = href if href.startswith('http') else f"https://za.national-lottery.com{href}"
                if full_url not in draw_links:
                    draw_links.append(full_url)
        
        logger.info(f"Found {len(draw_links)} draw links for {lottery_type_name}")
        
        # Get first 10 draws
        results = []
        for i, draw_url in enumerate(draw_links[:10]):
            try:
                logger.info(f"  Fetching draw {i+1}: {draw_url}")
                draw_response = requests.get(draw_url, headers=headers, timeout=20)
                draw_response.raise_for_status()
                
                draw_soup = BeautifulSoup(draw_response.text, 'html.parser')
                
                # Extract draw data from the page
                # This structure may vary, but typically includes:
                # - Draw number/ID
                # - Draw date
                # - Winning numbers
                # - Prize information
                
                result_data = {
                    'url': draw_url,
                    'html': str(draw_soup)[:5000],  # Save first 5000 chars for analysis
                    'lottery_type': lottery_type_name
                }
                
                results.append(result_data)
                
            except Exception as e:
                logger.error(f"  Error fetching draw {i+1}: {str(e)}")
                continue
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching {lottery_type_name} results: {str(e)}")
        return []

def main():
    """
    Main function to scrape historical data for all lottery types
    """
    
    logger.info("Starting historical lottery data scrape")
    logger.info("=" * 60)
    
    # Lottery types and their history URLs
    lottery_types = {
        'LOTTO': 'https://za.national-lottery.com/lotto/results/history',
        'LOTTO PLUS 1': 'https://za.national-lottery.com/lotto-plus-1/results/history',
        'LOTTO PLUS 2': 'https://za.national-lottery.com/lotto-plus-2/results/history',
        'POWERBALL': 'https://za.national-lottery.com/powerball/results/history',
        'POWERBALL PLUS': 'https://za.national-lottery.com/powerball-plus/results/history',
        'DAILY LOTTO': 'https://za.national-lottery.com/daily-lotto/results/history'
    }
    
    all_results = {}
    
    for lottery_name, history_url in lottery_types.items():
        results = fetch_historical_results(history_url, lottery_name)
        all_results[lottery_name] = results
        logger.info(f"✅ Fetched {len(results)} draws for {lottery_name}")
        logger.info("")
    
    # Save results to a JSON file for analysis
    output_file = f"historical_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info("=" * 60)
    logger.info(f"✅ SCRAPE COMPLETE")
    logger.info(f"Total draws fetched: {sum(len(v) for v in all_results.values())}")
    logger.info(f"Data saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("HISTORICAL DATA SCRAPE SUMMARY")
    print("=" * 60)
    for lottery_name, results in all_results.items():
        print(f"{lottery_name:20s}: {len(results):2d} draws")
    print("=" * 60)
    
    return all_results

if __name__ == '__main__':
    main()
