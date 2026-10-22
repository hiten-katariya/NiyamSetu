from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from backend.app.schemas.common import BaseSchema


class RouteStageResponse(BaseSchema):
    id: uuid.UUID
    route_type_id: uuid.UUID
    route_version: int
    stage_code: str
    stage_name: str
    sequence: int
    required_role: str
    timeline_days: int
    day_type: str
    is_required: bool


class RouteTypeResponse(BaseSchema):
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    current_version: int
    stages: List[RouteStageResponse] = []


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
    institution_name: Optional[str] = None
    institution_code: Optional[str] = None
    route_name: Optional[str] = None
    route_code: Optional[str] = None
    current_stage_name: Optional[str] = None
    current_stage_code: Optional[str] = None
    current_stage_role: Optional[str] = None
    current_stage_sequence: Optional[int] = None
    total_stages: Optional[int] = None
    assigned_to_name: Optional[str] = None
    submitted_at: Optional[datetime] = None
    stage_entered_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class StageHistoryResponse(BaseSchema):
    id: uuid.UUID
    application_id: uuid.UUID
    from_stage_id: Optional[uuid.UUID] = None
    from_stage_name: Optional[str] = None
    to_stage_id: Optional[uuid.UUID] = None
    to_stage_name: Optional[str] = None
    action: str
    reason: Optional[str] = None
    performed_by_user_id: uuid.UUID
    performed_by_name: Optional[str] = None
    performed_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class ApplicationDetailResponse(ApplicationResponse):
    stages: List[RouteStageResponse] = []
    history: List[StageHistoryResponse] = []
    available_actions: List[str] = []


class CreateApplicationRequest(BaseModel):
    route_type_id: uuid.UUID
    institution_id: Optional[uuid.UUID] = None


class AdvanceStageRequest(BaseModel):
    comments: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ReturnStageRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Mandatory reason for returning application")
    target_stage_id: Optional[uuid.UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class HoldStageRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Mandatory reason for placing application on hold")
    metadata: Optional[Dict[str, Any]] = None


class ResumeStageRequest(BaseModel):
    comments: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AssignApplicationRequest(BaseModel):
    target_user_id: uuid.UUID
    notes: Optional[str] = None
