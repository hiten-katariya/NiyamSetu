from fastapi import APIRouter

from backend.app.api.v1.endpoints import admin, applications, auth, dashboard, health, workflow

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["Workflow Engine"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & Configuration"])
