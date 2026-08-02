import logging
from typing import List, Tuple
from app.reasoning.schemas import ReasoningContext, RetrievedEvidence, RoutingDecision, ActionType

logger = logging.getLogger("reasoning_engine")

DEFAULT_ACTION = ActionType.DIGEST
DEFAULT_CONFIDENCE = 0.50

def _get_action_precedence(action: ActionType) -> int:
    """
    Assigns precedence mapping to actions for deterministic conflict resolution.
    Higher integer = Higher precedence in tie-breaking.
    """
    precedence = {
        ActionType.MUTE: 3,
        ActionType.DIGEST: 2,
        ActionType.NOTIFY: 1
    }
    return precedence.get(action, 0)

def evaluate_decision(
    context: ReasoningContext,
    evidence: RetrievedEvidence
) -> RoutingDecision:
    """
    Orchestrates candidate rule selections and resolves routing conflicts deterministically.
    """
    rules = evidence.retrieved_rules
    
    if not rules:
        # Fallback default decision parameters
        return RoutingDecision(
            action=DEFAULT_ACTION,
            confidence=DEFAULT_CONFIDENCE,
            applied_rules=[],
            rationale=["No rules were retrieved. Default fallback option applied."]
        )
        
    # Rules are already sorted by priority in the retrieval engine.
    # To resolve conflict, we sort rules deterministically using:
    # 1. priority descending
    # 2. weight descending
    # 3. action precedence descending (MUTE > DIGEST > NOTIFY)
    # 4. rule_id lexicographically
    
    sorted_rules = sorted(
        rules,
        key=lambda r: (
            -r.priority,
            -r.weight,
            -_get_action_precedence(r.recommended_action),
            r.rule_id
        )
    )
    
    winning_rule = sorted_rules[0]
    
    # Calculate simple base confidence: base_score + (winning_weight * 0.25)
    base_score = 0.50
    confidence = base_score + (winning_rule.weight * 0.25)
    confidence = min(1.0, max(0.0, confidence))
    
    # Build decision
    applied_rules = [r.rule_id for r in sorted_rules]
    rationale = [r.condition_description for r in sorted_rules]
    
    logger.info(
        "Decision evaluated for message %s: Action=%s, Confidence=%.2f via winning rule %s",
        context.message_id,
        winning_rule.recommended_action.value,
        confidence,
        winning_rule.rule_id
    )
    
    return RoutingDecision(
        action=winning_rule.recommended_action,
        confidence=confidence,
        applied_rules=applied_rules,
        rationale=rationale
    )
