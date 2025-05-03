from main import app
from models import ScheduleConfig, db

with app.app_context():
    # Fix Daily Lotto URL
    daily_lotto = ScheduleConfig.query.filter_by(id=6).first()
    if daily_lotto:
        print(f"Fixing URL for {daily_lotto.lottery_type}: {daily_lotto.url} -> https://www.nationallottery.co.za/daily-lotto-history")
        daily_lotto.url = "https://www.nationallottery.co.za/daily-lotto-history"
        db.session.commit()
    
    # Fix Daily Lotto Results URL
    daily_results = ScheduleConfig.query.filter_by(id=12).first()
    if daily_results:
        print(f"Fixing URL for {daily_results.lottery_type}: {daily_results.url} -> https://www.nationallottery.co.za/results/daily-lotto")
        daily_results.url = "https://www.nationallottery.co.za/results/daily-lotto"
        db.session.commit()
    
    # Verify updates
    configs = ScheduleConfig.query.filter(ScheduleConfig.id.in_([6, 12])).all()
    for config in configs:
        print(f"Updated {config.lottery_type}: {config.url}")