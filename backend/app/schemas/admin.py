from datetime import datetime
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


class ReminderRuleSchema(BaseSchema):
    id: uuid.UUID
    name: str
    target_type: str
    days_before_due: int
    recipient_roles: List[str]
    is_active: bool


class EscalationRuleSchema(BaseSchema):
    id: uuid.UUID
    name: str
    target_type: str
    level: int
    days_after_due: int
    recipient_roles: List[str]
    is_active: bool
