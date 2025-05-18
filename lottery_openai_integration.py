"""
OpenAI integration for fetching lottery data directly from the South African National Lottery.
"""

import os
import json
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('openai_integration')

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def query_openai(prompt):
    """
    Send a query to OpenAI and get the response.
    
    Args:
        prompt (str): The prompt to send to OpenAI
        
    Returns:
        str: The OpenAI response
    """
    try:
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not found in environment variables")
            return json.dumps({"error": "OpenAI API key not configured"})
        
        response = client.chat.completions.create(
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specializing in South African lottery data extraction and verification."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for factual responses
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error querying OpenAI: {e}")
        return json.dumps({"error": f"OpenAI API error: {str(e)}"})

def fetch_lottery_data(lottery_type, draw_id=None):
    """
    Fetch lottery data from OpenAI for a specific lottery type and draw ID.
    
    Args:
        lottery_type (str): Type of lottery (e.g., "Lottery", "Powerball")
        draw_id (str, optional): Specific draw ID to fetch
        
    Returns:
        dict: Structured lottery data
    """
    prompt = f"""
    I need you to provide official South African National Lottery results for {lottery_type} draw #{draw_id if draw_id else 'the most recent draw'}.
    
    Please give me:
    1. The draw number
    2. The draw date (YYYY-MM-DD format)
    3. The winning numbers 
    4. Any bonus balls or powerball numbers
    5. The division information (match requirements, winner counts, and payouts)
    
    Format your response as a JSON object with these keys:
    {{
        "draw_number": "string",
        "draw_date": "YYYY-MM-DD",
        "numbers": ["string", "string", ...],
        "bonus_numbers": ["string", ...],
        "divisions": {{
            "Division 1": {{
                "match": "string",
                "winners": number,
                "payout": "string"
            }},
            ...
        }}
    }}
    
    For this specific lottery game:
    - Lottery (previously called Lotto) has 6 main numbers and 1 bonus ball with 8 prize divisions
    - Lottery Plus 1 and Plus 2 also have 6 main numbers and 1 bonus ball with 8 prize divisions
    - Powerball has 5 main numbers and 1 powerball with 9 prize divisions
    - Powerball Plus has 5 main numbers and 1 powerball with 9 prize divisions
    - Daily Lottery has 5 main numbers with 4 prize divisions
    
    Please give me accurate, official data as would be found on the South African National Lottery website.
    """
    
    response = query_openai(prompt)
    
    # Try to extract JSON data from the response
    try:
        import re
        json_match = re.search(r'({[\s\S]*})', response)
        if json_match:
            json_str = json_match.group(1)
            try:
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError:
                logger.error(f"Could not parse JSON from OpenAI response: {json_str}")
                return None
        else:
            logger.error(f"No JSON found in OpenAI response: {response}")
            return None
    except Exception as e:
        logger.error(f"Error extracting JSON from OpenAI response: {e}")
        return None