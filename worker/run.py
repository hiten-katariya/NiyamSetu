"""
NiyamSetu Background Worker Process.

Runs scheduled jobs independently from the FastAPI API process using APScheduler.
Ensures API startup is not blocked and jobs do not degrade API responsiveness.
"""
import logging
import signal
import sys
import time
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("niyamsetu.worker")


def daily_deadline_and_reminder_scan():
    """
    Scans applications, undertakings, documents, and EVCs for approaching due dates
    and overdue status. Generates notifications and escalations idempotently.
    """
    logger.info("Running daily deadline and reminder scan...")
    # In Phase 1 foundation: worker stub reports healthy execution and logs execution
    try:
        from backend.app.core.config import settings
        logger.info(f"Worker connected with environment: {settings.ENVIRONMENT}")
    except Exception as exc:
        logger.warning(f"Worker running in standalone mode (backend configuration notice: {exc})")
    logger.info("Daily deadline scan complete. Items scanned: 0 (foundation phase).")


def main():
    logger.info("Starting NiyamSetu background worker...")
    scheduler = BlockingScheduler(timezone="UTC")

    # Add daily scan job (runs at UTC 00:00 or configurable intervals)
    scheduler.add_job(
        daily_deadline_and_reminder_scan,
        "interval",
        minutes=60,
        id="deadline_scan",
        name="Hourly Deadline and Escalation Scan",
        next_run_time=datetime.now(timezone.utc),
    )

    def shutdown(signum, frame):
        logger.info("Received termination signal. Shutting down worker gracefully...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker stopped.")


if __name__ == "__main__":
    main()
