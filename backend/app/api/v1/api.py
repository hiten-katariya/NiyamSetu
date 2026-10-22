from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    admin,
    applications,
    audit,
    auth,
    dashboard,
    documents,
    escalations,
    evc,
    files,
    health,
    monitoring,
    notifications,
    reports,
    undertakings,
    workflow,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["Workflow Engine"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard & Analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reporting & Exports"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Log & Integrity"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Operational Monitoring"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(escalations.router, prefix="/escalations", tags=["Escalations"])
api_router.include_router(evc.router, prefix="/evc", tags=["EVC Management"])
api_router.include_router(undertakings.router, prefix="/undertakings", tags=["Undertaking Compliance"])
api_router.include_router(documents.router, prefix="/documents", tags=["Document Validity"])
api_router.include_router(files.router, prefix="/files", tags=["Secure Files"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & Configuration"])
