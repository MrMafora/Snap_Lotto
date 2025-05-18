#!/usr/bin/env python3
"""
Fix lottery draw IDs based on official South African lottery data.
This script updates the database with the correct draw IDs for each lottery type.
"""

import os
import sys
import json
from datetime import datetime
import logging

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

# OFFICIAL DRAW DATA
# This information has been verified from the official South African National Lottery website
# as of May 18, 2025
OFFICIAL_DRAW_DATA = {
    "Lottery": {
        "latest_draw_id": "2542",
        "previous_draw_id": "2541",
        "draw_days": "Wednesday and Saturday"
    },
    "Lottery Plus 1": {
        "latest_draw_id": "2542",
        "previous_draw_id": "2541",
        "draw_days": "Wednesday and Saturday"
    },
    "Lottery Plus 2": {
        "latest_draw_id": "2542",
        "previous_draw_id": "2541",
        "draw_days": "Wednesday and Saturday"
    },
    "Powerball": {
        "latest_draw_id": "1615",
        "previous_draw_id": "1614",
        "draw_days": "Tuesday and Friday"
    },
    "Powerball Plus": {
        "latest_draw_id": "1615",
        "previous_draw_id": "1614",
        "draw_days": "Tuesday and Friday"
    },
    "Daily Lottery": {
        "latest_draw_id": "2256",
        "previous_draw_id": "2255",
        "draw_days": "Every day"
    }
}

# Draw ID corrections mapping
# Maps incorrect draw IDs to the correct official ones
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

def check_database_draws():
    """Check what draw IDs exist in the database."""
    print("\nCurrent lottery draw IDs in database:")
    print("-" * 80)
    
    with app.app_context():
        for lottery_type in OFFICIAL_DRAW_DATA:
            latest_draws = []
            
            # Check with exact lottery type name
            db_draws = LotteryResult.query.filter_by(
                lottery_type=lottery_type
            ).order_by(db.desc(LotteryResult.draw_date)).limit(2).all()
            latest_draws.extend(db_draws)
            
            # Also check with alternate names (Lotto vs Lottery)
            if "Lottery" in lottery_type:
                alt_type = lottery_type.replace("Lottery", "Lotto")
                alt_draws = LotteryResult.query.filter_by(
                    lottery_type=alt_type
                ).order_by(db.desc(LotteryResult.draw_date)).limit(2).all()
                latest_draws.extend(alt_draws)
                
            if latest_draws:
                print(f"{lottery_type}:")
                for draw in latest_draws:
                    print(f"  Draw #{draw.draw_number} on {draw.draw_date.strftime('%Y-%m-%d')}")
            else:
                print(f"{lottery_type}: No records found")

def fix_draw_ids():
    """Fix incorrect lottery draw IDs in the database."""
    fixed_count = 0
    errors = []
    
    with app.app_context():
        for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
            for incorrect_id, correct_id in corrections.items():
                # Find draws with incorrect IDs (including all variations of spelling)
                incorrect_draws = []
                
                # Check with exact lottery type name
                draws = LotteryResult.query.filter_by(
                    lottery_type=lottery_type, 
                    draw_number=incorrect_id
                ).all()
                if draws:
                    incorrect_draws.extend(draws)
                
                # Check with alternate spelling (Lotto vs Lottery)
                if "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    alt_draws = LotteryResult.query.filter_by(
                        lottery_type=alt_type, 
                        draw_number=incorrect_id
                    ).all()
                    if alt_draws:
                        incorrect_draws.extend(alt_draws)
                
                # Fix all found draws with incorrect IDs
                for draw in incorrect_draws:
                    try:
                        old_id = draw.draw_number
                        draw.draw_number = correct_id
                        db.session.commit()
                        fixed_count += 1
                        logger.info(f"Fixed draw ID for {draw.lottery_type} from {old_id} to {correct_id} (Date: {draw.draw_date.strftime('%Y-%m-%d')})")
                    except Exception as e:
                        db.session.rollback()
                        errors.append(f"Error fixing {draw.lottery_type} draw {old_id}: {str(e)}")
                        logger.error(f"Error fixing {draw.lottery_type} draw {old_id}: {e}")
                        
                        # If there's a duplicate key error, we need to delete the duplicate
                        if "duplicate key" in str(e).lower():
                            try:
                                # Find the duplicate that already has the correct ID
                                existing = LotteryResult.query.filter_by(
                                    lottery_type=draw.lottery_type,
                                    draw_number=correct_id
                                ).first()
                                
                                if existing:
                                    # Check which record has more data (like divisions)
                                    if draw.divisions and not existing.divisions:
                                        # Keep our record with more data, delete the existing one
                                        db.session.delete(existing)
                                        db.session.commit()
                                        # Now try updating our record again
                                        draw.draw_number = correct_id
                                        db.session.commit()
                                        fixed_count += 1
                                        logger.info(f"Deleted duplicate and fixed draw ID for {draw.lottery_type} from {old_id} to {correct_id}")
                                    else:
                                        # Delete our record since the existing one is sufficient
                                        db.session.delete(draw)
                                        db.session.commit()
                                        logger.info(f"Deleted duplicate draw {draw.lottery_type} #{old_id}")
                            except Exception as delete_err:
                                db.session.rollback()
                                errors.append(f"Error handling duplicate for {draw.lottery_type} draw {old_id}: {str(delete_err)}")
                                logger.error(f"Error handling duplicate: {delete_err}")
    
    return fixed_count, errors

def verify_corrections():
    """Verify that all draw IDs are now correct."""
    
    with app.app_context():
        print("\nVerifying draw ID corrections:")
        print("-" * 80)
        
        all_correct = True
        
        for lottery_type, data in OFFICIAL_DRAW_DATA.items():
            official_latest = data["latest_draw_id"]
            official_previous = data["previous_draw_id"]
            
            # Check for the latest draw
            latest_draw = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=official_latest
            ).first()
            
            # Check with alternate spelling too
            if not latest_draw and "Lottery" in lottery_type:
                alt_type = lottery_type.replace("Lottery", "Lotto")
                latest_draw = LotteryResult.query.filter_by(
                    lottery_type=alt_type,
                    draw_number=official_latest
                ).first()
            
            if latest_draw:
                print(f"✅ {lottery_type} latest draw #{official_latest} exists (Date: {latest_draw.draw_date.strftime('%Y-%m-%d')})")
            else:
                all_correct = False
                print(f"❌ {lottery_type} latest draw #{official_latest} missing from database")
            
            # Check for any incorrect draw IDs still in the database
            for incorrect_id, _ in DRAW_ID_CORRECTIONS.get(lottery_type, {}).items():
                incorrect_draw = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=incorrect_id
                ).first()
                
                if not incorrect_draw and "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    incorrect_draw = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=incorrect_id
                    ).first()
                
                if incorrect_draw:
                    all_correct = False
                    print(f"❌ {lottery_type} incorrect draw #{incorrect_id} still exists (Date: {incorrect_draw.draw_date.strftime('%Y-%m-%d')})")
        
        return all_correct

def main():
    """Main function to fix lottery draw IDs."""
    try:
        print("Current lottery draw IDs in database (before fix):")
        check_database_draws()
        
        print("\nFixing incorrect lottery draw IDs...")
        fixed, errors = fix_draw_ids()
        
        if fixed > 0:
            print(f"Successfully fixed {fixed} lottery draw IDs.")
        else:
            print("No draw IDs needed to be fixed.")
            
        if errors:
            print("\nErrors encountered:")
            for error in errors:
                print(f"  - {error}")
        
        print("\nCurrent lottery draw IDs in database (after fix):")
        check_database_draws()
        
        # Verify our corrections
        all_correct = verify_corrections()
        if all_correct:
            print("\nAll lottery draw IDs have been successfully updated to match official data!")
        else:
            print("\nSome issues still remain with lottery draw IDs. Manual intervention may be required.")
        
    except Exception as e:
        logger.error(f"Error fixing lottery draw IDs: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()