import logging
import pandas as pd
from typing import List, Dict, Any

from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.routing.routing_service import RoutingService
from app.evaluation.metrics import EvaluationReport
from app.evaluation.confusion_matrix import compute_metrics, print_evaluation_report

logger = logging.getLogger("evaluator")

class DatasetEvaluator:
    """
    Evaluator engine comparing real routing service predictions
    against Ground Truth labeled data configurations (sample_messages.csv).
    """
    def __init__(self, routing_service: RoutingService = None):
        self.service = routing_service or RoutingService()

    def evaluate_dataset(self, sample_messages_path: str = None) -> EvaluationReport:
        datasets = load_all_datasets()
        context = build_extraction_context(datasets)
        
        # Load targets Ground Truth sample messages
        if sample_messages_path and os.path.exists(sample_messages_path):
            sample_df = pd.read_csv(sample_messages_path)
        else:
            sample_df = datasets["sample_messages"]
            
        print(f"Loaded {len(sample_df)} target ground-truth records for evaluation.")
        
        predictions = []
        ground_truth = []
        
        # Rule statistics tracking map: {rule_id: {"fired": int, "correct": int}}
        rule_stats = {}
        
        for _, row in sample_df.iterrows():
            raw_msg = row.to_dict()
            # Standard labels expected inside sample_messages.csv:
            # action -> ground truth value
            expected_action = str(raw_msg.get("action", "")).strip().lower()
            if not expected_action or expected_action == "nan":
                continue
                
            # Execute processing
            result = self.service.process_message(raw_msg, context)
            if not result.success or not result.routing_result:
                # Fallback digest default action on boundaries failures
                predicted_action = "digest"
                applied_rules = []
            else:
                predicted_action = result.routing_result.decision.action.value.strip().lower()
                applied_rules = result.routing_result.decision.applied_rules
                
            predictions.append(predicted_action)
            ground_truth.append(expected_action)
            
            # Populate rule firing stats
            is_correct = (predicted_action == expected_action)
            for rule_id in applied_rules:
                if rule_id not in rule_stats:
                    rule_stats[rule_id] = {"fired": 0, "correct": 0}
                rule_stats[rule_id]["fired"] += 1
                if is_correct:
                    rule_stats[rule_id]["correct"] += 1
            
        report = compute_metrics(predictions, ground_truth)
        
        # Print Rule Coverage Report
        print("\n" + "="*50)
        print(" RULE COVERAGE REPORT")
        print("="*50)
        print(f"{'Rule ID':<30} | {'Fired':<6} | {'Correct':<8} | {'Incorrect':<9}")
        print("-"*50)
        for r_id, stats in sorted(rule_stats.items(), key=lambda x: -x[1]["fired"]):
            incorrect = stats["fired"] - stats["correct"]
            print(f"{r_id:<30} | {stats['fired']:<6} | {stats['correct']:<8} | {incorrect:<9}")
        print("="*50 + "\n")
        
        # Baseline Comparison telemetry printout
        # Previous Baseline is 46.7% accuracy
        print("="*50)
        print(" RUN COMPARISON VS BASELINE")
        print("="*50)
        print(f"  Current Accuracy:  {report.accuracy*100:.1f}%")
        print(f"  Previous Best:     46.7%")
        delta = (report.accuracy - 0.467) * 100.0
        sign = "+" if delta >= 0 else ""
        print(f"  Delta:             {sign}{delta:.1f}%")
        print("="*50 + "\n")
        
        return report

if __name__ == "__main__":
    import os
    evaluator = DatasetEvaluator()
    report = evaluator.evaluate_dataset()
    print_evaluation_report(report)
