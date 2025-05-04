"""
Utility script to check and fix inconsistent draw IDs in the database
This ensures that lottery games drawn together always share the same draw ID
"""
import logging
import sys
from datetime import datetime, timedelta
from main import app, db
from models import LotteryResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define related lottery games that must share the same draw ID
LOTTERY_GROUPS = {
    'lottery': ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2'],
    'powerball': ['Powerball', 'Powerball Plus']
}

def get_inconsistent_draws():
    """
    Find all cases where lottery games drawn together have different draw IDs
    
    Returns:
        dict: Dictionary of inconsistent draws grouped by date and lottery group
    """
    inconsistent_draws = {}
    
    with app.app_context():
        # Check each lottery group separately
        for group_name, lottery_types in LOTTERY_GROUPS.items():
            logger.info(f"Checking {group_name} group consistency...")
            
            # Get all draws for all lottery types in this group
            all_draws = {}
            for lottery_type in lottery_types:
                results = LotteryResult.query.filter_by(lottery_type=lottery_type).all()
                logger.info(f"Found {len(results)} draws for {lottery_type}")
                all_draws[lottery_type] = results
            
            # Group draws by date
            draws_by_date = {}
            for lottery_type, results in all_draws.items():
                for result in results:
                    # Use date only as the key
                    date_key = result.draw_date.strftime('%Y-%m-%d')
                    if date_key not in draws_by_date:
                        draws_by_date[date_key] = {}
                    if lottery_type not in draws_by_date[date_key]:
                        draws_by_date[date_key][lottery_type] = []
                    draws_by_date[date_key][lottery_type].append(result)
            
            # Check each date for inconsistencies
            for date_key, draws_by_type in draws_by_date.items():
                # If we have draws for more than one lottery type on this date
                if len(draws_by_type) > 1:
                    draw_numbers = {}
                    for lottery_type, draws in draws_by_type.items():
                        if draws:  # Check if the list is not empty
                            draw_numbers[lottery_type] = draws[0].draw_number
                    
                    # If we have more than one distinct draw number, we have an inconsistency
                    unique_draw_numbers = set(draw_numbers.values())
                    if len(unique_draw_numbers) > 1:
                        logger.warning(f"Inconsistent draw numbers for {group_name} on {date_key}: {draw_numbers}")
                        
                        if group_name not in inconsistent_draws:
                            inconsistent_draws[group_name] = {}
                        inconsistent_draws[group_name][date_key] = draw_numbers
    
    return inconsistent_draws

def fix_inconsistent_draws(inconsistent_draws, dry_run=True):
    """
    Fix inconsistent draw IDs by updating records to use a common draw ID
    
    Args:
        inconsistent_draws (dict): Dictionary of inconsistent draws as returned by get_inconsistent_draws()
        dry_run (bool): If True, don't modify the database, just show what would be done
        
    Returns:
        int: Number of records fixed
    """
    fixed_count = 0
    
    with app.app_context():
        # Process each lottery group
        for group_name, dates in inconsistent_draws.items():
            logger.info(f"Processing {group_name} group...")
            
            # Process each date with inconsistencies
            for date_key, draw_numbers in dates.items():
                logger.info(f"Processing date {date_key}...")
                
                # Determine which draw number to use as the common one
                # Strategy: Use the first lottery type in the group's list as the primary one
                common_draw_number = None
                for lottery_type in LOTTERY_GROUPS[group_name]:
                    if lottery_type in draw_numbers:
                        common_draw_number = draw_numbers[lottery_type]
                        logger.info(f"Using draw number {common_draw_number} from {lottery_type} as the common one")
                        break
                
                if common_draw_number is None:
                    logger.warning(f"Couldn't determine a common draw number for {group_name} on {date_key}")
                    continue
                
                # Update all records to use the common draw number
                date_start = datetime.strptime(date_key, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date_start.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                for lottery_type in LOTTERY_GROUPS[group_name]:
                    if lottery_type in draw_numbers and draw_numbers[lottery_type] != common_draw_number:
                        old_draw_number = draw_numbers[lottery_type]
                        
                        # Find the record to update
                        record = LotteryResult.query.filter(
                            LotteryResult.lottery_type == lottery_type,
                            LotteryResult.draw_number == old_draw_number,
                            LotteryResult.draw_date >= date_start,
                            LotteryResult.draw_date <= date_end
                        ).first()
                        
                        if record:
                            logger.info(f"{'Would update' if dry_run else 'Updating'} {lottery_type} draw {old_draw_number} to {common_draw_number}")
                            
                            if not dry_run:
                                # Check if there's already a record with the new draw number
                                existing = LotteryResult.query.filter_by(
                                    lottery_type=lottery_type,
                                    draw_number=common_draw_number
                                ).first()
                                
                                if existing:
                                    logger.warning(f"A record for {lottery_type} with draw number {common_draw_number} already exists. Merging data...")
                                    
                                    # Update the existing record with any missing data from the old record
                                    if not existing.numbers and record.numbers:
                                        existing.numbers = record.numbers
                                    if not existing.bonus_numbers and record.bonus_numbers:
                                        existing.bonus_numbers = record.bonus_numbers
                                    if not existing.divisions and record.divisions:
                                        existing.divisions = record.divisions
                                    
                                    # Delete the old record
                                    db.session.delete(record)
                                else:
                                    # Update the record with the new draw number
                                    record.draw_number = common_draw_number
                                
                                db.session.commit()
                                fixed_count += 1
    
    return fixed_count

def check_for_missing_relationships():
    """
    Check for cases where a lottery type from a group exists but related types are missing
    
    Returns:
        dict: Dictionary of missing relationships
    """
    missing_relationships = {}
    
    with app.app_context():
        # Check each lottery group
        for group_name, lottery_types in LOTTERY_GROUPS.items():
            logger.info(f"Checking for missing relationships in {group_name} group...")
            
            # Get all draws for all lottery types in this group
            all_draws = {}
            for lottery_type in lottery_types:
                results = LotteryResult.query.filter_by(lottery_type=lottery_type).all()
                logger.info(f"Found {len(results)} draws for {lottery_type}")
                all_draws[lottery_type] = {r.draw_number: r for r in results}
            
            # Check each lottery type for draws that are missing in other types
            for primary_type in lottery_types:
                for draw_number, record in all_draws[primary_type].items():
                    # Check if this draw exists in all other lottery types in the group
                    missing_types = []
                    for other_type in lottery_types:
                        if other_type != primary_type and draw_number not in all_draws[other_type]:
                            missing_types.append(other_type)
                    
                    if missing_types:
                        logger.warning(f"Draw {draw_number} exists for {primary_type} but is missing for {', '.join(missing_types)}")
                        
                        date_key = record.draw_date.strftime('%Y-%m-%d')
                        if group_name not in missing_relationships:
                            missing_relationships[group_name] = {}
                        if date_key not in missing_relationships[group_name]:
                            missing_relationships[group_name][date_key] = {}
                        if primary_type not in missing_relationships[group_name][date_key]:
                            missing_relationships[group_name][date_key][primary_type] = {}
                        
                        missing_relationships[group_name][date_key][primary_type][draw_number] = missing_types
    
    return missing_relationships

def print_integrity_report():
    """
    Print a comprehensive integrity report about draw ID relationships
    """
    print("\n=== LOTTERY DRAW ID INTEGRITY REPORT ===\n")
    
    # Check for inconsistent draw IDs
    inconsistent_draws = get_inconsistent_draws()
    if inconsistent_draws:
        print(f"\nFound {sum(len(dates) for dates in inconsistent_draws.values())} dates with inconsistent draw IDs:")
        for group_name, dates in inconsistent_draws.items():
            print(f"\n  {group_name.upper()} GROUP:")
            for date_key, draw_numbers in dates.items():
                print(f"    {date_key}: {draw_numbers}")
    else:
        print("\nNo inconsistent draw IDs found. All related lottery games share the same draw ID.")
    
    # Check for missing relationships
    missing_relationships = check_for_missing_relationships()
    if missing_relationships:
        print(f"\nFound missing relationships between lottery games:")
        for group_name, dates in missing_relationships.items():
            print(f"\n  {group_name.upper()} GROUP:")
            for date_key, primary_types in dates.items():
                print(f"    {date_key}:")
                for primary_type, draws in primary_types.items():
                    for draw_number, missing_types in draws.items():
                        print(f"      {primary_type} draw {draw_number} exists but is missing for {', '.join(missing_types)}")
    else:
        print("\nNo missing relationships found. All related lottery games have corresponding draws.")
    
    print("\n=== END OF REPORT ===\n")

def fix_all_issues(dry_run=True):
    """
    Fix all identified integrity issues
    
    Args:
        dry_run (bool): If True, don't modify the database, just show what would be done
        
    Returns:
        dict: Dictionary with counts of fixed issues
    """
    results = {
        "inconsistent_draws_fixed": 0,
        "missing_relationships_addressed": 0
    }
    
    # Fix inconsistent draw IDs
    inconsistent_draws = get_inconsistent_draws()
    if inconsistent_draws:
        fixed_count = fix_inconsistent_draws(inconsistent_draws, dry_run)
        results["inconsistent_draws_fixed"] = fixed_count
    
    # TODO: Implement fix for missing relationships if needed
    
    return results

if __name__ == "__main__":
    print_integrity_report()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        dry_run = len(sys.argv) > 2 and sys.argv[2] == "--dry-run"
        print(f"\nRunning in {'DRY RUN' if dry_run else 'LIVE'} mode")
        
        results = fix_all_issues(dry_run)
        print(f"\nFixed {results['inconsistent_draws_fixed']} inconsistent draws")
        print(f"Addressed {results['missing_relationships_addressed']} missing relationships")
        
        if dry_run:
            print("\nThis was a dry run. No changes were made to the database.")
            print("Run with 'python fix_lottery_relationships.py --fix' to make actual changes.")
    else:
        print("\nThis was a report only. No changes were made to the database.")
        print("Run with 'python fix_lottery_relationships.py --fix' to fix the issues.")
        print("Run with 'python fix_lottery_relationships.py --fix --dry-run' to simulate fixing the issues.")