import sys
import os
import unittest
from fastapi.testclient import TestClient

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.app import app
from app.loaders.csv_loader import load_all_datasets
import app.api.dependencies as deps

class TestAPIService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Force initialization of lifespan dependencies for test contexts
        from app.features.feature_context import build_extraction_context
        from app.routing.routing_service import RoutingService
        deps.app_datasets = load_all_datasets()
        deps.app_feature_context = build_extraction_context(deps.app_datasets)
        deps.app_routing_service = RoutingService()
        cls.client = TestClient(app)

    def test_health_live(self):
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")

    def test_health_ready(self):
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "READY")

    def test_version_parameters(self):
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["api_version"], "1.0")

    def test_route_message_success(self):
        # Create valid message payload matching CSV structure
        payload = {
            "message": {
                "message_id": "msg_api_test",
                "user_id": "u_001",
                "conversation_type": "personal",
                "sender_user_id": "u_002",
                "created_at": "2026-07-24T12:00:00",
                "message_text": "Hello, urgent payment request here.",
                "forwarded_count": 0
            }
        }
        response = self.client.post("/route", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["result"]["success"])

    def test_route_batch_messages(self):
        payload = {
            "messages": [
                {
                    "message_id": "msg_batch_1",
                    "user_id": "u_001",
                    "conversation_type": "personal",
                    "sender_user_id": "u_002",
                    "created_at": "2026-07-24T12:00:00",
                    "message_text": "Batch message number one.",
                    "forwarded_count": 0
                },
                {
                    "message_id": "msg_batch_2",
                    "user_id": "u_001",
                    "conversation_type": "personal",
                    "sender_user_id": "u_002",
                    "created_at": "2026-07-24T12:05:00",
                    "message_text": "Batch message number two.",
                    "forwarded_count": 0
                }
            ]
        }
        response = self.client.post("/route/batch", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 2)

    def test_metrics_collection_updates(self):
        # Check starting metric state
        response_init = self.client.get("/metrics")
        init_count = response_init.json()["messages_processed"]
        
        # Route one message
        payload = {
            "message": {
                "message_id": "msg_metric_test",
                "user_id": "u_001",
                "conversation_type": "personal",
                "sender_user_id": "u_002",
                "created_at": "2026-07-24T12:00:00",
                "message_text": "Audit logging metrics test.",
                "forwarded_count": 0
            }
        }
        self.client.post("/route", json=payload)
        
        response_post = self.client.get("/metrics")
        self.assertEqual(response_post.json()["messages_processed"], init_count + 1)

    def test_invalid_payload_error(self):
        # Send payload missing required message_id
        payload = {
            "message": {
                "user_id": "u_001",
                "sender_user_id": "u_002"
            }
        }
        response = self.client.post("/route", json=payload)
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main()
