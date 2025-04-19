#!/usr/bin/env python
"""
Script to check details of existing draw 2534 records
"""

import json
from models import LotteryResult
from main import app

def check_draw_2534():
    """Check all existing draw 2534 records"""
    with app.app_context():
        results = LotteryResult.query.filter_by(draw_number='2534').all()
        
        print('Draw 2534 records:')
        for r in results:
            print(f'{r.lottery_type}: Numbers={json.loads(r.numbers)}, '
                  f'Bonus={json.loads(r.bonus_numbers) if r.bonus_numbers else None}, '
                  f'Date={r.draw_date}')

if __name__ == "__main__":
    check_draw_2534()