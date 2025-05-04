"""
Web scraping module specifically built for extracting clean text from lottery websites.
Uses trafilatura for high-quality text extraction that removes boilerplate content.
Provides fallback functionality for preview generation when visual methods fail.
"""

import logging
import trafilatura
from typing import Optional, Tuple, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    Extract clean, readable text content from a website URL.
    
    This function removes navigation elements, ads, and other non-content
    elements to provide clean text that can be analyzed or presented to users.
    
    Args:
        url (str): The full URL of the website to scrape
        
    Returns:
        str: Extracted main text content, or empty string on failure
    """
    try:
        logger.info(f"Downloading content from {url}")
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            logger.warning(f"Failed to download content from {url}")
            return ""
        
        logger.info(f"Extracting text content from {url}")
        text = trafilatura.extract(downloaded)
        
        if not text:
            logger.warning(f"No text content extracted from {url}")
            return ""
            
        return text
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return ""

def get_website_full_content(url: str) -> Dict[str, Any]:
    """
    Extract both text content and metadata from a website URL.
    
    This function provides more detailed information about the page,
    including title, author, date, and structured content.
    
    Args:
        url (str): The full URL of the website to scrape
        
    Returns:
        dict: Dictionary with text, title, author, date, and other metadata
    """
    try:
        logger.info(f"Downloading content from {url}")
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            logger.warning(f"Failed to download content from {url}")
            return {"error": "Failed to download content"}
        
        logger.info(f"Extracting content and metadata from {url}")
        result = trafilatura.extract(downloaded, output_format="json", include_comments=False, 
                                   include_tables=True, include_images=True, include_links=True,
                                   with_metadata=True)
                                   
        if not result:
            logger.warning(f"No content extracted from {url}")
            return {"error": "No content extracted"}
            
        # Parse the JSON string if successful
        import json
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON result from {url}")
            return {"error": "Failed to parse content", "raw_text": result}
            
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return {"error": str(e)}

def extract_lottery_results(url: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Specialized function for extracting lottery results from websites.
    
    This function attempts to identify and extract structured lottery result
    information from a website.
    
    Args:
        url (str): URL of the lottery results page
        
    Returns:
        tuple: (success, data) where data contains extracted lottery information
    """
    try:
        # Get the full content including structure
        content = get_website_full_content(url)
        
        if "error" in content:
            return False, {"error": content["error"]}
            
        # Extract basic metadata
        result = {
            "title": content.get("title", ""),
            "date": content.get("date", ""),
            "text": content.get("text", ""),
            "url": url,
            "lottery_numbers": []
        }
        
        # TODO: Implement specialized extraction for lottery numbers
        # This would require pattern matching specific to each lottery website
        
        return True, result
        
    except Exception as e:
        logger.error(f"Error extracting lottery results from {url}: {str(e)}")
        return False, {"error": str(e)}

def generate_text_preview_image(url: str, lottery_type: str = None) -> Tuple[bytes, str]:
    """
    Generate a text-based preview image for websites when visual screenshots fail.
    This is a fallback method when the Playwright-based screenshot approach fails.
    
    Args:
        url (str): The URL to extract content from
        lottery_type (str, optional): Type of lottery for contextual info
        
    Returns:
        tuple: (image_bytes, error_message) where image_bytes is the PNG data
               and error_message is None on success or an error string on failure
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO
        import textwrap
        import datetime
        
        # First, attempt to extract text content from the URL
        content = get_website_text_content(url)
        
        if not content:
            logger.warning(f"Could not extract text content from {url}")
            return None, "Could not extract text content from website"
        
        # Create a background image that resembles a website
        width, height = 800, 600
        image = Image.new('RGB', (width, height), color=(248, 249, 250))
        draw = ImageDraw.Draw(image)
        
        # Try to use a default font
        try:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
            font_url = ImageFont.load_default()
        except Exception:
            font_title = None
            font_body = None
            font_url = None
        
        # Draw a header bar to simulate browser
        draw.rectangle([(0, 0), (width, 50)], fill=(53, 58, 64))
        
        # Draw URL in address bar
        draw.rectangle([(50, 15), (width-50, 35)], fill=(255, 255, 255))
        draw.text((55, 17), url[:70] + "..." if len(url) > 70 else url, 
                 fill=(0, 0, 0), font=font_url)
        
        # Draw lottery type and timestamp
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        lottery_info = f"{lottery_type or 'Lottery'} - {current_time}"
        draw.text((10, 60), lottery_info, fill=(0, 102, 204), font=font_title)
        
        # Draw separator line
        draw.line([(10, 85), (width-10, 85)], fill=(200, 200, 200), width=1)
        
        # Truncate content if too long
        if len(content) > 1500:
            content = content[:1500] + "...\n(content truncated)"
        
        # Wrap text to fit width and draw main content
        wrapped_text = textwrap.fill(content, width=70)
        y_position = 100
        for line in wrapped_text.split('\n'):
            draw.text((20, y_position), line, fill=(33, 37, 41), font=font_body)
            y_position += 20
            if y_position > height - 40:  # Stop if we're running out of space
                draw.text((20, y_position), "... (content continues)", 
                         fill=(100, 100, 100), font=font_body)
                break
        
        # Draw footer with note
        draw.text((20, height-30), 
                 "Note: This is a text-based preview as visual capture failed.", 
                 fill=(108, 117, 125), font=font_body)
        
        # Save image to BytesIO buffer
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        logger.info(f"Successfully generated text-based preview for {url}")
        return buffer.getvalue(), None
        
    except Exception as e:
        logger.error(f"Error generating text preview: {str(e)}")
        return None, f"Error generating text preview: {str(e)}"