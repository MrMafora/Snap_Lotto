#!/usr/bin/env python3
"""
Check Powerball data in the database to diagnose why it's showing "No results available"
"""

import os
import sys
sys.path.append('.')

from models import db, LotteryResult
from main import app

def check_powerball_data():
    """Check what Powerball data exists in the database"""
    
    with app.app_context():
        print("=== CHECKING POWERBALL DATA ===")
        
        # Check all lottery types in database
        all_types = db.session.query(LotteryResult.lottery_type).distinct().all()
        print(f"All lottery types in database: {[t[0] for t in all_types]}")
        
        # Check Powerball specifically
        powerball_results = LotteryResult.query.filter_by(lottery_type='Powerball').order_by(LotteryResult.draw_date.desc()).limit(5).all()
        print(f"\nPowerball results count: {len(powerball_results)}")
        
        if powerball_results:
            print("\nLatest Powerball results:")
            for result in powerball_results:
                print(f"  Draw Date: {result.draw_date}")
                print(f"  Numbers: {result.number_1}, {result.number_2}, {result.number_3}, {result.number_4}, {result.number_5}")
                print(f"  Powerball: {result.powerball_number}")
                print(f"  Draw ID: {getattr(result, 'draw_number', 'N/A')}")
                print("  ---")
        else:
            print("No Powerball results found!")
            
        # Check for similar names
        similar_names = db.session.query(LotteryResult.lottery_type).filter(
            LotteryResult.lottery_type.ilike('%power%')
        ).distinct().all()
        print(f"\nLottery types containing 'power': {[t[0] for t in similar_names]}")
        
        # Check recent results of all types
        print("\nRecent results by type:")
        for lottery_type in ['Lotto', 'Lotto Plus 1', 'Lotto Plus 2', 'Powerball', 'Powerball Plus', 'Daily Lotto']:
            count = LotteryResult.query.filter_by(lottery_type=lottery_type).count()
            print(f"  {lottery_type}: {count} results")

if __name__ == "__main__":
    check_powerball_data()