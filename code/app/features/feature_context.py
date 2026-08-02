import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Any
from app.config import (
    BUSINESS_REPORT_CAP,
    NOTIFICATION_LOAD_CAP,
    INTERACTION_CAP,
    FORWARD_THRESHOLD,
)

# Custom Type Aliases
UserIndex = dict[str, dict[str, Any]]
GroupIndex = dict[str, dict[str, Any]]
GroupMemberIndex = dict[tuple[str, str], dict[str, Any]]
BusinessIndex = dict[str, dict[str, Any]]
BusinessHistoryIndex = dict[tuple[str, str], dict[str, Any]]
ImageLookup = dict[str, str]
VoiceLookup = dict[str, str]
DailySummaryIndex = dict[tuple[str, str], dict[str, Any]]

# Custom Type Aliases
UserIndex = dict[str, dict[str, Any]]
GroupIndex = dict[str, dict[str, Any]]
GroupMemberIndex = dict[tuple[str, str], dict[str, Any]]
BusinessIndex = dict[str, dict[str, Any]]
BusinessHistoryIndex = dict[tuple[str, str], dict[str, Any]]
ImageLookup = dict[str, str]
VoiceLookup = dict[str, str]
DailySummaryIndex = dict[tuple[str, str], dict[str, Any]]

def _parse_dt(dt_val: Any) -> Optional[datetime]:
    """Helper to convert date objects or strings to datetime objects cleanly."""
    if pd.isna(dt_val) or dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        return dt_val
    try:
        return pd.to_datetime(dt_val).to_pydatetime()
    except Exception:
        return None

@dataclass(frozen=True)
class ConversationStats:
    """
    Holds precomputed interaction metrics between a user and a sender.
    """
    message_count: int = 0
    reply_count: int = 0
    first_message_time: Optional[datetime] = None
    last_message_time: Optional[datetime] = None
    last_reply_time: Optional[datetime] = None

ConversationIndex = dict[tuple[str, str], ConversationStats]

@dataclass(frozen=True)
class FeatureConfig:
    """
    Injected threshold controls for normalize calculations.
    """
    business_report_cap: int = BUSINESS_REPORT_CAP
    notification_load_cap: int = NOTIFICATION_LOAD_CAP
    interaction_cap: int = INTERACTION_CAP
    forward_threshold: int = FORWARD_THRESHOLD

@dataclass(frozen=True)
class FeatureExtractionContext:
    """
    Immutable memory-mapped search context containing loaded datasets.
    """
    config: FeatureConfig
    users_index: UserIndex
    groups_index: GroupIndex
    group_members_index: GroupMemberIndex
    business_index: BusinessIndex
    business_history_index: BusinessHistoryIndex
    image_lookup: ImageLookup
    voice_lookup: VoiceLookup
    conversation_history: ConversationIndex
    daily_summary_index: DailySummaryIndex
    statistics: dict[str, int] = field(default_factory=dict)

def _build_users_index(df: pd.DataFrame) -> UserIndex:
    return {str(row["user_id"]): row.to_dict() for _, row in df.iterrows()}

def _build_groups_index(df: pd.DataFrame) -> GroupIndex:
    return {str(row["group_id"]): row.to_dict() for _, row in df.iterrows()}

def _build_group_members_index(df: pd.DataFrame) -> GroupMemberIndex:
    return {(str(row["group_id"]), str(row["user_id"])): row.to_dict() for _, row in df.iterrows()}

def _build_business_index(df: pd.DataFrame) -> BusinessIndex:
    return {str(row["business_id"]): row.to_dict() for _, row in df.iterrows()}

def _build_business_history_index(df: pd.DataFrame) -> BusinessHistoryIndex:
    return {(str(row["user_id"]), str(row["business_id"])): row.to_dict() for _, row in df.iterrows()}

def _build_image_lookup(df: pd.DataFrame) -> ImageLookup:
    return {str(row["image_id"]): str(row["file_path"]) for _, row in df.iterrows()}

def _build_voice_lookup(df: pd.DataFrame) -> VoiceLookup:
    return {str(row["voice_note_id"]): str(row["file_path"]) for _, row in df.iterrows()}

def _build_daily_summary_index(df: pd.DataFrame) -> DailySummaryIndex:
    return {(str(row["user_id"]), str(row["date"])): row.to_dict() for _, row in df.iterrows()}

def _build_conversation_history(df: pd.DataFrame, events_df: Optional[pd.DataFrame] = None) -> ConversationIndex:
    """
    Aggregates and precomputes user-sender relationship statistics.
    """
    # Sort messages by date to resolve timeline first/last bounds easily
    sorted_df = df.copy()
    sorted_df["parsed_time"] = sorted_df["created_at"].apply(_parse_dt)
    sorted_df = sorted_df.sort_values(by="parsed_time")
    
    # Join with message_events to check user reply dynamics
    event_replied = {}
    if events_df is not None:
        event_replied = {str(row["message_id"]): bool(row["message_replied"]) for _, row in events_df.iterrows()}
        
    conversation_index: dict[tuple[str, str], ConversationStats] = {}
    
    for _, row in sorted_df.iterrows():
        user_id = str(row["user_id"])
        sender_id = str(row["sender_user_id"])
        key = (user_id, sender_id)
        
        msg_time = row["parsed_time"]
        is_reply = event_replied.get(str(row["message_id"]), False)
        
        if key not in conversation_index:
            conversation_index[key] = ConversationStats(
                message_count=1,
                reply_count=1 if is_reply else 0,
                first_message_time=msg_time,
                last_message_time=msg_time,
                last_reply_time=msg_time if is_reply else None
            )
        else:
            prev = conversation_index[key]
            # Accumulate values directly on the existing statistics entry
            conversation_index[key] = ConversationStats(
                message_count=prev.message_count + 1,
                reply_count=prev.reply_count + (1 if is_reply else 0),
                first_message_time=prev.first_message_time or msg_time,
                last_message_time=msg_time,
                last_reply_time=msg_time if is_reply else prev.last_reply_time
            )
        
    return conversation_index

def build_extraction_context(datasets: dict[str, pd.DataFrame]) -> FeatureExtractionContext:
    """
    Orchestrates building the FeatureExtractionContext indexes from DataFrames.
    Raises ValueError if required datasets are missing.
    """
    required_keys = [
        "users", "groups", "group_members", "business_accounts",
        "user_business_history", "images", "voice_notes", 
        "message_history", "message_events", "daily_notification_summary"
    ]
    
    for r_key in required_keys:
        if r_key not in datasets:
            raise ValueError(f"Missing required dataset context target: {r_key}")
            
    users_index = _build_users_index(datasets["users"])
    groups_index = _build_groups_index(datasets["groups"])
    group_members_index = _build_group_members_index(datasets["group_members"])
    business_index = _build_business_index(datasets["business_accounts"])
    business_history_index = _build_business_history_index(datasets["user_business_history"])
    image_lookup = _build_image_lookup(datasets["images"])
    voice_lookup = _build_voice_lookup(datasets["voice_notes"])
    daily_summary_index = _build_daily_summary_index(datasets["daily_notification_summary"])
    
    conversation_history = _build_conversation_history(
        datasets["message_history"], 
        datasets.get("message_events")
    )
    
    statistics = {
        "users": len(users_index),
        "groups": len(groups_index),
        "group_members": len(group_members_index),
        "businesses": len(business_index),
        "images": len(image_lookup),
        "voice_notes": len(voice_lookup),
        "conversation_pairs": len(conversation_history)
    }
    
    return FeatureExtractionContext(
        config=FeatureConfig(),
        users_index=users_index,
        groups_index=groups_index,
        group_members_index=group_members_index,
        business_index=business_index,
        business_history_index=business_history_index,
        image_lookup=image_lookup,
        voice_lookup=voice_lookup,
        conversation_history=conversation_history,
        daily_summary_index=daily_summary_index,
        statistics=statistics
    )
