import sys
import os
import unittest

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    RuleCategory,
    ActionType
)
from app.reasoning.rule_repository import RuleDefinition, RULES
from app.reasoning.retrieval_engine import retrieve_rules

# Stub Context for testing
def create_stub_context(
    in_dnd: bool = False,
    domain_mismatch: bool = False,
    is_muted: bool = False,
    promo_allowed: bool = True,
    previous_exists: bool = False
) -> ReasoningContext:
    from app.features.routing_features import ActivityLevel, TemporalBucket
    return ReasoningContext(
        message_id="m_test",
        user_id="u_test",
        message=MessageContext(
            has_media=False,
            has_link=False,
            has_urgency_phrase=False,
            text_length=10,
            is_mass_forwarded=False
        ),
        user=UserContext(
            user_reply_ratio=0.5,
            user_open_ratio=0.5,
            user_dismiss_ratio=0.1,
            in_dnd=in_dnd
        ),
        business=BusinessContext(
            verified=False,
            risk=0.0,
            promotions_allowed=promo_allowed,
            interaction_score=0.0
        ),
        group=GroupContext(
            is_muted=is_muted,
            is_admin=False,
            activity_level=ActivityLevel.MEDIUM,
            member_count=0
        ),
        media=MediaContext(
            has_media=False,
            has_qr=False,
            has_payment_request=False,
            contains_deadline=False,
            contains_phone=False,
            media_file_size_bytes=0
        ),
        relationship=RelationshipContext(
            sender_is_known=True,
            sender_is_frequent_contact=False,
            sender_is_business=False
        ),
        conversation=ConversationContext(
            last_message_delta_minutes=10.0,
            conversation_age_days=1.0,
            previous_reply_exists=False,
            previous_interaction_exists=previous_exists
        ),
        safety=SafetyContext(
            domain_mismatch=domain_mismatch,
            high_forward_count=False,
            reported_business=False,
            unknown_sender=False
        ),
        temporal=TemporalContext(
            message_hour=12,
            is_weekend=False,
            time_bucket=TemporalBucket.AFTERNOON
        ),
        system=SystemContext(
            daily_alert_load_score=0.0
        )
    )

class TestRetrievalEngine(unittest.TestCase):

    def test_empty_rules_retrieval(self):
        # Temporarily mock empty RULES list
        from unittest.mock import patch
        with patch("app.reasoning.retrieval_engine.RULES", []):
            ctx = create_stub_context()
            evidence = retrieve_rules(ctx)
            self.assertEqual(len(evidence.retrieved_rules), 0)
            self.assertEqual(len(evidence.matched_sources), 0)

    def test_rule_evaluator_exception_handling(self):
        # Create a rule that raises unexpectedly
        def bad_evaluator(ctx):
            raise RuntimeError("Unexpected failure")
            
        bad_rule = RuleDefinition(
            rule_id="RULE_BAD",
            category=RuleCategory.SAFETY,
            priority=1000,
            weight=1.0,
            description="Always errors.",
            evaluator=bad_evaluator,
            recommended_action=ActionType.MUTE
        )
        
        from unittest.mock import patch
        with patch("app.reasoning.retrieval_engine.RULES", [bad_rule]):
            ctx = create_stub_context()
            evidence = retrieve_rules(ctx)
            # Confirms retrieval completed successfully despite exception
            self.assertEqual(len(evidence.retrieved_rules), 0)

    def test_retrieval_ordering_and_sources(self):
        ctx = create_stub_context(in_dnd=True, domain_mismatch=True)
        evidence = retrieve_rules(ctx)
        
        # Verify matched counts
        self.assertGreater(len(evidence.retrieved_rules), 0)
        
        # Verify deterministic priority order: SAFETY (1000) should be before USER_PREFERENCE (900)
        rules = evidence.retrieved_rules
        priorities = [r.priority for r in rules]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
        
        # Verify matched sources contains sorted unique values
        self.assertIn("safety", evidence.matched_sources)
        self.assertIn("user_preference", evidence.matched_sources)

if __name__ == "__main__":
    unittest.main()
