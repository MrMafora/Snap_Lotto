#!/usr/bin/env python3
"""
Quick test of comprehensive lottery extraction with advanced prompt
"""

import os
import json
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_advanced_extraction():
    """Test advanced extraction on LOTTO screenshot"""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        if not api_key:
            logger.error("Google API key not found")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        image_path = "screenshots/20250606_171929_lotto.png"
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Advanced comprehensive prompt
        prompt = """You are an automated data extraction API. Extract lottery data from this image as JSON:

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

Extract all prize divisions, winner counts, and financial details visible in the image."""

        response = model.generate_content([
            prompt,
            {"mime_type": "image/png", "data": image_data}
        ])
        
        if response and response.text:
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            
            data = json.loads(text)
            
            print("=== COMPREHENSIVE LOTTERY EXTRACTION ===")
            print(f"Game: {data.get('gameName')}")
            print(f"Draw: {data.get('drawId')}")
            print(f"Date: {data.get('drawDate')}")
            print(f"Numbers: {data.get('winningNumbers', {}).get('asDrawn')} + [{data.get('winningNumbers', {}).get('bonusBall')}]")
            
            divisions = data.get('prizeDivisions', [])
            print(f"\nPrize Divisions ({len(divisions)} tiers):")
            for div in divisions:
                print(f"  Div {div.get('division')}: {div.get('description')}")
                print(f"    Winners: {div.get('winners')}, Prize: {div.get('prizeAmount')}")
            
            jackpot = data.get('jackpotInfo', {})
            if jackpot.get('nextJackpot'):
                print(f"\nNext Jackpot: {jackpot.get('nextJackpot')}")
            
            additional = data.get('additionalInfo', {})
            for key, value in additional.items():
                if value:
                    print(f"{key}: {value}")
            
            return data
    
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None

if __name__ == "__main__":
    result = test_advanced_extraction()
    if result:
        print("\n✅ Advanced comprehensive extraction successful!")
    else:
        print("\n❌ Extraction failed")