import time
import logging
from typing import Any, Callable
from app.features.feature_context import FeatureExtractionContext
from app.features.feature_extractor import extract_features
from app.reasoning.decision_service import evaluate_message
from app.routing.schemas import RoutingServiceResult, PipelineMetadata
from app.persistence.result_store import PersistenceBackend, JSONFilePersistenceBackend

from pydantic import ValidationError
from app.features.routing_features import FEATURE_SCHEMA_VERSION

logger = logging.getLogger("routing_service")

class RoutingService:
    """
    Centralized Application Routing Service orchestrating feature extraction,
    reasoning decision engines, confidence scoring, and result persistence.
    Exposes dependency injection endpoints.
    """
    def __init__(
        self,
        persistence_backend: PersistenceBackend = None,
        extractor_fn: Callable[[dict[str, Any], FeatureExtractionContext], Any] = extract_features,
        decision_fn: Callable[[Any], Any] = evaluate_message
    ):
        self.persistence = persistence_backend or JSONFilePersistenceBackend()
        self.extractor_fn = extractor_fn
        self.decision_fn = decision_fn

    def process_message(
        self,
        message: dict[str, Any],
        context: FeatureExtractionContext
    ) -> RoutingServiceResult:
        start_time = time.perf_counter()
        message_id = str(message.get("message_id", "unknown"))
        
        try:
            # 1. Feature Extraction
            features = self.extractor_fn(message, context)
            
            # 2. Decision Service Logic
            result = self.decision_fn(features)
            
            # 3. Persist Output Result
            self.persistence.save(message_id, result)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            
            metadata = PipelineMetadata(
                pipeline_version=result.metadata.pipeline_version,
                feature_version=FEATURE_SCHEMA_VERSION,
                ruleset_version=result.metadata.ruleset_version,
                confidence_version=result.metadata.confidence_version,
                elapsed_ms=elapsed_ms
            )
            
            logger.info(
                "Message %s successfully routed: Action=%s, Confidence=%.2f, Elapsed=%.1f ms",
                message_id,
                result.decision.action.value,
                result.confidence.final_confidence,
                elapsed_ms
            )
            
            return RoutingServiceResult(
                success=True,
                routing_result=result,
                error=None,
                metadata=metadata
            )
            
        except ValidationError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception("Pydantic validation error processing message: %s", message_id)
            return self._build_failure_result(str(e), elapsed_ms)
            
        except (IOError, OSError) as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception("I/O file storage error processing message: %s", message_id)
            return self._build_failure_result(str(e), elapsed_ms)
            
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception("Unexpected runtime execution error processing message: %s", message_id)
            return self._build_failure_result(str(e), elapsed_ms)

    def _build_failure_result(self, error_msg: str, elapsed_ms: float) -> RoutingServiceResult:
        metadata = PipelineMetadata(
            pipeline_version="1.0",
            feature_version=FEATURE_SCHEMA_VERSION,
            ruleset_version="1.0",
            confidence_version="1.0",
            elapsed_ms=elapsed_ms
        )
        return RoutingServiceResult(
            success=False,
            routing_result=None,
            error=error_msg,
            metadata=metadata
        )
