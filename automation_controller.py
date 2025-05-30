"""
Clean Automation Controller
Manages the 4-step lottery automation workflow
"""
import logging
from step1_cleanup import cleanup_screenshots
from step2_capture import capture_lottery_screenshots
from step3_ai_process import process_screenshots_with_ai
from step4_database import update_database

logger = logging.getLogger(__name__)

class AutomationController:
    def __init__(self):
        logger.info("Automation controller initialized")
    
    def run_step_1(self):
        """Step 1: Clean screenshots folder"""
        logger.info("Starting Step 1: Cleanup")
        return cleanup_screenshots()
    
    def run_step_2(self):
        """Step 2: Capture fresh screenshots"""
        logger.info("Starting Step 2: Screenshot Capture")
        return capture_lottery_screenshots()
    
    def run_step_3(self):
        """Step 3: Process with AI"""
        logger.info("Starting Step 3: AI Processing")
        return process_screenshots_with_ai()
    
    def run_step_4(self):
        """Step 4: Update database"""
        logger.info("Starting Step 4: Database Update")
        return update_database()
    
    def run_complete_workflow(self):
        """Run all 4 steps in sequence"""
        logger.info("Starting complete automation workflow")
        
        results = {}
        
        # Step 1: Cleanup
        success_1, count_1 = self.run_step_1()
        results['step_1'] = {'success': success_1, 'count': count_1}
        if not success_1:
            logger.error("Step 1 failed, stopping workflow")
            return False, results
        
        # Step 2: Capture
        success_2, count_2 = self.run_step_2()
        results['step_2'] = {'success': success_2, 'count': count_2}
        if not success_2:
            logger.error("Step 2 failed, stopping workflow")
            return False, results
        
        # Step 3: AI Process
        success_3, count_3 = self.run_step_3()
        results['step_3'] = {'success': success_3, 'count': count_3}
        if not success_3:
            logger.error("Step 3 failed, stopping workflow")
            return False, results
        
        # Step 4: Database
        success_4, count_4 = self.run_step_4()
        results['step_4'] = {'success': success_4, 'count': count_4}
        
        logger.info("Complete workflow finished")
        return success_4, results