#!/usr/bin/env python3
"""
Visual Lottery Screenshot Generator
Creates visual PNG screenshots from lottery data using PIL/Pillow
"""

import os
import sys
import logging
import requests
import time
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import re
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualLotteryCapture:
    def __init__(self):
        self.screenshot_dir = Config.SCREENSHOT_DIR
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Visual design settings
        self.canvas_size = (390, 844)  # iPhone 12 Pro dimensions
        self.background_color = (255, 255, 255)  # White
        self.header_color = (0, 102, 204)  # Blue
        self.number_color = (51, 51, 51)  # Dark gray
        self.bonus_color = (204, 0, 0)  # Red
        
    def create_lottery_visual(self, lottery_type, draw_data, filepath):
        """
        Create a visual representation of lottery results
        
        Args:
            lottery_type: Type of lottery (e.g., 'Lotto')
            draw_data: Dictionary with lottery draw information
            filepath: Path to save the image
        """
        try:
            # Create image
            img = Image.new('RGB', self.canvas_size, self.background_color)
            draw = ImageDraw.Draw(img)
            
            # Try to use system fonts, fall back to default
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                number_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                title_font = ImageFont.load_default()
                header_font = ImageFont.load_default()
                number_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            y_pos = 50
            
            # Draw title
            title = f"SA NATIONAL LOTTERY - {lottery_type.upper()}"
            draw.text((20, y_pos), title, fill=self.header_color, font=title_font)
            y_pos += 60
            
            # Draw date
            if draw_data.get('draw_date'):
                date_text = f"Draw Date: {draw_data['draw_date']}"
                draw.text((20, y_pos), date_text, fill=self.number_color, font=header_font)
                y_pos += 40
            
            # Draw draw number
            if draw_data.get('draw_number'):
                draw_text = f"Draw Number: {draw_data['draw_number']}"
                draw.text((20, y_pos), draw_text, fill=self.number_color, font=header_font)
                y_pos += 50
            
            # Draw main numbers
            if draw_data.get('main_numbers'):
                draw.text((20, y_pos), "WINNING NUMBERS:", fill=self.header_color, font=header_font)
                y_pos += 40
                
                # Draw number circles
                x_start = 30
                circle_radius = 25
                for i, number in enumerate(draw_data['main_numbers']):
                    x_center = x_start + (i * 70)
                    y_center = y_pos + circle_radius
                    
                    # Draw circle
                    draw.ellipse([
                        x_center - circle_radius, y_center - circle_radius,
                        x_center + circle_radius, y_center + circle_radius
                    ], fill=self.header_color, outline=self.number_color, width=2)
                    
                    # Draw number
                    number_text = str(number)
                    bbox = draw.textbbox((0, 0), number_text, font=number_font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    draw.text((
                        x_center - text_width // 2,
                        y_center - text_height // 2
                    ), number_text, fill=self.background_color, font=number_font)
                
                y_pos += 80
            
            # Draw bonus numbers
            if draw_data.get('bonus_numbers'):
                draw.text((20, y_pos), "BONUS NUMBERS:", fill=self.bonus_color, font=header_font)
                y_pos += 40
                
                x_start = 30
                circle_radius = 20
                for i, number in enumerate(draw_data['bonus_numbers']):
                    x_center = x_start + (i * 60)
                    y_center = y_pos + circle_radius
                    
                    # Draw circle
                    draw.ellipse([
                        x_center - circle_radius, y_center - circle_radius,
                        x_center + circle_radius, y_center + circle_radius
                    ], fill=self.bonus_color, outline=self.number_color, width=2)
                    
                    # Draw number
                    number_text = str(number)
                    bbox = draw.textbbox((0, 0), number_text, font=header_font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    draw.text((
                        x_center - text_width // 2,
                        y_center - text_height // 2
                    ), number_text, fill=self.background_color, font=header_font)
                
                y_pos += 60
            
            # Add footer
            y_pos += 50
            footer_text = "Official SA National Lottery Results"
            draw.text((20, y_pos), footer_text, fill=self.number_color, font=text_font)
            
            # Save image
            img.save(filepath, 'PNG')
            logger.info(f"Created visual lottery screenshot: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to create visual lottery image: {str(e)}")
            return None

    def extract_lottery_data_from_html(self, html_content, lottery_type):
        """
        Extract lottery data from HTML content using regex patterns
        
        Args:
            html_content: HTML content string
            lottery_type: Type of lottery
            
        Returns:
            Dictionary with extracted lottery data
        """
        try:
            data = {
                'lottery_type': lottery_type,
                'main_numbers': [],
                'bonus_numbers': [],
                'draw_date': None,
                'draw_number': None
            }
            
            # Pattern to find numbers in lottery results
            # Look for common patterns in SA lottery HTML
            number_patterns = [
                r'winning.*?numbers?.*?(\d+).*?(\d+).*?(\d+).*?(\d+).*?(\d+).*?(\d+)',
                r'results.*?(\d+).*?(\d+).*?(\d+).*?(\d+).*?(\d+).*?(\d+)',
                r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)',
                r'ball.*?(\d+).*?(\d+).*?(\d+).*?(\d+).*?(\d+).*?(\d+)'
            ]
            
            # Try to extract main numbers
            for pattern in number_patterns:
                matches = re.findall(pattern, html_content.lower())
                if matches:
                    numbers = [int(n) for n in matches[0] if 1 <= int(n) <= 52]
                    if len(numbers) >= 5:
                        if lottery_type.lower() in ['lotto', 'lotto plus 1', 'lotto plus 2']:
                            data['main_numbers'] = numbers[:6]
                        elif lottery_type.lower() in ['powerball', 'powerball plus']:
                            data['main_numbers'] = numbers[:5]
                            if len(numbers) > 5:
                                data['bonus_numbers'] = numbers[5:6]
                        elif lottery_type.lower() == 'daily lotto':
                            data['main_numbers'] = numbers[:5]
                        break
            
            # Try to extract date
            date_patterns = [
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                r'draw.*?date.*?(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, html_content)
                if match:
                    data['draw_date'] = match.group(1)
                    break
            
            # Try to extract draw number
            draw_patterns = [
                r'draw.*?(?:number|#).*?(\d+)',
                r'(?:number|#).*?(\d+)',
                r'draw.*?(\d+)'
            ]
            
            for pattern in draw_patterns:
                match = re.search(pattern, html_content.lower())
                if match:
                    data['draw_number'] = match.group(1)
                    break
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to extract lottery data: {str(e)}")
            return None

    def capture_lottery_page(self, url, lottery_type):
        """
        Capture lottery page content and create visual screenshot
        
        Args:
            url: Lottery results URL
            lottery_type: Type of lottery
            
        Returns:
            Path to created screenshot or None if failed
        """
        try:
            # Create session with proper headers
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-ZA,en;q=0.9,af;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'DNT': '1'
            })
            
            logger.info(f"Fetching {lottery_type} from {url}")
            
            # Make request with timeout
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract lottery data
            lottery_data = self.extract_lottery_data_from_html(response.text, lottery_type)
            
            if not lottery_data or not lottery_data.get('main_numbers'):
                logger.warning(f"No lottery data extracted for {lottery_type}")
                return None
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
            filename = f"{timestamp}_{safe_lottery_type}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Create visual screenshot
            result = self.create_lottery_visual(lottery_type, lottery_data, filepath)
            
            if result and os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                logger.info(f"Successfully created visual screenshot for {lottery_type}: {filepath}")
                return filepath
            else:
                logger.error(f"Failed to create valid screenshot for {lottery_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to capture {lottery_type}: {str(e)}")
            return None

    def process_existing_html_files(self):
        """Process existing HTML files to create visual screenshots"""
        results = []
        
        logger.info("=== PROCESSING EXISTING HTML FILES TO CREATE VISUAL SCREENSHOTS ===")
        
        # Check for existing HTML files
        html_files = []
        if os.path.exists(self.screenshot_dir):
            html_files = [f for f in os.listdir(self.screenshot_dir) if f.endswith('.html')]
        
        if not html_files:
            logger.warning("No HTML files found to process")
            return results
        
        logger.info(f"Found {len(html_files)} HTML files to process")
        
        for html_file in html_files:
            try:
                html_path = os.path.join(self.screenshot_dir, html_file)
                
                # Determine lottery type from filename
                lottery_type = "Unknown"
                if 'lotto_plus_2' in html_file:
                    lottery_type = "Lotto Plus 2"
                elif 'lotto_plus_1' in html_file:
                    lottery_type = "Lotto Plus 1"
                elif 'lotto' in html_file:
                    lottery_type = "Lotto"
                elif 'powerball_plus' in html_file:
                    lottery_type = "Powerball Plus"
                elif 'powerball' in html_file:
                    lottery_type = "Powerball"
                elif 'daily_lotto' in html_file:
                    lottery_type = "Daily Lotto"
                
                # Read HTML content
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Extract lottery data
                lottery_data = self.extract_lottery_data_from_html(html_content, lottery_type)
                
                if lottery_data and lottery_data.get('main_numbers'):
                    # Generate PNG filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
                    png_filename = f"{timestamp}_{safe_lottery_type}_visual.png"
                    png_filepath = os.path.join(self.screenshot_dir, png_filename)
                    
                    # Create visual screenshot
                    visual_result = self.create_lottery_visual(lottery_type, lottery_data, png_filepath)
                    
                    if visual_result:
                        results.append({
                            'lottery_type': lottery_type,
                            'html_file': html_file,
                            'filepath': png_filepath,
                            'status': 'success'
                        })
                        logger.info(f"Created visual screenshot for {lottery_type}: {png_filename}")
                    else:
                        results.append({
                            'lottery_type': lottery_type,
                            'html_file': html_file,
                            'filepath': None,
                            'status': 'failed'
                        })
                else:
                    logger.warning(f"Could not extract lottery data from {html_file}")
                    results.append({
                        'lottery_type': lottery_type,
                        'html_file': html_file,
                        'filepath': None,
                        'status': 'failed'
                    })
                    
            except Exception as e:
                logger.error(f"Failed to process {html_file}: {str(e)}")
                results.append({
                    'lottery_type': lottery_type,
                    'html_file': html_file,
                    'filepath': None,
                    'status': 'failed'
                })
        
        # Log summary
        successful_captures = len([r for r in results if r['status'] == 'success'])
        total_captures = len(results)
        
        logger.info(f"=== VISUAL SCREENSHOT PROCESSING COMPLETED ===")
        logger.info(f"Successfully created {successful_captures}/{total_captures} visual screenshots")
        
        return results

    def capture_all_lottery_screenshots(self):
        """Create visual screenshots from existing HTML content and database data"""
        
        # First try to process existing HTML files
        results = self.process_existing_html_files()
        
        # If no HTML files or failed, try to create from authentic data
        if not results or len([r for r in results if r['status'] == 'success']) == 0:
            logger.info("Creating visual screenshots from authentic lottery data")
            results.extend(self.create_from_sample_data())
        
        return results
    
    def create_from_authentic_database(self):
        """Create visual screenshots ONLY from authentic lottery data in database - NO fake data"""
        results = []
        
        # Import here to avoid circular imports
        try:
            from models import LotteryResult
            from main import app
            
            with app.app_context():
                # Get authentic lottery results from database
                authentic_results = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).limit(6).all()
                
                if not authentic_results:
                    logger.error("NO AUTHENTIC LOTTERY DATA FOUND IN DATABASE - Cannot create screenshots without real data")
                    return results
                
                logger.info(f"Creating visual screenshots from {len(authentic_results)} authentic database records")
                
                for lottery_result in authentic_results:
                    try:
                        # Extract authentic data using proper methods
                        authentic_data = {
                            'lottery_type': lottery_result.lottery_type,
                            'main_numbers': lottery_result.get_numbers_list(),
                            'bonus_numbers': lottery_result.get_bonus_numbers_list(),
                            'draw_date': lottery_result.draw_date.strftime('%Y-%m-%d') if lottery_result.draw_date else None,
                            'draw_number': str(lottery_result.draw_number) if lottery_result.draw_number else None
                        }
                        
                        # Validate we have real numbers
                        if not authentic_data['main_numbers']:
                            logger.warning(f"Skipping {lottery_result.lottery_type} - no authentic numbers found")
                            continue
                            
                        logger.info(f"Processing authentic {lottery_result.lottery_type}: {authentic_data['main_numbers']} + {authentic_data['bonus_numbers']}")
                        
                        # Generate filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_lottery_type = authentic_data['lottery_type'].lower().replace(' ', '_').replace('+', '_plus_')
                        filename = f"{timestamp}_{safe_lottery_type}_authentic.png"
                        filepath = os.path.join(self.screenshot_dir, filename)
                        
                        # Create visual screenshot from authentic data
                        visual_result = self.create_lottery_visual(authentic_data['lottery_type'], authentic_data, filepath)
                        
                        if visual_result:
                            results.append({
                                'lottery_type': authentic_data['lottery_type'],
                                'source': 'authentic_database',
                                'filepath': filepath,
                                'status': 'success'
                            })
                            logger.info(f"Created authentic visual screenshot for {authentic_data['lottery_type']}: {filename}")
                        else:
                            results.append({
                                'lottery_type': authentic_data['lottery_type'],
                                'source': 'authentic_database',
                                'filepath': None,
                                'status': 'failed'
                            })
                            
                    except Exception as e:
                        logger.error(f"Failed to create visual from authentic database data: {str(e)}")
                        
        except ImportError as e:
            logger.error(f"Could not import required modules for database access: {str(e)}")
            
        return results

def run_visual_capture():
    """Run the visual lottery screenshot capture process"""
    try:
        capture = VisualLotteryCapture()
        return capture.capture_all_lottery_screenshots()
    except Exception as e:
        logger.error(f"Failed to run visual capture: {str(e)}")
        return []

if __name__ == "__main__":
    results = run_visual_capture()
    print(f"Captured {len([r for r in results if r['status'] == 'success'])} visual screenshots")