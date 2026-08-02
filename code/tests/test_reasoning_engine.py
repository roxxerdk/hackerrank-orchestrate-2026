import sys
import os
import unittest

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.reasoning.schemas import (
    ReasoningContext,
    RetrievedEvidence,
    RetrievedRule,
    RuleCategory,
    ActionType,
)
from app.reasoning.reasoning_engine import evaluate_decision, DEFAULT_ACTION, DEFAULT_CONFIDENCE
from test_retrieval_engine import create_stub_context

class TestReasoningEngine(unittest.TestCase):

    def test_no_retrieved_rules_fallback(self):
        ctx = create_stub_context()
        evidence = RetrievedEvidence(
            ruleset_version="1.0",
            retrieved_rules=[],
            historical_match_count=0,
            matched_sources=[]
        )
        
        decision = evaluate_decision(ctx, evidence)
        self.assertEqual(decision.action, DEFAULT_ACTION)
        self.assertEqual(decision.confidence, DEFAULT_CONFIDENCE)
        self.assertEqual(len(decision.applied_rules), 0)

    def test_single_notify_rule(self):
        ctx = create_stub_context()
        rule = RetrievedRule(
            rule_id="RULE_URGENT",
            category=RuleCategory.MESSAGE,
            condition_description="Urgent message tag found.",
            priority=500,
            weight=0.8,
            recommended_action=ActionType.NOTIFY
        )
        evidence = RetrievedEvidence(
            ruleset_version="1.0",
            retrieved_rules=[rule],
            historical_match_count=0,
            matched_sources=["message"]
        )
        
        decision = evaluate_decision(ctx, evidence)
        self.assertEqual(decision.action, ActionType.NOTIFY)
        self.assertEqual(decision.confidence, 0.50 + (0.8 * 0.25))

    def test_conflict_resolution_priority_wins(self):
        ctx = create_stub_context()
        rule_low = RetrievedRule(
            rule_id="RULE_LOW",
            category=RuleCategory.MESSAGE,
            condition_description="Low priority notify rule.",
            priority=300,
            weight=1.0,
            recommended_action=ActionType.NOTIFY
        )
        rule_high = RetrievedRule(
            rule_id="RULE_HIGH",
            category=RuleCategory.SAFETY,
            condition_description="Domain mismatch detected.",
            priority=1000,
            weight=0.9,
            recommended_action=ActionType.MUTE
        )
        evidence = RetrievedEvidence(
            ruleset_version="1.0",
            retrieved_rules=[rule_low, rule_high],
            historical_match_count=0,
            matched_sources=["message", "safety"]
        )
        
        decision = evaluate_decision(ctx, evidence)
        # Priority 1000 wins over Priority 300
        self.assertEqual(decision.action, ActionType.MUTE)
        self.assertEqual(decision.applied_rules[0], "RULE_HIGH")

    def test_conflict_resolution_tie_breaking(self):
        ctx = create_stub_context()
        # Same priority, same weight, tie break action precedence check: MUTE > DIGEST
        rule_digest = RetrievedRule(
            rule_id="RULE_DIGEST",
            category=RuleCategory.USER_PREFERENCE,
            condition_description="Test digest description.",
            priority=900,
            weight=0.9,
            recommended_action=ActionType.DIGEST
        )
        rule_mute = RetrievedRule(
            rule_id="RULE_MUTE",
            category=RuleCategory.USER_PREFERENCE,
            condition_description="Test mute description.",
            priority=900,
            weight=0.9,
            recommended_action=ActionType.MUTE
        )
        evidence = RetrievedEvidence(
            ruleset_version="1.0",
            retrieved_rules=[rule_digest, rule_mute],
            historical_match_count=0,
            matched_sources=["user_preference"]
        )
        
        decision = evaluate_decision(ctx, evidence)
        self.assertEqual(decision.action, ActionType.MUTE)

if __name__ == "__main__":
    unittest.main()
