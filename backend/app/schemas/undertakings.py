from datetime import date, datetime
from typing import Any, List, Optional
import uuid
from pydantic import BaseModel, Field, field_validator, model_validator
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
    application_id: Optional[uuid.UUID] = None
    title: str = Field(..., min_length=2, max_length=200)
    condition_title: Optional[str] = None
    description: str = Field(..., min_length=2, max_length=2000)
    condition_description: Optional[str] = None
    due_date: date
    assigned_institution_id: Optional[uuid.UUID] = None
    institution_id: Optional[uuid.UUID] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Resolve title from condition_title
            t = str(data.get("title") or data.get("condition_title") or "").strip()
            data["title"] = t
            data["condition_title"] = t

            # Resolve description from condition_description or title fallback
            d = str(data.get("description") or data.get("condition_description") or t).strip()
            data["description"] = d
            data["condition_description"] = d

            # Resolve institution
            inst = data.get("assigned_institution_id") or data.get("institution_id")
            if inst:
                data["assigned_institution_id"] = inst
                data["institution_id"] = inst
        return data

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 2:
            raise ValueError("Condition Title must be at least 2 characters.")
        return s

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 2:
            raise ValueError("Condition Description must be at least 2 characters.")
        return s


class ReviewUndertakingRequest(BaseModel):
    decision: str = Field(..., pattern="^(accepted|rejected|returned)$")
    review_comments: str = Field(..., min_length=5, max_length=2000)
