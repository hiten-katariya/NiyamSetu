"""
NiyamSetu Demonstration Seed Data Script.

Populates initial synthetic development and demonstration data.
All routes, timelines, institutions, and users are synthetic demonstration artifacts.
Do not use in production.
"""
from datetime import date, datetime, timedelta, timezone
import logging
import os
import sys
import uuid

# Ensure backend package is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import get_password_hash
from backend.app.db.session import SessionLocal, engine
from backend.app.models.entities import (
    Application,
    AuditLog,
    Document,
    EscalationRule,
    Institution,
    MessageTemplate,
    Region,
    ReminderRule,
    RouteStage,
    RouteType,
    User,
)
from backend.app.permissions.roles import UserRole
from backend.app.services.audit_service import AuditService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("niyamsetu.seed")


def seed_database(db: Session) -> None:
    logger.info("Checking and seeding demonstration data for NiyamSetu...")

    # 1. Seed Administrative Regions (Synthetic Demo Data)
    demo_regions = [
        {"name": "Northern Regional Office", "code": "NRO"},
        {"name": "Western Regional Office", "code": "WRO"},
        {"name": "Southern Regional Office", "code": "SRO"},
        {"name": "Eastern Regional Office", "code": "ERO"},
    ]
    regions_map = {}
    for r_data in demo_regions:
        stmt = select(Region).where(Region.code == r_data["code"])
        region = db.scalars(stmt).first()
        if not region:
            region = Region(
                id=uuid.uuid4(),
                name=r_data["name"],
                code=r_data["code"],
                is_active=True,
            )
            db.add(region)
            db.flush()
            logger.info(f"Created region: {region.code}")
        regions_map[r_data["code"]] = region

    # 2. Seed Institutions (Synthetic Demo Data)
    demo_institutions = [
        {
            "name": "Apex Institute of Technology & Management (Demo)",
            "code": "INST-DEMO-001",
            "region_code": "NRO",
            "address": "Plot 101, Knowledge Park, Demo City",
            "email": "contact@apex-demo.edu",
        },
        {
            "name": "Vanguard Engineering College (Demo)",
            "code": "INST-DEMO-002",
            "region_code": "WRO",
            "address": "Sector 42, Tech Corridor, Demo Town",
            "email": "contact@vanguard-demo.edu",
        },
    ]
    institutions_map = {}
    for inst_data in demo_institutions:
        stmt = select(Institution).where(Institution.institution_code == inst_data["code"])
        inst = db.scalars(stmt).first()
        if not inst:
            region = regions_map[inst_data["region_code"]]
            inst = Institution(
                id=uuid.uuid4(),
                name=inst_data["name"],
                institution_code=inst_data["code"],
                region_id=region.id,
                address=inst_data["address"],
                contact_email=inst_data["email"],
                is_active=True,
            )
            db.add(inst)
            db.flush()
            logger.info(f"Created institution: {inst.institution_code}")
        institutions_map[inst_data["code"]] = inst

    # 3. Seed Users across all 7 Roles
    admin_pw_hash = get_password_hash(settings.SEED_ADMIN_PASSWORD)
    user_pw_hash = get_password_hash(settings.SEED_DEFAULT_USER_PASSWORD)

    demo_users = [
        {
            "email": "admin@niyamsetu.local",
            "full_name": "System Administrator",
            "role": UserRole.SYSTEM_ADMIN.value,
            "hash": admin_pw_hash,
            "region": None,
            "inst": None,
        },
        {
            "email": "scrutiny.officer@niyamsetu.local",
            "full_name": "Demo Scrutiny Officer",
            "role": UserRole.SCRUTINY_OFFICER.value,
            "hash": user_pw_hash,
            "region": None,
            "inst": None,
        },
        {
            "email": "ro.north@niyamsetu.local",
            "full_name": "Northern Regional Officer",
            "role": UserRole.REGIONAL_OFFICER.value,
            "hash": user_pw_hash,
            "region": "NRO",
            "inst": None,
        },
        {
            "email": "bureau.officer@niyamsetu.local",
            "full_name": "Demo Bureau Officer",
            "role": UserRole.BUREAU_OFFICER.value,
            "hash": user_pw_hash,
            "region": None,
            "inst": None,
        },
        {
            "email": "committee.member@niyamsetu.local",
            "full_name": "Demo Committee Member",
            "role": UserRole.COMMITTEE_MEMBER.value,
            "hash": user_pw_hash,
            "region": None,
            "inst": None,
        },
        {
            "email": "senior.authority@niyamsetu.local",
            "full_name": "Demo Senior Authority",
            "role": UserRole.SENIOR_AUTHORITY.value,
            "hash": user_pw_hash,
            "region": None,
            "inst": None,
        },
        {
            "email": "institution.user@apex-demo.edu",
            "full_name": "Apex Inst Representative",
            "role": UserRole.INSTITUTION_USER.value,
            "hash": user_pw_hash,
            "region": None,
            "inst": "INST-DEMO-001",
        },
    ]

    users_map = {}
    for u in demo_users:
        stmt = select(User).where(User.email == u["email"])
        user = db.scalars(stmt).first()
        if not user:
            reg_id = regions_map[u["region"]].id if u["region"] else None
            inst_id = institutions_map[u["inst"]].id if u["inst"] else None
            user = User(
                id=uuid.uuid4(),
                email=u["email"],
                full_name=u["full_name"],
                role=u["role"],
                password_hash=u["hash"],
                region_id=reg_id,
                institution_id=inst_id,
                is_active=True,
            )
            db.add(user)
            db.flush()
            logger.info(f"Created demo user: {user.email} [{user.role}]")
        users_map[u["email"]] = user

    # 4. Seed Configurable Route Types and Stages (Demonstration Configuration Only)
    # Notice: Explicitly labelled as demo configuration, not hardcoded statutory APH rules
    stmt = select(RouteType).where(RouteType.code == "DEMO_SCRUTINY_EVC")
    demo_route = db.scalars(stmt).first()
    if not demo_route:
        demo_route = RouteType(
            id=uuid.uuid4(),
            name="Sample Scrutiny + EVC Route (Demonstration Only)",
            code="DEMO_SCRUTINY_EVC",
            description="Demonstration route sequence with scrutiny, EVC, and review. Timelines are synthetic parameters.",
            is_active=True,
            current_version=1,
        )
        db.add(demo_route)
        db.flush()

        stages_data = [
            {"code": "SCRUTINY", "name": "Document Scrutiny", "seq": 1, "role": "scrutiny_officer", "days": 7, "day_type": "working"},
            {"code": "RE_SCRUTINY", "name": "Re-Scrutiny (Deficiencies)", "seq": 2, "role": "scrutiny_officer", "days": 5, "day_type": "working"},
            {"code": "EVC_SCHEDULING", "name": "EVC Committee Scheduling", "seq": 3, "role": "regional_officer", "days": 10, "day_type": "calendar"},
            {"code": "EVC_CONDUCT", "name": "EVC Inspection Conduct", "seq": 4, "role": "committee_member", "days": 7, "day_type": "calendar"},
            {"code": "REPORT_REVIEW", "name": "EVC Report Review", "seq": 5, "role": "regional_officer", "days": 5, "day_type": "working"},
            {"code": "FINAL_REVIEW", "name": "Competent Authority Decision Review", "seq": 6, "role": "senior_authority", "days": 7, "day_type": "calendar"},
        ]
        for s in stages_data:
            stage = RouteStage(
                id=uuid.uuid4(),
                route_type_id=demo_route.id,
                route_version=1,
                stage_code=s["code"],
                stage_name=s["name"],
                sequence=s["seq"],
                required_role=s["role"],
                timeline_days=s["days"],
                day_type=s["day_type"],
                is_required=True,
            )
            db.add(stage)
        db.flush()
        logger.info(f"Created demo route: {demo_route.code} with 6 configurable stages")

    # Fetch first stage of demo route
    stmt_stage = select(RouteStage).where(RouteStage.route_type_id == demo_route.id, RouteStage.sequence == 1)
    first_stage = db.scalars(stmt_stage).first()

    # 5. Seed Demonstration Applications
    app_ref = "NS-DEMO-2026-0001"
    stmt = select(Application).where(Application.reference_no == app_ref)
    app = db.scalars(stmt).first()
    if not app:
        inst = institutions_map["INST-DEMO-001"]
        assigned_user = users_map["scrutiny.officer@niyamsetu.local"]
        now = datetime.now(timezone.utc)
        app = Application(
            id=uuid.uuid4(),
            reference_no=app_ref,
            institution_id=inst.id,
            route_type_id=demo_route.id,
            route_version=1,
            current_stage_id=first_stage.id if first_stage else None,
            status="in_progress",
            assigned_to_user_id=assigned_user.id,
            submitted_at=now - timedelta(days=2),
            stage_entered_at=now - timedelta(days=2),
        )
        db.add(app)
        db.flush()
        logger.info(f"Created demonstration application: {app.reference_no}")

    # 6. Seed Configurable Reminder and Escalation Rules
    stmt = select(ReminderRule).where(ReminderRule.name == "Demo 3-Day Prior Reminder")
    if not db.scalars(stmt).first():
        rem = ReminderRule(
            id=uuid.uuid4(),
            name="Demo 3-Day Prior Reminder",
            target_type="application",
            days_before_due=3,
            recipient_roles=["scrutiny_officer", "institution_user"],
            is_active=True,
        )
        db.add(rem)

    stmt = select(EscalationRule).where(EscalationRule.name == "Demo Level 1 Escalation")
    if not db.scalars(stmt).first():
        esc = EscalationRule(
            id=uuid.uuid4(),
            name="Demo Level 1 Escalation",
            target_type="application",
            level=1,
            days_after_due=1,
            recipient_roles=["regional_officer"],
            is_active=True,
        )
        db.add(esc)

    # 7. Record an Initial Seed Audit Log with Hash Chain
    admin_user = users_map["admin@niyamsetu.local"]
    AuditService.record_action(
        db=db,
        action="SEED_DATABASE",
        entity_type="system",
        entity_id="init",
        actor_user_id=admin_user.id,
        metadata={"environment": settings.ENVIRONMENT, "note": "Initial demonstration synthetic data seeded"},
    )

    db.commit()
    logger.info("Demonstration seed data setup completed successfully.")


def main():
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
