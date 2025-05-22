#!/usr/bin/env python3
"""
Fix incorrect lottery draw ID numbers (Version 2).
This script safely corrects the draw IDs to match official Ithuba National Lottery data.
"""

import os
import sys
import json
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError

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

# Draw ID corrections for main lottery games
DRAW_ID_CORRECTIONS = {
    "Lottery": {
        "2642": "2542", # Latest Saturday draw
        "2641": "2541"  # Previous Wednesday draw
    },
    "Lottery Plus 1": {
        "2642": "2542", # Latest Saturday draw
        "2641": "2541"  # Previous Wednesday draw
    },
    "Lottery Plus 2": {
        "2642": "2542", # Latest Saturday draw
        "2641": "2541"  # Previous Wednesday draw
    },
    "Powerball": {
        "1616": "1615", # Latest Friday draw 
    },
    "Powerball Plus": {
        "1616": "1615", # Latest Friday draw
    }
}

def check_existing_draws():
    """Check what draw IDs exist in the database before making any changes."""
    print("\nExisting draw IDs in database:")
    print("-" * 80)
    
    with app.app_context():
        for lottery_type in DRAW_ID_CORRECTIONS.keys():
            # Check both incorrect and correct IDs
            for incorrect_id, correct_id in DRAW_ID_CORRECTIONS[lottery_type].items():
                # Check incorrect IDs
                incorrect_draws = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=incorrect_id
                ).all()
                
                if lottery_type.startswith("Lottery"):
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    alt_incorrect = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=incorrect_id
                    ).all()
                    incorrect_draws.extend(alt_incorrect)
                
                # Check correct IDs
                correct_draws = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=correct_id
                ).all()
                
                if lottery_type.startswith("Lottery"):
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    alt_correct = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=correct_id
                    ).all()
                    correct_draws.extend(alt_correct)
                
                print(f"{lottery_type}:")
                print(f"  Draw #{incorrect_id} (incorrect ID): {len(incorrect_draws)} records")
                print(f"  Draw #{correct_id} (correct ID): {len(correct_draws)} records")
                
                # Show details of each record
                for draw in incorrect_draws:
                    print(f"    * ID: {draw.id}, Type: {draw.lottery_type}, Date: {draw.draw_date.strftime('%Y-%m-%d')}")
                
                for draw in correct_draws:
                    print(f"    * ID: {draw.id}, Type: {draw.lottery_type}, Date: {draw.draw_date.strftime('%Y-%m-%d')}")

def handle_duplicates():
    """
    Handle cases where both incorrect and correct draw IDs exist.
    In cases of duplication, keep the more accurate record and delete the other.
    """
    merged_count = 0
    deleted_count = 0
    
    with app.app_context():
        for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
            for incorrect_id, correct_id in corrections.items():
                # First, check if duplicates exist
                incorrect_draws = []
                correct_draws = []
                
                # Get draws with incorrect IDs
                base_incorrect = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=incorrect_id
                ).all()
                incorrect_draws.extend(base_incorrect)
                
                if lottery_type.startswith("Lottery"):
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    alt_incorrect = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=incorrect_id
                    ).all()
                    incorrect_draws.extend(alt_incorrect)
                
                # Get draws with correct IDs
                base_correct = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=correct_id
                ).all()
                correct_draws.extend(base_correct)
                
                if lottery_type.startswith("Lottery"):
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    alt_correct = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=correct_id
                    ).all()
                    correct_draws.extend(alt_correct)
                
                # If both exist, we need to handle the duplicate
                if incorrect_draws and correct_draws:
                    logger.info(f"Duplicate found for {lottery_type}: both #{incorrect_id} and #{correct_id} exist")
                    
                    # If both exist, keep the record with more data (like divisions)
                    for incorrect_draw in incorrect_draws:
                        keep_incorrect = False
                        
                        # Check if the incorrect draw has valuable data
                        if incorrect_draw.divisions and not any(d.divisions for d in correct_draws):
                            keep_incorrect = True
                        
                        if keep_incorrect:
                            # Delete all correct draws (we'll update the incorrect one instead)
                            for correct_draw in correct_draws:
                                logger.info(f"Deleting duplicate {correct_draw.lottery_type} #{correct_draw.draw_number} (ID: {correct_draw.id})")
                                db.session.delete(correct_draw)
                                deleted_count += 1
                            
                            # Now we can safely update the incorrect draw
                            incorrect_draw.draw_number = correct_id
                            logger.info(f"Updated {incorrect_draw.lottery_type} from #{incorrect_id} to #{correct_id} (ID: {incorrect_draw.id})")
                            merged_count += 1
                        else:
                            # Delete the incorrect draw since correct one has better data
                            logger.info(f"Deleting duplicate {incorrect_draw.lottery_type} #{incorrect_draw.draw_number} (ID: {incorrect_draw.id})")
                            db.session.delete(incorrect_draw)
                            deleted_count += 1
                
                db.session.commit()  # Commit after each lottery type to avoid long transactions
    
    return merged_count, deleted_count

def fix_draw_ids():
    """Fix incorrect lottery draw IDs in the database after handling duplicates."""
    fixed_count = 0
    
    with app.app_context():
        for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
            for incorrect_id, correct_id in corrections.items():
                # Only attempt to fix if correct ID doesn't already exist
                existing_correct = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=correct_id
                ).first()
                
                if lottery_type.startswith("Lottery"):
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    alt_existing = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=correct_id
                    ).first()
                    if alt_existing:
                        existing_correct = alt_existing
                
                if not existing_correct:
                    # Safe to update incorrect IDs
                    incorrect_draws = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=incorrect_id
                    ).all()
                    
                    if lottery_type.startswith("Lottery"):
                        alt_type = lottery_type.replace("Lottery", "Lotto")
                        alt_incorrect = LotteryResult.query.filter_by(
                            lottery_type=alt_type,
                            draw_number=incorrect_id
                        ).all()
                        incorrect_draws.extend(alt_incorrect)
                    
                    for result in incorrect_draws:
                        try:
                            old_id = result.draw_number
                            result.draw_number = correct_id
                            db.session.commit()
                            fixed_count += 1
                            logger.info(f"Fixed draw ID for {result.lottery_type} from {old_id} to {correct_id} (Date: {result.draw_date.strftime('%Y-%m-%d')})")
                        except IntegrityError:
                            db.session.rollback()
                            logger.warning(f"Could not update {result.lottery_type} #{incorrect_id} due to duplicate entry")
    
    return fixed_count

def verify_corrections():
    """Verify that all draw IDs are now correct."""
    
    with app.app_context():
        print("\nVerifying draw ID corrections:")
        print("-" * 80)
        
        all_correct = True
        
        for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
            for incorrect_id, correct_id in corrections.items():
                # Check if incorrect IDs still exist
                incorrect_draws = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=incorrect_id
                ).all()
                
                if lottery_type.startswith("Lottery"):
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    alt_incorrect = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=incorrect_id
                    ).all()
                    incorrect_draws.extend(alt_incorrect)
                
                # Check if correct IDs exist
                correct_draws = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=correct_id
                ).all()
                
                if lottery_type.startswith("Lottery"):
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    alt_correct = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=correct_id
                    ).all()
                    correct_draws.extend(alt_correct)
                
                if incorrect_draws:
                    all_correct = False
                    print(f"❌ {lottery_type} Draw #{incorrect_id} still exists in database ({len(incorrect_draws)} records)")
                else:
                    print(f"✅ {lottery_type} Draw #{incorrect_id} no longer exists in database")
                
                if correct_draws:
                    print(f"✅ {lottery_type} Draw #{correct_id} exists in database ({len(correct_draws)} records)")
                    for draw in correct_draws:
                        print(f"    * ID: {draw.id}, Type: {draw.lottery_type}, Date: {draw.draw_date.strftime('%Y-%m-%d')}")
                else:
                    all_correct = False
                    print(f"❌ {lottery_type} Draw #{correct_id} missing from database")
        
        return all_correct

def main():
    """Main function to fix lottery draw IDs."""
    try:
        print("Checking current lottery draw IDs in database...")
        check_existing_draws()
        
        print("\nHandling duplicate draw records...")
        merged, deleted = handle_duplicates()
        print(f"Merged {merged} records and deleted {deleted} duplicate records.")
        
        print("\nFixing remaining incorrect lottery draw IDs...")
        fixed = fix_draw_ids()
        print(f"Successfully fixed {fixed} additional lottery draw IDs.")
        
        # Verify our corrections
        all_correct = verify_corrections()
        if all_correct:
            print("\nAll lottery draw IDs have been successfully corrected!")
        else:
            print("\nSome issues still remain with lottery draw IDs.")
        
    except Exception as e:
        logger.error(f"Error fixing lottery draw IDs: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()