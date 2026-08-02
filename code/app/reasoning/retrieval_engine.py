import logging
from typing import List
from app.reasoning.schemas import ReasoningContext, RetrievedEvidence, RetrievedRule
from app.reasoning.rule_repository import RULES, RULESET_VERSION

logger = logging.getLogger("retrieval_engine")

def retrieve_rules(context: ReasoningContext) -> RetrievedEvidence:
    """
    Evaluates context predicates, filters matched items, and returns RetrievedEvidence.
    Orders matches descending by (-priority, rule_id) deterministically.
    Fault-tolerant: Logs and continues if individual evaluators raise exceptions.
    """
    matched_rules = []
    
    for rule in RULES:
        try:
            if rule.evaluator(context):
                matched_rules.append(rule)
        except Exception as e:
            logger.exception(
                "Rule %s failed during evaluation",
                rule.rule_id
            )
            
    # Sort deterministically descending by (-priority, rule_id)
    # priority ascending sort key is priority, so descending is -priority
    # rule_id is string, sorting alphabetically handles rule_id
    matched_rules.sort(key=lambda r: (-r.priority, r.rule_id))
    
    # 2-5 sentence log mapping category properties and ruleset load summary
    logger.info(
        "Retrieved %d matching rules using ruleset version %s.",
        len(matched_rules),
        RULESET_VERSION
    )
    if matched_rules:
        logger.info(
            "Highest priority matching rule: %s (Priority: %d)",
            matched_rules[0].rule_id,
            matched_rules[0].priority
        )
        
    retrieved_list: List[RetrievedRule] = [r.to_retrieved_rule() for r in matched_rules]
    
    # Categories resolved from mapping enums values
    matched_sources = sorted({r.category.value for r in matched_rules})
    
    # Historical match count refers to total count metadata statistics
    historical_count = 1 if context.conversation.previous_interaction_exists else 0
    
    return RetrievedEvidence(
        ruleset_version=RULESET_VERSION,
        retrieved_rules=retrieved_list,
        historical_match_count=historical_count,
        matched_sources=matched_sources
    )
