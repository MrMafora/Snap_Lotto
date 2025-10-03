#!/usr/bin/env python3
"""
Fetch individual draw results from 2025 archive pages
This will get the actual recent lottery draws with all details
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_draws_from_archive(archive_url, lottery_type_name, max_draws=10):
    """
    Fetch individual draw links from a yearly archive page
    Then fetch each individual draw's full details
    """
    try:
        logger.info(f"Fetching {lottery_type_name} draws from: {archive_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Get the archive page
        response = requests.get(archive_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all draw result links on the archive page
        # These are typically formatted as /lottery-type/results/DD-MONTH-YYYY
        draw_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Look for individual draw result pages
            if '/results/' in href and any(month in href.lower() for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
                full_url = href if href.startswith('http') else f"https://za.national-lottery.com{href}"
                if full_url not in draw_links:
                    draw_links.append(full_url)
        
        logger.info(f"Found {len(draw_links)} individual draw links")
        
        # Get the first max_draws draws
        results = []
        for i, draw_url in enumerate(draw_links[:max_draws]):
            try:
                logger.info(f"  Fetching draw {i+1}/{min(max_draws, len(draw_links))}: {draw_url}")
                
                draw_response = requests.get(draw_url, headers=headers, timeout=20)
                draw_response.raise_for_status()
                
                # Save the full HTML for later analysis/extraction
                result_data = {
                    'url': draw_url,
                    'lottery_type': lottery_type_name,
                    'html': draw_response.text,
                    'fetched_at': datetime.now().isoformat()
                }
                
                results.append(result_data)
                time.sleep(0.5)  # Be nice to the server
                
            except Exception as e:
                logger.error(f"  Error fetching draw {i+1}: {str(e)}")
                continue
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching archive {archive_url}: {str(e)}")
        return []

def main():
    """
    Fetch recent draws from 2025 archive pages
    """
    
    logger.info("Fetching recent lottery draws from 2025 archives")
    logger.info("=" * 60)
    
    # 2025 archive URLs
    archives = {
        'LOTTO': 'https://za.national-lottery.com/lotto/results/2025-archive',
        'LOTTO PLUS 1': 'https://za.national-lottery.com/lotto-plus-1/results/2025-archive',
        'LOTTO PLUS 2': 'https://za.national-lottery.com/lotto-plus-2/results/2025-archive',
        'POWERBALL': 'https://za.national-lottery.com/powerball/results/2025-archive',
        'POWERBALL PLUS': 'https://za.national-lottery.com/powerball-plus/results/2025-archive',
        'DAILY LOTTO': 'https://za.national-lottery.com/daily-lotto/results/2025-archive'
    }
    
    all_results = {}
    total_draws = 0
    
    for lottery_name, archive_url in archives.items():
        results = fetch_draws_from_archive(archive_url, lottery_name, max_draws=10)
        all_results[lottery_name] = results
        total_draws += len(results)
        logger.info(f"✅ Fetched {len(results)} draws for {lottery_name}\n")
    
    # Save all results
    output_file = f"recent_draws_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Save with HTML content
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    logger.info("=" * 60)
    logger.info(f"✅ FETCH COMPLETE: {total_draws} draws fetched")
    logger.info(f"Data saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("RECENT DRAWS FETCH SUMMARY")
    print("=" * 60)
    for lottery_name, results in all_results.items():
        print(f"{lottery_name:20s}: {len(results):2d} draws")
    print("=" * 60)
    print(f"Total: {total_draws} draws")
    print(f"Saved to: {output_file}")
    print("=" * 60)
    
    return all_results

if __name__ == '__main__':
    main()
