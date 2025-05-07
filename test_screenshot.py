from main import app
from selenium_screenshot_manager import capture_screenshot

with app.app_context():
    result = capture_screenshot('https://www.nationallottery.co.za/results/daily-lotto')
    print(f'Success: {result[0] is not None}')
    if result[0]:
        print(f'Screenshot saved to: {result[0]}')