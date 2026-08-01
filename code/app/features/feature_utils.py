import re
from datetime import datetime
from app.features.routing_features import TemporalBucket
from app.config import (
    BUSINESS_REPORT_CAP,
    NOTIFICATION_LOAD_CAP,
    INTERACTION_CAP,
)

from typing import Union, Optional

# Common regex patterns compiled once
URL_REGEX = re.compile(r"https?://\S+", re.IGNORECASE)

KEYWORDS = (
    "urgent",
    "asap",
    "immediately",
    "deadline",
    "expires",
    "action required",
    "pay now",
    "attention",
    "today",
    "quickly",
)

URGENCY_REGEX = re.compile(
    r"\b(?:" + "|".join(map(re.escape, KEYWORDS)) + r")\b",
    re.IGNORECASE
)

def clamp_ratio(value: Union[int, float], cap: Union[int, float]) -> float:
    """
    Clamps a numeric value divided by a cap threshold to the range [0.0 - 1.0].
    """
    if cap <= 0.0:
        return 0.0
    return min(1.0, max(0.0, float(value) / float(cap)))

def is_in_dnd(message_time: datetime, dnd_window: str) -> bool:
    """
    Checks if a given message timestamp falls within a user's DND window (format: 'HH:MM-HH:MM').
    Handles overnight windows (e.g., '22:00-07:00') correctly.
    """
    if not dnd_window or "-" not in dnd_window:
        return False
        
    try:
        start_str, end_str = dnd_window.split("-")
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        
        msg_time = message_time.time()
        start_time = msg_time.replace(hour=sh, minute=sm, second=0, microsecond=0)
        end_time = msg_time.replace(hour=eh, minute=em, second=0, microsecond=0)
        
        if sh > eh or (sh == eh and sm > em):
            # Overnight DND window (e.g. 22:00-07:00)
            return msg_time >= start_time or msg_time <= end_time
        else:
            # Daytime DND window (e.g. 09:00-17:00)
            return start_time <= msg_time <= end_time
    except (ValueError, TypeError, IndexError):
        return False

def detect_links(text: Optional[str]) -> bool:
    """
    Scans the text using regex to verify if it contains URL links.
    """
    if not text:
        return False
    return bool(URL_REGEX.search(text))

def detect_urgency_keywords(text: Optional[str]) -> bool:
    """
    Checks if any standard urgency phrase is visible in the text using word boundaries.
    """
    if not text:
        return False
    return bool(URGENCY_REGEX.search(text))

def get_time_bucket(timestamp: datetime) -> TemporalBucket:
    """
    Maps the hour of a timestamp to a TemporalBucket enum.
    """
    hour = timestamp.hour
    if 5 <= hour < 12:
        return TemporalBucket.MORNING
    elif 12 <= hour < 17:
        return TemporalBucket.AFTERNOON
    elif 17 <= hour < 22:
        return TemporalBucket.EVENING
    else:
        return TemporalBucket.NIGHT

def is_weekend(timestamp: datetime) -> bool:
    """
    Returns True if the timestamp represents a weekend day (Saturday/Sunday).
    """
    return timestamp.weekday() in (5, 6)

def compute_business_risk(reports: Union[int, float]) -> float:
    """
    Derives normalized business risk score from user reports.
    """
    return clamp_ratio(reports, BUSINESS_REPORT_CAP)

def compute_interaction_score(activity_count: Union[int, float]) -> float:
    """
    Derives normalized business interaction score from 180-day activity counts.
    """
    return clamp_ratio(activity_count, INTERACTION_CAP)

def compute_daily_alert_load(notification_count: Union[int, float]) -> float:
    """
    Derives normalized alert load score from user notification aggregate counts.
    """
    return clamp_ratio(notification_count, NOTIFICATION_LOAD_CAP)
