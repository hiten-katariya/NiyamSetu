from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, verify_csrf_token
from backend.app.core.exceptions import NotFoundError
from backend.app.db.session import get_db
from backend.app.models.entities import Notification, User
from backend.app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from backend.app.schemas.notifications import NotificationResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[NotificationResponse], summary="List Notifications")
def list_notifications(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: unread, read"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns paginated notifications strictly scoped to the authenticated user.
    """
    stmt = (
        select(Notification)
        .where(Notification.recipient_user_id == current_user.id)
    )

    if status_filter:
        stmt = stmt.where(Notification.status == status_filter)

    total_items = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    total_pages = max(1, (total_items + limit - 1) // limit)
    offset = (page - 1) * limit

    notifications = list(
        db.scalars(
            stmt.order_by(Notification.sent_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )

    return {
        "data": [
            NotificationResponse.model_validate(n) for n in notifications
        ],
        "meta": PaginationMeta(
            page=page,
            page_size=limit,
            total=total_items,
            total_pages=total_pages,
        ),
    }


@router.get("/unread-count", response_model=DataResponse[dict], summary="Get Unread Notification Count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the total count of unread notifications for the authenticated user.
    """
    count = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.recipient_user_id == current_user.id,
            Notification.status == "unread",
        )
    ) or 0

    return {"data": {"unread_count": count}}


@router.post("/{notification_id}/read", response_model=DataResponse[NotificationResponse], summary="Mark Notification as Read")
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Marks a specific notification as read.
    """
    notif = db.get(Notification, notification_id)
    if not notif or notif.recipient_user_id != current_user.id:
        raise NotFoundError("Notification not found.")

    if notif.status != "read":
        notif.status = "read"
        notif.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notif)

    return {"data": NotificationResponse.model_validate(notif)}


@router.post("/read-all", response_model=DataResponse[dict], summary="Mark All Notifications as Read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Marks all unread notifications for the authenticated user as read.
    """
    now = datetime.now(timezone.utc)
    unread_notifs = list(
        db.scalars(
            select(Notification).where(
                Notification.recipient_user_id == current_user.id,
                Notification.status == "unread",
            )
        ).all()
    )

    for notif in unread_notifs:
        notif.status = "read"
        notif.read_at = now

    count = len(unread_notifs)
    if count > 0:
        db.commit()

    return {"data": {"marked_read": count}}
