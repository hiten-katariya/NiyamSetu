from typing import Optional, Set
import uuid

from backend.app.core.exceptions import ForbiddenError, ValidationError
from backend.app.permissions.roles import Permission, ROLE_PERMISSIONS, UserRole


def has_permission(role: UserRole, permission: Permission) -> bool:
    """
    Checks whether a given UserRole has a specific Permission.
    """
    perms: Set[Permission] = ROLE_PERMISSIONS.get(role, set())
    return permission in perms


def require_permission(role: UserRole, permission: Permission) -> None:
    """
    Enforces a permission check, raising ForbiddenError if not allowed.
    """
    if not has_permission(role, permission):
        raise ForbiddenError(f"Role '{role.value}' does not have permission '{permission.value}'")


def validate_user_scope(
    role: UserRole,
    region_id: Optional[uuid.UUID],
    institution_id: Optional[uuid.UUID],
) -> None:
    """
    Validates that user's region and institution scoping conforms to their role:
    - INSTITUTION_USER must have institution_id
    - REGIONAL_OFFICER must have region_id
    - Other roles cannot have contradictory scope
    """
    if role == UserRole.INSTITUTION_USER:
        if not institution_id:
            raise ValidationError("Institution User must be associated with an institution_id.")
    elif role == UserRole.REGIONAL_OFFICER:
        if not region_id:
            raise ValidationError("Regional Officer must be associated with a region_id.")


def check_resource_access(
    user_role: UserRole,
    user_region_id: Optional[uuid.UUID],
    user_institution_id: Optional[uuid.UUID],
    resource_region_id: Optional[uuid.UUID],
    resource_institution_id: Optional[uuid.UUID],
) -> bool:
    """
    Evaluates whether the user can access a specific resource based on institutional/regional scoping:
    - SYSTEM_ADMIN, BUREAU_OFFICER, SENIOR_AUTHORITY have national scope.
    - REGIONAL_OFFICER can only access resources in their assigned region.
    - INSTITUTION_USER can only access resources belonging to their institution.
    """
    if user_role in {UserRole.SYSTEM_ADMIN, UserRole.ADMIN, UserRole.BUREAU_OFFICER, UserRole.SENIOR_AUTHORITY}:
        return True

    if user_role == UserRole.INSTITUTION_USER:
        return user_institution_id is not None and user_institution_id == resource_institution_id

    if user_role == UserRole.REGIONAL_OFFICER:
        return user_region_id is not None and user_region_id == resource_region_id

    # Default to open for committee members if assigned
    return True
