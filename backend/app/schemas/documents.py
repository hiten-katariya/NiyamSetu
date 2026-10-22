from datetime import date, datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from backend.app.schemas.common import BaseSchema


class DocumentRenewalResponse(BaseSchema):
    id: uuid.UUID
    document_id: uuid.UUID
    renewal_due_date: date
    status: str
    replacement_document_id: Optional[uuid.UUID] = None
    replacement_filename: Optional[str] = None
    reviewed_by_user_id: Optional[uuid.UUID] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class DocumentResponse(BaseSchema):
    id: uuid.UUID
    institution_id: uuid.UUID
    institution_name: Optional[str] = None
    application_id: Optional[uuid.UUID] = None
    application_number: Optional[str] = None
    document_type: str
    original_filename: str
    size_bytes: int
    mime_type: str
    checksum: str
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_expired: bool = False
    is_expiring_soon: bool = False
    verification_status: str
    verified_by_user_id: Optional[uuid.UUID] = None
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    renewals: List[DocumentRenewalResponse] = []


class VerifyDocumentRequest(BaseModel):
    decision: str = Field(..., pattern="^(verified|rejected|correction_requested)$")
    review_comments: str = Field(..., min_length=5, max_length=2000)


class CreateRenewalRequest(BaseModel):
    renewal_due_date: date
