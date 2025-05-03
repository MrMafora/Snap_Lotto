from main import app
from models import ScheduleConfig

with app.app_context():
    configs = ScheduleConfig.query.filter_by(active=True).all()
    
    # Check for duplicate lottery types
    type_to_urls = {}
    for config in configs:
        if config.lottery_type not in type_to_urls:
            type_to_urls[config.lottery_type] = []
        type_to_urls[config.lottery_type].append(config.url)
    
    # Print URL configurations
    print("URL Configurations:")
    for config in configs:
        print(f"ID: {config.id}, Type: {config.lottery_type}, URL: {config.url}")
    
    # Check for duplicate lottery types
    print("\nDuplicate lottery types:")
    for lottery_type, urls in type_to_urls.items():
        if len(urls) > 1:
            print(f"{lottery_type}: {len(urls)} URLs - {urls}")