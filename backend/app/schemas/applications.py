from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field

from backend.app.schemas.common import BaseSchema


class ApplicationBase(BaseSchema):
    reference_no: str
    institution_id: uuid.UUID
    route_type_id: uuid.UUID
    route_version: int
    current_stage_id: Optional[uuid.UUID] = None
    status: str = "in_progress"
    assigned_to_user_id: Optional[uuid.UUID] = None


class ApplicationResponse(ApplicationBase):
    id: uuid.UUID
    submitted_at: Optional[datetime] = None
    stage_entered_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AdvanceStageRequest(BaseModel):
    action: str = Field("advance", description="Action name e.g. advance")
    comments: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ReturnStageRequest(BaseModel):
    action: str = Field("return", description="Action name e.g. return")
    reason: str = Field(..., min_length=5, description="Mandatory reason for returning application")
    target_stage_id: Optional[uuid.UUID] = None
    metadata: Optional[Dict[str, Any]] = None
