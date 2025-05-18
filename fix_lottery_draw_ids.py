#!/usr/bin/env python3
"""
Fix incorrect lottery draw ID numbers.
This script corrects the draw IDs to match official Ithuba National Lottery data.
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
    }
}

def fix_draw_ids():
    """Fix incorrect lottery draw IDs in the database."""
    fixed_count = 0
    
    with app.app_context():
        for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
            for incorrect_id, correct_id in corrections.items():
                # Find draws with incorrect IDs (including all variations of spelling)
                results = []
                
                # Check with exact lottery type name
                result = LotteryResult.query.filter_by(
                    lottery_type=lottery_type, 
                    draw_number=incorrect_id
                ).first()
                if result:
                    results.append(result)
                
                # Check with Lotto spelling
                if "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    result = LotteryResult.query.filter_by(
                        lottery_type=alt_type, 
                        draw_number=incorrect_id
                    ).first()
                    if result:
                        results.append(result)
                
                # Fix all found results
                for result in results:
                    old_id = result.draw_number
                    result.draw_number = correct_id
                    fixed_count += 1
                    logger.info(f"Fixed draw ID for {result.lottery_type} from {old_id} to {correct_id} (Date: {result.draw_date.strftime('%Y-%m-%d')})")
        
        # Commit all changes
        db.session.commit()
    
    return fixed_count

def verify_corrections():
    """Verify that corrections were applied successfully."""
    
    with app.app_context():
        print("\nVerifying draw ID corrections:")
        print("-" * 80)
        
        for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
            for _, correct_id in corrections.items():
                # Try to find the corrected draw
                result = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=correct_id
                ).first()
                
                # Also check alternate spellings
                if not result and "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    result = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=correct_id
                    ).first()
                
                if result:
                    print(f"✅ {lottery_type} Draw #{correct_id} (Date: {result.draw_date.strftime('%Y-%m-%d')})")
                else:
                    print(f"❌ {lottery_type} Draw #{correct_id} not found in database")
        
        # Verify no incorrect IDs remain
        for lottery_type, corrections in DRAW_ID_CORRECTIONS.items():
            for incorrect_id, _ in corrections.items():
                # Check for any remaining incorrect IDs
                result = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=incorrect_id
                ).first()
                
                if "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    alt_result = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=incorrect_id
                    ).first()
                    
                    if alt_result:
                        result = alt_result
                
                if result:
                    print(f"❌ {lottery_type} Draw #{incorrect_id} still exists in database")

def main():
    """Main function to fix lottery draw IDs."""
    try:
        print("Fixing incorrect lottery draw IDs...")
        fixed = fix_draw_ids()
        print(f"Successfully fixed {fixed} lottery draw IDs.")
        
        # Verify our corrections
        verify_corrections()
        
    except Exception as e:
        logger.error(f"Error fixing lottery draw IDs: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()