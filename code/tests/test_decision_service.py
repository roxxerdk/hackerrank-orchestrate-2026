import sys
import os
import unittest
from unittest.mock import patch

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.features.feature_extractor import extract_features
from app.reasoning.decision_service import evaluate_message
from app.reasoning.schemas import FinalRoutingResult

class TestDecisionService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.datasets = load_all_datasets()
        cls.context = build_extraction_context(cls.datasets)

    def test_end_to_end_decision_service(self):
        # 1. Run extractor on a representative message
        messages_df = self.datasets["messages"]
        raw_msg = messages_df.iloc[0].to_dict()
        
        routing_features = extract_features(raw_msg, self.context)
        
        # 2. Evaluate using Decision Service
        result = evaluate_message(routing_features)
        
        # 3. Assert structured contracts exist
        self.assertIsInstance(result, FinalRoutingResult)
        self.assertEqual(result.reasoning_context.message_id, routing_features.message_id)
        self.assertGreaterEqual(result.confidence.final_confidence, 0.0)
        self.assertGreater(result.metadata.execution_time_ms, 0.0)
        self.assertEqual(result.metadata.ruleset_version, "1.0")
        
        # 4. Round-trip serialization integrity
        dumped = result.model_dump()
        reconstructed = FinalRoutingResult.model_validate(dumped)
        self.assertEqual(reconstructed.decision.action, result.decision.action)

    def test_pipeline_exception_propagation(self):
        # Mock context_builder to raise exception and verify orchestrator handles it consistently
        messages_df = self.datasets["messages"]
        raw_msg = messages_df.iloc[0].to_dict()
        routing_features = extract_features(raw_msg, self.context)
        
        with patch("app.reasoning.decision_service.build_reasoning_context", side_effect=ValueError("Mock mapping failure")):
            with self.assertRaises(ValueError):
                evaluate_message(routing_features)

if __name__ == "__main__":
    unittest.main()
