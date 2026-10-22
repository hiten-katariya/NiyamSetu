from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.models.entities import User
from backend.app.permissions.roles import UserRole
from backend.app.schemas.common import DataResponse
from backend.app.schemas.reports import (
    ReportExportRequest,
    ReportFilterRequest,
    ReportPreviewResponse,
    ReportTypeInfo,
)
from backend.app.services.report_service import REPORT_METADATA, ReportService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/types", response_model=DataResponse[List[ReportTypeInfo]], summary="List Available Report Types")
def list_reports(
    current_user: User = Depends(get_current_user),
):
    """
    Returns metadata for all reporting types available to the user.
    """
    reports = ReportService.list_available_reports(current_user)
    return {"data": reports}


@router.post("/preview", response_model=DataResponse[ReportPreviewResponse], summary="Preview Filtered Report Data")
def preview_report(
    req: ReportFilterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns paginated tabular preview data for the selected report and filter parameters.
    """
    filters = {
        "date_from": req.date_from,
        "date_to": req.date_to,
        "region_id": req.region_id,
        "institution_id": req.institution_id,
        "status": req.status,
        "route_type_id": req.route_type_id,
    }
    columns, all_rows = ReportService.fetch_report_data(
        db=db, user=current_user, report_type=req.report_type, filters=filters
    )

    total_rows = len(all_rows)
    start_idx = (req.page - 1) * req.page_size
    end_idx = start_idx + req.page_size
    page_rows = all_rows[start_idx:end_idx]

    report_title = REPORT_METADATA.get(req.report_type, {}).get("name", req.report_type)

    return {
        "data": ReportPreviewResponse(
            report_type=req.report_type,
            report_title=report_title,
            generated_at=datetime.now(timezone.utc),
            columns=columns,
            rows=page_rows,
            total_rows=total_rows,
            page=req.page,
            page_size=req.page_size,
        )
    }


@router.post("/export", summary="Export Report to CSV")
def export_report(
    req: ReportExportRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates and downloads a spreadsheet formula-safe, Excel-compatible CSV report.
    Logs an immutable audit event for compliance tracking.
    """
    filters = {
        "date_from": req.date_from,
        "date_to": req.date_to,
        "region_id": req.region_id,
        "institution_id": req.institution_id,
        "status": req.status,
        "route_type_id": req.route_type_id,
    }
    columns, all_rows = ReportService.fetch_report_data(
        db=db, user=current_user, report_type=req.report_type, filters=filters
    )

    csv_content = ReportService.generate_csv_export(columns, all_rows)

    client_ip = request.client.host if request.client else None
    ReportService.record_export_audit(
        db=db,
        actor_user=current_user,
        report_type=req.report_type,
        record_count=len(all_rows),
        filters=filters,
        ip_address=client_ip,
    )
    db.commit()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"niyamsetu_{req.report_type}_{ts}.csv"

    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
