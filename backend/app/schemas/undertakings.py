from datetime import date, datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from backend.app.schemas.common import BaseSchema


class UndertakingSubmissionResponse(BaseSchema):
    id: uuid.UUID
    undertaking_id: uuid.UUID
    submitted_by_user_id: uuid.UUID
    submitted_by_name: Optional[str] = None
    file_id: uuid.UUID
    original_filename: Optional[str] = None
    comments: Optional[str] = None
    submitted_at: datetime
    review_status: str
    reviewed_by_user_id: Optional[uuid.UUID] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comments: Optional[str] = None


class UndertakingResponse(BaseSchema):
    id: uuid.UUID
    application_id: uuid.UUID
    application_number: Optional[str] = None
    institution_id: uuid.UUID
    institution_name: Optional[str] = None
    title: str
    description: str
    due_date: date
    status: str
    verified_by_user_id: Optional[uuid.UUID] = None
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    submissions: List[UndertakingSubmissionResponse] = []
    created_at: datetime
    updated_at: datetime


class CreateUndertakingRequest(BaseModel):
    application_id: uuid.UUID
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=2000)
    due_date: date
    assigned_institution_id: Optional[uuid.UUID] = None


class ReviewUndertakingRequest(BaseModel):
    decision: str = Field(..., pattern="^(accepted|rejected|returned)$")
    review_comments: str = Field(..., min_length=5, max_length=2000)
