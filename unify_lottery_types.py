"""
Script to unify lottery type names in the database.

This script standardizes lottery type names by converting legacy "Lotto" to
the SEO-preferred "Lottery" naming convention.

WARNING: Makes changes to the database. Please backup before running.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variable"""
    return os.environ.get('DATABASE_URL')

def unify_lottery_types(dry_run=True):
    """
    Unify lottery type names in the database.
    
    Args:
        dry_run (bool): If True, only show what changes would be made without executing them
        
    Returns:
        dict: Statistics about the changes
    """
    logger.info(f"Unifying lottery type names (dry_run={dry_run})")
    
    # Get database URL
    db_url = get_database_url()
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return {'success': False, 'error': 'Database URL not set'}
    
    # Define mapping of old to new names
    rename_mapping = {
        'Lotto': 'Lottery',
        'Lotto Plus 1': 'Lottery Plus 1',
        'Lotto Plus 2': 'Lottery Plus 2',
        'Daily Lotto': 'Daily Lottery'
    }
    
    stats = {
        'total_updated': 0,
        'by_type': {}
    }
    
    try:
        # Create database engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check current counts
                logger.info("Current lottery type counts:")
                count_query = text("SELECT lottery_type, COUNT(*) FROM lottery_result GROUP BY lottery_type ORDER BY lottery_type")
                results = conn.execute(count_query)
                
                for lottery_type, count in results:
                    print(f"{lottery_type}: {count}")
                
                # Process each rename
                for old_name, new_name in rename_mapping.items():
                    # Count records with old name
                    count_query = text("SELECT COUNT(*) FROM lottery_result WHERE lottery_type = :old_name")
                    count = conn.execute(count_query, {'old_name': old_name}).scalar()
                    
                    if count > 0:
                        logger.info(f"Found {count} records with type '{old_name}'")
                        stats['by_type'][old_name] = count
                        stats['total_updated'] += count
                        
                        # Check for conflicts
                        conflict_query = text("""
                            SELECT old.draw_number, old.lottery_type, new.lottery_type
                            FROM 
                                (SELECT draw_number FROM lottery_result WHERE lottery_type = :old_name) AS old
                            JOIN 
                                (SELECT draw_number FROM lottery_result WHERE lottery_type = :new_name) AS new
                            ON old.draw_number = new.draw_number
                        """)
                        
                        conflicts = list(conn.execute(conflict_query, {'old_name': old_name, 'new_name': new_name}))
                        if conflicts:
                            logger.warning(f"Found {len(conflicts)} potential conflicts when renaming '{old_name}' to '{new_name}'")
                            for draw_number, old_type, new_type in conflicts[:5]:  # Show first 5 conflicts
                                logger.warning(f"  Conflict for draw {draw_number}: {old_type} → {new_type}")
                        
                        # Update records if not a dry run
                        if not dry_run:
                            update_query = text("""
                                UPDATE lottery_result 
                                SET lottery_type = :new_name
                                WHERE lottery_type = :old_name
                            """)
                            
                            result = conn.execute(update_query, {'old_name': old_name, 'new_name': new_name})
                            logger.info(f"Updated {result.rowcount} records from '{old_name}' to '{new_name}'")
                    else:
                        logger.info(f"No records found with type '{old_name}'")
                
                if dry_run:
                    logger.info("Dry run completed. No changes were made.")
                    trans.rollback()
                else:
                    logger.info("Committing changes...")
                    trans.commit()
                    logger.info("Changes committed successfully")
                
                    # Show updated counts
                    logger.info("Updated lottery type counts:")
                    count_query = text("SELECT lottery_type, COUNT(*) FROM lottery_result GROUP BY lottery_type ORDER BY lottery_type")
                    results = conn.execute(count_query)
                    
                    for lottery_type, count in results:
                        print(f"{lottery_type}: {count}")
            
            except Exception as e:
                trans.rollback()
                logger.error(f"Error during update: {str(e)}")
                return {'success': False, 'error': f'Error during update: {str(e)}'}
        
        return {'success': True, 'stats': stats}
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return {'success': False, 'error': f'Database error: {str(e)}'}
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return {'success': False, 'error': f'General error: {str(e)}'}

if __name__ == "__main__":
    dry_run = True
    
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'execute':
        dry_run = False
        print("WARNING: This will modify the database. Press Ctrl+C to cancel...")
        try:
            import time
            for i in range(5, 0, -1):
                print(f"Executing in {i} seconds...", end="\r")
                time.sleep(1)
            print("Executing now...                ")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)
    
    result = unify_lottery_types(dry_run=dry_run)