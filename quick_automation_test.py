#!/usr/bin/env python3
"""
Quick Automation Test Script
Tests the core automation components to verify functionality
"""

import os
import logging
from datetime import datetime
from main import app
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_anthropic_connection():
    """Test if Anthropic API is accessible"""
    try:
        import anthropic
        from config import Config
        
        config = Config()
        api_key = config.ANTHROPIC_API_KEY
        
        if not api_key:
            logger.error("Anthropic API key not configured")
            return False
            
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test message
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Hello, respond with just 'API working'"}]
        )
        
        if "API working" in response.content[0].text:
            logger.info("✓ Anthropic API connection successful")
            return True
        else:
            logger.warning("Anthropic API responded but with unexpected content")
            return False
            
    except Exception as e:
        logger.error(f"Anthropic API test failed: {e}")
        return False

def test_database_operations():
    """Test database read/write operations"""
    try:
        with app.app_context():
            from main import db
            
            # Test read operation
            result = db.session.execute(db.text("SELECT COUNT(*) as count FROM lottery_results")).fetchone()
            current_count = result.count
            logger.info(f"✓ Database read successful - {current_count} records")
            
            # Test write operation (insert a test record)
            test_data = {
                'lottery_type': 'TEST',
                'draw_date': datetime.now().date(),
                'draw_number': 9999,
                'main_numbers': '[1, 2, 3, 4, 5]',
                'bonus_numbers': None,
                'created_at': datetime.now()
            }
            
            db.session.execute(db.text("""
                INSERT INTO lottery_results (lottery_type, draw_date, draw_number, main_numbers, bonus_numbers, created_at)
                VALUES (:lottery_type, :draw_date, :draw_number, :main_numbers, :bonus_numbers, :created_at)
            """), test_data)
            db.session.commit()
            
            # Verify the insert
            new_result = db.session.execute(db.text("SELECT COUNT(*) as count FROM lottery_results")).fetchone()
            if new_result.count > current_count:
                logger.info("✓ Database write successful")
                
                # Clean up test record
                db.session.execute(db.text("DELETE FROM lottery_results WHERE lottery_type = 'TEST'"))
                db.session.commit()
                logger.info("✓ Test record cleaned up")
                return True
            else:
                logger.error("Database write failed - count did not increase")
                return False
                
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return False

def test_screenshot_capture():
    """Test screenshot capture functionality"""
    try:
        from screenshot_manager import ScreenshotManager
        
        manager = ScreenshotManager()
        
        # Test with one URL
        test_url = 'https://www.nationallottery.co.za/results/daily-lotto'
        result = manager.capture_screenshot(test_url, 'Daily Lotto Test')
        
        if result and result.get('success'):
            logger.info(f"✓ Screenshot capture successful: {result.get('filename')}")
            return True
        else:
            logger.warning(f"Screenshot capture failed or returned no result: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Screenshot capture test failed: {e}")
        return False

def run_all_tests():
    """Run all automation component tests"""
    logger.info("=== AUTOMATION COMPONENT TESTING ===")
    
    results = {
        'anthropic': test_anthropic_connection(),
        'database': test_database_operations(),
        'screenshots': test_screenshot_capture()
    }
    
    logger.info("=== TEST RESULTS ===")
    for component, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{component.upper()}: {status}")
    
    overall_success = all(results.values())
    logger.info(f"Overall automation health: {'GOOD' if overall_success else 'NEEDS ATTENTION'}")
    
    return overall_success, results

if __name__ == "__main__":
    run_all_tests()