from datetime import date, datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class ReportColumn(BaseModel):
    key: str
    label: str


class ReportTypeInfo(BaseModel):
    code: str
    name: str
    description: str
    supported_filters: List[str]


class ReportFilterRequest(BaseModel):
    report_type: str
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    region_id: Optional[uuid.UUID] = None
    institution_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    route_type_id: Optional[uuid.UUID] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)


class ReportPreviewResponse(BaseModel):
    report_type: str
    report_title: str
    generated_at: datetime
    columns: List[ReportColumn]
    rows: List[Dict[str, Any]]
    total_rows: int
    page: int
    page_size: int


class ReportExportRequest(BaseModel):
    report_type: str
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    region_id: Optional[uuid.UUID] = None
    institution_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    route_type_id: Optional[uuid.UUID] = None
    export_format: str = "csv"  # csv
