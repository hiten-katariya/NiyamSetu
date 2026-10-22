from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel
from backend.app.schemas.common import BaseSchema


class AuditLogEntrySchema(BaseSchema):
    id: uuid.UUID
    actor_user_id: Optional[uuid.UUID] = None
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    occurred_at: datetime
    ip_address: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = None
    entry_hash: str


class AuditVerificationResponse(BaseModel):
    is_valid: bool
    verified_count: int
    error_message: Optional[str] = None
