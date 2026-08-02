from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.routing.schemas import RoutingServiceResult

class MessageModel(BaseModel):
    message_id: str = Field(..., description="Unique message identifier")
    user_id: str = Field(..., description="Recipient user identifier")
    conversation_type: str = Field("personal", description="Conversation mode (personal or group)")
    group_id: Optional[str] = Field(None, description="Optional target group channel ID")
    business_id: Optional[str] = Field(None, description="Optional target business sender ID")
    sender_user_id: str = Field(..., description="Sender contact identifier")
    created_at: str = Field(..., description="UTC ISO-8601 message timestamp string")
    message_text: Optional[str] = Field("", description="Plain text contents of the message request")
    media_type: Optional[str] = Field(None, description="Optional media format specifier (image or voice)")
    media_id: Optional[str] = Field(None, description="Optional target media cache lookup key")
    forwarded_count: int = Field(0, ge=0, description="Cumulative count of forwarding events")

class RouteRequest(BaseModel):
    message: MessageModel

class RouteResponse(BaseModel):
    result: RoutingServiceResult

class BatchRouteRequest(BaseModel):
    messages: List[MessageModel] = Field(..., description="Collection of messages to evaluate")

class BatchRouteResponse(BaseModel):
    results: List[RoutingServiceResult] = Field(..., description="Aggregated evaluated decisions outputs")

class HealthStatus(BaseModel):
    status: str = Field("OK")
    details: Optional[Dict[str, Any]] = None

class VersionInfo(BaseModel):
    pipeline_version: str = "1.0"
    feature_schema_version: str = "1.0"
    ruleset_version: str = "1.0"
    confidence_version: str = "1.0"
    api_version: str = "1.0"
