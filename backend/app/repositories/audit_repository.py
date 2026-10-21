from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import AuditLog
from backend.app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self):
        super().__init__(AuditLog)

    def get_by_entity(self, db: Session, entity_type: str, entity_id: str) -> List[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.occurred_at.asc())
        )
        return list(db.scalars(stmt).all())

    def get_latest_entry(self, db: Session) -> Optional[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc()).limit(1)
        return db.scalars(stmt).first()


audit_repo = AuditRepository()
