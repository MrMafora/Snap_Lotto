#!/usr/bin/env python3
"""
HTML to Screenshot Converter for SA National Lottery
Converts captured HTML content into visual PNG screenshots
"""

import os
import sys
import logging
from datetime import datetime
from playwright.async_api import async_playwright
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def convert_html_to_screenshot(html_file_path, output_dir="screenshots"):
    """
    Convert HTML file to PNG screenshot using Playwright
    
    Args:
        html_file_path: Path to the HTML file
        output_dir: Directory to save screenshots
    
    Returns:
        Path to generated screenshot or None if failed
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(html_file_path))[0]
        screenshot_path = os.path.join(output_dir, f"{base_name}.png")
        
        async with async_playwright() as p:
            # Launch browser with optimized settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--allow-running-insecure-content',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            try:
                # Create page with mobile viewport (matching your examples)
                page = await browser.new_page(
                    viewport={'width': 390, 'height': 844}  # iPhone 12 Pro size
                )
                
                # Load HTML file
                html_file_url = f"file://{os.path.abspath(html_file_path)}"
                await page.goto(html_file_url, wait_until='networkidle')
                
                # Wait for content to load
                await page.wait_for_timeout(2000)
                
                # Take screenshot of the main content area
                await page.screenshot(
                    path=screenshot_path,
                    full_page=True,
                    type='png'
                )
                
                logger.info(f"Successfully converted {html_file_path} to {screenshot_path}")
                return screenshot_path
                
            finally:
                await browser.close()
                
    except Exception as e:
        logger.error(f"Failed to convert HTML to screenshot: {str(e)}")
        return None

async def convert_all_html_files(input_dir="screenshots", output_dir="screenshots"):
    """
    Convert all HTML files in directory to PNG screenshots
    
    Args:
        input_dir: Directory containing HTML files
        output_dir: Directory to save screenshots
    
    Returns:
        List of generated screenshot paths
    """
    results = []
    
    if not os.path.exists(input_dir):
        logger.error(f"Input directory {input_dir} doesn't exist")
        return results
    
    # Find all HTML files
    html_files = [f for f in os.listdir(input_dir) if f.endswith('.html')]
    
    if not html_files:
        logger.info("No HTML files found to convert")
        return results
    
    logger.info(f"Found {len(html_files)} HTML files to convert")
    
    # Convert each HTML file
    for html_file in html_files:
        html_path = os.path.join(input_dir, html_file)
        screenshot_path = await convert_html_to_screenshot(html_path, output_dir)
        
        if screenshot_path:
            results.append(screenshot_path)
    
    logger.info(f"Successfully converted {len(results)} HTML files to screenshots")
    return results

def run_html_to_screenshot_conversion():
    """
    Main function to run HTML to screenshot conversion
    """
    try:
        logger.info("=== STARTING HTML TO SCREENSHOT CONVERSION ===")
        
        # Run async conversion
        results = asyncio.run(convert_all_html_files())
        
        logger.info(f"=== CONVERSION COMPLETED: {len(results)} screenshots generated ===")
        return results
        
    except Exception as e:
        logger.error(f"HTML to screenshot conversion failed: {str(e)}")
        return []

if __name__ == "__main__":
    run_html_to_screenshot_conversion()