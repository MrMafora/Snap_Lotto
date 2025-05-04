#!/usr/bin/env python3
"""
Check the database for the latest Daily Lottery results
"""
import os
import sys
from datetime import datetime

# Application context is required for database queries
from main import app
from models import LotteryResult, db

def check_daily_lottery_data():
    """
    Check the database for the latest Daily Lottery results
    """
    with app.app_context():
        print('--- Database Check for Daily Lottery ---')
        
        # Get the latest Daily Lottery draws
        latest_draws = LotteryResult.query.filter_by(
            lottery_type='Daily Lottery'
        ).order_by(
            LotteryResult.draw_number.desc()
        ).limit(5).all()
        
        if latest_draws:
            print(f'Latest draws in database: {[r.draw_number for r in latest_draws]}')
            latest_draw = latest_draws[0]
            print(f'Most recent: #{latest_draw.draw_number} ({latest_draw.draw_date})')
        else:
            print('No Daily Lottery draws found in database')
        
        print('--- End of Database Check ---')
        
        return latest_draws

if __name__ == '__main__':
    check_daily_lottery_data()