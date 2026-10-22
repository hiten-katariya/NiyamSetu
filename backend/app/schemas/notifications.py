from datetime import datetime
from typing import Optional
import uuid
from backend.app.schemas.common import BaseSchema


class NotificationResponse(BaseSchema):
    id: uuid.UUID
    recipient_user_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    target_type: str
    target_id: uuid.UUID
    channel: str
    title: str
    body: str
    status: str
    sent_at: datetime
    read_at: Optional[datetime] = None
    created_at: datetime
