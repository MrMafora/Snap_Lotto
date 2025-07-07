"""
Admin Utilities Module
Extracted from main.py for better code organization (Phase 2 refactoring)
Contains admin-specific functions and system management utilities
"""

import json
import logging
import os
import zipfile
from datetime import datetime
from io import BytesIO
from flask import send_file
from database_utils import get_database_stats, cleanup_old_health_checks
from lottery_utils import get_lottery_statistics_summary

logger = logging.getLogger(__name__)

def create_system_diagnostics():
    """Create comprehensive system diagnostics report"""
    diagnostics = {
        'timestamp': datetime.now().isoformat(),
        'database': {
            'stats': get_database_stats(),
            'health_checks_cleaned': cleanup_old_health_checks()
        },
        'system': {
            'python_version': os.sys.version,
            'environment': os.environ.get('ENVIRONMENT', 'development'),
            'debug_mode': os.environ.get('DEBUG', 'False').lower() == 'true'
        }
    }
    
    return diagnostics

def export_system_data():
    """Export system data for backup/analysis"""
    try:
        # Create in-memory ZIP file
        memory_file = BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add system diagnostics
            diagnostics = create_system_diagnostics()
            zf.writestr('system_diagnostics.json', json.dumps(diagnostics, indent=2))
            
            # Add database stats
            db_stats = get_database_stats()
            if db_stats:
                zf.writestr('database_stats.json', json.dumps(db_stats, indent=2, default=str))
        
        memory_file.seek(0)
        return memory_file
        
    except Exception as e:
        logger.error(f"Error creating system export: {e}")
        return None

def check_system_health():
    """Comprehensive system health check"""
    health_status = {
        'overall_status': 'healthy',
        'checks': {},
        'issues': []
    }
    
    try:
        # Database connectivity check
        db_stats = get_database_stats()
        if db_stats:
            health_status['checks']['database'] = 'healthy'
        else:
            health_status['checks']['database'] = 'unhealthy'
            health_status['issues'].append('Database connectivity issues')
            health_status['overall_status'] = 'unhealthy'
        
        # File system check
        try:
            test_file = 'health_check_temp.txt'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            health_status['checks']['filesystem'] = 'healthy'
        except:
            health_status['checks']['filesystem'] = 'unhealthy'
            health_status['issues'].append('File system write issues')
            health_status['overall_status'] = 'degraded'
        
        # Memory usage check (basic)
        import psutil
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            health_status['checks']['memory'] = 'warning'
            health_status['issues'].append(f'High memory usage: {memory.percent}%')
            health_status['overall_status'] = 'degraded'
        else:
            health_status['checks']['memory'] = 'healthy'
        
    except Exception as e:
        logger.error(f"Error in system health check: {e}")
        health_status['overall_status'] = 'unhealthy'
        health_status['issues'].append(f'Health check error: {str(e)}')
    
    return health_status

def cleanup_system_files():
    """Clean up temporary and old system files"""
    cleaned_files = 0
    
    try:
        # Clean up screenshots older than 30 days
        screenshot_dir = 'screenshots'
        if os.path.exists(screenshot_dir):
            for filename in os.listdir(screenshot_dir):
                filepath = os.path.join(screenshot_dir, filename)
                if os.path.isfile(filepath):
                    # Check file age
                    file_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(filepath))
                    if file_age.days > 30:
                        os.remove(filepath)
                        cleaned_files += 1
        
        # Clean up old log files
        log_files = ['app.log', 'error.log', 'debug.log']
        for log_file in log_files:
            if os.path.exists(log_file) and os.path.getsize(log_file) > 10 * 1024 * 1024:  # > 10MB
                # Archive large log files
                archive_name = f"{log_file}.{datetime.now().strftime('%Y%m%d')}"
                os.rename(log_file, archive_name)
                cleaned_files += 1
        
        logger.info(f"System cleanup completed: {cleaned_files} files processed")
        
    except Exception as e:
        logger.error(f"Error in system cleanup: {e}")
    
    return cleaned_files

def get_admin_dashboard_data():
    """Get comprehensive data for admin dashboard"""
    try:
        dashboard_data = {
            'system_health': check_system_health(),
            'database_stats': get_database_stats(),
            'lottery_summary': get_lottery_statistics_summary(),
            'recent_activity': get_recent_system_activity()
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard data: {e}")
        return {}

def get_recent_system_activity():
    """Get recent system activity for admin monitoring"""
    try:
        from models import db
        from sqlalchemy import text
        
        # Get recent lottery data additions
        recent_query = text("""
            SELECT 
                lottery_type,
                draw_number,
                draw_date,
                created_at
            FROM lottery_results 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        result = db.session.execute(recent_query)
        recent_activity = result.fetchall()
        
        return [dict(row._mapping) for row in recent_activity]
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return []