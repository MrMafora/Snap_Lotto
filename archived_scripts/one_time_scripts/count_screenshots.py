"""
Script to count the number of screenshots in the database.
"""

from main import app
from models import Screenshot

with app.app_context():
    screenshot_count = Screenshot.query.count()
    print(f'Current number of screenshots: {screenshot_count}')
    
    # Print the URLs to see if we have unique ones
    unique_urls = set()
    urls_with_counts = {}
    
    screenshots = Screenshot.query.all()
    for screenshot in screenshots:
        unique_urls.add(screenshot.url)
        
        if screenshot.url in urls_with_counts:
            urls_with_counts[screenshot.url] += 1
        else:
            urls_with_counts[screenshot.url] = 1
    
    print(f'Number of unique URLs: {len(unique_urls)}')
    print('Screenshot counts by URL:')
    
    for url, count in urls_with_counts.items():
        print(f'  - {url}: {count} screenshot(s)')