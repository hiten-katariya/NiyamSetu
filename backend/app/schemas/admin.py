from datetime import date, datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field

from backend.app.schemas.common import BaseSchema


class RouteStageSchema(BaseSchema):
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


class RouteTypeSchema(BaseSchema):
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    current_version: int
    stages: List[RouteStageSchema] = Field(default_factory=list)


class StageUpdateRequest(BaseModel):
    stage_name: Optional[str] = None
    timeline_days: Optional[int] = Field(None, ge=1, le=365)
    day_type: Optional[str] = None  # working_days, calendar_days
    required_role: Optional[str] = None
    is_required: Optional[bool] = None
    change_reason: str = Field(..., min_length=3, description="Mandatory justification for configuration change")


class StageCreateRequest(BaseModel):
    stage_code: str = Field(..., min_length=2, max_length=50)
    stage_name: str = Field(..., min_length=2, max_length=100)
    sequence: int = Field(..., ge=1)
    timeline_days: int = Field(..., ge=1, le=365)
    day_type: str = Field("working_days", pattern="^(working_days|calendar_days)$")
    required_role: str
    is_required: bool = True
    change_reason: str = Field(..., min_length=3, description="Mandatory justification for stage addition")


class ReminderRuleSchema(BaseSchema):
    id: uuid.UUID
    name: str
    target_type: str
    days_before_due: int
    recipient_roles: List[str]
    is_active: bool


class ReminderRuleCreateUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    target_type: str = Field("application", pattern="^(application|undertaking|document)$")
    days_before_due: int = Field(..., ge=0, le=365)
    recipient_roles: List[str] = Field(default_factory=list)
    is_active: bool = True
    change_reason: str = Field(..., min_length=3, description="Mandatory justification for rule change")


class EscalationRuleSchema(BaseSchema):
    id: uuid.UUID
    name: str
    target_type: str
    level: int
    days_after_due: int
    recipient_roles: List[str]
    is_active: bool


class EscalationRuleCreateUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    target_type: str = Field("application", pattern="^(application|undertaking|document)$")
    level: int = Field(..., ge=1, le=5)
    days_after_due: int = Field(..., ge=0, le=365)
    recipient_roles: List[str] = Field(default_factory=list)
    is_active: bool = True
    change_reason: str = Field(..., min_length=3, description="Mandatory justification for rule change")


class HolidaySchema(BaseSchema):
    id: uuid.UUID
    region_id: Optional[uuid.UUID] = None
    holiday_date: date
    name: str
    created_at: datetime


class HolidayCreateRequest(BaseModel):
    region_id: Optional[uuid.UUID] = None
    holiday_date: date
    name: str = Field(..., min_length=2)
    change_reason: str = Field(..., min_length=3, description="Mandatory justification for holiday entry")


class MessageTemplateSchema(BaseSchema):
    id: uuid.UUID
    code: str
    channel: str
    subject_template: str
    body_template: str
    is_active: bool
    updated_at: datetime


class MessageTemplateUpdateRequest(BaseModel):
    subject_template: str = Field(..., min_length=2)
    body_template: str = Field(..., min_length=5)
    is_active: bool = True
    change_reason: str = Field(..., min_length=3, description="Mandatory justification for template change")


class ConfigVersionSchema(BaseSchema):
    id: uuid.UUID
    config_type: str
    version: int
    changed_by_user_id: Optional[uuid.UUID] = None
    change_summary: str
    created_at: datetime
