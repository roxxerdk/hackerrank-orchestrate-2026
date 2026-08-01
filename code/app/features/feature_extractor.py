import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app.features.routing_features import (
    RoutingFeatures,
    UserFeatures,
    GroupFeatures,
    BusinessFeatures,
    MessageContentFeatures,
    MediaSignalFeatures,
    RelationshipFeatures,
    ConversationFeatures,
    TemporalFeatures,
    SafetySignals,
    SystemFeatures,
    FeatureMetadata,
    ActivityLevel,
    TemporalBucket,
)
from app.features.feature_context import FeatureExtractionContext, ConversationStats, _parse_dt
from app.features.feature_utils import (
    clamp_ratio,
    is_in_dnd,
    detect_links,
    detect_urgency_keywords,
    get_time_bucket,
    is_weekend,
    compute_business_risk,
    compute_interaction_score,
    compute_daily_alert_load,
)
from app.media.media_loader import MediaType, MediaInfo
from app.media.media_cache import load_analysis, CacheMetadata

from app.config import (
    BUSINESS_REPORT_CAP,
    NOTIFICATION_LOAD_CAP,
    INTERACTION_CAP,
    USER_OPEN_CAP,
    USER_DISMISS_CAP,
    DATASET_DIR,
)

logger = logging.getLogger("feature_extractor")

@dataclass(frozen=True)
class ExtractionInput:
    """
    Structured immutable input parameters for feature mapper helpers.
    """
    message: dict[str, Any]
    context: FeatureExtractionContext
    media_info: Optional[MediaInfo] = None
    media_analysis: Optional[CacheMetadata] = None

def _extract_user_features(inp: ExtractionInput) -> UserFeatures:
    user_id = str(inp.message.get("user_id", ""))
    user_data = inp.context.users_index.get(user_id)
    if not user_data:
        return UserFeatures()
        
    # Calculate ratios from user engagement metrics
    opened = float(user_data.get("messages_opened_30d", 0))
    replied = float(user_data.get("messages_replied_30d", 0))
    dismissed = float(user_data.get("notifications_dismissed_30d", 0))
    
    user_reply_ratio = replied / opened if opened > 0 else 0.0
    user_reply_ratio = min(1.0, max(0.0, user_reply_ratio)) # Cap within [0.0 - 1.0]
    
    # Extract do_not_disturb window
    dnd_window = str(user_data.get("do_not_disturb_window", ""))
    msg_time = _parse_dt(inp.message.get("created_at"))
    in_dnd = is_in_dnd(msg_time, dnd_window) if msg_time else False
    
    return UserFeatures(
        user_reply_ratio=user_reply_ratio,
        user_open_ratio=clamp_ratio(opened, USER_OPEN_CAP),
        user_dismiss_ratio=clamp_ratio(dismissed, USER_DISMISS_CAP),
        in_dnd_window=in_dnd
    )

def _extract_group_features(inp: ExtractionInput) -> GroupFeatures:
    group_id = str(inp.message.get("group_id", ""))
    user_id = str(inp.message.get("user_id", ""))
    
    if not group_id or group_id == "nan":
        return GroupFeatures()
        
    group_data = inp.context.groups_index.get(group_id)
    member_data = inp.context.group_members_index.get((group_id, user_id))
    
    is_muted = False
    is_admin = False
    if member_data:
        is_muted = bool(member_data.get("group_muted_by_user", False))
        is_admin = str(member_data.get("role", "")).lower() == "admin"
        
    activity_level = ActivityLevel.MEDIUM
    member_count = 0
    if group_data:
        member_count = int(group_data.get("member_count", 0))
        messages_sent = float(group_data.get("messages_30d", 0))
        if messages_sent > 1000:
            activity_level = ActivityLevel.HIGH
        elif messages_sent < 100:
            activity_level = ActivityLevel.LOW
            
    return GroupFeatures(
        is_group_muted=is_muted,
        is_group_admin=is_admin,
        group_activity_level=activity_level,
        member_count=member_count
    )

def _extract_business_features(inp: ExtractionInput) -> BusinessFeatures:
    business_id = str(inp.message.get("business_id", ""))
    user_id = str(inp.message.get("user_id", ""))
    
    if not business_id or business_id == "nan":
        return BusinessFeatures()
        
    business_data = inp.context.business_index.get(business_id)
    history_data = inp.context.business_history_index.get((user_id, business_id))
    
    verified = False
    reports = 0.0
    if business_data:
        verified = bool(business_data.get("verified", False))
        reports = float(business_data.get("user_reports_30d", 0))
        
    promotions = True
    interaction_count = 0.0
    if history_data:
        promotions = bool(history_data.get("allows_promotions", True))
        interaction_count = float(history_data.get("activity_count_180d", 0))
        
    return BusinessFeatures(
        business_verified=verified,
        business_risk_score=compute_business_risk(reports),
        promotions_allowed=promotions,
        business_interaction_score=compute_interaction_score(interaction_count)
    )

def _extract_message_features(inp: ExtractionInput) -> MessageContentFeatures:
    text = str(inp.message.get("message_text", ""))
    media_type_val = str(inp.message.get("media_type", ""))
    forwarded = float(inp.message.get("forwarded_count", 0))
    
    has_media = bool(media_type_val and media_type_val != "nan")
    has_link = detect_links(text)
    has_urgency = detect_urgency_keywords(text)
    
    return MessageContentFeatures(
        has_media=has_media,
        has_link=has_link,
        has_urgency_phrase=has_urgency,
        text_length=len(text),
        is_mass_forwarded=forwarded >= inp.context.config.forward_threshold
    )

def _extract_media_features(inp: ExtractionInput) -> MediaSignalFeatures:
    if not inp.media_analysis:
        return MediaSignalFeatures()
        
    analysis = inp.media_analysis.analysis
    
    # Extract details safely using dictionary mappings from verified schema structure
    facts = analysis.get("facts", {})
    signals = analysis.get("detected_signals", {})
    
    has_qr = bool(signals.get("contains_qr", False))
    has_payment = bool(signals.get("contains_payment_request", False))
    contains_deadline = bool(signals.get("contains_deadline", False))
    contains_phone = bool(signals.get("contains_phone", False))
    
    # Resolve file size if path exists
    file_size_bytes = 0
    if inp.media_info:
        file_size_bytes = inp.media_info.file_size_bytes
    
    return MediaSignalFeatures(
        has_qr=has_qr,
        has_payment_request=has_payment,
        contains_deadline=contains_deadline,
        contains_phone=contains_phone,
        media_file_size_bytes=file_size_bytes
    )

def _extract_relationship_features(inp: ExtractionInput) -> RelationshipFeatures:
    user_id = str(inp.message.get("user_id", ""))
    sender_id = str(inp.message.get("sender_user_id", ""))
    business_id = str(inp.message.get("business_id", ""))
    
    is_known = sender_id in inp.context.users_index
    is_business = bool(business_id and business_id != "nan")
    
    conversation = inp.context.conversation_history.get((user_id, sender_id))
    frequent = False
    if conversation:
        # User is frequent if interaction exceeds 15 messages historically
        frequent = conversation.message_count > 15
        
    return RelationshipFeatures(
        sender_is_known=is_known,
        sender_is_frequent_contact=frequent,
        sender_is_business=is_business
    )

def _extract_conversation_features(inp: ExtractionInput) -> ConversationFeatures:
    user_id = str(inp.message.get("user_id", ""))
    sender_id = str(inp.message.get("sender_user_id", ""))
    
    conversation = inp.context.conversation_history.get((user_id, sender_id))
    if not conversation:
        return ConversationFeatures()
        
    last_delta = -1.0
    msg_time = _parse_dt(inp.message.get("created_at"))
    
    if msg_time and conversation.last_message_time:
        delta = msg_time - conversation.last_message_time
        last_delta = float(delta.total_seconds() / 60.0)
        
    age_days = 0.0
    if msg_time and conversation.first_message_time:
        age_delta = msg_time - conversation.first_message_time
        age_days = float(age_delta.total_seconds() / 86400.0)
        
    prev_reply = conversation.reply_count > 0
    prev_interact = conversation.message_count > 0
    
    return ConversationFeatures(
        last_message_delta_minutes=last_delta,
        conversation_age_days=age_days,
        previous_reply_exists=prev_reply,
        previous_interaction_exists=prev_interact
    )

def _extract_temporal_features(inp: ExtractionInput) -> TemporalFeatures:
    msg_time = _parse_dt(inp.message.get("created_at"))
    if not msg_time:
        return TemporalFeatures()
        
    return TemporalFeatures(
        message_hour=msg_time.hour,
        is_weekend=is_weekend(msg_time),
        time_bucket=get_time_bucket(msg_time)
    )

def _extract_safety_features(inp: ExtractionInput) -> SafetySignals:
    business_id = str(inp.message.get("business_id", ""))
    business_data = inp.context.business_index.get(business_id)
    
    domain_mismatch = False
    reported_business = False
    
    if business_data:
        official = str(business_data.get("official_domain", ""))
        used = str(business_data.get("domain_used_by_sender", ""))
        domain_mismatch = bool(official and used and official != used)
        
        reports = float(business_data.get("user_reports_30d", 0))
        reported_business = reports >= inp.context.config.business_report_cap
        
    forwarded = float(inp.message.get("forwarded_count", 0))
    high_forward = forwarded >= inp.context.config.forward_threshold
    
    sender_id = str(inp.message.get("sender_user_id", ""))
    unknown_sender = sender_id not in inp.context.users_index and business_id not in inp.context.business_index
    
    return SafetySignals(
        domain_mismatch=domain_mismatch,
        high_forward_count=high_forward,
        reported_business=reported_business,
        unknown_sender=unknown_sender
    )

def _extract_system_features(inp: ExtractionInput) -> SystemFeatures:
    user_id = str(inp.message.get("user_id", ""))
    msg_time = _parse_dt(inp.message.get("created_at"))
    if not msg_time:
        return SystemFeatures()
        
    date_str = msg_time.strftime("%Y-%m-%d")
    summary = inp.context.daily_summary_index.get((user_id, date_str))
    
    load_score = 0.0
    if summary:
        sent = float(summary.get("notifications_sent", 0))
        load_score = compute_daily_alert_load(sent)
        
    return SystemFeatures(
        daily_alert_load_score=load_score
    )

def extract_features(
    message: dict[str, Any],
    context: FeatureExtractionContext
) -> RoutingFeatures:
    """
    Pipeline orchestrator resolving media files, initializing inputs, and instantiating 
    the validated RoutingFeatures output schema contract.
    """
    media_id = str(message.get("media_id", ""))
    media_type_val = str(message.get("media_type", ""))
    
    media_info: Optional[MediaInfo] = None
    media_analysis: Optional[CacheMetadata] = None
    
    # 1. Resolve media cache if has_media is active
    if media_id and media_id != "nan":
        try:
            rel_path = ""
            media_type = MediaType.IMAGE if media_type_val.lower() == "image" else MediaType.VOICE
            
            # Retrieve path mapping directly from precomputed lookup indexes
            if media_type == MediaType.IMAGE:
                rel_path = context.image_lookup.get(media_id, "")
            else:
                rel_path = context.voice_lookup.get(media_id, "")
                
            if rel_path:
                media_info = MediaInfo(
                    media_id=media_id,
                    media_type=media_type,
                    file_path=(DATASET_DIR / rel_path).resolve(),
                    mime_type="image/jpeg" if media_type == MediaType.IMAGE else "audio/mpeg",
                    file_size_bytes=0
                )
                media_analysis = load_analysis(media_info)
        except Exception as e:
            logger.warning("Failed to load media metadata for %s (non-fatal): %s", media_id, e)
            
    # 2. Build extraction input
    inp = ExtractionInput(
        message=message,
        context=context,
        media_info=media_info,
        media_analysis=media_analysis
    )
    
    # 3. Instantiate RoutingFeatures contract mapping
    return RoutingFeatures(
        message_id=str(message.get("message_id", "")),
        user_id=str(message.get("user_id", "")),
        metadata=FeatureMetadata(),
        user=_extract_user_features(inp),
        group=_extract_group_features(inp),
        business=_extract_business_features(inp),
        message=_extract_message_features(inp),
        media=_extract_media_features(inp),
        relationship=_extract_relationship_features(inp),
        conversation=_extract_conversation_features(inp),
        temporal=_extract_temporal_features(inp),
        safety=_extract_safety_features(inp),
        system=_extract_system_features(inp)
    )
