from app.features.routing_features import RoutingFeatures
from app.reasoning.schemas import (
    ReasoningContext,
    MessageContext,
    UserContext,
    BusinessContext,
    GroupContext,
    MediaContext,
    RelationshipContext,
    ConversationContext,
    SafetyContext,
    TemporalContext,
    SystemContext,
)

def build_reasoning_context(features: RoutingFeatures) -> ReasoningContext:
    """
    Pure mapper translating large RoutingFeatures schema to compact ReasoningContext model.
    Contains no reasoning logic or decision making.
    """
    return ReasoningContext(
        message_id=features.message_id,
        user_id=features.user_id,
        
        message=MessageContext(
            has_media=features.message.has_media,
            has_link=features.message.has_link,
            has_urgency_phrase=features.message.has_urgency_phrase,
            text_length=features.message.text_length,
            is_mass_forwarded=features.message.is_mass_forwarded
        ),
        
        user=UserContext(
            user_reply_ratio=features.user.user_reply_ratio,
            user_open_ratio=features.user.user_open_ratio,
            user_dismiss_ratio=features.user.user_dismiss_ratio,
            in_dnd=features.user.in_dnd_window
        ),
        
        business=BusinessContext(
            verified=features.business.business_verified,
            risk=features.business.business_risk_score,
            promotions_allowed=features.business.promotions_allowed,
            interaction_score=features.business.business_interaction_score
        ),
        
        group=GroupContext(
            is_muted=features.group.is_group_muted,
            is_admin=features.group.is_group_admin,
            activity_level=features.group.group_activity_level,
            member_count=features.group.member_count
        ),
        
        media=MediaContext(
            has_media=features.message.has_media,
            has_qr=features.media.has_qr,
            has_payment_request=features.media.has_payment_request,
            contains_deadline=features.media.contains_deadline,
            contains_phone=features.media.contains_phone,
            media_file_size_bytes=features.media.media_file_size_bytes
        ),
        
        relationship=RelationshipContext(
            sender_is_known=features.relationship.sender_is_known,
            sender_is_frequent_contact=features.relationship.sender_is_frequent_contact,
            sender_is_business=features.relationship.sender_is_business
        ),
        
        conversation=ConversationContext(
            last_message_delta_minutes=features.conversation.last_message_delta_minutes,
            conversation_age_days=features.conversation.conversation_age_days,
            previous_reply_exists=features.conversation.previous_reply_exists,
            previous_interaction_exists=features.conversation.previous_interaction_exists
        ),
        
        safety=SafetyContext(
            domain_mismatch=features.safety.domain_mismatch,
            high_forward_count=features.safety.high_forward_count,
            reported_business=features.safety.reported_business,
            unknown_sender=features.safety.unknown_sender
        ),
        
        temporal=TemporalContext(
            message_hour=features.temporal.message_hour,
            is_weekend=features.temporal.is_weekend,
            time_bucket=features.temporal.time_bucket
        ),
        
        system=SystemContext(
            daily_alert_load_score=features.system.daily_alert_load_score
        )
    )
