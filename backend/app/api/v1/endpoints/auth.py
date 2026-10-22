from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from backend.app.api.deps import clear_auth_cookies, get_current_user, set_auth_cookies, verify_csrf_token
from backend.app.db.session import get_db
from backend.app.models.entities import User
from backend.app.permissions.roles import ROLE_PERMISSIONS, UserRole, normalize_role
from backend.app.schemas.auth import (
    CsrfTokenResponse,
    LoginRequest,
    LoginSuccessResponse,
    LogoutSuccessResponse,
    UserProfileResponse,
    UserResponse,
)
from backend.app.schemas.common import DataResponse
from backend.app.services.auth_service import AuthService
from backend.app.services.session_service import SessionService

router = APIRouter()


@router.post(
    "/login",
    response_model=DataResponse[LoginSuccessResponse],
    summary="User Login & Session Creation",
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticates user credentials, creates a high-entropy server-managed session,
    sets secure HttpOnly and CSRF cookies, and returns the authenticated user's safe profile.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    user, raw_token, csrf_token, session = AuthService.authenticate_and_create_session(
        db=db,
        email=payload.email,
        password=payload.password,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # Set secure HttpOnly session cookie and accessible Anti-CSRF cookie
    set_auth_cookies(response, raw_session_token=raw_token, csrf_token=csrf_token)

    return {
        "data": LoginSuccessResponse(
            message="Authentication successful",
            csrf_token=csrf_token,
            user=UserResponse.model_validate(user),
        )
    }


@router.post(
    "/logout",
    response_model=DataResponse[LogoutSuccessResponse],
    summary="Terminate Session & Logout",
    dependencies=[Depends(verify_csrf_token)],
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Invalidates the active session in the database, records audit trail, and deletes cookies.
    """
    raw_token = request.cookies.get("niyamsetu_session")
    if not raw_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header[7:].strip()

    client_ip = request.client.host if request.client else None
    AuthService.terminate_session(
        db=db,
        raw_token=raw_token,
        user=current_user,
        ip_address=client_ip,
    )

    clear_auth_cookies(response)
    return {"data": LogoutSuccessResponse(message="Session successfully terminated")}


@router.get(
    "/me",
    response_model=DataResponse[UserProfileResponse],
    summary="Get Authenticated User Profile & Scope",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the authenticated user's safe profile, role, permitted scopes, and active permissions.
    Never exposes passwords, session identifiers, or cryptographic secrets.
    """
    role_enum = normalize_role(current_user.role)
    perms = [p.value for p in ROLE_PERMISSIONS.get(role_enum, set())]
    scope = AuthService.get_user_permitted_scope(current_user)

    return {
        "data": UserProfileResponse(
            user=UserResponse.model_validate(current_user),
            permissions=sorted(perms),
            permitted_scope=scope,
        )
    }


@router.get(
    "/csrf",
    response_model=DataResponse[CsrfTokenResponse],
    summary="Obtain Anti-CSRF Token",
)
def get_csrf_token(response: Response):
    """
    Returns an anti-CSRF token and sets the niyamsetu_csrf cookie.
    """
    token = SessionService.generate_csrf_token()
    response.set_cookie(
        key="niyamsetu_csrf",
        value=token,
        httponly=False,
        secure=False,
        samesite="lax",
        path="/",
    )
    return {"data": CsrfTokenResponse(csrf_token=token)}
