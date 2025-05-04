"""
Web scraping module specifically built for extracting clean text from lottery websites.
Uses trafilatura for high-quality text extraction that removes boilerplate content.
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