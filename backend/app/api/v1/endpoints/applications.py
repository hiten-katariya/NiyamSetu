from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import Application
from backend.app.schemas.applications import ApplicationResponse
from backend.app.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ApplicationResponse], summary="List Applications")
def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List applications with optional status filter and pagination.
    """
    stmt = select(Application)
    if status:
        stmt = stmt.where(Application.status == status)

    # For Phase 1 initial foundation: query database records
    offset = (page - 1) * page_size
    items = db.scalars(stmt.offset(offset).limit(page_size)).all()
    total = len(items)  # In Phase 1 foundation

    return {
        "data": items,
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=(total + page_size - 1) // page_size if total > 0 else 1,
        ),
    }
