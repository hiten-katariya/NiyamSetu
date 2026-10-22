from datetime import datetime
from typing import Optional
import uuid
from pydantic import Field
from backend.app.schemas.common import BaseSchema


class EscalationResponse(BaseSchema):
    id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    target_type: str
    target_id: uuid.UUID
    level: int
    assigned_to_user_id: Optional[uuid.UUID] = None
    assigned_to_name: Optional[str] = None
    status: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    application_number: Optional[str] = None
    institution_name: Optional[str] = None


class ResolveEscalationRequest(BaseSchema):
    resolution_notes: str = Field(..., min_length=3, max_length=2000, description="Detailed explanation of the resolution actions taken.")
