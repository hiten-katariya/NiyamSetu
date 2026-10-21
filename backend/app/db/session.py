from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.core.logging import logger

# Create SQLAlchemy 2 engine
# Uses pool_pre_ping=True to check connection vitality
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request.
    Closes the session cleanly upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> Tuple[bool, str]:
    """
    Checks if the database is reachable and accepting queries.
    Returns (is_connected, message).
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True, "Database connection healthy"
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        return False, str(exc)
