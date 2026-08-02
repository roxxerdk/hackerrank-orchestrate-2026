import pandas as pd
from pathlib import Path
from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.routing.routing_service import RoutingService
from app.output.output_generator import classify_message_type, generate_reason, find_evidence_message_ids
from app.config import DATASET_DIR

def run_submission_generator():
    print("="*60)
    print(" EXECUTING SUBMISSION OUTPUT GENERATOR FOR dataset/output.csv")
    print("="*60)
    
    datasets = load_all_datasets()
    context = build_extraction_context(datasets)
    service = RoutingService()
    
    messages_df = datasets["messages"]
    rows = []
    
    for _, row in messages_df.iterrows():
        msg_dict = row.to_dict()
        message_id = str(msg_dict.get("message_id", ""))
        
        # 1. Process routing result
        result = service.process_message(msg_dict, context)
        if result.success and result.routing_result:
            rr = result.routing_result
            action = rr.decision.action.value
            confidence = rr.decision.confidence
            applied_rules = rr.decision.applied_rules
            
            # Extract features for classifier mapping
            has_qr = rr.reasoning_context.media.has_qr
            has_pay = rr.reasoning_context.media.has_payment_request
            is_fwd = rr.reasoning_context.message.is_mass_forwarded
            
            is_scam = "scam" in applied_rules or any("scam" in r.lower() for r in applied_rules)
            is_spam = "spam" in applied_rules or any("spam" in r.lower() for r in applied_rules)
            
            sender_is_known = rr.reasoning_context.relationship.sender_is_known
            sender_is_frequent = rr.reasoning_context.relationship.sender_is_frequent_contact
            is_business = rr.reasoning_context.relationship.sender_is_business
            
            # Map action type parameters
            m_type = classify_message_type(
                message_text=msg_dict.get("message_text", ""),
                media_type=str(msg_dict.get("media_type", "")),
                media_has_qr=has_qr,
                media_has_payment=has_pay,
                is_forwarded=is_fwd,
                is_spam=is_spam,
                is_scam=is_scam,
                is_personal=not is_business,
                is_business=is_business,
                is_dnd=rr.reasoning_context.user.in_dnd
            )
            
            reason_str = generate_reason(
                action=action,
                message_type=m_type,
                applied_rules=applied_rules,
                sender_is_known=sender_is_known,
                sender_is_frequent=sender_is_frequent,
                is_group=(msg_dict.get("conversation_type") == "group"),
                is_muted=rr.reasoning_context.group.is_muted
            )
            
            evidence_str = find_evidence_message_ids(
                user_id=str(msg_dict.get("user_id")),
                sender_id=str(msg_dict.get("sender_user_id")),
                message_text=str(msg_dict.get("message_text", "")),
                datasets=datasets
            )
        else:
            action = "digest"
            m_type = "unknown"
            reason_str = "Fallback digest route assigned."
            confidence = 0.50
            evidence_str = "none"
            
        rows.append({
            "message_id": message_id,
            "action": action,
            "message_type": m_type,
            "reason": reason_str,
            "confidence": round(confidence, 2),
            "evidence_message_ids": evidence_str
        })
        
    # Write to target submission CSV path
    output_df = pd.DataFrame(rows)
    target_path = DATASET_DIR / "output.csv"
    output_df.to_csv(target_path, index=False)
    print(f"\n[Success] Submission saved to: {target_path} | Total rows written: {len(output_df)}")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_submission_generator()
