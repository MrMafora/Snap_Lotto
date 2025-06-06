#!/usr/bin/env python3
"""
Test comprehensive lottery extraction on a single screenshot
"""

import os
import json
import base64
import logging
from datetime import datetime
from models import LotteryResult, db
from main import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_comprehensive_extraction():
    """Test comprehensive extraction on LOTTO screenshot"""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        image_path = "screenshots/20250606_171929_lotto.png"
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Advanced developer-focused prompt for comprehensive extraction
        advanced_prompt = """You are an automated data extraction API. Your task is to analyze the provided image of a lottery result and return the data in a structured JSON format.

Instructions:
- Strictly adhere to the JSON schema defined below.
- Extract all data points accurately from the image.
- If a field is not present in the image (e.g., a bonus ball in Daily Lotto), use null as its value.
- Parse numbers from strings where specified (e.g., Draw ID, Winners). Currency values should remain as strings to preserve formatting.

JSON Output Schema:
{
  "gameName": "String",
  "drawId": "Number",
  "drawDate": "String (YYYY-MM-DD)",
  "winningNumbers": {
    "asDrawn": ["Array of Numbers"],
    "numericalOrder": ["Array of Numbers"],
    "bonusBall": "Number | null"
  },
  "prizeDivisions": [
    {
      "division": "Number",
      "description": "String",
      "winners": "Number",
      "prizeAmount": "String"
    }
  ],
  "jackpotInfo": {
     "nextJackpot": "String",
     "nextDrawDate": "String (YYYY-MM-DD)"
  },
  "additionalInfo": {
    "rolloverAmount": "String | null",
    "totalPoolSize": "String | null",
    "totalSales": "String | null"
  }
}

Example Extraction Guidelines:
- gameName: Extract from the main title (e.g., "LOTTO PLUS 1").
- drawId: Extract the "DRAW ID" number.
- winningNumbers.bonusBall: This is the number after the + sign.
- prizeDivisions.description: Extract the text description for each prize tier (e.g., "SIX CORRECT NUMBERS", "FIVE CORRECT NUMBERS + BONUS BALL").
- jackpotInfo.nextJackpot: Find the estimated jackpot amount for the next draw, often at the bottom of the page.

Process the attached image and return the JSON output."""

        response = model.generate_content([
            advanced_prompt,
            {"mime_type": "image/png", "data": image_data}
        ])
        
        if response and response.text:
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            
            extracted_data = json.loads(text)
            
            logger.info("=== COMPREHENSIVE EXTRACTION RESULTS ===")
            logger.info(f"Game: {extracted_data.get('gameName')}")
            logger.info(f"Draw ID: {extracted_data.get('drawId')}")
            logger.info(f"Draw Date: {extracted_data.get('drawDate')}")
            logger.info(f"Winning Numbers: {extracted_data.get('winningNumbers', {}).get('asDrawn')}")
            logger.info(f"Bonus Ball: {extracted_data.get('winningNumbers', {}).get('bonusBall')}")
            
            # Display prize divisions
            divisions = extracted_data.get('prizeDivisions', [])
            logger.info(f"Prize Divisions ({len(divisions)} tiers):")
            for div in divisions:
                logger.info(f"  Division {div.get('division')}: {div.get('description')}")
                logger.info(f"    Winners: {div.get('winners')}, Prize: {div.get('prizeAmount')}")
            
            # Display jackpot info
            jackpot_info = extracted_data.get('jackpotInfo', {})
            if jackpot_info:
                logger.info(f"Next Jackpot: {jackpot_info.get('nextJackpot')}")
                logger.info(f"Next Draw Date: {jackpot_info.get('nextDrawDate')}")
            
            # Display additional info
            additional_info = extracted_data.get('additionalInfo', {})
            if additional_info:
                logger.info("Additional Information:")
                for key, value in additional_info.items():
                    if value:
                        logger.info(f"  {key}: {value}")
            
            return extracted_data
    
    except Exception as e:
        logger.error(f"Comprehensive extraction failed: {e}")
        return None

if __name__ == "__main__":
    test_comprehensive_extraction()