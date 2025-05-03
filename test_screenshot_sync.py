import requests
import time
import os
from datetime import datetime

# Function to check the number of screenshots from today
def count_todays_screenshots():
    today_str = datetime.now().strftime("%Y%m%d")
    screenshot_count = 0
    
    # List all PNG files in the screenshots directory
    for filename in os.listdir('./screenshots'):
        if filename.startswith(today_str) and filename.endswith('.png'):
            screenshot_count += 1
    
    return screenshot_count

# First login to get session
s = requests.Session()
login_data = {
    'username': 'admin',
    'password': 'St0n3@g3'
}

print('Logging in...')
login_resp = s.post('http://localhost:5000/login', data=login_data)
print(f'Login status: {login_resp.status_code}')

if login_resp.status_code == 200:
    print('Login successful')
    
    # Count screenshots before sync
    before_count = count_todays_screenshots()
    print(f'Screenshots before sync: {before_count}')
    
    # Trigger the screenshot sync
    print('Triggering screenshot sync...')
    sync_resp = s.post('http://localhost:5000/sync-all-screenshots')
    print(f'Sync triggered, status: {sync_resp.status_code}')
    
    # Wait for the operation to complete (60 seconds should be enough)
    print('Waiting for screenshot captures to finish...')
    for i in range(12):
        print(f'Waiting... {i+1}/12 (5 seconds)')
        time.sleep(5)
        
        # Check if new screenshots appeared
        current_count = count_todays_screenshots()
        new_screenshots = current_count - before_count
        print(f'Current screenshots: {current_count} (New: {new_screenshots})')
        
        if new_screenshots >= 12:
            print('All 12 screenshots captured successfully!')
            break
    
    # Final count
    final_count = count_todays_screenshots()
    new_screenshots = final_count - before_count
    print(f'Final screenshot count: {final_count} (New: {new_screenshots})')
    
    if new_screenshots >= 12:
        print('SUCCESS: All 12 screenshots were captured!')
    else:
        print(f'PARTIAL SUCCESS: Only {new_screenshots} screenshots were captured out of 12')
else:
    print('Login failed')
