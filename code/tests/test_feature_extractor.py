import sys
import os
import unittest
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.features.feature_extractor import extract_features
from app.features.routing_features import ActivityLevel, TemporalBucket

class TestFeatureExtractor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.datasets = load_all_datasets()
        cls.context = build_extraction_context(cls.datasets)

    def test_extract_features_fallback(self):
        # Test mapping a message referencing unknown user and group
        unknown_message = {
            "message_id": "m_test_999",
            "user_id": "u_unknown_999",
            "conversation_type": "group",
            "group_id": "g_unknown_999",
            "sender_user_id": "u_unknown_888",
            "created_at": "2026-08-01 12:00:00",
            "message_text": "Urgent attention required: visit http://unsafe-link.org",
            "media_type": "nan",
            "media_id": "nan",
            "forwarded_count": 8
        }
        
        features = extract_features(unknown_message, self.context)
        
        # Verify basic mappings
        self.assertEqual(features.message_id, "m_test_999")
        self.assertEqual(features.user_id, "u_unknown_999")
        
        # Verify text flags from pure utilities
        self.assertTrue(features.message.has_link)
        self.assertTrue(features.message.has_urgency_phrase)
        self.assertTrue(features.message.is_mass_forwarded)
        
        # Verify DND falls back safely (since user is unknown)
        self.assertFalse(features.user.in_dnd_window)
        
        # Verify group values default safely
        self.assertEqual(features.group.member_count, 0)
        self.assertEqual(features.group.group_activity_level, ActivityLevel.MEDIUM)
        
        # Verify safety flags
        self.assertTrue(features.safety.high_forward_count)
        self.assertTrue(features.safety.unknown_sender)

    def test_extract_features_known_user(self):
        # Fetch a valid message row from datasets to verify joins
        messages_df = self.datasets["messages"]
        known_row = messages_df.iloc[0].to_dict()
        
        features = extract_features(known_row, self.context)
        
        self.assertEqual(features.message_id, str(known_row["message_id"]))
        self.assertEqual(features.user_id, str(known_row["user_id"]))
        
        # Verify temporal hour parsing matches
        try:
            parsed_time = datetime.strptime(str(known_row["created_at"]), "%Y-%m-%d %H:%M")
        except ValueError:
            parsed_time = datetime.strptime(str(known_row["created_at"]), "%Y-%m-%d %H:%M:%S")
        self.assertEqual(features.temporal.message_hour, parsed_time.hour)

    def test_extract_features_known_business(self):
        # Scan messages to find one with a valid business relation
        business_msgs = [
            m for _, m in self.datasets["messages"].iterrows()
            if str(m.get("business_id", "")) != "nan"
        ]
        if not business_msgs:
            self.skipTest("No messages with business_id found in active dataset")
            
        known_biz_row = business_msgs[0]
        features = extract_features(dict(known_biz_row), self.context)
        
        # Verify verified parameters are boolean
        self.assertIsInstance(features.business.business_verified, bool)
        self.assertTrue(features.relationship.sender_is_business)
        self.assertGreaterEqual(features.business.business_risk_score, 0.0)

    def test_extract_features_known_group(self):
        group_msgs = [
            m for _, m in self.datasets["messages"].iterrows()
            if str(m.get("group_id", "")) != "nan"
        ]
        if not group_msgs:
            self.skipTest("No group messages found in active dataset")
            
        known_grp_row = group_msgs[0]
        features = extract_features(dict(known_grp_row), self.context)
        
        self.assertGreater(features.group.member_count, 0)
        self.assertIsInstance(features.group.is_group_muted, bool)

    def test_extract_features_conversation_history(self):
        # Select first conversation pair from computed indexes
        pairs = list(self.context.conversation_history.keys())
        if not pairs:
            self.skipTest("No conversation histories precomputed")
            
        user_id, sender_id = pairs[0]
        
        # Ensure sender is in users index for relationship check
        if sender_id not in self.context.users_index:
            self.context.users_index[sender_id] = {
                "user_id": sender_id,
                "messages_opened_30d": 0,
                "messages_replied_30d": 0,
                "notifications_dismissed_30d": 0,
                "do_not_disturb_window": ""
            }
            
        sample_msg = {
            "message_id": "m_conv_test_1",
            "user_id": user_id,
            "sender_user_id": sender_id,
            "conversation_type": "personal",
            "created_at": "2026-08-01 12:00:00",
            "message_text": "Normal conversing text."
        }
        
        features = extract_features(sample_msg, self.context)
        
        # Self-interaction metrics
        self.assertTrue(features.conversation.previous_interaction_exists)
        self.assertTrue(features.relationship.sender_is_known)

    def test_extract_features_mocked_media_cache(self):
        # Test mocked contains_qr matching
        from unittest.mock import patch
        from app.media.media_cache import CacheMetadata
        
        mock_meta = CacheMetadata(
            version="1.0",
            created_at=datetime.utcnow().isoformat(),
            media_id="img_001",
            media_type="image",
            model="gemini-1.5-flash",
            prompt_version="1.0",
            analysis={
                "facts": {},
                "detected_signals": {
                    "contains_qr": True,
                    "contains_payment_request": False,
                    "contains_deadline": False,
                    "contains_phone": True
                }
            }
        )
        
        with patch("app.features.feature_extractor.load_analysis", return_value=mock_meta):
            sample_media_msg = {
                "message_id": "m_media_test_2",
                "user_id": "u_001",
                "sender_user_id": "u_002",
                "media_id": "img_001",
                "media_type": "image",
                "created_at": "2026-08-01 12:00:00"
            }
            # Temporarily register dummy image in image_lookup
            self.context.image_lookup["img_001"] = "media/images/img_001.jpg"
            
            features = extract_features(sample_media_msg, self.context)
            self.assertTrue(features.media.has_qr)
            self.assertTrue(features.media.contains_phone)
            self.assertFalse(features.media.has_payment_request)

if __name__ == "__main__":
    unittest.main()
