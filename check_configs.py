from main import app
from models import ScheduleConfig
from flask import current_app

with app.app_context():
    configs = ScheduleConfig.query.filter_by(active=True).all()
    print(f'Total active configs: {len(configs)}')
    
    for config in configs:
        print(f'ID: {config.id}, URL: {config.url}, Lottery Type: {config.lottery_type}, Last Run: {config.last_run}')