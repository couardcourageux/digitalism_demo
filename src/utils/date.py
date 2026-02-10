from datetime import datetime, timezone

def get_current_time() -> datetime:
    return datetime.now(timezone.utc)

def get_time_stamp(date: datetime) -> float:
    return date.timestamp()
