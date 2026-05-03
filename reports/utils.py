# reports/utils.py
from datetime import datetime, timedelta

def range_to_dates(range_val: str):
    now = datetime.utcnow()
    if range_val == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_val == '7d':
        start = now - timedelta(days=7)
    elif range_val == '30d':
        start = now - timedelta(days=30)
    elif range_val == '90d':
        start = now - timedelta(days=90)
    else:
        start = now - timedelta(days=30)
    return start.isoformat(), now.isoformat()