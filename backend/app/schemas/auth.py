from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from backend.app.permissions.roles import UserRole
from backend.app.schemas.common import BaseSchema

# Standard email regex pattern without requiring optional email-validator package
EmailType = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
    ),
]


class LoginRequest(BaseModel):
    email: EmailType
    password: str = Field(..., min_length=6)


class UserBase(BaseSchema):
    email: EmailType
    full_name: str
    role: str
    region_id: Optional[uuid.UUID] = None
    institution_id: Optional[uuid.UUID] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: uuid.UUID
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PermittedScope(BaseModel):
    is_global: bool
    region_id: Optional[uuid.UUID] = None
    institution_id: Optional[uuid.UUID] = None
    scope_description: str


class UserProfileResponse(BaseModel):
    user: UserResponse
    permissions: List[str]
    permitted_scope: PermittedScope


class LoginSuccessResponse(BaseModel):
    message: str = "Authentication successful"
    csrf_token: str
    user: UserResponse


class LogoutSuccessResponse(BaseModel):
    message: str = "Session successfully terminated"


class CsrfTokenResponse(BaseModel):
    csrf_token: str


class RoleUpdateRequest(BaseModel):
    role: str
    region_id: Optional[uuid.UUID] = None
    institution_id: Optional[uuid.UUID] = None


class AccountStatusUpdateRequest(BaseModel):
    is_active: bool
