from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import BadRequestError, NotFoundError
from backend.app.models.entities import (
    ConfigVersion,
    EscalationRule,
    Holiday,
    MessageTemplate,
    ReminderRule,
    RouteStage,
    RouteType,
    User,
)
from backend.app.services.audit_service import AuditService


class ConfigService:
    @staticmethod
    def record_config_change(
        db: Session,
        config_type: str,
        actor_user: User,
        change_summary: str,
        ip_address: Optional[str] = None,
    ) -> ConfigVersion:
        """
        Records an immutable configuration version entry and links it into the audit trail.
        """
        current_max = (
            db.scalar(
                select(func.max(ConfigVersion.version)).where(ConfigVersion.config_type == config_type)
            )
            or 0
        )
        new_version = current_max + 1

        version_record = ConfigVersion(
            id=uuid.uuid4(),
            config_type=config_type,
            version=new_version,
            changed_by_user_id=actor_user.id,
            change_summary=change_summary,
            created_at=datetime.now(timezone.utc),
        )
        db.add(version_record)
        db.flush()

        AuditService.record_action(
            db=db,
            action=f"config_version_created",
            entity_type="config_version",
            entity_id=str(version_record.id),
            actor_user_id=actor_user.id,
            ip_address=ip_address,
            metadata={
                "config_type": config_type,
                "version": new_version,
                "change_summary": change_summary,
            },
        )
        return version_record

    @classmethod
    def update_route_stage(
        cls,
        db: Session,
        stage_id: uuid.UUID,
        stage_name: Optional[str],
        timeline_days: Optional[int],
        day_type: Optional[str],
        required_role: Optional[str],
        is_required: Optional[bool],
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> RouteStage:
        """
        Updates an existing workflow stage while preserving historical route versions.
        """
        stage = db.get(RouteStage, stage_id)
        if not stage:
            raise NotFoundError("Route stage not found")

        changes = []
        if stage_name is not None and stage_name != stage.stage_name:
            changes.append(f"name: {stage.stage_name} -> {stage_name}")
            stage.stage_name = stage_name

        if timeline_days is not None and timeline_days != stage.timeline_days:
            if timeline_days <= 0:
                raise BadRequestError("Timeline days must be a positive integer greater than zero")
            changes.append(f"timeline: {stage.timeline_days}d -> {timeline_days}d")
            stage.timeline_days = timeline_days

        if day_type is not None and day_type != stage.day_type:
            if day_type not in ("working_days", "calendar_days"):
                raise BadRequestError("Day type must be 'working_days' or 'calendar_days'")
            changes.append(f"day_type: {stage.day_type} -> {day_type}")
            stage.day_type = day_type

        if required_role is not None and required_role != stage.required_role:
            changes.append(f"role: {stage.required_role} -> {required_role}")
            stage.required_role = required_role

        if is_required is not None and is_required != stage.is_required:
            changes.append(f"is_required: {stage.is_required} -> {is_required}")
            stage.is_required = is_required

        summary = f"Updated stage {stage.stage_code}: {', '.join(changes)}. Reason: {change_reason}"
        cls.record_config_change(db, "route_stage", actor_user, summary, ip_address)
        db.commit()
        db.refresh(stage)
        return stage

    @classmethod
    def create_reminder_rule(
        cls,
        db: Session,
        name: str,
        target_type: str,
        days_before_due: int,
        recipient_roles: List[str],
        is_active: bool,
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> ReminderRule:
        if days_before_due < 0:
            raise BadRequestError("Days before due must be non-negative")

        rule = ReminderRule(
            id=uuid.uuid4(),
            name=name,
            target_type=target_type,
            days_before_due=days_before_due,
            recipient_roles=recipient_roles,
            is_active=is_active,
        )
        db.add(rule)
        db.flush()

        summary = f"Created reminder rule '{name}' ({days_before_due}d before due for {target_type}). Reason: {change_reason}"
        cls.record_config_change(db, "reminder_rule", actor_user, summary, ip_address)
        db.commit()
        db.refresh(rule)
        return rule

    @classmethod
    def update_reminder_rule(
        cls,
        db: Session,
        rule_id: uuid.UUID,
        name: str,
        target_type: str,
        days_before_due: int,
        recipient_roles: List[str],
        is_active: bool,
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> ReminderRule:
        rule = db.get(ReminderRule, rule_id)
        if not rule:
            raise NotFoundError("Reminder rule not found")

        rule.name = name
        rule.target_type = target_type
        rule.days_before_due = days_before_due
        rule.recipient_roles = recipient_roles
        rule.is_active = is_active

        summary = f"Updated reminder rule '{name}'. Reason: {change_reason}"
        cls.record_config_change(db, "reminder_rule", actor_user, summary, ip_address)
        db.commit()
        db.refresh(rule)
        return rule

    @classmethod
    def delete_reminder_rule(
        cls,
        db: Session,
        rule_id: uuid.UUID,
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> None:
        rule = db.get(ReminderRule, rule_id)
        if not rule:
            raise NotFoundError("Reminder rule not found")

        name = rule.name
        db.delete(rule)
        summary = f"Deleted reminder rule '{name}'. Reason: {change_reason}"
        cls.record_config_change(db, "reminder_rule", actor_user, summary, ip_address)
        db.commit()

    @classmethod
    def create_escalation_rule(
        cls,
        db: Session,
        name: str,
        target_type: str,
        level: int,
        days_after_due: int,
        recipient_roles: List[str],
        is_active: bool,
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> EscalationRule:
        if days_after_due < 0:
            raise BadRequestError("Days after due must be non-negative")
        if level < 1:
            raise BadRequestError("Escalation level must be at least 1")

        rule = EscalationRule(
            id=uuid.uuid4(),
            name=name,
            target_type=target_type,
            level=level,
            days_after_due=days_after_due,
            recipient_roles=recipient_roles,
            is_active=is_active,
        )
        db.add(rule)
        db.flush()

        summary = f"Created escalation rule '{name}' (Level {level}, +{days_after_due}d). Reason: {change_reason}"
        cls.record_config_change(db, "escalation_rule", actor_user, summary, ip_address)
        db.commit()
        db.refresh(rule)
        return rule

    @classmethod
    def update_escalation_rule(
        cls,
        db: Session,
        rule_id: uuid.UUID,
        name: str,
        target_type: str,
        level: int,
        days_after_due: int,
        recipient_roles: List[str],
        is_active: bool,
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> EscalationRule:
        rule = db.get(EscalationRule, rule_id)
        if not rule:
            raise NotFoundError("Escalation rule not found")

        rule.name = name
        rule.target_type = target_type
        rule.level = level
        rule.days_after_due = days_after_due
        rule.recipient_roles = recipient_roles
        rule.is_active = is_active

        summary = f"Updated escalation rule '{name}' (Level {level}). Reason: {change_reason}"
        cls.record_config_change(db, "escalation_rule", actor_user, summary, ip_address)
        db.commit()
        db.refresh(rule)
        return rule

    @classmethod
    def delete_escalation_rule(
        cls,
        db: Session,
        rule_id: uuid.UUID,
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> None:
        rule = db.get(EscalationRule, rule_id)
        if not rule:
            raise NotFoundError("Escalation rule not found")

        name = rule.name
        db.delete(rule)
        summary = f"Deleted escalation rule '{name}'. Reason: {change_reason}"
        cls.record_config_change(db, "escalation_rule", actor_user, summary, ip_address)
        db.commit()

    @classmethod
    def create_holiday(
        cls,
        db: Session,
        name: str,
        holiday_date: date,
        region_id: Optional[uuid.UUID],
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> Holiday:
        existing = db.scalar(
            select(Holiday).where(
                Holiday.holiday_date == holiday_date,
                Holiday.region_id == region_id,
            )
        )
        if existing:
            raise BadRequestError(f"A holiday is already registered for date {holiday_date}")

        hol = Holiday(
            id=uuid.uuid4(),
            name=name,
            holiday_date=holiday_date,
            region_id=region_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(hol)
        db.flush()

        summary = f"Created holiday '{name}' on {holiday_date}. Reason: {change_reason}"
        cls.record_config_change(db, "holiday", actor_user, summary, ip_address)
        db.commit()
        db.refresh(hol)
        return hol

    @classmethod
    def delete_holiday(
        cls,
        db: Session,
        holiday_id: uuid.UUID,
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> None:
        hol = db.get(Holiday, holiday_id)
        if not hol:
            raise NotFoundError("Holiday record not found")

        name = hol.name
        dt = hol.holiday_date
        db.delete(hol)
        summary = f"Deleted holiday '{name}' on {dt}. Reason: {change_reason}"
        cls.record_config_change(db, "holiday", actor_user, summary, ip_address)
        db.commit()

    @classmethod
    def update_message_template(
        cls,
        db: Session,
        template_id: uuid.UUID,
        subject_template: str,
        body_template: str,
        is_active: bool,
        change_reason: str,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> MessageTemplate:
        tpl = db.get(MessageTemplate, template_id)
        if not tpl:
            raise NotFoundError("Message template not found")

        tpl.subject_template = subject_template
        tpl.body_template = body_template
        tpl.is_active = is_active

        summary = f"Updated message template '{tpl.code}'. Reason: {change_reason}"
        cls.record_config_change(db, "message_template", actor_user, summary, ip_address)
        db.commit()
        db.refresh(tpl)
        return tpl
