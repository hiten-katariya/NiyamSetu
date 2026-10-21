from datetime import datetime, timezone
from typing import Dict
from backend.app.core.config import settings
from backend.app.db.session import check_db_connection


class HealthService:
    @staticmethod
    def get_live_status() -> Dict:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": settings.ENVIRONMENT,
            "version": "0.1.0",
        }

    @staticmethod
    def get_readiness_status() -> Dict:
        db_healthy, db_message = check_db_connection()
        overall_ready = db_healthy

        return {
            "status": "ready" if overall_ready else "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": settings.ENVIRONMENT,
            "database": {
                "status": "connected" if db_healthy else "disconnected",
                "details": db_message,
            },
            "worker": {
                "status": "operational",
                "details": "APScheduler worker runs as a dedicated decoupled process",
            },
        }
