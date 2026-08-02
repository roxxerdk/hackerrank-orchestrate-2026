import logging
from app.reasoning.schemas import (
    ReasoningContext,
    RetrievedEvidence,
    RoutingDecision,
    ConfidenceBreakdown
)
from app.config import (
    RULE_WEIGHT_FACTOR,
    ENGAGEMENT_FACTOR,
    SYSTEM_LOAD_FACTOR,
    DOMAIN_MISMATCH_PENALTY,
    UNKNOWN_SENDER_PENALTY,
    REPORTED_BUSINESS_PENALTY
)

logger = logging.getLogger("confidence_calculator")

def calculate_confidence(
    context: ReasoningContext,
    evidence: RetrievedEvidence,
    decision: RoutingDecision
) -> ConfidenceBreakdown:
    """
    Computes a deterministic, explainable confidence score breakdown.
    Does not modify the selected routing decision action.
    """
    base = decision.confidence
    
    # 1. Rule Strength Bonus
    highest_weight = 0.0
    if evidence.retrieved_rules:
        highest_weight = max(r.weight for r in evidence.retrieved_rules)
    rule_bonus = highest_weight * RULE_WEIGHT_FACTOR
    
    # 2. User Engagement Bonus
    # Average of user reply and open ratios, scaled by engagement factor
    opened = context.user.user_open_ratio
    replied = context.user.user_reply_ratio
    avg_engagement = (opened + replied) / 2.0
    engagement_bonus = avg_engagement * ENGAGEMENT_FACTOR
    
    # 3. Safety Penalty
    # Each matching indicator contributes a cumulative penalty
    safety_penalty = 0.0
    if context.safety.domain_mismatch:
        safety_penalty += DOMAIN_MISMATCH_PENALTY
    if context.safety.unknown_sender:
        safety_penalty += UNKNOWN_SENDER_PENALTY
    if context.safety.reported_business:
        safety_penalty += REPORTED_BUSINESS_PENALTY
        
    # 4. System Load Penalty
    system_penalty = context.system.daily_alert_load_score * SYSTEM_LOAD_FACTOR
    
    # 5. Final calculation and clamp
    raw_final = base + rule_bonus + engagement_bonus - safety_penalty - system_penalty
    final = min(1.0, max(0.0, raw_final))
    
    logger.info(
        "Confidence calculation for message %s: Base=%.2f, Rule=+%.2f, Engagement=+%.2f, Safety=-%.2f, System=-%.2f -> Final=%.2f",
        context.message_id,
        base,
        rule_bonus,
        engagement_bonus,
        safety_penalty,
        system_penalty,
        final
    )
    
    return ConfidenceBreakdown(
        confidence_version="1.0",
        base_confidence=base,
        safety_penalty=safety_penalty,
        user_engagement_bonus=engagement_bonus,
        rule_strength_bonus=rule_bonus,
        system_load_penalty=system_penalty,
        final_confidence=final
    )
