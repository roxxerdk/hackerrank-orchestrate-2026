from typing import List, Dict
from pydantic import BaseModel, Field

class RuleMetrics(BaseModel):
    rule_id: str
    fired: int = Field(0, ge=0)
    correct: int = Field(0, ge=0)
    incorrect: int = Field(0, ge=0)
    precision: float = Field(0.0, ge=0.0, le=1.0)

def print_rule_dashboard(rule_stats: Dict[str, Dict[str, int]]) -> None:
    """
    Computes rule precision dashboard tables.
    Flags weak (precision < 50%), rare (fired < 3), and dead rules.
    """
    print("\n" + "="*50)
    print(" RULE PRECISION DASHBOARD")
    print("="*50)
    print(f"{'Rule ID':<30} | {'Fired':<6} | {'Correct':<8} | {'Precision':<9}")
    print("-"*50)
    
    warnings = []
    
    for r_id, stats in sorted(rule_stats.items(), key=lambda x: -x[1]["fired"]):
        fired = stats["fired"]
        correct = stats["correct"]
        precision = correct / fired if fired > 0 else 0.0
        
        print(f"{r_id:<30} | {fired:<6} | {correct:<8} | {precision*100:>8.1f}%")
        
        # Analyze issues
        if fired > 0 and precision < 0.50:
            warnings.append(f"  [Warning] {r_id}: Low precision ({precision*100:.1f}%)")
        if 0 < fired < 3:
            warnings.append(f"  [Warning] {r_id}: Insufficient evidence (fired {fired} times)")
            
    if warnings:
        print("\n" + "-"*50)
        print(" DIAGNOSTIC WARNINGS")
        print("-"*50)
        for w in warnings:
            print(w)
            
    print("="*50 + "\n")
