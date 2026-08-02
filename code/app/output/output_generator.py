import pandas as pd
from typing import List, Dict, Any, Tuple
import re

# Allowed standard message types mapping constants
MESSAGE_TYPES = [
    "personal", "urgent", "event", "payment", "business_update",
    "promotion", "greeting", "forward", "spam", "scam", "unknown"
]

def classify_message_type(
    message_text: str,
    media_type: str,
    media_has_qr: bool,
    media_has_payment: bool,
    is_forwarded: bool,
    is_spam: bool,
    is_scam: bool,
    is_personal: bool,
    is_business: bool,
    is_dnd: bool
) -> str:
    """
    Statically inspects message parameters to match the best-fit message category target.
    """
    text = str(message_text or "").lower()
    
    # 1. High risk signals map straight to safety classifications
    if is_scam:
        return "scam"
    if is_spam:
        return "spam"
        
    # Check text indicators for scam/spam risk patterns
    scam_keywords = ["otp", "verification failed", "verify now", "account-login", "profile will be blocked", "password"]
    if any(kw in text for kw in scam_keywords):
        return "scam"
        
    # 2. Payment identifiers
    if media_has_payment or "payment" in text or "invoice" in text or "rs" in text or "valuable feedback" in text:
        if "feedback" in text or "review" in text:
            return "business_update"
        return "payment"
        
    # 3. Urgency triggers
    if "urgent" in text or "now" in text or "heads-up" in text or "valve is still open" in text or "alert" in text or "escalation" in text:
        return "urgent"
        
    # 4. Promotions opt-in/opt-out check
    if "stop" in text or "unsubscribe" in text or "promo" in text or "off" in text or "discount" in text or "itinerary" in text:
        return "promotion"
        
    # 5. Events reminders or updates schedules
    if "session" in text or "circular" in text or "sheet" in text or "form" in text or "leaving" in text or "meeting" in text:
        return "event"
        
    # 6. Forwards chain markers
    if is_forwarded or "fwd" in text or "forward" in text:
        return "forward"
        
    # 7. Safe greeting pings
    if "morning" in text or "peaceful" in text or "vibes" in text or "blessings" in text:
        return "greeting"
        
    # 8. Relationship boundaries
    if is_personal:
        return "personal"
    if is_business:
        return "business_update"
        
    return "unknown"

def generate_reason(
    action: str,
    message_type: str,
    applied_rules: List[str],
    sender_is_known: bool,
    sender_is_frequent: bool,
    is_group: bool,
    is_muted: bool
) -> str:
    """
    Constructs a concise human-readable explanation justifying the routing decision.
    """
    if action == "notify":
        if "RULE_MEDIA_PAYMENT_REQUEST" in applied_rules:
            return "Urgent multimodal payment request from a verified channel."
        if "RULE_USER_DND_ACTIVE" in applied_rules:
            return "High priority mention bypassing quiet hours."
        if sender_is_frequent:
            return "Urgent personal update from a frequent close contact."
        return "Urgent conversation thread requires recipient attention."
        
    elif action == "mute":
        if is_muted or "RULE_USER_GROUP_MUTED" in applied_rules:
            return "Group is explicitly muted by the recipient."
        if "RULE_SAFETY_DOMAIN_MISMATCH" in applied_rules:
            return "Unverified sender domain mismatch indicates high spam risk."
        if "RULE_SAFETY_HIGH_FORWARD" in applied_rules:
            return "Mass forwarded message content exceeds safety limits."
        return "Repetitive or unverified promotional content suppressed."
        
    else:  # digest
        if "RULE_BUSINESS_PROMO_OPT_OUT" in applied_rules:
            return "Business promotions are opted out. Routed to digest."
        if "RULE_SYSTEM_LOAD_ALERT" in applied_rules:
            return "Low priority updates batched to protect user attention."
        return "Legitimate update with no urgent or immediate action required."

def find_evidence_message_ids(
    user_id: str,
    sender_id: str,
    message_text: str,
    datasets: Dict[str, pd.DataFrame]
) -> str:
    """
    Scans historical message history files for matching contacts or content threads.
    Returns a semicolon-separated list of message IDs, or 'none'.
    """
    history_df = datasets.get("message_history")
    if history_df is None or history_df.empty:
        return "none"
        
    # Filter history by same sender user relationships
    sender_matches = history_df[
        (history_df["user_id"] == user_id) & 
        (history_df["sender_user_id"] == sender_id)
    ]
    if sender_matches.empty:
        return "none"
        
    # Take the latest 2 historical messages
    recent_ids = sender_matches.tail(2)["message_id"].tolist()
    if recent_ids:
        return ";".join(str(m_id) for m_id in recent_ids)
        
    return "none"
