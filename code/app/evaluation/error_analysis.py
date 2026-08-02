from pydantic import BaseModel, Field
from typing import List
from app.reasoning.schemas import ActionType

class MisclassificationRecord(BaseModel):
    message_id: str
    expected_action: ActionType
    predicted_action: ActionType
    confidence: float
    applied_rules: List[str] = Field(default_factory=list)
    rationale: List[str] = Field(default_factory=list)
    message_type: str

def print_error_report(records: List[MisclassificationRecord]) -> None:
    """Computes and prints structured error analysis reports to stdout."""
    if not records:
        print("\n==========================================")
        print(" ERROR ANALYSIS: No misclassifications found!")
        print("==========================================\n")
        return
        
    print("\n" + "="*50)
    print(f" ERROR ANALYSIS REPORT ({len(records)} Misclassifications)")
    print("="*50)
    
    # 1. Group by mismatch transitions (e.g. Notify -> Digest)
    transitions = {}
    for r in records:
        key = f"{r.expected_action.value.upper()} -> {r.predicted_action.value.upper()}"
        if key not in transitions:
            transitions[key] = []
        transitions[key].append(r)
        
    for path, path_records in sorted(transitions.items(), key=lambda x: -len(x[1])):
        print(f"\n Mismatch transition: {path} ({len(path_records)} cases)")
        print("-" * 50)
        
        # Count rules contributing to this specific transition
        rule_counts = {}
        for r in path_records:
            for rule_id in r.applied_rules:
                rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
                
        print("  Top contributing rules:")
        for rule_id, count in sorted(rule_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"    {rule_id:<30} ...... {count}")
            
    # 2. Confidence distributions
    confidences = [r.confidence for r in records]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    print("\n" + "-"*50)
    print(f" Avg Confidence of Wrong Predictions: {avg_conf:.2f}")
    print("="*50 + "\n")
