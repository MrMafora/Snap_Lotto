#!/usr/bin/env python3
"""
Test script for the complete 4-step automation workflow
Tests each step individually and then the complete workflow
"""

import sys
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_step_modules():
    """Test that all step modules are importable and functional"""
    logger.info("=== TESTING STEP MODULES ===")
    
    try:
        # Test Step 1: Cleanup
        import step1_cleanup
        logger.info("✓ Step 1 (cleanup) module imported successfully")
        
        # Test Step 2: Capture
        import step2_capture
        logger.info("✓ Step 2 (capture) module imported successfully")
        
        # Test Step 3: AI Process
        import step3_ai_process
        logger.info("✓ Step 3 (AI process) module imported successfully")
        
        # Test Step 4: Database
        import step4_database
        logger.info("✓ Step 4 (database) module imported successfully")
        
        # Test daily automation controller
        import daily_automation
        logger.info("✓ Daily automation controller imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Module import failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {str(e)}")
        return False

def test_complete_workflow():
    """Test the complete automation workflow"""
    logger.info("=== TESTING COMPLETE WORKFLOW ===")
    
    try:
        from daily_automation import run_complete_automation
        
        logger.info("Starting complete automation workflow test...")
        results = run_complete_automation()
        
        logger.info("Workflow results:")
        for step, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {step}: {success}")
        
        if results['overall_success']:
            logger.info("✓ Complete workflow executed successfully")
            return True
        else:
            logger.warning("⚠ Workflow completed with some failures")
            return False
            
    except Exception as e:
        logger.error(f"✗ Workflow test failed: {str(e)}")
        return False

def test_database_connection():
    """Test database connectivity and recent data"""
    logger.info("=== TESTING DATABASE CONNECTION ===")
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models import LotteryResult
        from config import Config
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Query recent results
        recent_results = session.query(LotteryResult).order_by(LotteryResult.draw_date.desc()).limit(10).all()
        
        logger.info(f"✓ Database connected successfully")
        logger.info(f"✓ Found {len(recent_results)} recent lottery results")
        
        if recent_results:
            latest = recent_results[0]
            logger.info(f"  Latest: {latest.lottery_type} Draw {latest.draw_number} ({latest.draw_date})")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Database test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting complete workflow tests...")
    start_time = datetime.now()
    
    tests = [
        ("Module Import Test", test_step_modules),
        ("Database Connection Test", test_database_connection),
        ("Complete Workflow Test", test_complete_workflow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED: {str(e)}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"\n=== TEST SUMMARY ===")
    logger.info(f"Tests passed: {passed}/{total}")
    logger.info(f"Test duration: {duration:.2f} seconds")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Complete workflow is ready!")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED - Check logs for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())