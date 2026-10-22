from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Fallback to JSON if JSONB is not supported (e.g. SQLite test environment)
JsonType = JSON().with_variant(JSONB, "postgresql")


class Region(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "regions"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    institutions: Mapped[List["Institution"]] = relationship("Institution", back_populates="region")


class Institution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "institutions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    region_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    region: Mapped["Region"] = relationship("Region", back_populates="institutions")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="institution")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="institution")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    region_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class RouteType(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "route_types"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    stages: Mapped[List["RouteStage"]] = relationship("RouteStage", back_populates="route_type", cascade="all, delete-orphan")


class RouteStage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "route_stages"

    route_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    route_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    stage_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    stage_name: Mapped[str] = mapped_column(String(150), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    required_role: Mapped[str] = mapped_column(String(50), nullable=False)
    timeline_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    day_type: Mapped[str] = mapped_column(String(20), default="calendar", nullable=False)  # "calendar" or "working"
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    route_type: Mapped["RouteType"] = relationship("RouteType", back_populates="stages")

    __table_args__ = (
        UniqueConstraint("route_type_id", "route_version", "stage_code", name="uq_route_version_stage_code"),
        UniqueConstraint("route_type_id", "route_version", "sequence", name="uq_route_version_sequence"),
        Index("ix_route_stages_lookup", "route_type_id", "route_version", "sequence"),
    )


class Application(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "applications"

    reference_no: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    route_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    route_version: Mapped[int] = mapped_column(Integer, nullable=False)
    current_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_stages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="in_progress", index=True, nullable=False)
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    stage_entered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped["Institution"] = relationship("Institution", back_populates="applications")
    route_type: Mapped["RouteType"] = relationship("RouteType")
    current_stage: Mapped[Optional["RouteStage"]] = relationship("RouteStage", foreign_keys=[current_stage_id])
    assigned_to_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_user_id])
    history: Mapped[List["StageHistory"]] = relationship("StageHistory", back_populates="application", order_by="StageHistory.performed_at.asc()")
    evcs: Mapped[List["EVC"]] = relationship("EVC", back_populates="application")
    undertakings: Mapped[List["Undertaking"]] = relationship("Undertaking", back_populates="application")


class StageHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "stage_history"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_stages.id", ondelete="SET NULL"), nullable=True
    )
    to_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_stages.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # advance, return, hold, resume
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JsonType, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="history")
    from_stage: Mapped[Optional["RouteStage"]] = relationship("RouteStage", foreign_keys=[from_stage_id])
    to_stage: Mapped[Optional["RouteStage"]] = relationship("RouteStage", foreign_keys=[to_stage_id])
    performed_by: Mapped["User"] = relationship("User", foreign_keys=[performed_by_user_id])


class FileRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "files"

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class EVC(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evcs"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True, nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    due_by: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    conducted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    report_due_by: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    report_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_region_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="evcs")
    members: Mapped[List["EVCMember"]] = relationship("EVCMember", back_populates="evc", cascade="all, delete-orphan")
    reports: Mapped[List["EVCReport"]] = relationship("EVCReport", back_populates="evc", cascade="all, delete-orphan")


class EVCMember(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "evc_members"

    evc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evcs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    member_name: Mapped[str] = mapped_column(String(150), nullable=False)
    member_role: Mapped[str] = mapped_column(String(50), nullable=False)  # chairman, expert, convenor
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    evc: Mapped["EVC"] = relationship("EVC", back_populates="members")


class EVCReport(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "evc_reports"

    evc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evcs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="RESTRICT"), nullable=False
    )
    submitted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    review_status: Mapped[str] = mapped_column(String(50), default="pending_review", nullable=False)
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evc: Mapped["EVC"] = relationship("EVC", back_populates="reports")


class Undertaking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "undertakings"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    assigned_institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    verified_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="undertakings")
    submissions: Mapped[List["UndertakingSubmission"]] = relationship(
        "UndertakingSubmission", back_populates="undertaking", cascade="all, delete-orphan"
    )


class UndertakingSubmission(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "undertaking_submissions"

    undertaking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("undertakings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submitted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="RESTRICT"), nullable=False
    )
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    review_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    undertaking: Mapped["Undertaking"] = relationship("Undertaking", back_populates="submissions")


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "documents"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    verified_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    institution: Mapped["Institution"] = relationship("Institution", back_populates="documents")
    renewals: Mapped[List["DocumentRenewal"]] = relationship(
        "DocumentRenewal", foreign_keys="DocumentRenewal.document_id", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentRenewal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_renewals"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    renewal_due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    replacement_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped["Document"] = relationship("Document", foreign_keys=[document_id], back_populates="renewals")


class ReminderRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reminder_rules"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # application, evc, undertaking, document
    days_before_due: Mapped[int] = mapped_column(Integer, nullable=False)
    recipient_roles: Mapped[List[str]] = mapped_column(JsonType, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EscalationRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "escalation_rules"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # application, evc, undertaking, document
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1, 2, 3
    days_after_due: Mapped[int] = mapped_column(Integer, nullable=False)
    recipient_roles: Mapped[List[str]] = mapped_column(JsonType, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MessageTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "message_templates"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="in_app", nullable=False)  # in_app, email
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Notification(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "notifications"

    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="in_app", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="unread", index=True, nullable=False)  # unread, read, acknowledged
    dedupe_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_user_id])
    application: Mapped[Optional["Application"]] = relationship("Application", foreign_keys=[application_id])


class Escalation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "escalations"

    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="open", index=True, nullable=False)  # open, resolved
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    application: Mapped[Optional["Application"]] = relationship("Application", foreign_keys=[application_id])
    assigned_to_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_user_id])


class SchedulerRun(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "scheduler_runs"

    job_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # running, success, failed
    items_scanned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Holiday(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "holidays"

    region_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class ConfigVersion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "config_versions"

    config_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class AuditLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "audit_log"

    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JsonType, nullable=True)
    previous_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
