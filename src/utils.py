# src/utils.py
from datetime import datetime, timedelta

def get_date_range(days=14):
    today = datetime.now().date()
    return [today - timedelta(days=i) for i in range(days)]