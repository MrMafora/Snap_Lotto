"""
Comprehensive test for daily automation workflow
Verifies all components are properly configured and working
"""
import os
import logging
import traceback
from datetime import datetime
from main import app
from daily_automation import DailyLotteryAutomation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_automation_initialization():
    """Test if automation system initializes properly"""
    try:
        automation = DailyLotteryAutomation(app)
        logger.info("✓ Automation system initialized successfully")
        return True, automation
    except Exception as e:
        logger.error(f"✗ Automation initialization failed: {str(e)}")
        return False, None

def test_lottery_group_detection(automation):
    """Test lottery group detection for today"""
    try:
        today_groups = automation.get_todays_lottery_groups()
        all_urls = automation.get_urls_for_groups(['all'])
        
        logger.info(f"✓ Today's active groups: {today_groups}")
        logger.info(f"✓ Total URLs configured: {len(all_urls)}")
        
        # Verify URL structure
        for url_info in all_urls:
            if not url_info.get('url') or not url_info.get('lottery_type'):
                logger.error(f"✗ Invalid URL configuration: {url_info}")
                return False
        
        logger.info("✓ All URLs properly configured")
        return True
    except Exception as e:
        logger.error(f"✗ Group detection failed: {str(e)}")
        return False

def test_cleanup_functionality(automation):
    """Test screenshot cleanup functionality"""
    try:
        success, count = automation.cleanup_old_screenshots()
        if success:
            logger.info(f"✓ Cleanup successful - processed {count} files")
            return True
        else:
            logger.error("✗ Cleanup failed")
            return False
    except Exception as e:
        logger.error(f"✗ Cleanup test failed: {str(e)}")
        return False

def test_screenshot_directory():
    """Test screenshot directory structure"""
    try:
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        
        # Ensure directory exists
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir, exist_ok=True)
            logger.info("✓ Created screenshots directory")
        else:
            logger.info("✓ Screenshots directory exists")
        
        # Check permissions
        if os.access(screenshot_dir, os.W_OK):
            logger.info("✓ Screenshots directory is writable")
            return True
        else:
            logger.error("✗ Screenshots directory is not writable")
            return False
    except Exception as e:
        logger.error(f"✗ Directory test failed: {str(e)}")
        return False

def test_data_extractor():
    """Test data extractor initialization"""
    try:
        from automated_data_extractor import LotteryDataExtractor
        
        # Test initialization
        extractor = LotteryDataExtractor()
        logger.info("✓ Data extractor initialized")
        
        # Check API key
        if hasattr(extractor, 'client') and extractor.client:
            logger.info("✓ Anthropic client configured")
            return True
        else:
            logger.error("✗ Anthropic client not properly configured")
            return False
    except Exception as e:
        logger.error(f"✗ Data extractor test failed: {str(e)}")
        return False

def test_database_connectivity():
    """Test database connection and models"""
    try:
        with app.app_context():
            from models import LotteryResult, db
            
            # Test database connection
            result_count = LotteryResult.query.count()
            logger.info(f"✓ Database connected - {result_count} lottery results in database")
            
            # Test database write capability
            test_record = LotteryResult(
                lottery_type='TEST',
                draw_number='0',
                draw_date=datetime.now(),
                main_numbers='[1,2,3,4,5]',
                created_at=datetime.now()
            )
            
            db.session.add(test_record)
            db.session.commit()
            
            # Clean up test record
            db.session.delete(test_record)
            db.session.commit()
            
            logger.info("✓ Database write/delete operations successful")
            return True
    except Exception as e:
        logger.error(f"✗ Database test failed: {str(e)}")
        return False

def test_scheduler_functionality():
    """Test scheduler system"""
    try:
        from scheduler import LotteryScheduler
        
        # Test scheduler initialization
        scheduler = LotteryScheduler(app, "01:00")
        logger.info("✓ Scheduler initialized")
        
        # Test status retrieval
        status = scheduler.get_status()
        logger.info(f"✓ Scheduler status: running={status['running']}, time={status['run_time']}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Scheduler test failed: {str(e)}")
        return False

def test_error_handling(automation):
    """Test error handling in automation workflow"""
    try:
        # Test with invalid groups
        urls = automation.get_urls_for_groups(['invalid_group'])
        if len(urls) == 0:
            logger.info("✓ Invalid group handling works correctly")
        else:
            logger.warning("⚠ Invalid group returned URLs - may need attention")
        
        # Test database verification step
        success, count = automation.update_database_with_results()
        if success is not None:  # Should return True or False, not None
            logger.info(f"✓ Database verification step works - {count} results")
            return True
        else:
            logger.error("✗ Database verification returned None")
            return False
    except Exception as e:
        logger.error(f"✗ Error handling test failed: {str(e)}")
        return False

def run_comprehensive_automation_test():
    """Run complete automation system test"""
    logger.info("=" * 60)
    logger.info("COMPREHENSIVE DAILY AUTOMATION WORKFLOW TEST")
    logger.info("=" * 60)
    
    test_results = []
    
    # Test 1: Initialization
    logger.info("\n1. Testing automation initialization...")
    init_success, automation = test_automation_initialization()
    test_results.append(("Initialization", init_success))
    
    if not init_success:
        logger.error("Cannot continue - initialization failed")
        return False
    
    # Test 2: Group detection
    logger.info("\n2. Testing lottery group detection...")
    group_success = test_lottery_group_detection(automation)
    test_results.append(("Group Detection", group_success))
    
    # Test 3: Directory structure
    logger.info("\n3. Testing directory structure...")
    dir_success = test_screenshot_directory()
    test_results.append(("Directory Structure", dir_success))
    
    # Test 4: Cleanup functionality
    logger.info("\n4. Testing cleanup functionality...")
    cleanup_success = test_cleanup_functionality(automation)
    test_results.append(("Cleanup Functionality", cleanup_success))
    
    # Test 5: Data extractor
    logger.info("\n5. Testing data extractor...")
    extractor_success = test_data_extractor()
    test_results.append(("Data Extractor", extractor_success))
    
    # Test 6: Database connectivity
    logger.info("\n6. Testing database connectivity...")
    db_success = test_database_connectivity()
    test_results.append(("Database Connectivity", db_success))
    
    # Test 7: Scheduler functionality
    logger.info("\n7. Testing scheduler functionality...")
    scheduler_success = test_scheduler_functionality()
    test_results.append(("Scheduler Functionality", scheduler_success))
    
    # Test 8: Error handling
    logger.info("\n8. Testing error handling...")
    error_success = test_error_handling(automation)
    test_results.append(("Error Handling", error_success))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{test_name:<25} {status}")
        if success:
            passed += 1
    
    logger.info(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Daily automation is ready for production!")
        return True
    else:
        logger.error(f"⚠️  {total - passed} tests failed - requires attention before production")
        return False

if __name__ == "__main__":
    success = run_comprehensive_automation_test()
    exit(0 if success else 1)