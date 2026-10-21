from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorObject(BaseModel):
    code: str
    message: str
    details: List[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorObject


class DataResponse(BaseModel, Generic[T]):
    data: T


class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
