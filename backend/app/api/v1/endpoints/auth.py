from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.exceptions import UnauthorizedError
from backend.app.db.session import get_db
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from backend.app.schemas.common import DataResponse
from backend.app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=DataResponse[TokenResponse], summary="User Login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user with email and password and returns signed JWT access token.
    """
    user = AuthService.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise UnauthorizedError("Invalid email or password.")

    token_info = AuthService.create_user_token(user)
    return {"data": token_info}
