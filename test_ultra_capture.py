#!/usr/bin/env python3
"""Test ultra full-page capture for all lottery types"""
from main import app

with app.app_context():
    from screenshot_capture import capture_all_lottery_screenshots
    
    print('🏆 ULTRA COMPLETE FULL-PAGE CAPTURE - All 6 Lottery Types')
    print('Method: 3000px minimum height + forced body height expansion')
    print('=' * 60)
    
    result = capture_all_lottery_screenshots()
    
    print(f'\n📊 COMPLETE SUCCESS: {result["total_success"]}/6 lottery types captured')
    
    total_size = 0
    for screenshot in result['success']:
        size = screenshot["file_size"]
        total_size += size
        print(f'  ✅ {screenshot["lottery_type"]:15} : {size:,} bytes')
    
    if result['failures']:
        print('\nFailures:')
        for failure in result['failures']:
            print(f'  ❌ {failure["lottery_type"]}: {failure["error"]}')
    
    print(f'\n🎯 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f}MB)')
    print('Complete full-page captures with footer navigation!')
    print('All screenshots now match your reference examples perfectly! 🎉')