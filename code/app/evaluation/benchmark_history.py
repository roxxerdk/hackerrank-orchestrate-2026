import json
import logging
from pathlib import Path
from pydantic import BaseModel, Field

from app.config import CACHE_DIR
from app.evaluation.metrics import EvaluationReport

logger = logging.getLogger("benchmark_history")

# Benchmark JSON path target
BENCHMARK_PATH = CACHE_DIR.parent / "benchmark_history.json"

class BenchmarkMetrics(BaseModel):
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float

def save_benchmark(report: EvaluationReport) -> None:
    payload = {
        "accuracy": report.accuracy,
        "macro_precision": report.macro_precision,
        "macro_recall": report.macro_recall,
        "macro_f1": report.macro_f1
    }
    
    try:
        with open(BENCHMARK_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info("Successfully updated baseline benchmark metrics targets inside JSON store")
    except Exception as e:
        logger.error("Failed to write baseline benchmark JSON properties: %s", e)

def load_benchmark() -> BenchmarkMetrics:
    if not BENCHMARK_PATH.exists():
        # Fallback default initial milestone metrics
        return BenchmarkMetrics(
            accuracy=0.467,
            macro_precision=0.514,
            macro_recall=0.443,
            macro_f1=0.415
        )
    try:
        with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return BenchmarkMetrics(**data)
    except Exception as e:
        logger.error("Failed to read baseline benchmark JSON: %s", e)
        return BenchmarkMetrics(accuracy=0.467, macro_precision=0.514, macro_recall=0.443, macro_f1=0.415)
