import logging
import copy
from typing import Dict, Any, List

from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.routing.routing_service import RoutingService
from app.evaluation.tuning_config import tuning_config, RuleCalibrationConfig
from app.evaluation.metrics import EvaluationReport
from app.evaluation.confusion_matrix import compute_metrics
from app.reasoning.rule_repository import RULES

logger = logging.getLogger("threshold_optimizer")

def run_grid_search() -> RuleCalibrationConfig:
    """
    Executes a grid search sweep across NOTIFY and DIGEST thresholds.
    Finds the parameters maximizing the Macro F1 score on sample_messages.csv.
    """
    print("\n" + "="*50)
    print(" EXECUTING PARAMETERS THRESHOLDS GRID SEARCH")
    print("="*50)
    
    datasets = load_all_datasets()
    context = build_extraction_context(datasets)
    sample_df = datasets["sample_messages"]
    
    # 1. Precompute routing features to avoid redundant loops
    features_list = []
    ground_truth = []
    
    service = RoutingService()
    for _, row in sample_df.iterrows():
        raw_msg = row.to_dict()
        expected_action = str(raw_msg.get("action", "")).strip().lower()
        if not expected_action or expected_action == "nan":
            continue
            
        features = service.extractor_fn(raw_msg, context)
        features_list.append((raw_msg.get("message_id", "unknown"), features))
        ground_truth.append(expected_action)
        
    # Grid parameters definition
    notify_thresholds = [0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]
    digest_thresholds = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
    
    best_f1 = -1.0
    best_notify = 0.65
    best_digest = 0.45
    
    # Simple simulator logic mapping routing thresholds decisions
    # If winning weight recommendation is NOTIFY but confidence < notify_threshold, we downgrade to DIGEST.
    # If recommended action is DIGEST but confidence < digest_threshold, we downgrade to MUTE.
    # We resolve evaluated decision schemas internally to simulate different options quickly.
    
    from app.reasoning.retrieval_engine import retrieve_rules
    from app.reasoning.reasoning_engine import evaluate_decision
    
    for nt in notify_thresholds:
        for dt in digest_thresholds:
            if dt >= nt:
                continue
                
            predictions = []
            for msg_id, features in features_list:
                # Mock evaluation context builder pipelines
                from app.reasoning.context_builder import build_reasoning_context
                res_ctx = build_reasoning_context(features)
                evidence = retrieve_rules(res_ctx)
                decision = evaluate_decision(res_ctx, evidence)
                
                # Apply dynamic threshold mapping calibrations
                action = decision.action
                confidence = decision.confidence
                
                if action.value == "notify" and confidence < nt:
                    action_str = "digest"
                    confidence = 0.50 # Fallback baseline
                elif action.value == "digest" and confidence < dt:
                    action_str = "mute"
                else:
                    action_str = action.value
                    
                predictions.append(action_str)
                
            report = compute_metrics(predictions, ground_truth)
            if report.macro_f1 > best_f1:
                best_f1 = report.macro_f1
                best_notify = nt
                best_digest = dt
                
    print(f"Optimal Thresholds Found -> Macro F1: {best_f1*100:.1f}%")
    print(f"  Notify Threshold: {best_notify}")
    print(f"  Digest Threshold: {best_digest}")
    print("="*50 + "\n")
    
    # Save parameters back inside active tuning config
    tuning_config.DECISION_NOTIFY_THRESHOLD = best_notify
    tuning_config.DECISION_DIGEST_THRESHOLD = best_digest
    
    return tuning_config

if __name__ == "__main__":
    run_grid_search()
