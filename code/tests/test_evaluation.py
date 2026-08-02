import sys
import os
import unittest

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.evaluation.confusion_matrix import compute_metrics
from app.evaluation.evaluator import DatasetEvaluator

class TestEvaluationFramework(unittest.TestCase):

    def test_metrics_calculation(self):
        predictions = ["notify", "notify", "digest", "mute"]
        ground_truth = ["notify", "digest", "digest", "mute"]
        
        report = compute_metrics(predictions, ground_truth)
        self.assertEqual(report.accuracy, 0.75)
        self.assertEqual(report.per_class_metrics["mute"].precision, 1.0)
        self.assertEqual(report.per_class_metrics["digest"].recall, 0.5)
        self.assertEqual(report.confusion_matrix["notify"]["notify"], 1)

    def test_evaluator_runs_on_samples(self):
        evaluator = DatasetEvaluator()
        report = evaluator.evaluate_dataset()
        self.assertGreater(report.accuracy, 0.0)
        self.assertIn("digest", report.per_class_metrics)

if __name__ == "__main__":
    unittest.main()
