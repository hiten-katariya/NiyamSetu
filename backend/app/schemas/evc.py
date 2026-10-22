from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from backend.app.schemas.common import BaseSchema


class EVCMemberSchema(BaseSchema):
    id: uuid.UUID
    evc_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    member_name: str
    member_role: str
    created_at: datetime


class EVCMemberAssignItem(BaseModel):
    user_id: Optional[uuid.UUID] = None
    member_name: str = Field(..., min_length=2, max_length=150)
    member_role: str = Field(..., pattern="^(chairman|expert|convenor|member)$")


class AssignEVCMembersRequest(BaseModel):
    members: List[EVCMemberAssignItem] = Field(..., min_length=1)


class ScheduleEVCRequest(BaseModel):
    scheduled_at: datetime
    notes: Optional[str] = None
    reason: Optional[str] = Field(None, description="Mandatory when rescheduling an existing scheduled date.")


class ConductEVCRequest(BaseModel):
    conducted_at: Optional[datetime] = None
    notes: Optional[str] = None


class ReviewEVCReportRequest(BaseModel):
    decision: str = Field(..., pattern="^(accepted|returned_for_correction)$")
    review_comments: str = Field(..., min_length=5, max_length=2000)


class EVCReportResponse(BaseSchema):
    id: uuid.UUID
    evc_id: uuid.UUID
    file_id: uuid.UUID
    original_filename: Optional[str] = None
    submitted_by_user_id: uuid.UUID
    submitted_by_name: Optional[str] = None
    submitted_at: datetime
    review_status: str
    reviewed_by_user_id: Optional[uuid.UUID] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comments: Optional[str] = None


class EVCResponse(BaseSchema):
    id: uuid.UUID
    application_id: uuid.UUID
    application_number: Optional[str] = None
    institution_name: Optional[str] = None
    status: str
    scheduled_at: Optional[datetime] = None
    due_by: Optional[datetime] = None
    conducted_at: Optional[datetime] = None
    report_due_by: Optional[datetime] = None
    report_submitted_at: Optional[datetime] = None
    assigned_region_id: Optional[uuid.UUID] = None
    assigned_region_name: Optional[str] = None
    notes: Optional[str] = None
    members: List[EVCMemberSchema] = []
    reports: List[EVCReportResponse] = []
    created_at: datetime
    updated_at: datetime


class CreateEVCRequest(BaseModel):
    application_id: uuid.UUID
    due_by: Optional[datetime] = None
    notes: Optional[str] = None
