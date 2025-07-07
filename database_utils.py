"""
Database Utilities Module
Extracted from main.py for better code organization (Phase 2 refactoring)
"""

import logging
from sqlalchemy import text
from models import db

logger = logging.getLogger(__name__)

def get_database_stats():
    """Get comprehensive database statistics"""
    try:
        # Table sizes
        size_query = text("""
            SELECT 
                table_name,
                pg_size_pretty(pg_total_relation_size(table_name::regclass)) as size,
                pg_total_relation_size(table_name::regclass) as size_bytes
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY pg_total_relation_size(table_name::regclass) DESC
        """)
        
        result = db.session.execute(size_query)
        table_stats = result.fetchall()
        
        # Index information
        index_query = text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes 
            ORDER BY pg_relation_size(indexrelid) DESC
        """)
        
        result = db.session.execute(index_query)
        index_stats = result.fetchall()
        
        return {
            'tables': table_stats,
            'indexes': index_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return None

def cleanup_old_health_checks(days=7):
    """Clean up old health check records"""
    try:
        cleanup_query = text("""
            DELETE FROM health_check_history 
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """ % days)
        
        result = db.session.execute(cleanup_query)
        db.session.commit()
        
        logger.info(f"Cleaned up {result.rowcount} old health check records")
        return result.rowcount
        
    except Exception as e:
        logger.error(f"Error cleaning up health checks: {e}")
        db.session.rollback()
        return 0

def optimize_lottery_tables():
    """Ensure lottery_results table has proper indexes"""
    try:
        # Add missing indexes if they don't exist
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_lottery_results_type_date ON lottery_results(lottery_type, draw_date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_lottery_results_draw_number ON lottery_results(draw_number)",
            "CREATE INDEX IF NOT EXISTS idx_lottery_results_date ON lottery_results(draw_date DESC)"
        ]
        
        for index_sql in indexes:
            db.session.execute(text(index_sql))
        
        db.session.commit()
        logger.info("Lottery table indexes optimized")
        return True
        
    except Exception as e:
        logger.error(f"Error optimizing lottery tables: {e}")
        db.session.rollback()
        return False

def get_lottery_statistics():
    """Get lottery data statistics"""
    try:
        stats_query = text("""
            SELECT 
                lottery_type,
                COUNT(*) as record_count,
                MIN(draw_date) as earliest_date,
                MAX(draw_date) as latest_date,
                MAX(draw_number) as latest_draw_number
            FROM lottery_results 
            GROUP BY lottery_type 
            ORDER BY lottery_type
        """)
        
        result = db.session.execute(stats_query)
        return result.fetchall()
        
    except Exception as e:
        logger.error(f"Error getting lottery statistics: {e}")
        return []