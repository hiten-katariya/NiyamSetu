from enum import Enum
from typing import List, Set


class UserRole(str, Enum):
    INSTITUTION_USER = "institution_user"
    SCRUTINY_OFFICER = "scrutiny_officer"
    REGIONAL_OFFICER = "regional_officer"
    BUREAU_OFFICER = "bureau_officer"
    COMMITTEE_MEMBER = "committee_member"
    SENIOR_AUTHORITY = "senior_authority"
    SYSTEM_ADMIN = "system_admin"

    @classmethod
    def all_roles(cls) -> List[str]:
        return [r.value for r in cls]


class Permission(str, Enum):
    # Application permissions
    APPLICATION_VIEW = "application:view"
    APPLICATION_CREATE = "application:create"
    APPLICATION_ADVANCE = "application:advance"
    APPLICATION_RETURN = "application:return"
    APPLICATION_HOLD = "application:hold"
    APPLICATION_RESUME = "application:resume"
    APPLICATION_DECISION = "application:decision"

    # EVC permissions
    EVC_VIEW = "evc:view"
    EVC_SCHEDULE = "evc:schedule"
    EVC_ASSIGN = "evc:assign"
    EVC_CONDUCT = "evc:conduct"
    EVC_REPORT_SUBMIT = "evc:report_submit"
    EVC_REPORT_REVIEW = "evc:report_review"
    EVC_CLOSE = "evc:close"

    # Compliance & Undertakings
    UNDERTAKING_VIEW = "undertaking:view"
    UNDERTAKING_CREATE = "undertaking:create"
    UNDERTAKING_SUBMIT = "undertaking:submit"
    UNDERTAKING_VERIFY = "undertaking:verify"

    # Documents
    DOCUMENT_VIEW = "document:view"
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_VERIFY = "document:verify"

    # Admin & Configuration
    ADMIN_CONFIG_VIEW = "admin:config_view"
    ADMIN_CONFIG_EDIT = "admin:config_edit"
    ADMIN_USER_MANAGE = "admin:user_manage"
    ADMIN_SCHEDULER_RUN = "admin:scheduler_run"

    # Audit
    AUDIT_VIEW = "audit:view"
    AUDIT_VERIFY = "audit:verify"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.INSTITUTION_USER: {
        Permission.APPLICATION_VIEW,
        Permission.APPLICATION_CREATE,
        Permission.UNDERTAKING_VIEW,
        Permission.UNDERTAKING_SUBMIT,
        Permission.DOCUMENT_VIEW,
        Permission.DOCUMENT_UPLOAD,
    },
    UserRole.SCRUTINY_OFFICER: {
        Permission.APPLICATION_VIEW,
        Permission.APPLICATION_ADVANCE,
        Permission.APPLICATION_RETURN,
        Permission.APPLICATION_HOLD,
        Permission.APPLICATION_RESUME,
        Permission.DOCUMENT_VIEW,
        Permission.DOCUMENT_VERIFY,
        Permission.UNDERTAKING_VIEW,
    },
    UserRole.REGIONAL_OFFICER: {
        Permission.APPLICATION_VIEW,
        Permission.APPLICATION_ADVANCE,
        Permission.APPLICATION_RETURN,
        Permission.APPLICATION_HOLD,
        Permission.APPLICATION_RESUME,
        Permission.EVC_VIEW,
        Permission.EVC_SCHEDULE,
        Permission.EVC_ASSIGN,
        Permission.UNDERTAKING_VIEW,
        Permission.UNDERTAKING_CREATE,
        Permission.UNDERTAKING_VERIFY,
        Permission.DOCUMENT_VIEW,
        Permission.DOCUMENT_VERIFY,
        Permission.AUDIT_VIEW,
    },
    UserRole.BUREAU_OFFICER: {
        Permission.APPLICATION_VIEW,
        Permission.APPLICATION_ADVANCE,
        Permission.APPLICATION_RETURN,
        Permission.APPLICATION_HOLD,
        Permission.APPLICATION_RESUME,
        Permission.EVC_VIEW,
        Permission.UNDERTAKING_VIEW,
        Permission.DOCUMENT_VIEW,
        Permission.AUDIT_VIEW,
    },
    UserRole.COMMITTEE_MEMBER: {
        Permission.APPLICATION_VIEW,
        Permission.EVC_VIEW,
        Permission.EVC_CONDUCT,
        Permission.EVC_REPORT_SUBMIT,
        Permission.DOCUMENT_VIEW,
    },
    UserRole.SENIOR_AUTHORITY: {
        Permission.APPLICATION_VIEW,
        Permission.APPLICATION_DECISION,
        Permission.EVC_VIEW,
        Permission.EVC_REPORT_REVIEW,
        Permission.EVC_CLOSE,
        Permission.UNDERTAKING_VIEW,
        Permission.AUDIT_VIEW,
        Permission.AUDIT_VERIFY,
    },
    UserRole.SYSTEM_ADMIN: {
        perm for perm in Permission
    },
}
