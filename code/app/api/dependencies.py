from app.features.feature_context import FeatureExtractionContext
from app.routing.routing_service import RoutingService
from app.api.metrics_tracker import MetricsTracker

# Shared global lifespan application dependencies
app_datasets = None
app_feature_context = None
app_routing_service = None
app_metrics_tracker = MetricsTracker()

def get_routing_service() -> RoutingService:
    return app_routing_service

def get_feature_context() -> FeatureExtractionContext:
    return app_feature_context

def get_metrics_tracker() -> MetricsTracker:
    return app_metrics_tracker
