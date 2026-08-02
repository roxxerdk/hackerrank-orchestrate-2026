from dataclasses import dataclass
from typing import Final, Callable, List
from app.reasoning.schemas import ReasoningContext, RuleCategory, RetrievedRule, ActionType

RULESET_VERSION: Final[str] = "1.0"

from app.evaluation.tuning_config import tuning_config

# Rule Priority Bands
PRIORITY_SAFETY: Final[int] = 1000
PRIORITY_USER: Final[int] = 900
PRIORITY_BUSINESS: Final[int] = 700
PRIORITY_URGENCY: Final[int] = 500
PRIORITY_RELATIONSHIP: Final[int] = 300
PRIORITY_SYSTEM: Final[int] = 100

@dataclass(frozen=True)
class RuleDefinition:
    """
    Internal immutable container holding code-native rule evaluators.
    """
    rule_id: str
    category: RuleCategory
    priority: int
    weight: float
    description: str
    evaluator: Callable[[ReasoningContext], bool]
    recommended_action: ActionType

    def to_retrieved_rule(self) -> RetrievedRule:
        return RetrievedRule(
            rule_id=self.rule_id,
            category=self.category,
            condition_description=self.description,
            priority=self.priority,
            weight=self.weight,
            recommended_action=self.recommended_action
        )

# Named Evaluators
def safety_domain_mismatch(ctx: ReasoningContext) -> bool:
    return ctx.safety.domain_mismatch

def safety_high_forward(ctx: ReasoningContext) -> bool:
    return ctx.safety.high_forward_count

def user_in_dnd(ctx: ReasoningContext) -> bool:
    return ctx.user.in_dnd

def user_group_muted(ctx: ReasoningContext) -> bool:
    return ctx.group.is_muted

def business_not_allowed_promo(ctx: ReasoningContext) -> bool:
    return not ctx.business.promotions_allowed

def business_verified_interaction(ctx: ReasoningContext) -> bool:
    return ctx.business.verified and ctx.business.interaction_score > 0.1

def media_payment_request(ctx: ReasoningContext) -> bool:
    return ctx.media.has_payment_request

def media_has_qr(ctx: ReasoningContext) -> bool:
    return ctx.media.has_qr

def relationship_frequent(ctx: ReasoningContext) -> bool:
    return ctx.relationship.sender_is_frequent_contact

def system_high_load(ctx: ReasoningContext) -> bool:
    return ctx.system.daily_alert_load_score > 0.8

# Rules Definition List
RULES: List[RuleDefinition] = [
    RuleDefinition(
        rule_id="RULE_SAFETY_DOMAIN_MISMATCH",
        category=RuleCategory.SAFETY,
        priority=PRIORITY_SAFETY,
        weight=tuning_config.RULE_SAFETY_DOMAIN_MISMATCH_WEIGHT,
        description="Sender official domain does not match official brand metadata domain.",
        evaluator=safety_domain_mismatch,
        recommended_action=ActionType.MUTE
    ),
    RuleDefinition(
        rule_id="RULE_SAFETY_HIGH_FORWARD",
        category=RuleCategory.SAFETY,
        priority=PRIORITY_SAFETY,
        weight=tuning_config.RULE_SAFETY_HIGH_FORWARD_WEIGHT,
        description="Message content has been forwarded past standard threshold levels.",
        evaluator=safety_high_forward,
        recommended_action=ActionType.MUTE
    ),
    RuleDefinition(
        rule_id="RULE_USER_DND_ACTIVE",
        category=RuleCategory.USER_PREFERENCE,
        priority=PRIORITY_USER,
        weight=tuning_config.RULE_USER_DND_ACTIVE_WEIGHT,
        description="Recipient is currently within do_not_disturb window boundaries.",
        evaluator=user_in_dnd,
        recommended_action=ActionType.DIGEST
    ),
    RuleDefinition(
        rule_id="RULE_USER_GROUP_MUTED",
        category=RuleCategory.USER_PREFERENCE,
        priority=PRIORITY_USER,
        weight=tuning_config.RULE_USER_GROUP_MUTED_WEIGHT,
        description="Target group has been explicitly muted by the recipient.",
        evaluator=user_group_muted,
        recommended_action=ActionType.MUTE
    ),
    RuleDefinition(
        rule_id="RULE_BUSINESS_PROMO_OPT_OUT",
        category=RuleCategory.BUSINESS,
        priority=PRIORITY_USER,
        weight=tuning_config.RULE_BUSINESS_PROMO_OPT_OUT_WEIGHT,
        description="User explicitly disabled promotional material from this business.",
        evaluator=business_not_allowed_promo,
        recommended_action=ActionType.DIGEST
    ),
    RuleDefinition(
        rule_id="RULE_BUSINESS_VERIFIED_TRUST",
        category=RuleCategory.BUSINESS,
        priority=PRIORITY_BUSINESS,
        weight=tuning_config.RULE_BUSINESS_VERIFIED_TRUST_WEIGHT,
        description="Verified business has active history and high interaction scores.",
        evaluator=business_verified_interaction,
        recommended_action=ActionType.NOTIFY
    ),
    RuleDefinition(
        rule_id="RULE_MEDIA_PAYMENT_REQUEST",
        category=RuleCategory.MEDIA,
        priority=PRIORITY_URGENCY,
        weight=tuning_config.RULE_MEDIA_PAYMENT_REQUEST_WEIGHT,
        description="Media analysis indicates payment requests or payment receipts are present.",
        evaluator=media_payment_request,
        recommended_action=ActionType.NOTIFY
    ),
    RuleDefinition(
        rule_id="RULE_MEDIA_QR_PRESENT",
        category=RuleCategory.MEDIA,
        priority=PRIORITY_URGENCY,
        weight=tuning_config.RULE_MEDIA_QR_PRESENT_WEIGHT,
        description="Multimodal check indicates a scannable QR layout was identified.",
        evaluator=media_has_qr,
        recommended_action=ActionType.NOTIFY
    ),
    RuleDefinition(
        rule_id="RULE_RELATIONSHIP_FREQUENT",
        category=RuleCategory.RELATIONSHIP,
        priority=PRIORITY_RELATIONSHIP,
        weight=tuning_config.RULE_RELATIONSHIP_FREQUENT_WEIGHT,
        description="Sender has high interaction volumes and message history counts.",
        evaluator=relationship_frequent,
        recommended_action=ActionType.NOTIFY
    ),
    RuleDefinition(
        rule_id="RULE_SYSTEM_LOAD_ALERT",
        category=RuleCategory.SYSTEM,
        priority=PRIORITY_SYSTEM,
        weight=tuning_config.RULE_SYSTEM_LOAD_ALERT_WEIGHT,
        description="System notify alert volume sent to the recipient today is high.",
        evaluator=system_high_load,
        recommended_action=ActionType.DIGEST
    )
]
