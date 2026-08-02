import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.loaders.csv_loader import load_all_datasets
from app.features.feature_context import build_extraction_context
from app.routing.routing_service import RoutingService
from app.config import CACHE_DIR
import app.api.dependencies as deps

logger = logging.getLogger("lifespan")

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    FastAPI Lifespan handler executing startup loaded parameters sweeps.
    Ensures datasets and context are initialized once.
    """
    logger.info("Initializing application startup lifespan context...")
    
    # 1. Load datasets & build global contexts
    deps.app_datasets = load_all_datasets()
    deps.app_feature_context = build_extraction_context(deps.app_datasets)
    
    # 2. Instantiate unified routing service
    deps.app_routing_service = RoutingService()
    
    # 3. Verify target directories exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR.parent / "results").mkdir(parents=True, exist_ok=True)
    
    logger.info("Lifespan setup completed successfully.")
    
    yield
    
    logger.info("Cleaning up application lifespan boundaries...")
    # Add any resource teardown actions here if necessary
