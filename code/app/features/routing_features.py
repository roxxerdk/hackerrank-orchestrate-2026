"""
Stable feature contract shared across:
- Feature Extraction
- Context Builder
- Retrieval Engine
- Reasoning Engine
- Safety Validator
- Confidence Calculator

Do not modify without increasing FEATURE_SCHEMA_VERSION.
"""

from enum import Enum
from typing import List, Optional, Final
from datetime import datetime, timezone
from pydantic import BaseModel, Field

FEATURE_SCHEMA_VERSION: Final[str] = "1.0"

class ActivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TemporalBucket(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"

class FeatureMetadata(BaseModel):
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC ISO-8601 generation timestamp"
    )
    feature_version: str = Field(FEATURE_SCHEMA_VERSION, description="Feature schema contract version")

class UserFeatures(BaseModel):
    user_reply_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Replied / Opened ratio in the last 30 days")
    user_open_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Opened / Total messages ratio in the last 30 days")
    user_dismiss_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Dismissed notifications ratio in the last 30 days")
    in_dnd_window: bool = Field(False, description="True if the message arrived within user's do_not_disturb window")

class GroupFeatures(BaseModel):
    is_group_muted: bool = Field(False, description="True if the user has explicitly muted the group")
    is_group_admin: bool = Field(False, description="True if the sender is an admin of the group")
    group_activity_level: ActivityLevel = Field(ActivityLevel.MEDIUM, description="Activity level score of the group")
    member_count: int = Field(0, ge=0, description="Total members in the group")

class BusinessFeatures(BaseModel):
    business_verified: bool = Field(False, description="True if the business account is verified")
    business_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Normalized derived risk score based on reports and domain trust")
    promotions_allowed: bool = Field(True, description="True if the user allows promotions from this business")
    business_interaction_score: float = Field(0.0, ge=0.0, le=1.0, description="Normalized derived user interaction score over 180 days")

class MessageContentFeatures(BaseModel):
    has_media: bool = Field(False, description="True if message contains image or audio")
    has_link: bool = Field(False, description="True if message text contains a URL link")
    has_urgency_phrase: bool = Field(False, description="True if message contains urgent trigger phrases")
    text_length: int = Field(0, ge=0, description="Character length of message text")
    is_mass_forwarded: bool = Field(False, description="True if forwarded count exceeds threshold")

class MediaSignalFeatures(BaseModel):
    has_qr: bool = Field(False, description="Extracted from image analysis")
    has_payment_request: bool = Field(False, description="Extracted from image or voice analysis")
    contains_deadline: bool = Field(False, description="Extracted from image or voice analysis")
    contains_phone: bool = Field(False, description="Extracted from image or voice analysis")
    media_file_size_bytes: int = Field(0, ge=0, description="Raw file size of media asset")

class RelationshipFeatures(BaseModel):
    sender_is_known: bool = Field(False, description="True if the sender is a contact or known business")
    sender_is_frequent_contact: bool = Field(False, description="True if user has high message exchange with sender")
    sender_is_business: bool = Field(False, description="True if sender represents a business account")

class ConversationFeatures(BaseModel):
    last_message_delta_minutes: float = Field(-1.0, description="Minutes since last message in conversation thread (-1 if new)")
    conversation_age_days: float = Field(0.0, ge=0.0, description="Time since first interaction in days")
    previous_reply_exists: bool = Field(False, description="True if user has replied to this sender previously")
    previous_interaction_exists: bool = Field(False, description="True if historical interaction messages exist")

class TemporalFeatures(BaseModel):
    message_hour: int = Field(0, ge=0, le=23, description="Hour of the day (0-23)")
    is_weekend: bool = Field(False, description="True if message arrived on Saturday or Sunday")
    time_bucket: TemporalBucket = Field(TemporalBucket.AFTERNOON, description="Categorized time slice of the day")

class SafetySignals(BaseModel):
    domain_mismatch: bool = Field(False, description="True if domain used by sender does not match official domain")
    high_forward_count: bool = Field(False, description="True if message is heavily forwarded")
    reported_business: bool = Field(False, description="True if business reports count is high")
    unknown_sender: bool = Field(False, description="True if sender is not in users or business directory")

class SystemFeatures(BaseModel):
    daily_alert_load_score: float = Field(0.0, ge=0.0, le=1.0, description="Normalized derived density of notifications sent today")

class RoutingFeatures(BaseModel):
    """
    Stabilized feature contract consumed by downstream decision and confidence pipelines.
    """
    message_id: str = Field(..., description="Target message identifier")
    user_id: str = Field(..., description="Target user identifier")
    
    metadata: FeatureMetadata = Field(default_factory=FeatureMetadata, description="Lightweight feature extraction metadata")
    user: UserFeatures = Field(default_factory=UserFeatures)
    group: GroupFeatures = Field(default_factory=GroupFeatures)
    business: BusinessFeatures = Field(default_factory=BusinessFeatures)
    message: MessageContentFeatures = Field(default_factory=MessageContentFeatures)
    media: MediaSignalFeatures = Field(default_factory=MediaSignalFeatures)
    relationship: RelationshipFeatures = Field(default_factory=RelationshipFeatures)
    conversation: ConversationFeatures = Field(default_factory=ConversationFeatures)
    temporal: TemporalFeatures = Field(default_factory=TemporalFeatures)
    safety: SafetySignals = Field(default_factory=SafetySignals)
    system: SystemFeatures = Field(default_factory=SystemFeatures)
