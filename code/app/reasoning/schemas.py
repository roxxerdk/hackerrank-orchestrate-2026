from enum import Enum
from typing import List, Optional, Final
from pydantic import BaseModel, Field

REASONING_SCHEMA_VERSION: Final[str] = "1.0"

class ActionType(str, Enum):
    NOTIFY = "notify"
    DIGEST = "digest"
    MUTE = "mute"

class RuleCategory(str, Enum):
    SAFETY = "safety"
    USER_PREFERENCE = "user_preference"
    BUSINESS = "business"
    GROUP = "group"
    MESSAGE = "message"
    MEDIA = "media"
    RELATIONSHIP = "relationship"
    TEMPORAL = "temporal"
    SYSTEM = "system"

from app.features.routing_features import ActivityLevel, TemporalBucket

class MessageContext(BaseModel):
    has_media: bool
    has_link: bool
    has_urgency_phrase: bool
    text_length: int
    is_mass_forwarded: bool

class UserContext(BaseModel):
    user_reply_ratio: float
    user_open_ratio: float
    user_dismiss_ratio: float
    in_dnd: bool

class BusinessContext(BaseModel):
    verified: bool
    risk: float
    promotions_allowed: bool
    interaction_score: float

class GroupContext(BaseModel):
    is_muted: bool
    is_admin: bool
    activity_level: ActivityLevel
    member_count: int

class MediaContext(BaseModel):
    has_media: bool
    has_qr: bool
    has_payment_request: bool
    contains_deadline: bool
    contains_phone: bool
    media_file_size_bytes: int

class RelationshipContext(BaseModel):
    sender_is_known: bool
    sender_is_frequent_contact: bool
    sender_is_business: bool

class ConversationContext(BaseModel):
    last_message_delta_minutes: float
    conversation_age_days: float
    previous_reply_exists: bool
    previous_interaction_exists: bool

class SafetyContext(BaseModel):
    domain_mismatch: bool
    high_forward_count: bool
    reported_business: bool
    unknown_sender: bool

class TemporalContext(BaseModel):
    message_hour: int
    is_weekend: bool
    time_bucket: TemporalBucket

class SystemContext(BaseModel):
    daily_alert_load_score: float

class ReasoningContext(BaseModel):
    message_id: str
    user_id: str
    schema_version: str = Field(REASONING_SCHEMA_VERSION)
    
    message: MessageContext
    user: UserContext
    business: BusinessContext
    group: GroupContext
    media: MediaContext
    relationship: RelationshipContext
    conversation: ConversationContext
    safety: SafetyContext
    temporal: TemporalContext
    system: SystemContext

class RetrievedRule(BaseModel):
    rule_id: str = Field(..., description="Unique rule identifier (e.g. RULE_DND_001)")
    category: RuleCategory = Field(..., description="Functional group classification")
    condition_description: str = Field(..., description="Readable definition of logic triggers")
    priority: int = Field(0, description="Precedence rank on conflicting decisions")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Confidence strength weight parameter")
    recommended_action: ActionType = Field(ActionType.DIGEST, description="Recommended output path target")

class RetrievedEvidence(BaseModel):
    ruleset_version: str = Field("1.0", description="Rule repository engine version")
    retrieved_rules: List[RetrievedRule] = Field(default_factory=list)
    historical_match_count: int = Field(0, description="Matched patterns in historical message events")
    matched_sources: List[str] = Field(default_factory=list, description="IDs of indexes/rulesets queried")

class ConfidenceBreakdown(BaseModel):
    confidence_version: str = Field("1.0", description="Confidence calculation logic version")
    base_confidence: float = Field(0.5, ge=0.0, le=1.0)
    safety_penalty: float = Field(0.0, ge=0.0, le=1.0)
    user_engagement_bonus: float = Field(0.0, ge=0.0, le=1.0)
    rule_strength_bonus: float = Field(0.0, ge=0.0, le=1.0)
    system_load_penalty: float = Field(0.0, ge=0.0, le=1.0)
    final_confidence: float = Field(..., ge=0.0, le=1.0)

class RoutingDecision(BaseModel):
    action: ActionType = Field(..., description="Decision output path: notify, digest, mute")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Evaluated output confidence score")
    applied_rules: List[str] = Field(default_factory=list, description="IDs of rules triggered during reasoning")
    rationale: List[str] = Field(default_factory=list, description="Readable justifications explaining the path")
    confidence_breakdown: Optional[ConfidenceBreakdown] = None
