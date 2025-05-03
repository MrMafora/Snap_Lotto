from main import app
from models import Screenshot, ScheduleConfig

with app.app_context():
    screenshots = Screenshot.query.all()
    configs = ScheduleConfig.query.filter_by(active=True).all()
    
    print(f'Total screenshots in database: {len(screenshots)}')
    print(f'Total active configs: {len(configs)}')
    
    # List screenshots
    print("\nCurrent screenshots:")
    for s in screenshots:
        print(f'ID: {s.id}, Lottery Type: {s.lottery_type}, Timestamp: {s.timestamp}')
    
    # Check for missing screenshots
    screenshot_types = [s.lottery_type for s in screenshots]
    config_types = [c.lottery_type for c in configs]
    
    print("\nMissing screenshots:")
    for config_type in config_types:
        if config_type not in screenshot_types:
            print(f"No screenshot for: {config_type}")