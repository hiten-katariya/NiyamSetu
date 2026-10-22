import secrets
from typing import Callable, List, Optional
from fastapi import Cookie, Depends, Header, Request, Response
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import ForbiddenError, UnauthorizedError
from backend.app.db.session import get_db
from backend.app.models.entities import User
from backend.app.permissions.roles import Permission, ROLE_PERMISSIONS, UserRole, normalize_role
from backend.app.services.session_service import SessionService


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts the session token from the secure HttpOnly cookie (or Bearer header in tests),
    validates the session against the database hash, and verifies active user status.
    """
    raw_token = request.cookies.get(settings.SESSION_COOKIE_NAME)

    # Support Authorization header fallback (e.g. for API automated testing)
    if not raw_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header[7:].strip()

    if not raw_token:
        raise UnauthorizedError("Authentication required. Please log in.")

    session = SessionService.get_valid_session(db, raw_token)
    if not session:
        raise UnauthorizedError("Session has expired or is invalid. Please log in again.")

    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("User account is inactive or disabled.")

    request.state.user = user
    request.state.session = session
    return user


def verify_csrf_token(request: Request) -> None:
    """
    Validates anti-CSRF double-submit token on state-changing requests when authenticated via cookie.
    Ensures that malicious cross-origin requests cannot perform actions on behalf of the user.
    """
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        # Check if authenticated by session cookie
        has_session_cookie = settings.SESSION_COOKIE_NAME in request.cookies
        if has_session_cookie:
            csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
            csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)

            if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_header, csrf_cookie):
                raise ForbiddenError(
                    message="Anti-CSRF token validation failed. State-changing requests must include a valid X-CSRF-Token header matching the CSRF cookie.",
                    code="CSRF_VALIDATION_FAILED",
                )


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    """
    Dependency factory enforcing role-based authorization.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = normalize_role(current_user.role)
        target_roles = [normalize_role(r.value if isinstance(r, UserRole) else r) for r in allowed_roles]
        if user_role not in target_roles:
            raise ForbiddenError(
                f"Role '{current_user.role}' is not authorized to access this resource."
            )
        return current_user

    return role_checker


def require_permissions(*required_permissions: Permission) -> Callable[[User], User]:
    """
    Dependency factory enforcing granular permission-based authorization.
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = normalize_role(current_user.role)
        perms = ROLE_PERMISSIONS.get(user_role, set())
        for p in required_permissions:
            if p not in perms:
                raise ForbiddenError(
                    f"Role '{current_user.role}' lacks required permission '{p.value}'."
                )
        return current_user

    return permission_checker


def set_auth_cookies(response: Response, raw_session_token: str, csrf_token: str) -> None:
    """
    Sets secure HttpOnly session cookie and accessible CSRF cookie.
    """
    # 1. HttpOnly session cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_session_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_EXPIRE_SECONDS,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    # 2. Readable Anti-CSRF cookie (read by frontend JS to set X-CSRF-Token header)
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_EXPIRE_SECONDS,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Clears both authentication and CSRF cookies on logout.
    """
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
