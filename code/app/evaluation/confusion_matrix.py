from typing import List, Dict
from app.evaluation.metrics import ClassMetrics, EvaluationReport

def compute_metrics(
    predictions: List[str],
    ground_truth: List[str]
) -> EvaluationReport:
    """
    Computes accuracy, per-class precision, recall, f1, and support.
    Accepts raw prediction actions and targets ground truth arrays.
    """
    if not predictions or not ground_truth or len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truths must be non-empty and matching size.")
        
    total = len(predictions)
    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    accuracy = correct / total
    
    # Establish distinct classification classes
    classes = sorted(list(set(ground_truth + predictions)))
    
    per_class = {}
    for c in classes:
        tp = sum(1 for p, g in zip(predictions, ground_truth) if p == c and g == c)
        fp = sum(1 for p, g in zip(predictions, ground_truth) if p == c and g != c)
        fn = sum(1 for p, g in zip(predictions, ground_truth) if p != c and g == c)
        support = sum(1 for g in ground_truth if g == c)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        per_class[c] = ClassMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            support=support
        )
        
    # Calculate macro-averaged statistics
    macro_precision = sum(m.precision for m in per_class.values()) / len(per_class) if per_class else 0.0
    macro_recall = sum(m.recall for m in per_class.values()) / len(per_class) if per_class else 0.0
    macro_f1 = sum(m.f1_score for m in per_class.values()) / len(per_class) if per_class else 0.0
        
    # Build Confusion Matrix mapping Dict[true_label, Dict[pred_label, count]]
    matrix = {true_c: {pred_c: 0 for pred_c in classes} for true_c in classes}
    for p, g in zip(predictions, ground_truth):
        matrix[g][p] += 1
        
    return EvaluationReport(
        accuracy=accuracy,
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        per_class_metrics=per_class,
        confusion_matrix=matrix
    )

def print_evaluation_report(report: EvaluationReport) -> None:
    """Prints a beautiful summary report formatted to stdout."""
    print("\n" + "="*50)
    print(f" PIPELINE PERFORMANCE EVALUATION REPORT")
    print("="*50)
    print(f"  Accuracy:        {report.accuracy*100:.1f}%")
    print(f"  Macro Precision: {report.macro_precision*100:.1f}%")
    print(f"  Macro Recall:    {report.macro_recall*100:.1f}%")
    print(f"  Macro F1-Score:  {report.macro_f1*100:.1f}%")
    print("="*50)
    print(f"{'Class':<12} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | Support")
    print("-"*50)
    for cls, m in report.per_class_metrics.items():
        print(f"{cls:<12} | {m.precision*100:>8.1f}% | {m.recall*100:>8.1f}% | {m.f1_score*100:>8.1f}% | {m.support}")
    print("="*50)
    print(" CONFUSION MATRIX (True Label vs Predicted)")
    print("-"*50)
    classes = sorted(report.confusion_matrix.keys())
    print("True \\ Pred  | " + " | ".join(f"{c:<8}" for c in classes))
    print("-"*50)
    for true_c in classes:
        row_str = " | ".join(f"{report.confusion_matrix[true_c][pred_c]:>8}" for pred_c in classes)
        print(f"{true_c:<12} | {row_str}")
    print("="*50 + "\n")
