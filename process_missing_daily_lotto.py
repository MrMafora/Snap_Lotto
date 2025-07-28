#!/usr/bin/env python3
"""
Manual extraction of missing Daily Lotto data from user-provided image
Extracts Daily Lotto Draw 2325 from July 26, 2025
"""

import os
import sys
import json
import psycopg2
from datetime import datetime

def extract_daily_lotto_data():
    print("🎯 EXTRACTING MISSING DAILY LOTTO DATA")
    print("=" * 60)
    
    # Data extracted from the user's image: Daily Lotto Draw 2325 (July 26, 2025)
    daily_lotto_data = {
        'lottery_type': 'DAILY LOTTO',
        'draw_number': 2325,
        'draw_date': '2025-07-26',
        'main_numbers': '[14, 16, 21, 23, 29]',  # From the image: 14, 16, 23, 29, 21 (sorted)
        'bonus_numbers': None,  # Daily Lotto has no bonus numbers
        'prize_divisions': [
            {'division': 'DIV 1', 'match': '5', 'winners': 3, 'amount': 200000.00},
            {'division': 'DIV 2', 'match': '4', 'winners': 434, 'amount': 307.90},
            {'division': 'DIV 3', 'match': '3', 'winners': 13095, 'amount': 20.60},
            {'division': 'DIV 4', 'match': '2', 'winners': 124594, 'amount': 5.20}
        ],
        'financial_info': {
            'total_pool_size': 1662906.00,
            'total_sales': 3289590.00,
            'draw_machine': 'RNG 3',
            'next_draw_date': '2025-07-27'
        }
    }
    
    # Connect to database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not found")
        return False
        
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Check if this draw already exists
        cur.execute('''
            SELECT COUNT(*) FROM lottery_results 
            WHERE lottery_type = %s AND draw_number = %s AND draw_date = %s
        ''', (daily_lotto_data['lottery_type'], daily_lotto_data['draw_number'], daily_lotto_data['draw_date']))
        
        count = cur.fetchone()[0]
        
        if count == 0:
            # Insert the missing Daily Lotto result
            cur.execute('''
                INSERT INTO lottery_results 
                (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers, 
                 prize_divisions, rollover_amount, total_pool_size, total_sales, 
                 draw_machine, next_draw_date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ''', (
                daily_lotto_data['lottery_type'],
                daily_lotto_data['draw_number'],
                daily_lotto_data['draw_date'],
                daily_lotto_data['main_numbers'],
                daily_lotto_data['bonus_numbers'],
                json.dumps(daily_lotto_data['prize_divisions']),
                0.00,  # Daily Lotto doesn't have rollovers
                daily_lotto_data['financial_info']['total_pool_size'],
                daily_lotto_data['financial_info']['total_sales'],
                daily_lotto_data['financial_info']['draw_machine'],
                daily_lotto_data['financial_info']['next_draw_date']
            ))
            
            conn.commit()
            
            print(f"✅ INSERTED: {daily_lotto_data['lottery_type']} Draw {daily_lotto_data['draw_number']} ({daily_lotto_data['draw_date']})")
            print(f"   Numbers: {daily_lotto_data['main_numbers']}")
            print(f"   Prize Divisions: {len(daily_lotto_data['prize_divisions'])} divisions")
            print(f"   Total Pool: R{daily_lotto_data['financial_info']['total_pool_size']:,.2f}")
            print(f"   Total Sales: R{daily_lotto_data['financial_info']['total_sales']:,.2f}")
            
            return True
            
        else:
            print(f"ℹ️  EXISTS: {daily_lotto_data['lottery_type']} Draw {daily_lotto_data['draw_number']} already in database")
            return False
            
    except Exception as e:
        print(f"❌ ERROR inserting data: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def main():
    success = extract_daily_lotto_data()
    
    print("=" * 60)
    if success:
        print("🎯 MISSING DAILY LOTTO DATA SUCCESSFULLY ADDED!")
        print("✅ Database now has complete Daily Lotto results for July 26, 2025")
    else:
        print("ℹ️  No new data was added (may already exist)")
    
    return success

if __name__ == "__main__":
    main()