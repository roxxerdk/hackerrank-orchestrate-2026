import sys
import os
import unittest

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.reasoning.schemas import (
    ReasoningContext,
    RetrievedEvidence,
    RetrievedRule,
    RoutingDecision,
    ActionType,
    RuleCategory,
)
from app.reasoning.confidence import calculate_confidence
from test_retrieval_engine import create_stub_context

class TestConfidenceCalculator(unittest.TestCase):

    def test_base_confidence_only(self):
        ctx = create_stub_context()
        evidence = RetrievedEvidence(ruleset_version="1.0")
        decision = RoutingDecision(
            action=ActionType.DIGEST,
            confidence=0.50,
            applied_rules=[],
            rationale=[]
        )
        
        breakdown = calculate_confidence(ctx, evidence, decision)
        # Verify base match
        self.assertEqual(breakdown.base_confidence, 0.50)
        # Engagement = (0.5 + 0.5) / 2 = 0.5 -> 0.5 * 0.15 = 0.075 bonus
        # System load = 0 -> 0 penalty
        # Final = 0.50 + 0.075 = 0.575
        self.assertAlmostEqual(breakdown.final_confidence, 0.575)

    def test_strong_rule_bonus(self):
        ctx = create_stub_context()
        rule = RetrievedRule(
            rule_id="RULE_TEST",
            category=RuleCategory.MESSAGE,
            condition_description="Test rule.",
            priority=500,
            weight=1.0,
            recommended_action=ActionType.NOTIFY
        )
        evidence = RetrievedEvidence(
            ruleset_version="1.0",
            retrieved_rules=[rule]
        )
        decision = RoutingDecision(
            action=ActionType.NOTIFY,
            confidence=0.50,
            applied_rules=[],
            rationale=[]
        )
        
        breakdown = calculate_confidence(ctx, evidence, decision)
        # Rule weight 1.0 * 0.20 weight factor = 0.20 bonus
        self.assertEqual(breakdown.rule_strength_bonus, 0.20)

    def test_safety_penalties(self):
        ctx = create_stub_context(domain_mismatch=True)
        evidence = RetrievedEvidence(ruleset_version="1.0")
        decision = RoutingDecision(
            action=ActionType.MUTE,
            confidence=0.50,
            applied_rules=[],
            rationale=[]
        )
        
        breakdown = calculate_confidence(ctx, evidence, decision)
        # Domain mismatch penalty = 0.30
        self.assertEqual(breakdown.safety_penalty, 0.30)
        # Final = 0.50 (base) + 0.075 (engagement) - 0.30 (safety) = 0.275
        self.assertAlmostEqual(breakdown.final_confidence, 0.275)

    def test_clamping_ranges(self):
        ctx = create_stub_context(domain_mismatch=True)
        ctx.safety.unknown_sender = True
        ctx.safety.reported_business = True
        
        evidence = RetrievedEvidence(ruleset_version="1.0")
        decision = RoutingDecision(
            action=ActionType.MUTE,
            confidence=0.10,
            applied_rules=[],
            rationale=[]
        )
        
        breakdown = calculate_confidence(ctx, evidence, decision)
        # Safety penalties = 0.30 + 0.10 + 0.20 = 0.60
        # Raw = 0.10 (base) + 0.075 (engagement) - 0.60 (safety) = -0.425
        # Should clamp to 0.0
        self.assertEqual(breakdown.final_confidence, 0.0)

if __name__ == "__main__":
    unittest.main()
