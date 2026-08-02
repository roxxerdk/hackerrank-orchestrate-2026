import sys
import os
import unittest
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.routing.routing_service import RoutingService
from app.routing.schemas import RoutingServiceResult
from app.persistence.result_store import JSONFilePersistenceBackend

class TestRoutingServiceIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.datasets = load_all_datasets()
        cls.context = build_extraction_context(cls.datasets)
        cls.test_results_dir = Path("code/tests/scratch/routing_results_test")
        cls.test_results_dir.mkdir(parents=True, exist_ok=True)
        cls.backend = JSONFilePersistenceBackend(base_dir=cls.test_results_dir)
        cls.service = RoutingService(persistence_backend=cls.backend)

    @classmethod
    def tearDownClass(cls):
        if cls.test_results_dir.exists():
            shutil.rmtree(cls.test_results_dir)

    def test_routing_plain_personal_message(self):
        # Retrieve plain text message from dataset
        messages_df = self.datasets["messages"]
        raw_msg = messages_df[messages_df["conversation_type"] == "personal"].iloc[0].to_dict()
        
        result = self.service.process_message(raw_msg, self.context)
        self.assertTrue(result.success)
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.routing_result)
        
        # Verify JSON file was created
        expected_json = self.test_results_dir / f"{raw_msg['message_id']}.json"
        self.assertTrue(expected_json.exists())

    def test_central_error_boundary_on_extractor_failure(self):
        # Mock extractor function to throw value error
        mock_extractor = MagicMock(side_effect=ValueError("Bad extracted parameters"))
        err_service = RoutingService(
            persistence_backend=self.backend,
            extractor_fn=mock_extractor
        )
        
        raw_msg = {"message_id": "err_msg_test"}
        result = err_service.process_message(raw_msg, self.context)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Bad extracted parameters")
        self.assertIsNone(result.routing_result)

    def test_dependency_injection_persistence(self):
        mock_persistence = MagicMock()
        di_service = RoutingService(persistence_backend=mock_persistence)
        
        messages_df = self.datasets["messages"]
        raw_msg = messages_df.iloc[0].to_dict()
        
        result = di_service.process_message(raw_msg, self.context)
        self.assertTrue(result.success)
        # Verify custom save method was invoked once
        mock_persistence.save.assert_called_once()

    def test_routing_persistence_failure(self):
        # Mock persistence save to raise IOError to verify boundary captures it
        mock_persistence = MagicMock()
        mock_persistence.save.side_effect = IOError("Disk full or missing directory")
        
        err_service = RoutingService(persistence_backend=mock_persistence)
        messages_df = self.datasets["messages"]
        raw_msg = messages_df.iloc[0].to_dict()
        
        result = err_service.process_message(raw_msg, self.context)
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Disk full or missing directory")
        self.assertIsNone(result.routing_result)

if __name__ == "__main__":
    unittest.main()
