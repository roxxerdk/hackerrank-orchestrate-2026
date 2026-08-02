import sys
import os
import time

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.features.feature_extractor import extract_features
from app.reasoning.decision_service import evaluate_message

def run_integration_check():
    print("==================================================")
    print("   END-TO-END PIPELINE PERFORMANCE & CACHE TEST   ")
    print("==================================================")
    
    datasets = load_all_datasets()
    
    start_ctx = time.perf_counter()
    context = build_extraction_context(datasets)
    elapsed_ctx = (time.perf_counter() - start_ctx) * 1000.0
    print(f"Context Construction: {elapsed_ctx:.2f} ms")
    
    messages_df = datasets["messages"]
    
    # Target message msg_005 contains media_id img_005 which matches our mock cache analysis
    raw_msg = messages_df[messages_df["message_id"] == "msg_005"].iloc[0].to_dict()
    print(f"\nProcessing Target Message: {raw_msg['message_id']} (media_id: {raw_msg['media_id']})")
    
    # 1. Feature Extraction
    start_feat = time.perf_counter()
    routing_features = extract_features(raw_msg, context)
    elapsed_feat = (time.perf_counter() - start_feat) * 1000.0
    print(f"Feature Extraction:  {elapsed_feat:.2f} ms")
    
    # Verify cached features populated correctly
    print("\n--- Extracted Media Features ---")
    print(f"  has_qr:                {routing_features.media.has_qr}")
    print(f"  contains_phone:        {routing_features.media.contains_phone}")
    print(f"  contains_deadline:     {routing_features.media.contains_deadline}")
    print(f"  media_file_size_bytes: {routing_features.media.media_file_size_bytes} bytes")
    
    # Asserts media cache was hit successfully
    assert routing_features.media.has_qr is True, "Cache Miss: has_qr should be True"
    assert routing_features.media.media_file_size_bytes == 88042, "Cache Miss: Size should match mock payload"
    
    # 2. Decision Service evaluation
    start_eval = time.perf_counter()
    result = evaluate_message(routing_features)
    elapsed_eval = (time.perf_counter() - start_eval) * 1000.0
    print(f"Orchestrated Decision: {elapsed_eval:.2f} ms")
    
    print("\n--- Pipeline Outputs Summary ---")
    print(f"  Action:             {result.decision.action.value}")
    print(f"  Final Confidence:   {result.confidence.final_confidence:.3f}")
    print(f"  Applied Rules:      {result.decision.applied_rules}")
    print(f"  Ruleset Version:    {result.metadata.ruleset_version}")
    print(f"  Confidence Version: {result.metadata.confidence_version}")
    print(f"  Pipeline Version:   {result.metadata.pipeline_version}")
    print("==================================================")
    print("[Success] All Integration Verification Targets Passed!")
    print("==================================================")

if __name__ == "__main__":
    run_integration_check()
