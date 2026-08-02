import sys
import os
import unittest
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.features.feature_extractor import extract_features
from app.reasoning.context_builder import build_reasoning_context
from app.reasoning.schemas import ReasoningContext

class TestContextBuilder(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.datasets = load_all_datasets()
        cls.context = build_extraction_context(cls.datasets)

    def test_build_reasoning_context_mapping(self):
        # 1. Select a message row and run feature extractor
        messages_df = self.datasets["messages"]
        raw_msg = messages_df.iloc[0].to_dict()
        
        routing_features = extract_features(raw_msg, self.context)
        
        # 2. Convert to ReasoningContext
        reasoning_ctx = build_reasoning_context(routing_features)
        
        # 3. Assert correctness of properties
        self.assertEqual(reasoning_ctx.message_id, routing_features.message_id)
        self.assertEqual(reasoning_ctx.user_id, routing_features.user_id)
        self.assertEqual(reasoning_ctx.schema_version, "1.0")
        
        # 4. Check sub-schema conversions
        self.assertEqual(reasoning_ctx.message.text_length, routing_features.message.text_length)
        self.assertEqual(reasoning_ctx.user.in_dnd, routing_features.user.in_dnd_window)
        self.assertEqual(reasoning_ctx.group.member_count, routing_features.group.member_count)
        self.assertEqual(reasoning_ctx.media.has_qr, routing_features.media.has_qr)
        
        # 5. Check serialization / deserialization round-trip integrity
        model_dict = reasoning_ctx.model_dump()
        reconstructed = ReasoningContext.model_validate(model_dict)
        self.assertEqual(reconstructed.message_id, reasoning_ctx.message_id)
        self.assertEqual(reconstructed.user.in_dnd, reasoning_ctx.user.in_dnd)

if __name__ == "__main__":
    unittest.main()
