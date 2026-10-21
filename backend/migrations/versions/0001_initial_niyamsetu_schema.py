"""Initial NiyamSetu Relational Schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-10-21 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. regions
    op.create_table(
        "regions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_regions_code", "regions", ["code"], unique=True)

    # 2. institutions
    op.create_table(
        "institutions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("institution_code", sa.String(50), nullable=False),
        sa.Column("region_id", sa.UUID(), sa.ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_institutions_code", "institutions", ["institution_code"], unique=True)
    op.create_index("ix_institutions_region_id", "institutions", ["region_id"])

    # 3. users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("region_id", sa.UUID(), sa.ForeignKey("regions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("institution_id", sa.UUID(), sa.ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_region_id", "users", ["region_id"])
    op.create_index("ix_users_institution_id", "users", ["institution_id"])

    # 4. route_types
    op.create_table(
        "route_types",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("current_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_route_types_code", "route_types", ["code"], unique=True)

    # 5. route_stages
    op.create_table(
        "route_stages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("route_type_id", sa.UUID(), sa.ForeignKey("route_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("route_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("stage_code", sa.String(50), nullable=False),
        sa.Column("stage_name", sa.String(150), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("required_role", sa.String(50), nullable=False),
        sa.Column("timeline_days", sa.Integer(), server_default=sa.text("7"), nullable=False),
        sa.Column("day_type", sa.String(20), server_default="calendar", nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("route_type_id", "route_version", "stage_code", name="uq_route_version_stage_code"),
        sa.UniqueConstraint("route_type_id", "route_version", "sequence", name="uq_route_version_sequence"),
    )
    op.create_index("ix_route_stages_lookup", "route_stages", ["route_type_id", "route_version", "sequence"])

    # 6. applications
    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("reference_no", sa.String(50), nullable=False),
        sa.Column("institution_id", sa.UUID(), sa.ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("route_type_id", sa.UUID(), sa.ForeignKey("route_types.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("route_version", sa.Integer(), nullable=False),
        sa.Column("current_stage_id", sa.UUID(), sa.ForeignKey("route_stages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), server_default="in_progress", nullable=False),
        sa.Column("assigned_to_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stage_entered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_applications_ref_no", "applications", ["reference_no"], unique=True)
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_inst_id", "applications", ["institution_id"])
    op.create_index("ix_applications_route", "applications", ["route_type_id", "route_version"])

    # 7. stage_history
    op.create_table(
        "stage_history",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("application_id", sa.UUID(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_stage_id", sa.UUID(), sa.ForeignKey("route_stages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("to_stage_id", sa.UUID(), sa.ForeignKey("route_stages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("performed_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_stage_history_app_id", "stage_history", ["application_id"])
    op.create_index("ix_stage_history_performed_at", "stage_history", ["performed_at"])

    # 8. files
    op.create_table(
        "files",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("uploaded_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_files_storage_key", "files", ["storage_key"], unique=True)

    # 9. evcs
    op.create_table(
        "evcs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("application_id", sa.UUID(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), server_default="queued", nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_by", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conducted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report_due_by", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_region_id", sa.UUID(), sa.ForeignKey("regions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evcs_app_id", "evcs", ["application_id"])
    op.create_index("ix_evcs_status", "evcs", ["status"])
    op.create_index("ix_evcs_due_by", "evcs", ["due_by"])

    # 10. evc_members
    op.create_table(
        "evc_members",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("evc_id", sa.UUID(), sa.ForeignKey("evcs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("member_name", sa.String(150), nullable=False),
        sa.Column("member_role", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evc_members_evc_id", "evc_members", ["evc_id"])

    # 11. evc_reports
    op.create_table(
        "evc_reports",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("evc_id", sa.UUID(), sa.ForeignKey("evcs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.UUID(), sa.ForeignKey("files.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("submitted_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("review_status", sa.String(50), server_default="pending_review", nullable=False),
        sa.Column("reviewed_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_comments", sa.Text(), nullable=True),
    )
    op.create_index("ix_evc_reports_evc_id", "evc_reports", ["evc_id"])

    # 12. undertakings
    op.create_table(
        "undertakings",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("application_id", sa.UUID(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("assigned_institution_id", sa.UUID(), sa.ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("verified_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_undertakings_app_id", "undertakings", ["application_id"])
    op.create_index("ix_undertakings_due_date", "undertakings", ["due_date"])
    op.create_index("ix_undertakings_status", "undertakings", ["status"])

    # 13. undertaking_submissions
    op.create_table(
        "undertaking_submissions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("undertaking_id", sa.UUID(), sa.ForeignKey("undertakings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submitted_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("file_id", sa.UUID(), sa.ForeignKey("files.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("review_status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("reviewed_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_comments", sa.Text(), nullable=True),
    )
    op.create_index("ix_undertaking_submissions_uid", "undertaking_submissions", ["undertaking_id"])

    # 14. documents
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("institution_id", sa.UUID(), sa.ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("application_id", sa.UUID(), sa.ForeignKey("applications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("verification_status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("verified_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_storage_key", "documents", ["storage_key"], unique=True)
    op.create_index("ix_documents_institution_id", "documents", ["institution_id"])
    op.create_index("ix_documents_valid_to", "documents", ["valid_to"])
    op.create_index("ix_documents_type", "documents", ["document_type"])

    # 15. document_renewals
    op.create_table(
        "document_renewals",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("renewal_due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("replacement_document_id", sa.UUID(), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_doc_renewals_doc_id", "document_renewals", ["document_id"])
    op.create_index("ix_doc_renewals_due_date", "document_renewals", ["renewal_due_date"])

    # 16. reminder_rules
    op.create_table(
        "reminder_rules",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("days_before_due", sa.Integer(), nullable=False),
        sa.Column("recipient_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 17. escalation_rules
    op.create_table(
        "escalation_rules",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("level", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("days_after_due", sa.Integer(), nullable=False),
        sa.Column("recipient_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 18. message_templates
    op.create_table(
        "message_templates",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(20), server_default="in_app", nullable=False),
        sa.Column("subject_template", sa.String(255), nullable=False),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_message_templates_code", "message_templates", ["code"], unique=True)

    # 19. notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("recipient_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.UUID(), sa.ForeignKey("applications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.String(20), server_default="in_app", nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), server_default="unread", nullable=False),
        sa.Column("dedupe_key", sa.String(255), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_dedupe", "notifications", ["dedupe_key"], unique=True)
    op.create_index("ix_notifications_recipient", "notifications", ["recipient_user_id"])
    op.create_index("ix_notifications_status", "notifications", ["status"])

    # 20. escalations
    op.create_table(
        "escalations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("application_id", sa.UUID(), sa.ForeignKey("applications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("level", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("assigned_to_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), server_default="open", nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_escalations_status", "escalations", ["status"])
    op.create_index("ix_escalations_app_id", "escalations", ["application_id"])

    # 21. scheduler_runs
    op.create_table(
        "scheduler_runs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("job_name", sa.String(100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("items_scanned", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("items_processed", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_scheduler_runs_job", "scheduler_runs", ["job_name"])

    # 22. holidays
    op.create_table(
        "holidays",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("region_id", sa.UUID(), sa.ForeignKey("regions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("holiday_date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_holidays_date", "holidays", ["holiday_date"])

    # 23. config_versions
    op.create_table(
        "config_versions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("config_type", sa.String(100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("changed_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_config_versions_type", "config_versions", ["config_type"])

    # 24. audit_log
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("actor_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("previous_hash", sa.String(64), nullable=True),
        sa.Column("entry_hash", sa.String(64), nullable=False),
    )
    op.create_index("ix_audit_log_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("ix_audit_log_occurred_at", "audit_log", ["occurred_at"])
    op.create_index("ix_audit_log_entry_hash", "audit_log", ["entry_hash"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("config_versions")
    op.drop_table("holidays")
    op.drop_table("scheduler_runs")
    op.drop_table("escalations")
    op.drop_table("notifications")
    op.drop_table("message_templates")
    op.drop_table("escalation_rules")
    op.drop_table("reminder_rules")
    op.drop_table("document_renewals")
    op.drop_table("documents")
    op.drop_table("undertaking_submissions")
    op.drop_table("undertakings")
    op.drop_table("evc_reports")
    op.drop_table("evc_members")
    op.drop_table("evcs")
    op.drop_table("files")
    op.drop_table("stage_history")
    op.drop_table("applications")
    op.drop_table("route_stages")
    op.drop_table("route_types")
    op.drop_table("users")
    op.drop_table("institutions")
    op.drop_table("regions")
