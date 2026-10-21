import uuid
import pytest

from backend.app.core.exceptions import ForbiddenError, ValidationError
from backend.app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from backend.app.permissions.rbac import has_permission, require_permission, validate_user_scope
from backend.app.permissions.roles import Permission, UserRole


def test_password_hashing():
    pw = "SuperSecurePassword123!"
    pw_hash = get_password_hash(pw)
    assert pw_hash != pw
    assert verify_password(pw, pw_hash) is True
    assert verify_password("WrongPassword!", pw_hash) is False


def test_jwt_token_flow():
    payload = {"sub": str(uuid.uuid4()), "role": "system_admin"}
    token = create_access_token(payload)
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == payload["sub"]
    assert decoded["role"] == "system_admin"

    # Invalid token check
    assert decode_access_token("invalid.token.signature") is None


def test_rbac_permissions():
    # Admin has all permissions
    assert has_permission(UserRole.SYSTEM_ADMIN, Permission.ADMIN_CONFIG_EDIT) is True
    assert has_permission(UserRole.SYSTEM_ADMIN, Permission.APPLICATION_VIEW) is True

    # Institution user cannot edit admin config
    assert has_permission(UserRole.INSTITUTION_USER, Permission.ADMIN_CONFIG_EDIT) is False
    assert has_permission(UserRole.INSTITUTION_USER, Permission.APPLICATION_VIEW) is True

    # Enforce permission check
    with pytest.raises(ForbiddenError):
        require_permission(UserRole.INSTITUTION_USER, Permission.ADMIN_CONFIG_EDIT)


def test_user_scope_validation():
    # Institution user requires institution_id
    with pytest.raises(ValidationError):
        validate_user_scope(UserRole.INSTITUTION_USER, region_id=None, institution_id=None)

    # Valid institution user
    validate_user_scope(UserRole.INSTITUTION_USER, region_id=None, institution_id=uuid.uuid4())

    # Regional officer requires region_id
    with pytest.raises(ValidationError):
        validate_user_scope(UserRole.REGIONAL_OFFICER, region_id=None, institution_id=None)

    # Valid regional officer
    validate_user_scope(UserRole.REGIONAL_OFFICER, region_id=uuid.uuid4(), institution_id=None)
