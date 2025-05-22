#!/usr/bin/env python3
"""
Fix lottery draw IDs by first checking for duplicates and deleting them if needed.
"""

import os
import sys
import logging
from sqlalchemy import text

# Import app and database
try:
    from main import app, db
    from models import LotteryResult
except ImportError:
    print("Could not import app or models. Make sure you're in the right directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('draw_id_fix')

# Mapping of incorrect to correct IDs
DRAW_ID_CORRECTIONS = {
    "Lottery": {
        "2642": "2542",
        "2641": "2541"
    },
    "Lottery Plus 1": {
        "2642": "2542",
        "2641": "2541"
    },
    "Lottery Plus 2": {
        "2642": "2542",
        "2641": "2541"
    },
    "Powerball": {
        "1616": "1615",
        "1615": "1614"
    },
    "Powerball Plus": {
        "1616": "1615",
        "1615": "1614"
    },
    "Daily Lottery": {
        "2258": "2256",
        "2257": "2255",
        "2256": "2254",
        "2255": "2253"
    }
}

def check_current_draws():
    """Check what draw IDs exist in the database."""
    print("Current lottery draw IDs in database:")
    print("-" * 80)
    
    with app.app_context():
        # Check the draw IDs for each lottery type
        for lottery_type in DRAW_ID_CORRECTIONS.keys():
            # Get the most recent draws for this lottery type
            draws = LotteryResult.query.filter_by(
                lottery_type=lottery_type
            ).order_by(db.desc(LotteryResult.draw_date)).limit(5).all()
            
            if draws:
                print(f"{lottery_type}:")
                for draw in draws:
                    print(f"  Draw #{draw.draw_number} on {draw.draw_date.strftime('%Y-%m-%d')}")
            else:
                # Also check alternative naming (Lottery vs Lotto)
                if "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    draws = LotteryResult.query.filter_by(
                        lottery_type=alt_type
                    ).order_by(db.desc(LotteryResult.draw_date)).limit(5).all()
                    
                    if draws:
                        print(f"{alt_type}:")
                        for draw in draws:
                            print(f"  Draw #{draw.draw_number} on {draw.draw_date.strftime('%Y-%m-%d')}")
                    else:
                        print(f"{lottery_type}: No records found")
                else:
                    print(f"{lottery_type}: No records found")

def delete_conflicting_draws():
    """Delete draws that will conflict with our updates."""
    deleted_count = 0
    
    with app.app_context():
        for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
            for incorrect_id, correct_id in corrections.items():
                # First check if we have both the incorrect and correct IDs
                incorrect_draw = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=incorrect_id
                ).first()
                
                correct_draw = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=correct_id
                ).first()
                
                # Also check with alternative naming (Lottery vs Lotto)
                if "Lottery" in lottery_type and not incorrect_draw:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    incorrect_draw = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=incorrect_id
                    ).first()
                
                if "Lottery" in lottery_type and not correct_draw:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    correct_draw = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=correct_id
                    ).first()
                
                # If both exist, decide which to keep
                if incorrect_draw and correct_draw:
                    # Check which has more data (like divisions)
                    if incorrect_draw.divisions and not correct_draw.divisions:
                        # Delete the correct draw, we'll update the incorrect one
                        db.session.delete(correct_draw)
                        db.session.commit()
                        deleted_count += 1
                        print(f"Deleted redundant {correct_draw.lottery_type} draw #{correct_id}")
                    else:
                        # Delete the incorrect draw, keep the correct one
                        db.session.delete(incorrect_draw)
                        db.session.commit()
                        deleted_count += 1
                        print(f"Deleted redundant {incorrect_draw.lottery_type} draw #{incorrect_id}")
    
    return deleted_count

def fix_remaining_ids():
    """Fix remaining incorrect IDs after duplicates have been handled."""
    fixed_count = 0
    
    with app.app_context():
        for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
            for incorrect_id, correct_id in corrections.items():
                # Check if incorrect ID exists
                incorrect_draw = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=incorrect_id
                ).first()
                
                # Also check with alternative naming (Lottery vs Lotto)
                if "Lottery" in lottery_type and not incorrect_draw:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    incorrect_draw = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=incorrect_id
                    ).first()
                
                # Check if correct ID already exists
                correct_draw = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=correct_id
                ).first()
                
                # Also check with alternative naming (Lottery vs Lotto)
                if "Lottery" in lottery_type and not correct_draw:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    correct_draw = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=correct_id
                    ).first()
                
                # Only update if incorrect exists and correct doesn't
                if incorrect_draw and not correct_draw:
                    # Safe to update
                    try:
                        incorrect_draw.draw_number = correct_id
                        db.session.commit()
                        fixed_count += 1
                        print(f"Fixed {incorrect_draw.lottery_type} draw #{incorrect_id} -> #{correct_id}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error fixing {incorrect_draw.lottery_type} draw #{incorrect_id}: {e}")
    
    return fixed_count

def create_sql_from_corrections():
    """Create SQL statements for direct database updates."""
    sql_commands = []
    
    for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
        for incorrect_id, correct_id in corrections.items():
            # Delete any potential conflicts first
            sql_commands.append(f"DELETE FROM lottery_result WHERE lottery_type = '{lottery_type}' AND draw_number = '{correct_id}' AND id NOT IN (SELECT id FROM lottery_result WHERE lottery_type = '{lottery_type}' AND draw_number = '{incorrect_id}' LIMIT 1)")
            
            # Then update the records
            sql_commands.append(f"UPDATE lottery_result SET draw_number = '{correct_id}' WHERE lottery_type = '{lottery_type}' AND draw_number = '{incorrect_id}'")
            
            # Also fix names with Lotto instead of Lottery
            if "Lottery" in lottery_type:
                alt_type = lottery_type.replace("Lottery", "Lotto")
                # Delete any potential conflicts first
                sql_commands.append(f"DELETE FROM lottery_result WHERE lottery_type = '{alt_type}' AND draw_number = '{correct_id}' AND id NOT IN (SELECT id FROM lottery_result WHERE lottery_type = '{alt_type}' AND draw_number = '{incorrect_id}' LIMIT 1)")
                
                # Then update the records
                sql_commands.append(f"UPDATE lottery_result SET draw_number = '{correct_id}' WHERE lottery_type = '{alt_type}' AND draw_number = '{incorrect_id}'")
    
    return sql_commands

def fix_with_direct_sql():
    """Fix using direct SQL commands that handle conflicts."""
    fixed_count = 0
    
    # Generate SQL statements that handle conflicts
    sql_commands = create_sql_from_corrections()
    
    with app.app_context():
        for sql in sql_commands:
            try:
                result = db.session.execute(text(sql))
                rows = result.rowcount
                if rows > 0:
                    fixed_count += rows
                    print(f"Executed: {sql} ({rows} rows affected)")
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error executing SQL: {sql}")
                print(f"Error details: {e}")
    
    return fixed_count

def main():
    """Main function to fix lottery draw IDs."""
    try:
        print("Checking current lottery draw IDs (before fix)...")
        check_current_draws()
        
        print("\nDeleting duplicate/conflicting draws...")
        deleted = delete_conflicting_draws()
        print(f"Deleted {deleted} conflicting draws.")
        
        print("\nFixing remaining incorrect draw IDs...")
        fixed = fix_remaining_ids()
        print(f"Fixed {fixed} incorrect draw IDs.")
        
        if fixed == 0 and deleted == 0:
            print("\nAttempting direct SQL fix that handles conflicts...")
            sql_fixed = fix_with_direct_sql()
            print(f"Fixed {sql_fixed} draws using direct SQL.")
        
        print("\nChecking lottery draw IDs (after fix)...")
        check_current_draws()
        
    except Exception as e:
        logger.error(f"Error fixing lottery draw IDs: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()