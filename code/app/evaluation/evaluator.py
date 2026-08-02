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
        misclassifications = []
        
        from app.evaluation.error_analysis import MisclassificationRecord
        
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
                rationale = []
                confidence = 0.5
            else:
                predicted_action = result.routing_result.decision.action.value.strip().lower()
                applied_rules = result.routing_result.decision.applied_rules
                rationale = result.routing_result.decision.rationale
                confidence = result.routing_result.decision.confidence
                
            predictions.append(predicted_action)
            ground_truth.append(expected_action)
            
            # Populate rule firing stats
            is_correct = (predicted_action == expected_action)
            if not is_correct:
                misclassifications.append(
                    MisclassificationRecord(
                        message_id=str(raw_msg.get("message_id", "unknown")),
                        expected_action=expected_action,
                        predicted_action=predicted_action,
                        confidence=confidence,
                        applied_rules=applied_rules,
                        rationale=rationale,
                        message_type=str(raw_msg.get("media_type", "text"))
                    )
                )
            for rule_id in applied_rules:
                if rule_id not in rule_stats:
                    rule_stats[rule_id] = {"fired": 0, "correct": 0}
                rule_stats[rule_id]["fired"] += 1
                if is_correct:
                    rule_stats[rule_id]["correct"] += 1
            
        report = compute_metrics(predictions, ground_truth)
        
        # 1. Print Rule Coverage & Precision Dashboard
        from app.evaluation.rule_dashboard import print_rule_dashboard
        print_rule_dashboard(rule_stats)
        
        # 2. Print Error Analysis Report
        from app.evaluation.error_analysis import print_error_report
        print_error_report(misclassifications)
        
        # 3. Baseline Comparison & Regression checks
        from app.evaluation.benchmark_history import load_benchmark, save_benchmark
        prev_best = load_benchmark()
        
        print("="*50)
        print(" RUN COMPARISON VS HISTORICAL BASELINE")
        print("="*50)
        print(f"  Current Accuracy:  {report.accuracy*100:.1f}% (Prev Best: {prev_best.accuracy*100:.1f}%)")
        print(f"  Current Macro F1:  {report.macro_f1*100:.1f}% (Prev Best: {prev_best.macro_f1*100:.1f}%)")
        
        acc_delta = (report.accuracy - prev_best.accuracy) * 100.0
        f1_delta = (report.macro_f1 - prev_best.macro_f1) * 100.0
        
        print(f"  Accuracy Delta:    {'+' if acc_delta >= 0 else ''}{acc_delta:.1f}%")
        print(f"  Macro F1 Delta:    {'+' if f1_delta >= 0 else ''}{f1_delta:.1f}%")
        print("="*50 + "\n")
        
        # Fail the pipeline loop if metrics regress beyond acceptable tolerance bounds (e.g. -5%)
        TOLERANCE_BOUND = -0.05
        if (report.accuracy - prev_best.accuracy) < TOLERANCE_BOUND:
            raise ValueError(f"Regression Check Failed: Accuracy dropped significantly (Delta: {acc_delta:.1f}%)")
            
        # Update benchmark store on improvements
        if report.accuracy >= prev_best.accuracy:
            save_benchmark(report)
        
        return report

if __name__ == "__main__":
    import os
    evaluator = DatasetEvaluator()
    report = evaluator.evaluate_dataset()
    print_evaluation_report(report)
