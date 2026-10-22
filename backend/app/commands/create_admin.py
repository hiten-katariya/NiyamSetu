"""
NiyamSetu Administrator Bootstrap Command.

Explicit CLI command for bootstrapping the initial system administrator account.
- Never creates duplicate administrators.
- Obtains password from environment variable, arguments, or secure interactive prompt.
- Securely hashes passwords with bcrypt.
- Records the bootstrap action in the tamper-evident audit log.
- Never exposes an unauthenticated public API endpoint.
"""
import argparse
import getpass
import os
import sys
import uuid

# Ensure backend root is on sys.path
cmd_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(cmd_dir, "..", ".."))
repo_root = os.path.abspath(os.path.join(backend_dir, ".."))
for p in [repo_root, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import select

from backend.app.core.security import get_password_hash
from backend.app.db.session import SessionLocal
from backend.app.models.entities import User
from backend.app.permissions.roles import UserRole
from backend.app.services.audit_service import AuditService


def bootstrap_admin(email: str, full_name: str, password: str) -> bool:
    normalized_email = email.lower().strip()
    db = SessionLocal()
    try:
        # Check if user already exists
        stmt = select(User).where(User.email == normalized_email)
        existing = db.scalars(stmt).first()
        if existing:
            print(f"[ERROR] User with email '{normalized_email}' already exists (Role: {existing.role}).")
            print("Aborting bootstrap to prevent duplicate administrator creation.")
            return False

        # Hash password securely
        pw_hash = get_password_hash(password)

        new_admin = User(
            id=uuid.uuid4(),
            email=normalized_email,
            full_name=full_name,
            role=UserRole.SYSTEM_ADMIN.value,
            password_hash=pw_hash,
            region_id=None,
            institution_id=None,
            is_active=True,
        )
        db.add(new_admin)
        db.flush()

        # Record bootstrap in audit trail
        AuditService.record_action(
            db=db,
            action="BOOTSTRAP_ADMIN",
            entity_type="user",
            entity_id=str(new_admin.id),
            actor_user_id=new_admin.id,
            metadata={"email": normalized_email, "role": new_admin.role},
        )
        db.commit()
        print(f"[SUCCESS] System administrator '{normalized_email}' created successfully (ID: {new_admin.id}).")
        return True
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Bootstrap an initial system administrator for NiyamSetu")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--name", default="System Administrator", help="Administrator full name")
    parser.add_argument("--password", help="Administrator password (or use ADMIN_PASSWORD env var or interactive prompt)")

    args = parser.parse_args()

    email = args.email or os.getenv("ADMIN_EMAIL")
    if not email:
        email = input("Enter administrator email: ").strip()

    name = args.name or os.getenv("ADMIN_NAME", "System Administrator")

    password = args.password or os.getenv("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Enter administrator password: ")
        confirm = getpass.getpass("Confirm administrator password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match. Aborting.")
            sys.exit(1)

    if len(password) < 8:
        print("[ERROR] Password must be at least 8 characters long.")
        sys.exit(1)

    success = bootstrap_admin(email, name, password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
