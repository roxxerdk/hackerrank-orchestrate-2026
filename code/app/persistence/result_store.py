import json
import logging
from pathlib import Path
from typing import Any, Protocol
from app.reasoning.schemas import FinalRoutingResult
from app.config import CACHE_DIR

logger = logging.getLogger("result_store")

# Define base directory for results
RESULTS_DIR = CACHE_DIR.parent / "results"

class PersistenceBackend(Protocol):
    def save(self, message_id: str, result: FinalRoutingResult) -> None:
        """Saves a FinalRoutingResult to the persistence layer."""
        ...

class JSONFilePersistenceBackend:
    def __init__(self, base_dir: Path = RESULTS_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, message_id: str, result: FinalRoutingResult) -> None:
        file_path = self.base_dir / f"{message_id}.json"
        
        # Packaging schema
        from datetime import datetime, timezone
        payload = {
            "message_id": message_id,
            "action": result.decision.action.value,
            "confidence": result.confidence.final_confidence,
            "applied_rules": result.decision.applied_rules,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "versions": {
                "ruleset_version": result.metadata.ruleset_version,
                "confidence_version": result.metadata.confidence_version,
                "pipeline_version": result.metadata.pipeline_version
            }
        }
        
        # Write atomically via temp file rename
        temp_path = file_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            temp_path.replace(file_path)
            logger.info("Successfully persisted routing results to %s", file_path)
        except Exception as e:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            logger.error("Failed to persist routing results: %s", e)
            raise
