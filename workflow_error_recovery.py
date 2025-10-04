"""
Workflow Error Recovery System
Handles failures gracefully and provides recovery mechanisms
"""

import os
import logging
import psycopg2
from datetime import datetime
from typing import Dict, Optional
import json
import time

logger = logging.getLogger(__name__)

class WorkflowErrorRecovery:
    """
    Manages error handling and recovery for the automation workflow
    """
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.max_retries = 3
        self.retry_delay = 15  # seconds
    
    def log_error(self, error_type: str, error_message: str, context: Dict = None) -> int:
        """
        Log an error to the database
        
        Args:
            error_type: Type of error (e.g., 'screenshot_capture', 'ai_processing')
            error_message: Error message
            context: Additional context data
            
        Returns:
            Error log ID
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # Create error log table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workflow_error_logs (
                    id SERIAL PRIMARY KEY,
                    error_type VARCHAR(100) NOT NULL,
                    error_message TEXT NOT NULL,
                    context_data JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_notes TEXT
                )
            """)
            
            # Insert error log
            cur.execute("""
                INSERT INTO workflow_error_logs (error_type, error_message, context_data)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (error_type, error_message, json.dumps(context) if context else None))
            
            error_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            logger.warning(f"📝 Error logged: ID={error_id}, Type={error_type}")
            return error_id
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
            return -1
    
    def retry_operation(self, operation_func, operation_name: str, *args, **kwargs):
        """
        Retry an operation with exponential backoff
        
        Args:
            operation_func: Function to retry
            operation_name: Name of the operation for logging
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the operation or None if all retries failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔄 Attempting {operation_name} (attempt {attempt}/{self.max_retries})")
                result = operation_func(*args, **kwargs)
                logger.info(f"✅ {operation_name} succeeded on attempt {attempt}")
                return result
                
            except Exception as e:
                logger.warning(f"⚠️ {operation_name} failed on attempt {attempt}: {e}")
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * attempt  # Exponential backoff
                    logger.info(f"⏳ Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ {operation_name} failed after {self.max_retries} attempts")
                    self.log_error(
                        error_type=operation_name,
                        error_message=str(e),
                        context={'attempts': self.max_retries, 'final_error': str(e)}
                    )
                    return None
    
    def handle_screenshot_capture_failure(self, lottery_type: str) -> Dict:
        """
        Handle screenshot capture failure with fallback strategies
        
        Args:
            lottery_type: Type of lottery that failed
            
        Returns:
            Recovery result
        """
        logger.warning(f"🔧 Handling screenshot capture failure for {lottery_type}")
        
        recovery_strategies = [
            {
                'name': 'retry_with_delay',
                'description': 'Wait 30 seconds and retry',
                'action': lambda: time.sleep(30)
            },
            {
                'name': 'check_website_availability',
                'description': 'Verify lottery website is accessible',
                'action': self._check_website_availability
            },
            {
                'name': 'log_for_manual_intervention',
                'description': 'Log for admin review',
                'action': lambda: self.log_error(
                    'screenshot_capture_failure',
                    f'Failed to capture {lottery_type} screenshot',
                    {'lottery_type': lottery_type, 'timestamp': datetime.now().isoformat()}
                )
            }
        ]
        
        for strategy in recovery_strategies:
            try:
                logger.info(f"🔧 Trying recovery: {strategy['description']}")
                strategy['action']()
            except Exception as e:
                logger.warning(f"Recovery strategy failed: {e}")
        
        return {
            'recovered': False,
            'lottery_type': lottery_type,
            'strategies_attempted': len(recovery_strategies)
        }
    
    def handle_ai_processing_failure(self, screenshot_path: str, lottery_type: str) -> Optional[Dict]:
        """
        Handle AI processing failure
        
        Args:
            screenshot_path: Path to the screenshot
            lottery_type: Type of lottery
            
        Returns:
            Recovery result or None
        """
        logger.warning(f"🔧 Handling AI processing failure for {screenshot_path}")
        
        # Log the failure
        self.log_error(
            'ai_processing_failure',
            f'AI failed to process {screenshot_path}',
            {
                'screenshot_path': screenshot_path,
                'lottery_type': lottery_type,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Check if screenshot file exists and is valid
        if not os.path.exists(screenshot_path):
            logger.error(f"Screenshot file not found: {screenshot_path}")
            return None
        
        file_size = os.path.getsize(screenshot_path)
        if file_size < 1000:  # Less than 1KB, likely corrupted
            logger.error(f"Screenshot file too small ({file_size} bytes), likely corrupted")
            return None
        
        logger.info(f"Screenshot file exists and appears valid ({file_size} bytes)")
        return {
            'screenshot_valid': True,
            'file_size': file_size,
            'action_required': 'retry_ai_processing'
        }
    
    def handle_database_failure(self, error: Exception, data: Dict) -> bool:
        """
        Handle database operation failure
        
        Args:
            error: The exception that occurred
            data: Data that failed to save
            
        Returns:
            True if recovery was successful
        """
        logger.warning(f"🔧 Handling database failure: {error}")
        
        # Log the error
        self.log_error(
            'database_operation_failure',
            str(error),
            {
                'data_lottery_type': data.get('lottery_type'),
                'data_draw_id': data.get('draw_id'),
                'error_type': type(error).__name__
            }
        )
        
        # Check if it's a connection issue
        if 'connection' in str(error).lower():
            logger.info("Database connection issue detected, will retry")
            return False
        
        # Check if it's a duplicate key issue
        if 'duplicate' in str(error).lower() or 'unique constraint' in str(error).lower():
            logger.info("Duplicate entry detected, skipping insert")
            return True  # Not really a failure, data already exists
        
        return False
    
    def _check_website_availability(self) -> bool:
        """Check if the lottery website is accessible"""
        try:
            import requests
            response = requests.get('https://www.nationallottery.co.za/', timeout=10)
            is_available = response.status_code == 200
            logger.info(f"Website availability check: {'✅ Available' if is_available else '❌ Unavailable'}")
            return is_available
        except Exception as e:
            logger.warning(f"Website availability check failed: {e}")
            return False
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """
        Get recent workflow errors
        
        Args:
            limit: Number of errors to retrieve
            
        Returns:
            List of recent errors
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # Ensure error log table exists before querying
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workflow_error_logs (
                    id SERIAL PRIMARY KEY,
                    error_type VARCHAR(100) NOT NULL,
                    error_message TEXT NOT NULL,
                    context_data JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_notes TEXT
                )
            """)
            conn.commit()
            
            cur.execute("""
                SELECT id, error_type, error_message, context_data, created_at, resolved
                FROM workflow_error_logs
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            errors = []
            for row in cur.fetchall():
                errors.append({
                    'id': row[0],
                    'error_type': row[1],
                    'error_message': row[2],
                    'context': row[3],
                    'created_at': row[4].isoformat() if row[4] else None,
                    'resolved': row[5]
                })
            
            cur.close()
            conn.close()
            
            return errors
            
        except Exception as e:
            logger.error(f"Failed to retrieve errors: {e}")
            return []
    
    def mark_error_resolved(self, error_id: int, resolution_notes: str) -> bool:
        """
        Mark an error as resolved
        
        Args:
            error_id: ID of the error log
            resolution_notes: Notes about the resolution
            
        Returns:
            True if successful
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # Ensure error log table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workflow_error_logs (
                    id SERIAL PRIMARY KEY,
                    error_type VARCHAR(100) NOT NULL,
                    error_message TEXT NOT NULL,
                    context_data JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_notes TEXT
                )
            """)
            conn.commit()
            
            cur.execute("""
                UPDATE workflow_error_logs
                SET resolved = TRUE, resolution_notes = %s
                WHERE id = %s
            """, (resolution_notes, error_id))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ Error {error_id} marked as resolved")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark error as resolved: {e}")
            return False


# Global error recovery instance
_error_recovery = None

def get_error_recovery() -> WorkflowErrorRecovery:
    """Get or create the global error recovery instance"""
    global _error_recovery
    if _error_recovery is None:
        _error_recovery = WorkflowErrorRecovery()
    return _error_recovery


if __name__ == "__main__":
    # Test error recovery system
    logging.basicConfig(level=logging.INFO)
    
    recovery = WorkflowErrorRecovery()
    
    # Log a test error
    error_id = recovery.log_error(
        'test_error',
        'This is a test error',
        {'test': True}
    )
    print(f"Test error logged with ID: {error_id}")
    
    # Get recent errors
    errors = recovery.get_recent_errors(5)
    print(f"Recent errors: {json.dumps(errors, indent=2)}")
