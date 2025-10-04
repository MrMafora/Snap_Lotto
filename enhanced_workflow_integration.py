"""
Enhanced Workflow Integration System
Coordinates database updates, AI predictions, and screenshot archival seamlessly
"""

import os
import logging
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class EnhancedWorkflowOrchestrator:
    """
    Orchestrates the complete workflow:
    1. Database updates
    2. Prediction validation
    3. Fresh prediction generation
    4. Screenshot archival
    5. Error recovery
    """
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.workflow_stats = {
            'database_updates': 0,
            'predictions_validated': 0,
            'predictions_generated': 0,
            'screenshots_archived': 0,
            'errors': []
        }
    
    def execute_post_database_update_workflow(self, lottery_type: str, database_record_id: int) -> Dict:
        """
        Execute all post-database-update tasks
        
        Args:
            lottery_type: Type of lottery that was updated
            database_record_id: ID of the newly created database record
            
        Returns:
            Dict with workflow execution results
        """
        logger.info(f"🔄 WORKFLOW: Starting post-update tasks for {lottery_type}")
        
        results = {
            'prediction_validation': {'success': False, 'count': 0},
            'prediction_generation': {'success': False, 'count': 0},
            'workflow_complete': False
        }
        
        try:
            # Step 1: Validate existing predictions against new result
            validation_result = self._validate_predictions(lottery_type, database_record_id)
            results['prediction_validation'] = validation_result
            self.workflow_stats['predictions_validated'] += validation_result.get('count', 0)
            
            # Step 2: Ensure future predictions exist
            generation_result = self._ensure_future_predictions(lottery_type)
            results['prediction_generation'] = generation_result
            self.workflow_stats['predictions_generated'] += generation_result.get('count', 0)
            
            # Mark workflow as complete
            results['workflow_complete'] = True
            logger.info(f"✅ WORKFLOW: Post-update tasks completed for {lottery_type}")
            
        except Exception as e:
            logger.error(f"❌ WORKFLOW ERROR: {e}")
            results['error'] = str(e)
            self.workflow_stats['errors'].append({
                'lottery_type': lottery_type,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return results
    
    def _validate_predictions(self, lottery_type: str, database_record_id: int) -> Dict:
        """Validate predictions against newly uploaded result"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # Get the newly uploaded result
            cur.execute("""
                SELECT draw_date, main_numbers, bonus_numbers
                FROM lottery_results
                WHERE id = %s
            """, (database_record_id,))
            
            result_row = cur.fetchone()
            if not result_row:
                logger.warning(f"No result found for ID {database_record_id}")
                cur.close()
                conn.close()
                return {'success': False, 'count': 0, 'error': 'Result not found'}
            
            draw_date, actual_main, actual_bonus = result_row
            
            # Find predictions for this date/lottery type
            cur.execute("""
                SELECT id, predicted_numbers, bonus_numbers
                FROM lottery_predictions
                WHERE game_type = %s 
                  AND target_draw_date = %s
                  AND validation_status = 'pending'
            """, (lottery_type, draw_date))
            
            predictions = cur.fetchall()
            validated_count = 0
            
            for pred_id, pred_main, pred_bonus in predictions:
                # Calculate matches
                matches = self._calculate_prediction_accuracy(
                    actual_main, actual_bonus, pred_main, pred_bonus
                )
                
                # Update prediction with validation results
                cur.execute("""
                    UPDATE lottery_predictions
                    SET validation_status = CASE 
                            WHEN %s >= 4 THEN 'correct'
                            ELSE 'incorrect'
                        END,
                        verified_at = NOW(),
                        is_verified = TRUE,
                        main_number_matches = %s,
                        bonus_number_matches = %s,
                        accuracy_percentage = %s,
                        matched_main_numbers = %s
                    WHERE id = %s
                """, (
                    matches['main_matches'],
                    matches['main_matches'],
                    matches['bonus_matches'],
                    matches['accuracy_percentage'],
                    json.dumps(matches['matched_numbers']),
                    pred_id
                ))
                validated_count += 1
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ Validated {validated_count} predictions for {lottery_type}")
            return {'success': True, 'count': validated_count}
            
        except Exception as e:
            logger.error(f"❌ Prediction validation error: {e}")
            return {'success': False, 'count': 0, 'error': str(e)}
    
    def _calculate_prediction_accuracy(self, actual_main, actual_bonus, pred_main, pred_bonus) -> Dict:
        """Calculate how accurate a prediction was"""
        try:
            # Parse actual numbers
            if isinstance(actual_main, str):
                actual_main = json.loads(actual_main)
            if isinstance(actual_bonus, str):
                actual_bonus = json.loads(actual_bonus) if actual_bonus not in ['{}', '[]', None] else []
            
            # Parse predicted numbers
            if isinstance(pred_main, str):
                if pred_main.startswith('{'):
                    pred_main = [int(x.strip()) for x in pred_main.strip('{}').split(',') if x.strip()]
                else:
                    pred_main = json.loads(pred_main)
            
            if isinstance(pred_bonus, str):
                if pred_bonus.startswith('{'):
                    pred_bonus = [int(x.strip()) for x in pred_bonus.strip('{}').split(',') if x.strip()]
                else:
                    pred_bonus = json.loads(pred_bonus) if pred_bonus not in ['{}', '[]', None] else []
            
            # Calculate matches
            matched_main = set(actual_main or []) & set(pred_main or [])
            matched_bonus = set(actual_bonus or []) & set(pred_bonus or [])
            
            total_predicted = len(pred_main or []) + len(pred_bonus or [])
            total_matched = len(matched_main) + len(matched_bonus)
            
            accuracy_pct = (total_matched / total_predicted * 100) if total_predicted > 0 else 0
            
            return {
                'main_matches': len(matched_main),
                'bonus_matches': len(matched_bonus),
                'matched_numbers': sorted(list(matched_main)),
                'accuracy_percentage': round(accuracy_pct, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return {
                'main_matches': 0,
                'bonus_matches': 0,
                'matched_numbers': [],
                'accuracy_percentage': 0.0
            }
    
    def _ensure_future_predictions(self, lottery_type: str) -> Dict:
        """Ensure predictions exist for future draws"""
        try:
            # Import the fresh prediction generator
            from fresh_prediction_generator import generate_fresh_predictions_for_new_draws
            
            # Generate fresh predictions
            success = generate_fresh_predictions_for_new_draws()
            
            if success:
                logger.info(f"✅ Generated fresh predictions for {lottery_type}")
                return {'success': True, 'count': 1}
            else:
                logger.warning(f"⚠️ Fresh prediction generation returned False")
                return {'success': False, 'count': 0}
                
        except Exception as e:
            logger.error(f"❌ Fresh prediction generation error: {e}")
            return {'success': False, 'count': 0, 'error': str(e)}
    
    def get_workflow_statistics(self) -> Dict:
        """Get statistics about workflow execution"""
        return {
            'total_database_updates': self.workflow_stats['database_updates'],
            'total_predictions_validated': self.workflow_stats['predictions_validated'],
            'total_predictions_generated': self.workflow_stats['predictions_generated'],
            'total_screenshots_archived': self.workflow_stats['screenshots_archived'],
            'error_count': len(self.workflow_stats['errors']),
            'recent_errors': self.workflow_stats['errors'][-5:] if self.workflow_stats['errors'] else []
        }
    
    def health_check(self) -> Dict:
        """
        Perform a health check on the entire workflow system
        
        Returns:
            Dict with health status
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            health = {
                'database_connected': True,
                'recent_results': 0,
                'active_predictions': 0,
                'archived_screenshots': 0,
                'last_automation_run': None,
                'issues': []
            }
            
            # Check recent lottery results
            cur.execute("""
                SELECT COUNT(*) FROM lottery_results
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)
            health['recent_results'] = cur.fetchone()[0]
            
            # Check active predictions
            cur.execute("""
                SELECT COUNT(*) FROM lottery_predictions
                WHERE validation_status = 'pending'
                  AND target_draw_date >= CURRENT_DATE
            """)
            health['active_predictions'] = cur.fetchone()[0]
            
            # Check last automation run
            cur.execute("""
                SELECT MAX(created_at) FROM automation_logs
                WHERE success = TRUE
            """)
            last_run = cur.fetchone()[0]
            health['last_automation_run'] = last_run.isoformat() if last_run else None
            
            # Check for issues
            if health['recent_results'] == 0:
                health['issues'].append('No recent lottery results (7 days)')
            
            if health['active_predictions'] < 6:
                health['issues'].append(f'Only {health["active_predictions"]} active predictions (expected 6)')
            
            cur.close()
            conn.close()
            
            health['status'] = 'healthy' if not health['issues'] else 'needs_attention'
            
            return health
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'status': 'error',
                'database_connected': False,
                'error': str(e)
            }


# Global orchestrator instance
_workflow_orchestrator = None

def get_workflow_orchestrator() -> EnhancedWorkflowOrchestrator:
    """Get or create the global workflow orchestrator instance"""
    global _workflow_orchestrator
    if _workflow_orchestrator is None:
        _workflow_orchestrator = EnhancedWorkflowOrchestrator()
    return _workflow_orchestrator


if __name__ == "__main__":
    # Test the workflow orchestrator
    logging.basicConfig(level=logging.INFO)
    
    orchestrator = EnhancedWorkflowOrchestrator()
    
    # Run health check
    health = orchestrator.health_check()
    print(f"Workflow Health Check:")
    print(json.dumps(health, indent=2))
