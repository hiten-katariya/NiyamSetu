import csv
from datetime import date, datetime, timezone
import io
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.core.exceptions import BadRequestError, ForbiddenError
from backend.app.models.entities import (
    Application,
    Document,
    Escalation,
    EVC,
    EVCReport,
    Institution,
    Region,
    RouteStage,
    RouteType,
    Undertaking,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.schemas.reports import ReportColumn, ReportTypeInfo
from backend.app.services.audit_service import AuditService
from backend.app.services.deadline_service import DeadlineService

MAX_EXPORT_ROWS = 2000

REPORT_METADATA: Dict[str, Dict[str, Any]] = {
    "application_pendency": {
        "name": "Application Pendency & Stage Analysis",
        "description": "Comprehensive report of in-progress applications, current stages, pendency duration, and SLA urgency.",
        "supported_filters": ["date_from", "date_to", "region_id", "institution_id", "route_type_id", "status"],
        "columns": [
            ReportColumn(key="reference_no", label="Application Ref"),
            ReportColumn(key="institution_name", label="Institution Name"),
            ReportColumn(key="region_name", label="Region"),
            ReportColumn(key="route_name", label="Workflow Route"),
            ReportColumn(key="current_stage", label="Current Stage"),
            ReportColumn(key="status", label="Status"),
            ReportColumn(key="days_in_stage", label="Days in Stage"),
            ReportColumn(key="sla_deadline", label="Stage Deadline"),
            ReportColumn(key="sla_status", label="SLA Urgency"),
        ],
    },
    "application_ageing": {
        "name": "Application Ageing & SLA Breaches",
        "description": "Detailed analysis of application processing speed, stage ageing buckets, and SLA compliance.",
        "supported_filters": ["date_from", "date_to", "region_id", "institution_id", "route_type_id"],
        "columns": [
            ReportColumn(key="reference_no", label="Application Ref"),
            ReportColumn(key="institution_name", label="Institution Name"),
            ReportColumn(key="region_name", label="Region"),
            ReportColumn(key="current_stage", label="Current Stage"),
            ReportColumn(key="ageing_days", label="Ageing (Days)"),
            ReportColumn(key="ageing_bucket", label="Ageing Bucket"),
            ReportColumn(key="due_date", label="Due Date"),
            ReportColumn(key="is_overdue", label="Overdue Breach"),
            ReportColumn(key="stage_timeline_days", label="Configured Timeline (Days)"),
        ],
    },
    "evc_status": {
        "name": "EVC Visit Status & Inspection Reports",
        "description": "Status of Expert Visit Committee physical and hybrid inspections, expert rosters, and report determinations.",
        "supported_filters": ["date_from", "date_to", "region_id", "institution_id", "status"],
        "columns": [
            ReportColumn(key="application_ref", label="Application Ref"),
            ReportColumn(key="institution_name", label="Institution Name"),
            ReportColumn(key="visit_mode", label="Visit Mode"),
            ReportColumn(key="status", label="EVC Status"),
            ReportColumn(key="scheduled_date", label="Scheduled Date"),
            ReportColumn(key="conducted_date", label="Conducted Date"),
            ReportColumn(key="committee_members_count", label="Experts Assigned"),
            ReportColumn(key="latest_report_number", label="Report Number"),
            ReportColumn(key="recommendation", label="Recommendation"),
            ReportColumn(key="review_status", label="Officer Review Status"),
        ],
    },
    "undertaking_compliance": {
        "name": "Time-Bound Undertakings & Compliance Status",
        "description": "Compliance status of statutory undertakings, conditions precedent, evidence verification, and deadlines.",
        "supported_filters": ["date_from", "date_to", "region_id", "institution_id", "status"],
        "columns": [
            ReportColumn(key="condition_title", label="Condition Title"),
            ReportColumn(key="institution_name", label="Institution Name"),
            ReportColumn(key="application_ref", label="Application Ref"),
            ReportColumn(key="status", label="Compliance Status"),
            ReportColumn(key="due_date", label="Due Date"),
            ReportColumn(key="is_overdue", label="Is Overdue"),
            ReportColumn(key="submissions_count", label="Evidence Submissions"),
            ReportColumn(key="fulfilled_date", label="Fulfilled Date"),
        ],
    },
    "document_validity": {
        "name": "Statutory Document Validity & Expiry Register",
        "description": "Validity monitoring of land deeds, occupancy certificates, fire safety NOCs, and renewal records.",
        "supported_filters": ["date_from", "date_to", "region_id", "institution_id", "status"],
        "columns": [
            ReportColumn(key="title", label="Document Title"),
            ReportColumn(key="document_type", label="Document Type"),
            ReportColumn(key="institution_name", label="Institution Name"),
            ReportColumn(key="document_number", label="Document Ref / Deed No"),
            ReportColumn(key="valid_from", label="Valid From"),
            ReportColumn(key="valid_to", label="Valid Till"),
            ReportColumn(key="verification_status", label="Verification Status"),
            ReportColumn(key="validity_state", label="Validity State"),
        ],
    },
    "escalations_audit": {
        "name": "Workflow Escalations & SLA Breach Audit",
        "description": "Log of automated escalations triggered for overdue stages and institutional compliance.",
        "supported_filters": ["date_from", "date_to", "region_id", "institution_id", "status"],
        "columns": [
            ReportColumn(key="application_ref", label="Application Ref"),
            ReportColumn(key="institution_name", label="Institution Name"),
            ReportColumn(key="level", label="Escalation Level"),
            ReportColumn(key="target_type", label="Target Entity"),
            ReportColumn(key="status", label="Status"),
            ReportColumn(key="triggered_at", label="Triggered At"),
            ReportColumn(key="resolved_at", label="Resolved At"),
            ReportColumn(key="resolution_notes", label="Resolution Notes"),
        ],
    },
}


def sanitize_formula_injection(value: Any) -> str:
    """
    Prevents spreadsheet formula injection (CSV injection).
    If a cell value (or its leading content after stripping whitespace) begins with '=', '+', '-', '@', tab, or CR,
    it is safely escaped with a leading single quote.
    """
    if value is None:
        return ""
    val_str = str(value)
    stripped = val_str.lstrip()
    if (val_str and val_str[0] in ("=", "+", "-", "@", "\t", "\r")) or (stripped and stripped[0] in ("=", "+", "-", "@", "\t", "\r")):
        return f"'{val_str}"
    return val_str


class ReportService:
    @staticmethod
    def list_available_reports(user: User) -> List[ReportTypeInfo]:
        """
        Returns list of report definitions accessible to the requesting user.
        """
        results = []
        for code, meta in REPORT_METADATA.items():
            results.append(
                ReportTypeInfo(
                    code=code,
                    name=meta["name"],
                    description=meta["description"],
                    supported_filters=meta["supported_filters"],
                )
            )
        return results

    @classmethod
    def fetch_report_data(
        cls,
        db: Session,
        user: User,
        report_type: str,
        filters: Dict[str, Any],
    ) -> Tuple[List[ReportColumn], List[Dict[str, Any]]]:
        """
        Generates tabular report records applying strict role-based data scoping.
        """
        if report_type not in REPORT_METADATA:
            raise BadRequestError(f"Unsupported report type: '{report_type}'")

        meta = REPORT_METADATA[report_type]
        columns: List[ReportColumn] = meta["columns"]

        role_enum = normalize_role(user.role)
        date_from: Optional[date] = filters.get("date_from")
        date_to: Optional[date] = filters.get("date_to")
        region_id: Optional[uuid.UUID] = filters.get("region_id")
        institution_id: Optional[uuid.UUID] = filters.get("institution_id")
        status_filter: Optional[str] = filters.get("status")
        route_type_id: Optional[uuid.UUID] = filters.get("route_type_id")

        # Strict scoping enforcement
        if role_enum == UserRole.INSTITUTION_USER:
            institution_id = user.institution_id
            region_id = None
        elif role_enum == UserRole.REGIONAL_OFFICER:
            region_id = user.region_id

        rows: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        today = now.date()

        if report_type == "application_pendency":
            stmt = (
                select(Application)
                .join(Application.institution)
                .options(
                    joinedload(Application.institution),
                    joinedload(Application.current_stage),
                    joinedload(Application.route_type),
                )
            )
            if institution_id:
                stmt = stmt.where(Application.institution_id == institution_id)
            if region_id:
                stmt = stmt.where(Institution.region_id == region_id)
            if route_type_id:
                stmt = stmt.where(Application.route_type_id == route_type_id)
            if status_filter:
                stmt = stmt.where(Application.status == status_filter)
            if date_from:
                stmt = stmt.where(func.date(Application.created_at) >= date_from)
            if date_to:
                stmt = stmt.where(func.date(Application.created_at) <= date_to)

            apps = db.scalars(stmt.order_by(Application.created_at.desc()).limit(MAX_EXPORT_ROWS)).all()
            regions_map = {r.id: r.name for r in db.scalars(select(Region)).all()}

            for app in apps:
                reg_name = regions_map.get(app.institution.region_id, "N/A") if app.institution else "N/A"
                res = DeadlineService.calculate_application_deadline(db, app, as_of_time=now)
                days_in_stage = int(res.ageing_days)

                sla_status = "On Track"
                if res.is_overdue:
                    sla_status = "Breached"
                elif res.is_due_soon:
                    sla_status = "Due Soon"

                rows.append({
                    "reference_no": app.reference_no,
                    "institution_name": app.institution.name if app.institution else "N/A",
                    "region_name": reg_name,
                    "route_name": app.route_type.name if app.route_type else "N/A",
                    "current_stage": app.current_stage.stage_name if app.current_stage else "Completed",
                    "status": app.status.upper(),
                    "days_in_stage": days_in_stage,
                    "sla_deadline": res.due_date.strftime("%Y-%m-%d") if res.due_date else "N/A",
                    "sla_status": sla_status,
                })

        elif report_type == "application_ageing":
            stmt = (
                select(Application)
                .join(Application.institution)
                .options(
                    joinedload(Application.institution),
                    joinedload(Application.current_stage),
                )
                .where(Application.status.in_(["in_progress", "returned", "on_hold"]))
            )
            if institution_id:
                stmt = stmt.where(Application.institution_id == institution_id)
            if region_id:
                stmt = stmt.where(Institution.region_id == region_id)
            if route_type_id:
                stmt = stmt.where(Application.route_type_id == route_type_id)

            apps = db.scalars(stmt.limit(MAX_EXPORT_ROWS)).all()
            regions_map = {r.id: r.name for r in db.scalars(select(Region)).all()}

            for app in apps:
                reg_name = regions_map.get(app.institution.region_id, "N/A") if app.institution else "N/A"
                res = DeadlineService.calculate_application_deadline(db, app, as_of_time=now)
                ageing = round(res.ageing_days, 1)

                bucket = "< 7 Days"
                if ageing > 14:
                    bucket = "> 14 Days"
                elif ageing >= 7:
                    bucket = "7 - 14 Days"

                timeline_days = app.current_stage.timeline_days if app.current_stage else 0

                rows.append({
                    "reference_no": app.reference_no,
                    "institution_name": app.institution.name if app.institution else "N/A",
                    "region_name": reg_name,
                    "current_stage": app.current_stage.stage_name if app.current_stage else "Unassigned",
                    "ageing_days": ageing,
                    "ageing_bucket": bucket,
                    "due_date": res.due_date.strftime("%Y-%m-%d") if res.due_date else "N/A",
                    "is_overdue": "YES" if res.is_overdue else "NO",
                    "stage_timeline_days": timeline_days,
                })

        elif report_type == "evc_status":
            stmt = (
                select(EVC)
                .join(EVC.application)
                .join(Application.institution)
                .options(
                    joinedload(EVC.application).joinedload(Application.institution),
                    joinedload(EVC.members),
                    joinedload(EVC.reports),
                )
            )
            if institution_id:
                stmt = stmt.where(Application.institution_id == institution_id)
            if region_id:
                stmt = stmt.where(EVC.assigned_region_id == region_id)
            if status_filter:
                stmt = stmt.where(EVC.status == status_filter)

            evcs = db.scalars(stmt.order_by(EVC.created_at.desc()).limit(MAX_EXPORT_ROWS)).all()

            for evc in evcs:
                app = evc.application
                inst_name = app.institution.name if app and app.institution else "N/A"
                app_ref = app.reference_no if app else "N/A"

                sched = evc.scheduled_at.strftime("%Y-%m-%d") if evc.scheduled_at else "Not Scheduled"
                cond = evc.conducted_at.strftime("%Y-%m-%d") if evc.conducted_at else "Pending"

                latest_rep = evc.reports[-1] if evc.reports else None

                rows.append({
                    "application_ref": app_ref,
                    "institution_name": inst_name,
                    "visit_mode": "Physical / Hybrid",
                    "status": evc.status.upper(),
                    "scheduled_date": sched,
                    "conducted_date": cond,
                    "committee_members_count": len(evc.members),
                    "latest_report_number": f"REP-{latest_rep.id.hex[:6]}" if latest_rep else "N/A",
                    "recommendation": latest_rep.review_comments if latest_rep else "N/A",
                    "review_status": latest_rep.review_status.upper() if latest_rep else "No Report",
                })

        elif report_type == "undertaking_compliance":
            stmt = (
                select(Undertaking)
                .join(Institution, Undertaking.assigned_institution_id == Institution.id)
                .options(joinedload(Undertaking.submissions))
            )
            if institution_id:
                stmt = stmt.where(Undertaking.assigned_institution_id == institution_id)
            if region_id:
                stmt = stmt.where(Institution.region_id == region_id)
            if status_filter:
                stmt = stmt.where(Undertaking.status == status_filter)

            items = db.scalars(stmt.order_by(Undertaking.due_date.asc()).limit(MAX_EXPORT_ROWS)).all()
            inst_map = {i.id: (i.name, i.institution_code) for i in db.scalars(select(Institution)).all()}

            for u in items:
                inst_info = inst_map.get(u.assigned_institution_id, ("N/A", "N/A"))
                is_overdue = "YES" if (u.due_date < today and u.status in ("pending", "overdue")) else "NO"
                fulf = u.verified_at.strftime("%Y-%m-%d") if u.verified_at else "N/A"

                rows.append({
                    "condition_title": u.title,
                    "institution_name": inst_info[0],
                    "application_ref": str(u.application_id)[:8] if u.application_id else "Statutory",
                    "status": u.status.upper(),
                    "due_date": u.due_date.strftime("%Y-%m-%d"),
                    "is_overdue": is_overdue,
                    "submissions_count": len(u.submissions),
                    "fulfilled_date": fulf,
                })

        elif report_type == "document_validity":
            stmt = (
                select(Document)
                .join(Institution, Document.institution_id == Institution.id)
            )
            if institution_id:
                stmt = stmt.where(Document.institution_id == institution_id)
            if region_id:
                stmt = stmt.where(Institution.region_id == region_id)
            if status_filter:
                stmt = stmt.where(Document.verification_status == status_filter)

            docs = db.scalars(stmt.order_by(Document.valid_to.asc().nullslast()).limit(MAX_EXPORT_ROWS)).all()
            inst_map = {i.id: i.name for i in db.scalars(select(Institution)).all()}

            for d in docs:
                inst_name = inst_map.get(d.institution_id, "N/A")
                v_from = d.valid_from.strftime("%Y-%m-%d") if d.valid_from else "N/A"
                v_to = d.valid_to.strftime("%Y-%m-%d") if d.valid_to else "Perpetual"

                val_state = "Valid"
                if d.valid_to:
                    if d.valid_to < today or d.verification_status == "expired":
                        val_state = "Expired"
                    elif (d.valid_to - today).days <= 30:
                        val_state = "Expiring Soon"

                rows.append({
                    "title": d.original_filename or "Statutory Certificate",
                    "document_type": d.document_type.replace("_", " ").upper(),
                    "institution_name": inst_name,
                    "document_number": d.storage_key[:12],
                    "valid_from": v_from,
                    "valid_to": v_to,
                    "verification_status": d.verification_status.upper(),
                    "validity_state": val_state,
                })

        elif report_type == "escalations_audit":
            stmt = (
                select(Escalation)
                .join(Application)
                .join(Application.institution)
                .options(joinedload(Escalation.application).joinedload(Application.institution))
            )
            if institution_id:
                stmt = stmt.where(Application.institution_id == institution_id)
            if region_id:
                stmt = stmt.where(Institution.region_id == region_id)
            if status_filter:
                stmt = stmt.where(Escalation.status == status_filter)

            escs = db.scalars(stmt.order_by(Escalation.triggered_at.desc()).limit(MAX_EXPORT_ROWS)).all()

            for esc in escs:
                app = esc.application
                app_ref = app.reference_no if app else "N/A"
                inst_name = app.institution.name if app and app.institution else "N/A"
                res_at = esc.resolved_at.strftime("%Y-%m-%d %H:%M") if esc.resolved_at else "Open"

                rows.append({
                    "application_ref": app_ref,
                    "institution_name": inst_name,
                    "level": f"Level {esc.level}",
                    "target_type": esc.target_type.upper(),
                    "status": esc.status.upper(),
                    "triggered_at": esc.triggered_at.strftime("%Y-%m-%d %H:%M"),
                    "resolved_at": res_at,
                    "resolution_notes": esc.resolution_notes or "N/A",
                })

        return columns, rows

    @classmethod
    def generate_csv_export(
        cls,
        columns: List[ReportColumn],
        rows: List[Dict[str, Any]],
    ) -> str:
        """
        Generates CSV format with UTF-8 BOM and formula injection protection.
        """
        output = io.StringIO()
        # UTF-8 BOM so Excel opens non-ASCII characters seamlessly
        output.write("\ufeff")

        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header row
        writer.writerow([col.label for col in columns])

        # Data rows with formula injection sanitization
        for row in rows:
            sanitized_row = [sanitize_formula_injection(row.get(col.key, "")) for col in columns]
            writer.writerow(sanitized_row)

        return output.getvalue()

    @classmethod
    def record_export_audit(
        cls,
        db: Session,
        actor_user: User,
        report_type: str,
        record_count: int,
        filters: Dict[str, Any],
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Logs a tamper-evident audit record for every exported report.
        """
        safe_meta = {
            "report_type": report_type,
            "record_count": record_count,
            "export_format": "csv",
            "filters": {k: str(v) for k, v in filters.items() if v is not None},
        }
        AuditService.record_action(
            db=db,
            action="report_exported",
            entity_type="report",
            entity_id=report_type,
            actor_user_id=actor_user.id,
            ip_address=ip_address,
            metadata=safe_meta,
        )
