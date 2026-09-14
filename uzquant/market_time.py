from datetime import datetime
from zoneinfo import ZoneInfo
TASHKENT=ZoneInfo("Asia/Tashkent")
def normalize_exchange_timestamp(value:str,source_timezone:str="Asia/Tashkent"):
    parsed=datetime.fromisoformat(value)
    if parsed.tzinfo is None: parsed=parsed.replace(tzinfo=ZoneInfo(source_timezone))
    return parsed.astimezone(TASHKENT).isoformat()
