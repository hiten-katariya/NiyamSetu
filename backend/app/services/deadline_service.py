from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
import uuid
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.models.entities import (
    Application,
    Holiday,
    Institution,
    RouteStage,
    StageHistory,
)


@dataclass
class DeadlineCalculationResult:
    due_date: Optional[datetime]
    days_remaining: Optional[float]
    is_overdue: bool
    is_due_soon: bool
    ageing_days: float
    total_hold_days: float
    day_type: str
    timeline_days: Optional[int]
    calculation_basis: Dict[str, Any] = field(default_factory=dict)


class DeadlineService:
    """
    Core Deterministic Deadline & Stage Ageing Engine.
    Computes exact deadlines based on pinned route-stage timelines, calendar vs working days,
    region-specific holidays, and authorized hold duration deductions.
    """

    @staticmethod
    def get_region_holidays(db: Session, region_id: Optional[uuid.UUID]) -> Set[date]:
        """
        Retrieves all active holiday dates for a specific region, including national holidays.
        """
        stmt = select(Holiday.holiday_date)
        if region_id:
            stmt = stmt.where(or_(Holiday.region_id == region_id, Holiday.region_id.is_(None)))
        else:
            stmt = stmt.where(Holiday.region_id.is_(None))

        holiday_records = db.scalars(stmt).all()
        return set(holiday_records)

    @classmethod
    def calculate_raw_deadline(
        cls,
        start_datetime: datetime,
        timeline_days: int,
        day_type: str = "calendar",
        holiday_dates: Optional[Set[date]] = None,
    ) -> datetime:
        """
        Calculates target deadline from start timestamp and timeline duration.
        - Calendar days: straightforward timedelta addition.
        - Working days: skips weekends (Sat/Sun) and configured holidays.
        """
        if timeline_days <= 0:
            return start_datetime

        # Ensure UTC timezone awareness
        if start_datetime.tzinfo is None:
            start_datetime = start_datetime.replace(tzinfo=timezone.utc)

        if day_type.lower() == "calendar":
            return start_datetime + timedelta(days=timeline_days)

        # Working days calculation
        holidays = holiday_dates or set()
        current_date = start_datetime.date()
        allocated_working_days = 0

        while allocated_working_days < timeline_days:
            current_date += timedelta(days=1)
            # Weekend check: 5 = Saturday, 6 = Sunday
            if current_date.weekday() in (5, 6):
                continue
            # Holiday check
            if current_date in holidays:
                continue
            allocated_working_days += 1

        # Preserve the time component of the original entry timestamp
        return datetime.combine(current_date, start_datetime.time(), tzinfo=timezone.utc)

    @classmethod
    def calculate_hold_duration(
        cls,
        db: Session,
        application_id: uuid.UUID,
        since_datetime: datetime,
        as_of_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculates the total time (in seconds) the application was paused under official hold
        since the current stage was entered.
        """
        now = as_of_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        stmt = (
            select(StageHistory)
            .where(
                StageHistory.application_id == application_id,
                StageHistory.performed_at >= since_datetime,
                StageHistory.action.in_(["hold", "resume"]),
            )
            .order_by(StageHistory.performed_at.asc())
        )
        events = list(db.scalars(stmt).all())

        total_paused_seconds = 0.0
        current_hold_start: Optional[datetime] = None

        for event in events:
            evt_time = event.performed_at
            if evt_time.tzinfo is None:
                evt_time = evt_time.replace(tzinfo=timezone.utc)

            if event.action == "hold":
                current_hold_start = evt_time
            elif event.action == "resume" and current_hold_start is not None:
                paused = (evt_time - current_hold_start).total_seconds()
                if paused > 0:
                    total_paused_seconds += paused
                current_hold_start = None

        # If currently on hold without a resume event
        if current_hold_start is not None:
            paused = (now - current_hold_start).total_seconds()
            if paused > 0:
                total_paused_seconds += paused

        return total_paused_seconds

    @classmethod
    def calculate_application_deadline(
        cls,
        db: Session,
        application: Application,
        as_of_time: Optional[datetime] = None,
    ) -> DeadlineCalculationResult:
        """
        Computes the complete deadline result for an active application.
        Integrates pinned route-stage timeline, working days, holidays, hold extensions, and ageing.
        """
        now = as_of_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # Closed applications do not have active deadlines
        if application.status in ("completed", "withdrawn"):
            return DeadlineCalculationResult(
                due_date=None,
                days_remaining=None,
                is_overdue=False,
                is_due_soon=False,
                ageing_days=0.0,
                total_hold_days=0.0,
                day_type="calendar",
                timeline_days=None,
                calculation_basis={"status": application.status, "message": "Application is closed."},
            )

        if not application.current_stage_id:
            return DeadlineCalculationResult(
                due_date=None,
                days_remaining=None,
                is_overdue=False,
                is_due_soon=False,
                ageing_days=0.0,
                total_hold_days=0.0,
                day_type="calendar",
                timeline_days=None,
                calculation_basis={"message": "No active stage assigned."},
            )

        stage = application.current_stage
        if not stage or stage.id != application.current_stage_id:
            stage = db.get(RouteStage, application.current_stage_id)
        if not stage or stage.timeline_days is None or stage.timeline_days <= 0:
            return DeadlineCalculationResult(
                due_date=None,
                days_remaining=None,
                is_overdue=False,
                is_due_soon=False,
                ageing_days=0.0,
                total_hold_days=0.0,
                day_type=stage.day_type if stage else "calendar",
                timeline_days=stage.timeline_days if stage else None,
                calculation_basis={"message": "No configured timeline duration for stage."},
            )

        stage_entered = application.stage_entered_at or application.created_at
        if stage_entered.tzinfo is None:
            stage_entered = stage_entered.replace(tzinfo=timezone.utc)

        # Resolve region holidays
        inst = application.institution or db.get(Institution, application.institution_id)
        region_id = inst.region_id if inst else None
        holidays = cls.get_region_holidays(db, region_id)

        # 1. Base deadline
        base_deadline = cls.calculate_raw_deadline(
            start_datetime=stage_entered,
            timeline_days=stage.timeline_days,
            day_type=stage.day_type,
            holiday_dates=holidays,
        )

        # 2. Hold deductions
        paused_seconds = cls.calculate_hold_duration(
            db=db,
            application_id=application.id,
            since_datetime=stage_entered,
            as_of_time=now,
        )
        hold_days = round(paused_seconds / 86400.0, 2)

        # 3. Final extended deadline
        due_date = base_deadline + timedelta(seconds=paused_seconds)

        # 4. Net ageing
        gross_age_seconds = max(0.0, (now - stage_entered).total_seconds())
        net_age_seconds = max(0.0, gross_age_seconds - paused_seconds)
        ageing_days = round(net_age_seconds / 86400.0, 1)

        # 5. Overdue and due-soon determinations
        is_overdue = now > due_date
        days_remaining = round((due_date - now).total_seconds() / 86400.0, 1)
        is_due_soon = (not is_overdue) and (0.0 <= days_remaining <= 3.0)

        basis = {
            "stage_entered_at": stage_entered.isoformat(),
            "timeline_days": stage.timeline_days,
            "day_type": stage.day_type,
            "holidays_applied_count": len(holidays),
            "hold_deduction_seconds": paused_seconds,
            "hold_deduction_days": hold_days,
            "base_deadline": base_deadline.isoformat(),
            "final_due_date": due_date.isoformat(),
            "as_of_time": now.isoformat(),
        }

        return DeadlineCalculationResult(
            due_date=due_date,
            days_remaining=days_remaining,
            is_overdue=is_overdue,
            is_due_soon=is_due_soon,
            ageing_days=ageing_days,
            total_hold_days=hold_days,
            day_type=stage.day_type,
            timeline_days=stage.timeline_days,
            calculation_basis=basis,
        )
