from pydantic import BaseModel, Field
from typing import Optional
from app.reasoning.schemas import FinalRoutingResult

class PipelineMetadata(BaseModel):
    pipeline_version: str = Field("1.0")
    feature_version: str = Field("1.0")
    ruleset_version: str = Field("1.0")
    confidence_version: str = Field("1.0")
    elapsed_ms: float = Field(0.0, ge=0.0)

class RoutingServiceResult(BaseModel):
    success: bool = Field(..., description="Flag indicating if the orchestrator completed successfully")
    routing_result: Optional[FinalRoutingResult] = Field(None, description="Pipeline outputs payload")
    error: Optional[str] = Field(None, description="Detailed error description when failure occurs")
    metadata: PipelineMetadata = Field(default_factory=PipelineMetadata)
