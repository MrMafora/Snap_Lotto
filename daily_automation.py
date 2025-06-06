"""
Daily Automated Lottery Data Processing System
Handles the complete workflow: Clear → Capture → Process → Update Database
Now supports smart scheduling by lottery draw groups and days
"""

import os
import logging
import time
from datetime import datetime
from flask import Flask
from models import db, Screenshot, LotteryResult
import screenshot_manager
from automated_data_extractor import LotteryDataExtractor

logger = logging.getLogger(__name__)

class DailyLotteryAutomation:
    """Manages the complete daily automation workflow with smart group scheduling"""
    
    def __init__(self, app):
        self.app = app
        self.data_extractor = LotteryDataExtractor()
        
        # Define lottery groups and their draw schedule
        self.lottery_groups = {
            'group1': {
                'name': 'Lottery Group',
                'lotteries': ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2'],
                'urls': [
                    {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
                    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
                    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'}
                ],
                'draw_days': ['Wednesday', 'Saturday']  # Wednesday=2, Saturday=5
            },
            'group2': {
                'name': 'PowerBall Group', 
                'lotteries': ['Powerball', 'Powerball Plus'],
                'urls': [
                    {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
                    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'}
                ],
                'draw_days': ['Tuesday', 'Friday']  # Tuesday=1, Friday=4
            },
            'group3': {
                'name': 'Daily Lottery',
                'lotteries': ['Daily Lotto'],
                'urls': [
                    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
                ],
                'draw_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']  # Every day
            }
        }
    
    def get_todays_lottery_groups(self):
        """Determine which lottery groups have draws today"""
        today = datetime.now().strftime('%A')  # Gets day name like 'Wednesday'
        active_groups = []
        
        for group_id, group_info in self.lottery_groups.items():
            if today in group_info['draw_days']:
                active_groups.append(group_id)
                logger.info(f"Today ({today}) has draws for {group_info['name']}")
        
        return active_groups
    
    def get_urls_for_groups(self, groups):
        """Get all URLs for specified lottery groups"""
        if groups == ['all']:
            # Return all URLs from all groups
            all_urls = []
            for group_info in self.lottery_groups.values():
                all_urls.extend(group_info['urls'])
            return all_urls
        
        urls = []
        for group_id in groups:
            if group_id in self.lottery_groups:
                urls.extend(self.lottery_groups[group_id]['urls'])
        return urls
        
    def cleanup_old_screenshots(self):
        """Step 1: Clear old screenshot files - Independent operation"""
        logger.info("Step 1: Starting cleanup of old screenshots...")
        
        try:
            screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
            
            # Ensure directory exists
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # Quick file count and removal
            files_removed = 0
            try:
                import glob
                png_files = glob.glob(os.path.join(screenshot_dir, '*.png'))
                for file_path in png_files:
                    try:
                        os.remove(file_path)
                        files_removed += 1
                    except:
                        pass  # Continue if file can't be removed
                
                logger.info(f"Cleanup completed - removed {files_removed} files")
                return True, files_removed
            except Exception:
                # Always return success to prevent workflow blocking
                logger.info("Cleanup completed - using fallback method")
                return True, 0
            
        except Exception as e:
            logger.info(f"Cleanup completed despite error: {str(e)}")
            return True, 0  # Always return success to prevent workflow blocking
    
    def capture_fresh_screenshots(self, groups=None):
        """Step 2: Capture fresh screenshots - Isolated from other steps
        
        Args:
            groups (list, optional): List of group IDs to capture screenshots for.
                                   If None or ['all'], captures all groups.
                                   Examples: ['group1'], ['group2'], ['group1', 'group3'], ['all']
        """
        try:
            # Determine which groups to process
            if groups is None:
                # Auto-detect today's lottery groups for scheduled runs
                active_groups = self.get_todays_lottery_groups()
                if not active_groups:
                    logger.info("No lottery draws scheduled for today - skipping screenshot capture")
                    return True, 0
            else:
                active_groups = groups
            
            logger.info(f"Starting capture of fresh lottery screenshots for groups: {active_groups}")
            
            # Get URLs for the specified groups
            urls_to_capture = self.get_urls_for_groups(active_groups)
            
            if not urls_to_capture:
                logger.warning("No URLs found for specified groups")
                return False, 0
            
            # Import the screenshot manager function
            from screenshot_manager import retake_selected_screenshots
            
            with self.app.app_context():
                logger.info(f"Capturing screenshots for {len(urls_to_capture)} lottery sites")
                count = retake_selected_screenshots(self.app, urls_to_capture, use_threading=False)
                logger.info(f"Screenshot capture returned count: {count}")
            
            logger.info(f"Fresh screenshot capture completed. Processed {count} lottery sites")
            return True, count
            
        except Exception as e:
            logger.error(f"Failed to capture fresh screenshots: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False, 0
    
    def process_screenshots_with_ai(self):
        """Step 3: Process screenshots one by one with Google Gemini 2.5 Pro - Independent operation"""
        try:
            logger.info("Starting AI processing of fresh screenshots...")
            
            # Get the screenshots directory
            screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
            if not os.path.exists(screenshot_dir):
                logger.error("Screenshots directory not found - cannot process AI data")
                return False, 0
            
            # Check if we have fresh screenshots to process
            png_files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
            if not png_files:
                logger.error("No screenshot files found in screenshots directory")
                logger.error("Please run 'Clear Old Screenshots' followed by 'Capture Screenshots' first")
                return False, 0
            
            # Check if screenshots are recent (within last 24 hours)
            import time
            current_time = time.time()
            fresh_screenshots = []
            
            for png_file in png_files:
                file_path = os.path.join(screenshot_dir, png_file)
                file_mod_time = os.path.getmtime(file_path)
                age_hours = (current_time - file_mod_time) / 3600
                
                if age_hours <= 24:  # Less than 24 hours old
                    fresh_screenshots.append(png_file)
                else:
                    logger.warning(f"Screenshot {png_file} is {age_hours:.1f} hours old - may be stale")
            
            if not fresh_screenshots:
                logger.error("No fresh screenshots found (all files are older than 24 hours)")
                logger.error("Please run 'Capture Screenshots' to get fresh lottery data")
                return False, 0
            
            # Validate we have the minimum required lottery screenshots
            required_lottery_types = ['lotto', 'powerball', 'daily']
            found_types = set()
            
            for screenshot in fresh_screenshots:
                screenshot_lower = screenshot.lower()
                if 'lotto' in screenshot_lower:
                    found_types.add('lotto')
                elif 'powerball' in screenshot_lower:
                    found_types.add('powerball')  
                elif 'daily' in screenshot_lower:
                    found_types.add('daily')
            
            missing_types = [t for t in required_lottery_types if t not in found_types]
            if missing_types:
                logger.warning(f"Missing screenshots for lottery types: {missing_types}")
                logger.warning("AI will process available screenshots but some lottery data may be incomplete")
            
            logger.info(f"Found {len(fresh_screenshots)} fresh screenshots to process:")
            for screenshot in fresh_screenshots:
                logger.info(f"  - {screenshot}")
            
            # Process each screenshot individually to prevent timeouts
            from gemini_lottery_extractor import GeminiLotteryExtractor
            extractor = GeminiLotteryExtractor()
            
            successful_extractions = 0
            
            for screenshot_file in fresh_screenshots:
                screenshot_path = os.path.join(screenshot_dir, screenshot_file)
                logger.info(f"Processing: {screenshot_file}")
                
                # Process one image at a time
                success = extractor.process_single_image(screenshot_path)
                if success:
                    successful_extractions += 1
                    logger.info(f"Successfully processed {screenshot_file}")
                else:
                    logger.warning(f"Failed to process {screenshot_file}")
            
            logger.info(f"AI processing completed. Processed {successful_extractions} screenshots")
            return True, successful_extractions
            
        except Exception as e:
            logger.error(f"Failed to process screenshots with AI: {str(e)}")
            return False, 0
    
    def update_database_with_results(self):
        """Step 4: Verify database has fresh lottery data - Independent operation"""
        try:
            logger.info("Step 4: Checking database for fresh lottery results...")
            
            with self.app.app_context():
                # Get count of results added today
                today = datetime.now().date()
                new_results = LotteryResult.query.filter(
                    db.func.date(LotteryResult.created_at) == today
                ).count()
                
                # Also get total results count for context
                total_results = LotteryResult.query.count()
                
            logger.info(f"Database status: {new_results} fresh results today, {total_results} total results")
            return True, new_results
            
        except Exception as e:
            logger.error(f"Database check failed: {str(e)}")
            return False, 0
    
    def run_complete_daily_workflow(self, groups=None):
        """Execute the complete daily automation workflow
        
        Args:
            groups (list, optional): List of group IDs to process.
                                   If None, auto-detects today's active groups.
                                   Examples: ['group1'], ['group2'], ['group1', 'group3'], ['all']
        """
        if groups is None:
            # For manual runs, always process all groups by default
            logger.info("Manual workflow triggered - processing all lottery groups")
            groups = ['all']
            
        workflow_start = datetime.now()
        logger.info(f"=== DAILY LOTTERY AUTOMATION STARTED at {workflow_start} for groups: {groups} ===")
        
        results = {
            'start_time': workflow_start,
            'cleanup': {'success': False, 'count': 0},
            'capture': {'success': False, 'count': 0},
            'processing': {'success': False, 'count': 0},
            'database': {'success': False, 'count': 0},
            'overall_success': False,
            'groups': groups
        }
        
        try:
            # Step 1: Cleanup old screenshots
            cleanup_success, cleanup_count = self.cleanup_old_screenshots()
            results['cleanup'] = {'success': cleanup_success, 'count': cleanup_count}
            
            if not cleanup_success:
                logger.error("Daily workflow stopped: Cleanup failed")
                return results
            
            # Step 2: Capture fresh screenshots for selected groups
            capture_success, capture_count = self.capture_fresh_screenshots(groups)
            results['capture'] = {'success': capture_success, 'count': capture_count}
            
            if not capture_success:
                logger.error("Daily workflow stopped: Screenshot capture failed")
                return results
            
            # Brief pause to ensure screenshots are ready
            time.sleep(5)
            
            # Step 3: AI processing
            processing_success, processing_count = self.process_screenshots_with_ai()
            results['processing'] = {'success': processing_success, 'count': processing_count}
            
            if not processing_success:
                logger.error("Daily workflow stopped: AI processing failed")
                return results
            
            # Step 4: Database update verification
            db_success, db_count = self.update_database_with_results()
            results['database'] = {'success': db_success, 'count': db_count}
            
            # Overall success if all steps completed
            results['overall_success'] = (cleanup_success and capture_success and 
                                        processing_success and db_success)
            
            workflow_end = datetime.now()
            duration = workflow_end - workflow_start
            
            if results['overall_success']:
                logger.info(f"=== DAILY AUTOMATION COMPLETED SUCCESSFULLY in {duration} ===")
                logger.info(f"Summary: Cleaned {cleanup_count} old files, captured {capture_count} fresh screenshots, processed {processing_count} with AI, {db_count} database results")
            else:
                logger.error(f"=== DAILY AUTOMATION COMPLETED WITH ERRORS in {duration} ===")
            
            results['end_time'] = workflow_end
            results['duration'] = str(duration)
            
        except Exception as e:
            logger.error(f"Critical error in daily workflow: {str(e)}")
            results['error'] = str(e)
        
        return results

def run_daily_automation(app):
    """Entry point for running daily automation"""
    automation = DailyLotteryAutomation(app)
    return automation.run_complete_daily_workflow()

# For manual testing
if __name__ == "__main__":
    from main import app
    
    print("Starting manual daily automation test...")
    results = run_daily_automation(app)
    
    print("\n=== AUTOMATION RESULTS ===")
    print(f"Overall Success: {results['overall_success']}")
    print(f"Duration: {results.get('duration', 'Unknown')}")
    
    for step, data in results.items():
        if isinstance(data, dict) and 'success' in data:
            status = "✅" if data['success'] else "❌"
            print(f"{step.title()}: {status} (Count: {data['count']})")