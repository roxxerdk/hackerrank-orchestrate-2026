import time
import logging
from app.features.routing_features import RoutingFeatures
from app.reasoning.schemas import FinalRoutingResult, DecisionMetadata
from app.reasoning.context_builder import build_reasoning_context
from app.reasoning.retrieval_engine import retrieve_rules
from app.reasoning.reasoning_engine import evaluate_decision
from app.reasoning.confidence import calculate_confidence
from app.reasoning.rule_repository import RULES, RULESET_VERSION

logger = logging.getLogger("decision_service")

def evaluate_message(features: RoutingFeatures) -> FinalRoutingResult:
    """
    Unified public entry point orchestrating context mapping, rule retrieval,
    conflict reasoning, and confidence metrics calculations.
    """
    start_time = time.perf_counter()
    
    try:
        # 1. Map to reasoning context
        context = build_reasoning_context(features)
        
        # 2. Retrieve rules
        evidence = retrieve_rules(context)
        
        # 3. Evaluate decision routing
        decision = evaluate_decision(context, evidence)
        
        # 4. Calculate confidence breakdown
        confidence_breakdown = calculate_confidence(context, evidence, decision)
        
        # Map breakdown back inside RoutingDecision Pydantic schema model
        decision.confidence_breakdown = confidence_breakdown
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        metadata = DecisionMetadata(
            ruleset_version=RULESET_VERSION,
            confidence_version=confidence_breakdown.confidence_version,
            pipeline_version="1.0",
            execution_time_ms=elapsed_ms,
            evaluated_rule_count=len(RULES),
            matched_rule_count=len(evidence.retrieved_rules)
        )
        
        logger.info(
            "Decision evaluation complete: Message=%s, Action=%s, Confidence=%.2f, Matched Rules=%d, Elapsed=%.1f ms",
            features.message_id,
            decision.action.value,
            confidence_breakdown.final_confidence,
            len(evidence.retrieved_rules),
            elapsed_ms
        )
        
        return FinalRoutingResult(
            decision=decision,
            confidence=confidence_breakdown,
            evidence=evidence,
            reasoning_context=context,
            metadata=metadata
        )
        
    except Exception as e:
        logger.exception("Reasoning pipeline execution failed for message: %s", features.message_id)
        raise e
