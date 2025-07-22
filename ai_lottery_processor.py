"""
AI Lottery Screenshot Processing System - Complete Rebuild
Processes lottery screenshots one-by-one using Google Gemini 2.5 Pro API
Extracts comprehensive data and updates database with full validation
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import DictCursor
from google import genai
from google.genai import types
import traceback
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompleteLotteryProcessor:
    def __init__(self):
        """Initialize processor with Gemini API client"""
        try:
            api_key = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY_SNAP_LOTTERY environment variable not found")
            self.client = genai.Client(api_key=api_key)
            self.db_connection = None
            logger.info("AI Lottery Processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize processor: {e}")
            raise
        
    def connect_database(self):
        """Establish PostgreSQL database connection"""
        try:
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not found")
            
            self.db_connection = psycopg2.connect(database_url)
            logger.info("Database connection established")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def process_single_image(self, image_path: str, lottery_type: str) -> Dict[str, Any]:
        """
        Process a single lottery screenshot with comprehensive AI extraction
        """
        logger.info(f"Starting AI processing for: {image_path} (Type: {lottery_type})")
        
        try:
            # Read image file
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Create comprehensive extraction prompt
            extraction_prompt = f"""
            You are analyzing a South African National Lottery screenshot for {lottery_type}.
            
            Extract ALL the following data with EXACT values from the image:
            
            **DRAW INFORMATION:**
            - Draw ID/Number (find the specific draw number)
            - Draw Date (convert to YYYY-MM-DD format)
            - Lottery Type (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2, POWERBALL, POWERBALL PLUS, DAILY LOTTO)
            
            **WINNING NUMBERS:**
            - Main winning numbers (in numerical order, comma separated)
            - Bonus Ball/PowerBall (if applicable)
            
            **PRIZE DIVISIONS (extract ALL visible divisions):**
            - Division 1: Description, Number of winners, Prize amount
            - Division 2: Description, Number of winners, Prize amount
            - Division 3: Description, Number of winners, Prize amount
            - Continue for ALL visible divisions (up to 8 for LOTTO types, 9 for POWERBALL types)
            
            **FINANCIAL DATA:**
            - Rollover Amount
            - Rollover Number
            - Total Pool Size
            - Total Sales
            - Next Jackpot
            - Draw Machine (RNG number)
            - Next Draw Date
            
            Return ONLY valid JSON in this exact format:
            {{
                "draw_id": "2560",
                "draw_date": "2025-07-19", 
                "lottery_type": "LOTTO",
                "winning_numbers": [2, 8, 11, 13, 36, 46],
                "bonus_numbers": [30],
                "prize_divisions": [
                    {{
                        "division": "Div 1",
                        "description": "6 Correct Numbers",
                        "winners": 0,
                        "amount": "R0.00"
                    }},
                    {{
                        "division": "Div 2", 
                        "description": "5 Correct + Bonus",
                        "winners": 2,
                        "amount": "R45,321.30"
                    }}
                ],
                "rollover_amount": "R8,041,144.01",
                "rollover_number": 3,
                "total_pool_size": "R11,916,070.21",
                "total_sales": "R15,004,050.00",
                "next_jackpot": "R11,000,000.00",
                "draw_machine": "RNG 1",
                "next_draw_date": "2025-07-23",
                "extraction_confidence": 98
            }}
            
            CRITICAL REQUIREMENTS:
            - Extract ALL visible prize divisions (not just first few)
            - Include exact currency amounts with commas
            - Use numerical order for winning numbers
            - Confidence must be 95+ for production use
            - Return only the JSON object, no other text
            """
            
            # Call Gemini 2.5 Pro for extraction
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/png",
                    ),
                    extraction_prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini API")
            
            # Parse extracted data
            extracted_data = json.loads(response.text)
            confidence = extracted_data.get('extraction_confidence', 0)
            
            logger.info(f"AI extraction completed with {confidence}% confidence")
            logger.info(f"Extracted: Draw {extracted_data.get('draw_id')}, Date {extracted_data.get('draw_date')}")
            logger.info(f"Numbers: {extracted_data.get('winning_numbers')}, Bonus: {extracted_data.get('bonus_numbers')}")
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response: {response.text[:500] if 'response' in locals() else 'No response'}")
            raise
        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def save_to_database(self, lottery_data: Dict[str, Any]) -> int:
        """
        Save extracted lottery data to PostgreSQL database
        """
        try:
            cursor = self.db_connection.cursor(cursor_factory=DictCursor)
            
            # Prepare data for insertion
            draw_date = datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date()
            next_draw_date = None
            if lottery_data.get('next_draw_date'):
                next_draw_date = datetime.strptime(lottery_data['next_draw_date'], '%Y-%m-%d').date()
            
            # Insert lottery result without source_url (column doesn't exist)
            insert_query = """
                INSERT INTO lottery_results (
                    lottery_type, draw_number, draw_date, main_numbers, bonus_numbers,
                    prize_divisions, rollover_amount, next_jackpot, total_pool_size,
                    total_sales, draw_machine, next_draw_date, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            cursor.execute(insert_query, (
                lottery_data['lottery_type'],
                lottery_data['draw_id'],
                draw_date,
                json.dumps(lottery_data['winning_numbers']),
                json.dumps(lottery_data['bonus_numbers']) if lottery_data.get('bonus_numbers') else None,
                json.dumps(lottery_data['prize_divisions']),
                lottery_data.get('rollover_amount'),
                lottery_data.get('next_jackpot'),
                lottery_data.get('total_pool_size'),
                lottery_data.get('total_sales'),
                lottery_data.get('draw_machine'),
                next_draw_date,
                datetime.now()
            ))
            
            record_id = cursor.fetchone()[0]
            self.db_connection.commit()
            
            logger.info(f"Successfully saved to database with ID: {record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
            self.db_connection.rollback()
            raise
    
    def get_lottery_type_from_filename(self, filename: str) -> str:
        """Extract lottery type from screenshot filename"""
        filename_lower = filename.lower()
        
        if "lotto_plus_2" in filename_lower:
            return "LOTTO PLUS 2"
        elif "lotto_plus_1" in filename_lower:
            return "LOTTO PLUS 1"
        elif "lotto" in filename_lower and "plus" not in filename_lower:
            return "LOTTO"
        elif "powerball_plus" in filename_lower:
            return "POWERBALL PLUS"
        elif "powerball" in filename_lower and "plus" not in filename_lower:
            return "POWERBALL"
        elif "daily_lotto" in filename_lower:
            return "DAILY LOTTO"
        else:
            return "UNKNOWN"
    
    def process_all_screenshots(self) -> Dict[str, Any]:
        """
        Process all screenshots one by one with comprehensive AI extraction
        """
        results = {
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
            "processed_files": [],
            "failed_files": [],
            "database_records": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        try:
            # Connect to database
            self.connect_database()
            
            # Get all screenshot files
            screenshots_dir = "screenshots"
            if not os.path.exists(screenshots_dir):
                raise Exception(f"Screenshots directory '{screenshots_dir}' not found")
            
            screenshot_files = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
            results["total_processed"] = len(screenshot_files)
            
            logger.info(f"=== STARTING AI PROCESSING WORKFLOW ===")
            logger.info(f"Found {len(screenshot_files)} screenshots to process")
            
            # Process each screenshot individually
            for i, filename in enumerate(screenshot_files, 1):
                file_path = os.path.join(screenshots_dir, filename)
                logger.info(f"Processing [{i}/{len(screenshot_files)}]: {filename}")
                
                try:
                    # Extract lottery type
                    lottery_type = self.get_lottery_type_from_filename(filename)
                    if lottery_type == "UNKNOWN":
                        raise ValueError(f"Could not determine lottery type from filename: {filename}")
                    
                    # Process with AI
                    start_time = time.time()
                    lottery_data = self.process_single_image(file_path, lottery_type)
                    processing_time = time.time() - start_time
                    
                    # Validate confidence
                    confidence = lottery_data.get('extraction_confidence', 0)
                    if confidence < 95:
                        logger.warning(f"Low confidence ({confidence}%) for {filename}")
                    
                    # Save to database
                    record_id = self.save_to_database(lottery_data)
                    
                    # Record success
                    results["total_success"] += 1
                    results["processed_files"].append({
                        "filename": filename,
                        "lottery_type": lottery_type,
                        "draw_id": lottery_data.get('draw_id'),
                        "draw_date": lottery_data.get('draw_date'),
                        "confidence": confidence,
                        "record_id": record_id,
                        "processing_time": round(processing_time, 2),
                        "status": "success"
                    })
                    
                    results["database_records"].append(record_id)
                    
                    logger.info(f"✓ SUCCESS: {filename} -> DB ID {record_id} ({confidence}% confidence, {processing_time:.1f}s)")
                    
                    # Small delay between processing
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"✗ FAILED: {filename} - {str(e)}")
                    results["total_failed"] += 1
                    results["failed_files"].append({
                        "filename": filename,
                        "error": str(e),
                        "status": "failed"
                    })
            
            # Close database connection
            if self.db_connection:
                self.db_connection.close()
            
            results["end_time"] = datetime.now().isoformat()
            
            logger.info(f"=== AI PROCESSING COMPLETE ===")
            logger.info(f"Results: {results['total_success']}/{results['total_processed']} successful")
            logger.info(f"Database records created: {len(results['database_records'])}")
            
            return results
            
        except Exception as e:
            logger.error(f"Fatal error in process_all_screenshots: {e}")
            logger.error(traceback.format_exc())
            if self.db_connection:
                self.db_connection.close()
            
            results["end_time"] = datetime.now().isoformat()
            results["fatal_error"] = str(e)
            return results

def run_complete_ai_workflow():
    """
    Main function to execute the complete AI lottery processing workflow
    """
    try:
        logger.info("Initializing Complete Lottery Processor")
        processor = CompleteLotteryProcessor()
        
        logger.info("Starting complete AI workflow")
        results = processor.process_all_screenshots()
        
        return results
        
    except Exception as e:
        logger.error(f"Workflow initialization failed: {e}")
        return {
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 1,
            "error": str(e),
            "status": "initialization_failed"
        }

if __name__ == "__main__":
    # Test the processor directly
    results = run_complete_ai_workflow()
    print(json.dumps(results, indent=2))