#!/usr/bin/env python3
"""
Script to export development data and show SQL for production import.
Run this in development to get the data export SQL statements.
"""
import os
import psycopg2
import json

DATABASE_URL = os.environ.get('DATABASE_URL')

def export_lottery_data():
    """Export lottery results and predictions as INSERT statements"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("\n" + "="*90)
    print(" " * 25 + "📊 LOTTERY DATA EXPORT")
    print("="*90 + "\n")
    
    # Export lottery_results
    cur.execute("""
        SELECT 
            lottery_type, draw_number, draw_date, main_numbers, 
            bonus_numbers, jackpot_amount, total_winners
        FROM lottery_results
        ORDER BY draw_date DESC, lottery_type
        LIMIT 50
    """)
    
    results = cur.fetchall()
    print(f"Found {len(results)} lottery results to export\n")
    
    print("-- =====================================================")
    print("-- LOTTERY RESULTS INSERT STATEMENTS")
    print("-- Copy these into production database")
    print("-- =====================================================\n")
    
    for row in results:
        lottery_type, draw_num, draw_date, main_nums, bonus_nums, jackpot, winners = row
        print(f"""INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers, jackpot_amount, total_winners)
VALUES ('{lottery_type}', {draw_num}, '{draw_date}', '{main_nums}', {'NULL' if bonus_nums is None else f"'{bonus_nums}'"}, {jackpot if jackpot else 'NULL'}, {winners if winners else 'NULL'})
ON CONFLICT (lottery_type, draw_number) DO NOTHING;
""")
    
    # Export predictions
    cur.execute("""
        SELECT 
            game_type, predicted_numbers, bonus_numbers, confidence_score,
            prediction_method, reasoning, target_draw_date, linked_draw_id,
            validation_status, is_verified
        FROM lottery_predictions
        WHERE validation_status = 'pending'
          AND target_draw_date >= CURRENT_DATE
        ORDER BY target_draw_date, game_type
    """)
    
    predictions = cur.fetchall()
    print(f"\n-- =====================================================")
    print(f"-- AI PREDICTIONS INSERT STATEMENTS ({len(predictions)} predictions)")
    print("-- =====================================================\n")
    
    for row in predictions:
        game, pred_nums, bonus, conf, method, reason, target_date, draw_id, status, verified = row
        
        # Escape single quotes in reasoning
        safe_reason = reason.replace("'", "''") if reason else ''
        safe_method = method.replace("'", "''") if method else ''
        
        print(f"""INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('{game}', '{pred_nums}', {'NULL' if bonus is None else f"'{bonus}'"}, {conf}, '{safe_method}', '{safe_reason}', '{target_date}', {draw_id if draw_id else 'NULL'}, '{status}', {verified})
ON CONFLICT DO NOTHING;
""")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*90)
    print(" " * 20 + "✅ EXPORT COMPLETE - COPY SQL ABOVE")
    print("="*90 + "\n")
    print("NEXT STEPS:")
    print("1. Copy the SQL statements above")
    print("2. In production, run these SQL statements to populate the database")
    print("3. Restart your production deployment")
    print("="*90 + "\n")

if __name__ == "__main__":
    export_lottery_data()
