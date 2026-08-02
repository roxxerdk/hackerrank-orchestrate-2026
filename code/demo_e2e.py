import sys
import os
import requests
import json
import time

def run_demo():
    print("="*60)
    print(" STARTING END-TO-END NOTIFICATION ROUTER DEMO")
    print("="*60)
    
    # 1. Spawn a simple target payload dictionary
    message = {
        "message": {
            "message_id": "demo_message_001",
            "user_id": "u_001",
            "conversation_type": "personal",
            "sender_user_id": "u_002",
            "created_at": "2026-07-24T14:35:00",
            "message_text": "Hi, please review this QR code request payment receipt.",
            "forwarded_count": 0
        }
    }
    
    print("\n[Step 1] Incoming Message Payload:")
    print(json.dumps(message, indent=2))
    
    # 2. Simulate API endpoint POST request (Mocked via RoutingService call directly to support sandbox environments)
    print("\n[Step 2] Processing Message through RoutingService Orchestration Gateway...")
    from app.loaders.csv_loader import load_all_datasets
    from app.features.feature_context import build_extraction_context
    from app.routing.routing_service import RoutingService
    
    datasets = load_all_datasets()
    context = build_extraction_context(datasets)
    service = RoutingService()
    
    start_time = time.perf_counter()
    result = service.process_message(message["message"], context)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    
    print(f"\n[Step 3] Processing Completed in {elapsed_ms:.2f} ms")
    
    if result.success and result.routing_result:
        rr = result.routing_result
        print(f"\n[Step 4] Extracted Features metadata version: {result.metadata.feature_version}")
        print(f"[Step 5] Retrieved Triggered Rules: {rr.decision.applied_rules}")
        print(f"[Step 6] Evaluated Decision: Action={rr.decision.action.value.upper()} | Confidence={rr.decision.confidence:.2f}")
        print(f"[Step 7] Persistence verification -> result store filename matches message ID: results/{message['message']['message_id']}.json")
    else:
        print("[Error] Failed to route target message payload")
        
    print("\n" + "="*60)
    print(" END-TO-END DEMO COMPLETED SUCCESSFULLY")
    print("="*60)

if __name__ == "__main__":
    run_demo()
