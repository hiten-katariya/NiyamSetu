"""
NiyamSetu Background Worker Process.

Runs scheduled jobs independently from the FastAPI API process using APScheduler.
Ensures API startup is not blocked and jobs do not degrade API responsiveness.
"""
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone

# Ensure repository root is on sys.path
worker_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(worker_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

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
    try:
        from backend.app.core.config import settings
        logger.info(f"Worker connected to backend in '{settings.ENVIRONMENT}' environment.")
    except Exception as exc:
        logger.warning(f"Worker backend notice: {exc}")
    logger.info("Daily deadline scan complete. Items scanned: 0 (foundation phase).")


def main():
    logger.info("Starting NiyamSetu background worker...")
    scheduler = BlockingScheduler(timezone="UTC")

    # Add scan job
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
