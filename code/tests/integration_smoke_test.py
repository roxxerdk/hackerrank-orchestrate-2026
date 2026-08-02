import sys
import os
import json
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.features.feature_extractor import extract_features

def run_integration_check():
    print("--- Starting Milestone 4 Integration Check ---")
    datasets = load_all_datasets()
    context = build_extraction_context(datasets)
    
    messages_df = datasets["messages"]
    print(f"Total messages available for test: {len(messages_df)}")
    
    # 1. Identify representative messages from the dataset
    plain_text_msg = None
    image_msg = None
    voice_msg = None
    business_msg = None
    group_msg = None
    
    for _, row in messages_df.iterrows():
        msg = row.to_dict()
        conv_type = str(msg.get("conversation_type", ""))
        media_type = str(msg.get("media_type", ""))
        biz_id = str(msg.get("business_id", ""))
        
        if not plain_text_msg and (not media_type or media_type == "nan") and biz_id == "nan" and conv_type != "group":
            plain_text_msg = msg
        elif not image_msg and media_type.lower() == "image":
            image_msg = msg
        elif not voice_msg and media_type.lower() == "voice":
            voice_msg = msg
        elif not business_msg and biz_id != "nan":
            business_msg = msg
        elif not group_msg and conv_type.lower() == "group":
            group_msg = msg

    test_targets = {
        "Plain Text Message": plain_text_msg,
        "Image Message": image_msg,
        "Voice Message": voice_msg,
        "Business Message": business_msg,
        "Group Message": group_msg
    }

    # 2. Extract and print features for each target
    for label, msg in test_targets.items():
        print(f"\n==========================================")
        print(f" Target: {label}")
        print(f"==========================================")
        if not msg:
            print(" [Warning] No matching message found in datasets for this category.")
            continue
            
        print("Input Raw Message:", json.dumps({k: str(v) for k, v in msg.items()}))
        
        try:
            features = extract_features(msg, context)
            # Serialize the resulting RoutingFeatures using pydantic's model_dump_json
            serialized = features.model_dump_json(indent=2)
            print("\nExtracted RoutingFeatures:\n", serialized)
        except Exception as e:
            print(f" [ERROR] Feature extraction failed for {label}: {e}")
            raise e

    print("\n--- Milestone 4 Integration Check Completed Successfully ---")

if __name__ == "__main__":
    run_integration_check()
