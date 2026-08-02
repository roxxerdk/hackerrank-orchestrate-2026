import time
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.api.models import RouteRequest, RouteResponse, BatchRouteRequest, BatchRouteResponse, HealthStatus, VersionInfo
from app.api.dependencies import get_routing_service, get_feature_context, get_metrics_tracker
from app.routing.routing_service import RoutingService
from app.features.feature_context import FeatureExtractionContext
from app.api.metrics_tracker import MetricsTracker

router = APIRouter()

@router.post(
    "/route",
    response_model=RouteResponse,
    summary="Evaluate single message routing target",
    description="Executes full pipeline: maps context, parses cache, decides action & records metrics."
)
async def route_single_message(
    payload: RouteRequest,
    service: RoutingService = Depends(get_routing_service),
    context: FeatureExtractionContext = Depends(get_feature_context),
    tracker: MetricsTracker = Depends(get_metrics_tracker)
):
    start = time.perf_counter()
    msg_dict = payload.message.model_dump()
    
    result = service.process_message(msg_dict, context)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    if result.success and result.routing_result:
        tracker.record_route(
            action=result.routing_result.decision.action.value,
            latency_ms=elapsed_ms,
            feature_latency_ms=result.metadata.elapsed_ms * 0.8,  # Approximate distribution splits
            decision_latency_ms=result.metadata.elapsed_ms * 0.2,
            rules=result.routing_result.decision.applied_rules,
            media_hit=(result.routing_result.reasoning_context.media.media_file_size_bytes > 0)
        )
    return RouteResponse(result=result)

@router.post(
    "/route/batch",
    response_model=BatchRouteResponse,
    summary="Evaluate message collection batch parameters",
    description="Processes collection array using single initialized routing service mapping."
)
async def route_batch_messages(
    payload: BatchRouteRequest,
    service: RoutingService = Depends(get_routing_service),
    context: FeatureExtractionContext = Depends(get_feature_context),
    tracker: MetricsTracker = Depends(get_metrics_tracker)
):
    results = []
    for msg_model in payload.messages:
        start = time.perf_counter()
        msg_dict = msg_model.model_dump()
        result = service.process_message(msg_dict, context)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        
        if result.success and result.routing_result:
            tracker.record_route(
                action=result.routing_result.decision.action.value,
                latency_ms=elapsed_ms,
                feature_latency_ms=result.metadata.elapsed_ms * 0.8,
                decision_latency_ms=result.metadata.elapsed_ms * 0.2,
                rules=result.routing_result.decision.applied_rules,
                media_hit=(result.routing_result.reasoning_context.media.media_file_size_bytes > 0)
            )
        results.append(result)
    return BatchRouteResponse(results=results)

@router.get("/health/live", response_model=HealthStatus, summary="Liveness check endpoint")
async def health_liveness():
    return HealthStatus(status="OK")

@router.get("/health/ready", response_model=HealthStatus, summary="Readiness check endpoint")
async def health_readiness(
    service: RoutingService = Depends(get_routing_service),
    context: FeatureExtractionContext = Depends(get_feature_context)
):
    from app.config import CACHE_DIR
    if service is None or context is None or not CACHE_DIR.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dependencies initialization pending or cache path missing."
        )
    return HealthStatus(status="READY", details={"cache_path_ok": True, "context_loaded": True})

@router.get("/metrics", summary="Performance observation stats metrics")
async def metrics_summary(tracker: MetricsTracker = Depends(get_metrics_tracker)):
    return tracker.get_summary()

@router.get("/version", response_model=VersionInfo, summary="Pipeline specifications version parameters")
async def pipeline_version():
    from app.features.routing_features import FEATURE_SCHEMA_VERSION
    from app.reasoning.rule_repository import RULESET_VERSION
    return VersionInfo(
        pipeline_version="1.0",
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        ruleset_version=RULESET_VERSION,
        confidence_version="1.0",
        api_version="1.0"
    )
