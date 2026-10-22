from datetime import datetime, timezone
import secrets
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.core.exceptions import AppException, ForbiddenError, NotFoundError
from backend.app.models.entities import (
    Application,
    EVC,
    EVCMember,
    Institution,
    RouteStage,
    RouteType,
    StageHistory,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.services.audit_service import AuditService


class WorkflowService:
    """
    Transaction-safe Workflow Engine for Application Lifecycle Management.
    Enforces deterministic transitions, role authorizations, data scoping,
    pinned route versions, and tamper-evident audit logging.
    """

    @staticmethod
    def generate_reference_no(db: Session) -> str:
        """
        Generates a collision-safe unique reference number (e.g. NS-2026-A1B2C3D4).
        """
        year = datetime.now(timezone.utc).year
        for _ in range(10):
            token = secrets.token_hex(4).upper()
            ref_no = f"NS-{year}-{token}"
            existing = db.scalar(select(Application.id).where(Application.reference_no == ref_no))
            if not existing:
                return ref_no
        # Fallback to high-entropy token
        return f"NS-{year}-{secrets.token_hex(6).upper()}"

    @staticmethod
    def check_application_access(app: Application, user: User, db: Session) -> bool:
        """
        Verifies whether the authenticated user has authorization to access the application
        based on role, institutional boundaries, regional jurisdiction, or committee duty.
        """
        role_enum = normalize_role(user.role)

        if role_enum in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.BUREAU_OFFICER, UserRole.SENIOR_AUTHORITY):
            return True

        if role_enum == UserRole.INSTITUTION_USER:
            return bool(user.institution_id and app.institution_id == user.institution_id)

        if role_enum == UserRole.REGIONAL_OFFICER:
            if not user.region_id:
                return False
            # Check institution region
            inst = app.institution or db.get(Institution, app.institution_id)
            return bool(inst and inst.region_id == user.region_id)

        if role_enum == UserRole.COMMITTEE_MEMBER:
            # Check if user is assigned to any EVC for this application
            evc_stmt = (
                select(EVCMember.id)
                .join(EVC, EVCMember.evc_id == EVC.id)
                .where(EVC.application_id == app.id, EVCMember.user_id == user.id)
            )
            return db.scalar(evc_stmt) is not None

        if role_enum == UserRole.SCRUTINY_OFFICER:
            return True

        return False

    @staticmethod
    def list_active_routes(db: Session) -> List[RouteType]:
        """
        Retrieves all active workflow route configurations.
        """
        stmt = (
            select(RouteType)
            .where(RouteType.is_active == True)  # noqa: E712
            .order_by(RouteType.name.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_route_by_id(db: Session, route_id: uuid.UUID) -> RouteType:
        """
        Retrieves a route definition along with its stages.
        """
        route = db.get(RouteType, route_id)
        if not route:
            raise NotFoundError("Workflow route configuration not found.")
        return route

    @staticmethod
    def get_route_stages(db: Session, route_type_id: uuid.UUID, route_version: int) -> List[RouteStage]:
        """
        Retrieves the ordered sequence of stages for a pinned route version.
        """
        stmt = (
            select(RouteStage)
            .where(
                RouteStage.route_type_id == route_type_id,
                RouteStage.route_version == route_version,
            )
            .order_by(RouteStage.sequence.asc())
        )
        return list(db.scalars(stmt).all())

    @classmethod
    def create_application(
        cls,
        db: Session,
        user: User,
        route_type_id: uuid.UUID,
        institution_id: Optional[uuid.UUID] = None,
        reference_no: Optional[str] = None,
    ) -> Application:
        """
        Creates an application pinned to the active route's current version,
        assigns the initial workflow stage, records initial stage history,
        and generates an audit log entry within an atomic transaction.
        """
        role_enum = normalize_role(user.role)

        # 1. Validate route configuration
        route = db.get(RouteType, route_type_id)
        if not route:
            raise NotFoundError("Selected workflow route does not exist.")
        if not route.is_active:
            raise AppException(
                "Selected workflow route is inactive and cannot accept new applications.",
                code="INACTIVE_ROUTE",
                status_code=400,
            )

        # 2. Validate and enforce institution scoping
        target_institution_id: uuid.UUID
        if role_enum == UserRole.INSTITUTION_USER:
            if not user.institution_id:
                raise ForbiddenError("Authenticated user account is not associated with any registered institution.")
            if institution_id and institution_id != user.institution_id:
                raise ForbiddenError("Institution users cannot create applications on behalf of other institutions.")
            target_institution_id = user.institution_id
        else:
            if not institution_id:
                raise AppException("institution_id is required to create an application.", code="INSTITUTION_REQUIRED", status_code=422)
            target_institution_id = institution_id

        institution = db.get(Institution, target_institution_id)
        if not institution:
            raise NotFoundError("Specified institution does not exist.")
        if not institution.is_active:
            raise AppException("Specified institution is marked inactive.", code="INACTIVE_INSTITUTION", status_code=400)

        # 3. Pin route version and find initial stage
        pinned_version = route.current_version
        stages = cls.get_route_stages(db, route_type_id=route.id, route_version=pinned_version)
        if not stages:
            raise AppException(
                f"Route '{route.name}' (v{pinned_version}) has no configured stages.",
                code="INVALID_ROUTE_CONFIG",
                status_code=400,
            )

        first_stage = stages[0]
        now = datetime.now(timezone.utc)
        ref = reference_no or cls.generate_reference_no(db)

        # 4. Construct application entity
        app = Application(
            id=uuid.uuid4(),
            reference_no=ref,
            institution_id=target_institution_id,
            route_type_id=route.id,
            route_version=pinned_version,
            current_stage_id=first_stage.id,
            status="in_progress",
            submitted_at=now,
            stage_entered_at=now,
        )
        db.add(app)
        db.flush()

        # 5. Record initial stage history
        history = StageHistory(
            id=uuid.uuid4(),
            application_id=app.id,
            from_stage_id=None,
            to_stage_id=first_stage.id,
            action="created",
            reason="Application created and initial stage assigned.",
            performed_by_user_id=user.id,
            performed_at=now,
            metadata_={
                "route_code": route.code,
                "route_version": pinned_version,
                "initial_stage_code": first_stage.stage_code,
            },
        )
        db.add(history)

        # 6. Record tamper-evident audit event
        AuditService.record_action(
            db=db,
            action="APPLICATION_CREATED",
            entity_type="application",
            entity_id=str(app.id),
            actor_user_id=user.id,
            metadata={
                "reference_no": app.reference_no,
                "institution_id": str(target_institution_id),
                "route_code": route.code,
                "route_version": pinned_version,
                "initial_stage": first_stage.stage_code,
            },
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def advance_stage(
        cls,
        db: Session,
        application_id: uuid.UUID,
        user: User,
        comments: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Application:
        """
        Advances the application to the next sequential stage in its pinned route version.
        Guarantees row-level concurrency protection, stage role verification,
        atomic history insertion, and audit trail generation.
        """
        # Row-level lock against concurrent modifications
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(joinedload(Application.institution))
            .with_for_update()
        )
        app = db.scalars(stmt).first()
        if not app:
            raise NotFoundError("Application not found.")

        # Data scoping check
        if not cls.check_application_access(app, user, db):
            raise NotFoundError("Application not found.")

        # State checks
        if app.status == "on_hold":
            raise AppException(
                "Application is on hold. It must be resumed before it can advance.",
                code="APPLICATION_ON_HOLD",
                status_code=400,
            )
        if app.status in ("completed", "withdrawn"):
            raise AppException(
                f"Cannot advance application with closed status '{app.status}'.",
                code="APPLICATION_CLOSED",
                status_code=400,
            )

        if not app.current_stage_id:
            raise AppException("Application has no active stage assigned.", code="INVALID_STAGE", status_code=400)

        current_stage = db.get(RouteStage, app.current_stage_id)
        if not current_stage:
            raise NotFoundError("Current workflow stage record not found.")

        # Verify role authorization for advancing current stage
        role_enum = normalize_role(user.role)
        is_admin = role_enum in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN)
        if not is_admin and user.role != current_stage.required_role:
            raise ForbiddenError(
                f"User role '{user.role}' is not authorised to advance stage '{current_stage.stage_name}'. "
                f"Required role: '{current_stage.required_role}'."
            )

        # Determine next stage in pinned route version
        next_stage_stmt = (
            select(RouteStage)
            .where(
                RouteStage.route_type_id == app.route_type_id,
                RouteStage.route_version == app.route_version,
                RouteStage.sequence == current_stage.sequence + 1,
            )
        )
        next_stage = db.scalars(next_stage_stmt).first()

        if not next_stage:
            # Reached final stage; statutory AICTE regulations do not permit automated decisions
            raise AppException(
                "Application has reached the final stage of its configured workflow route. "
                "Autonomous statutory approval decisions are prohibited; formal human statutory determination required.",
                code="FINAL_STAGE_REACHED",
                status_code=400,
            )

        now = datetime.now(timezone.utc)
        from_stage_id = app.current_stage_id

        # Update application state
        app.current_stage_id = next_stage.id
        app.status = "in_progress"
        app.stage_entered_at = now

        # Record stage transition history
        history = StageHistory(
            id=uuid.uuid4(),
            application_id=app.id,
            from_stage_id=from_stage_id,
            to_stage_id=next_stage.id,
            action="advance",
            reason=comments or f"Advanced from {current_stage.stage_name} to {next_stage.stage_name}",
            performed_by_user_id=user.id,
            performed_at=now,
            metadata_=metadata,
        )
        db.add(history)

        # Record audit log event
        AuditService.record_action(
            db=db,
            action="APPLICATION_STAGE_ADVANCED",
            entity_type="application",
            entity_id=str(app.id),
            actor_user_id=user.id,
            metadata={
                "reference_no": app.reference_no,
                "from_stage": current_stage.stage_code,
                "to_stage": next_stage.stage_code,
                "comments": comments,
            },
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def return_application(
        cls,
        db: Session,
        application_id: uuid.UUID,
        user: User,
        reason: str,
        target_stage_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Application:
        """
        Returns an application for clarification or deficiency rectification.
        Requires a non-empty reason and authorized reviewer role.
        """
        if not reason or not reason.strip():
            raise AppException(
                "A non-empty reason is mandatory when returning an application.",
                code="REASON_REQUIRED",
                status_code=422,
            )

        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(joinedload(Application.institution))
            .with_for_update()
        )
        app = db.scalars(stmt).first()
        if not app:
            raise NotFoundError("Application not found.")

        if not cls.check_application_access(app, user, db):
            raise NotFoundError("Application not found.")

        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            raise ForbiddenError("Institution users cannot perform official return actions.")

        if app.status == "on_hold":
            raise AppException("Cannot return an application while it is on hold.", code="APPLICATION_ON_HOLD", status_code=400)
        if app.status in ("completed", "withdrawn"):
            raise AppException("Cannot return a closed application.", code="APPLICATION_CLOSED", status_code=400)

        current_stage = db.get(RouteStage, app.current_stage_id) if app.current_stage_id else None
        if not current_stage:
            raise NotFoundError("Current workflow stage record not found.")

        # Determine target stage
        target_stage: RouteStage
        if target_stage_id:
            target = db.get(RouteStage, target_stage_id)
            if not target:
                raise NotFoundError("Target return stage not found.")
            if target.route_type_id != app.route_type_id or target.route_version != app.route_version:
                raise AppException("Target stage belongs to a different route version.", code="ROUTE_MISMATCH", status_code=400)
            if target.sequence > current_stage.sequence:
                raise AppException("Cannot return forward in the workflow sequence.", code="INVALID_RETURN_TARGET", status_code=400)
            target_stage = target
        else:
            # Default to previous stage, or retain current if already at sequence 1
            if current_stage.sequence > 1:
                prev_stmt = select(RouteStage).where(
                    RouteStage.route_type_id == app.route_type_id,
                    RouteStage.route_version == app.route_version,
                    RouteStage.sequence == current_stage.sequence - 1,
                )
                prev = db.scalars(prev_stmt).first()
                target_stage = prev or current_stage
            else:
                target_stage = current_stage

        now = datetime.now(timezone.utc)
        from_stage_id = app.current_stage_id

        app.current_stage_id = target_stage.id
        app.status = "returned"
        app.stage_entered_at = now

        history = StageHistory(
            id=uuid.uuid4(),
            application_id=app.id,
            from_stage_id=from_stage_id,
            to_stage_id=target_stage.id,
            action="return",
            reason=reason.strip(),
            performed_by_user_id=user.id,
            performed_at=now,
            metadata_=metadata,
        )
        db.add(history)

        AuditService.record_action(
            db=db,
            action="APPLICATION_RETURNED",
            entity_type="application",
            entity_id=str(app.id),
            actor_user_id=user.id,
            metadata={
                "reference_no": app.reference_no,
                "from_stage": current_stage.stage_code,
                "to_stage": target_stage.stage_code,
                "reason": reason.strip(),
            },
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def hold_application(
        cls,
        db: Session,
        application_id: uuid.UUID,
        user: User,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Application:
        """
        Places an active application on hold with mandatory justification.
        """
        if not reason or not reason.strip():
            raise AppException(
                "A mandatory reason is required to place an application on hold.",
                code="REASON_REQUIRED",
                status_code=422,
            )

        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(joinedload(Application.institution))
            .with_for_update()
        )
        app = db.scalars(stmt).first()
        if not app:
            raise NotFoundError("Application not found.")

        if not cls.check_application_access(app, user, db):
            raise NotFoundError("Application not found.")

        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            raise ForbiddenError("Institution users cannot place applications on hold.")

        if app.status == "on_hold":
            raise AppException("Application is already on hold.", code="ALREADY_ON_HOLD", status_code=400)
        if app.status in ("completed", "withdrawn"):
            raise AppException("Cannot place a closed application on hold.", code="APPLICATION_CLOSED", status_code=400)

        now = datetime.now(timezone.utc)
        app.status = "on_hold"

        history = StageHistory(
            id=uuid.uuid4(),
            application_id=app.id,
            from_stage_id=app.current_stage_id,
            to_stage_id=app.current_stage_id,
            action="hold",
            reason=reason.strip(),
            performed_by_user_id=user.id,
            performed_at=now,
            metadata_=metadata,
        )
        db.add(history)

        AuditService.record_action(
            db=db,
            action="APPLICATION_HELD",
            entity_type="application",
            entity_id=str(app.id),
            actor_user_id=user.id,
            metadata={
                "reference_no": app.reference_no,
                "reason": reason.strip(),
            },
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def resume_application(
        cls,
        db: Session,
        application_id: uuid.UUID,
        user: User,
        comments: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Application:
        """
        Resumes an application that is currently on hold.
        """
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(joinedload(Application.institution))
            .with_for_update()
        )
        app = db.scalars(stmt).first()
        if not app:
            raise NotFoundError("Application not found.")

        if not cls.check_application_access(app, user, db):
            raise NotFoundError("Application not found.")

        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            raise ForbiddenError("Institution users cannot perform resume actions.")

        if app.status != "on_hold":
            raise AppException(
                f"Application is in '{app.status}' status, not on hold.",
                code="NOT_ON_HOLD",
                status_code=400,
            )

        now = datetime.now(timezone.utc)
        app.status = "in_progress"

        history = StageHistory(
            id=uuid.uuid4(),
            application_id=app.id,
            from_stage_id=app.current_stage_id,
            to_stage_id=app.current_stage_id,
            action="resume",
            reason=comments or "Application resumed from hold.",
            performed_by_user_id=user.id,
            performed_at=now,
            metadata_=metadata,
        )
        db.add(history)

        AuditService.record_action(
            db=db,
            action="APPLICATION_RESUMED",
            entity_type="application",
            entity_id=str(app.id),
            actor_user_id=user.id,
            metadata={
                "reference_no": app.reference_no,
                "comments": comments,
            },
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def assign_application(
        cls,
        db: Session,
        application_id: uuid.UUID,
        user: User,
        target_user_id: uuid.UUID,
        notes: Optional[str] = None,
    ) -> Application:
        """
        Assigns or reassigns an application to an active reviewer, validating regional jurisdiction.
        """
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(joinedload(Application.institution))
            .with_for_update()
        )
        app = db.scalars(stmt).first()
        if not app:
            raise NotFoundError("Application not found.")

        if not cls.check_application_access(app, user, db):
            raise NotFoundError("Application not found.")

        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            raise ForbiddenError("Institution users are not permitted to assign applications.")

        target_user = db.get(User, target_user_id)
        if not target_user or not target_user.is_active:
            raise AppException("Target assignee does not exist or is inactive.", code="INVALID_ASSIGNEE", status_code=400)

        target_role = normalize_role(target_user.role)
        if target_role == UserRole.INSTITUTION_USER:
            raise AppException("Applications cannot be assigned to institutional accounts.", code="INVALID_ASSIGNEE_ROLE", status_code=400)

        # Regional scoping: if assignee has a specific regional office, ensure institution is in that region
        if target_user.region_id:
            inst = app.institution or db.get(Institution, app.institution_id)
            if inst and inst.region_id and inst.region_id != target_user.region_id:
                raise AppException(
                    "Target officer belongs to a regional jurisdiction different from the application's institution.",
                    code="REGIONAL_SCOPE_MISMATCH",
                    status_code=400,
                )

        now = datetime.now(timezone.utc)
        app.assigned_to_user_id = target_user.id

        history = StageHistory(
            id=uuid.uuid4(),
            application_id=app.id,
            from_stage_id=app.current_stage_id,
            to_stage_id=app.current_stage_id,
            action="assigned",
            reason=notes or f"Assigned to {target_user.full_name} ({target_user.role})",
            performed_by_user_id=user.id,
            performed_at=now,
            metadata_={"assigned_to_user_id": str(target_user.id), "assigned_to_name": target_user.full_name},
        )
        db.add(history)

        AuditService.record_action(
            db=db,
            action="APPLICATION_ASSIGNED",
            entity_type="application",
            entity_id=str(app.id),
            actor_user_id=user.id,
            metadata={
                "reference_no": app.reference_no,
                "assigned_to_id": str(target_user.id),
                "assigned_to_name": target_user.full_name,
                "notes": notes,
            },
        )

        db.commit()
        db.refresh(app)
        return app

    @classmethod
    def get_available_actions(cls, app: Application, user: User, db: Session) -> List[str]:
        """
        Computes the list of permitted workflow actions for the authenticated user
        given the application's current state, stage requirements, and RBAC rules.
        """
        if app.status in ("completed", "withdrawn"):
            return []

        role_enum = normalize_role(user.role)
        is_admin = role_enum in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN)
        actions: List[str] = []

        if app.status == "on_hold":
            if role_enum != UserRole.INSTITUTION_USER:
                actions.append("resume")
            return actions

        # When status is in_progress or returned
        if role_enum != UserRole.INSTITUTION_USER:
            actions.append("hold")
            actions.append("assign")

        if app.current_stage_id:
            current_stage = db.get(RouteStage, app.current_stage_id)
            if current_stage:
                can_act = is_admin or (user.role == current_stage.required_role)
                if can_act:
                    # Check if next stage exists
                    next_stage_stmt = select(RouteStage.id).where(
                        RouteStage.route_type_id == app.route_type_id,
                        RouteStage.route_version == app.route_version,
                        RouteStage.sequence == current_stage.sequence + 1,
                    )
                    if db.scalar(next_stage_stmt):
                        actions.append("advance")

                    if role_enum != UserRole.INSTITUTION_USER:
                        actions.append("return")

        return actions
