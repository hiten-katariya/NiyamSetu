from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    status: str = Field(..., example="healthy")
    timestamp: datetime
    environment: str
    version: str = "0.1.0"


class ReadinessStatus(BaseModel):
    status: str = Field(..., example="ready")
    timestamp: datetime
    environment: str
    database: Dict[str, str] = Field(
        ...,
        example={"status": "connected", "details": "Database connection healthy"}
    )
    worker: Dict[str, str] = Field(
        ...,
        example={"status": "operational", "details": "APScheduler worker configured separately"}
    )
