from fastapi import FastAPI
from app.api.lifespan import app_lifespan
from app.api.routes import router
from app.api.exception_handlers import register_exception_handlers

# Scaffolding FastAPI Application
app = FastAPI(
    title="HackerRank Orchestrate API Service",
    description="WhatsApp Multimodal Notification Routing Reasoner API Gateway.",
    version="1.0.0",
    lifespan=app_lifespan
)

# Register exception boundaries mapping
register_exception_handlers(app)

# Include routes
app.include_router(router)
