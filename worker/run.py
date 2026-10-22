"""
NiyamSetu Background Worker Process.

Runs scheduled deadline scans, automated reminders, and escalations
independently from the FastAPI API process using APScheduler.
Ensures API startup is not blocked and jobs do not degrade API responsiveness.
"""
import argparse
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
from worker.deadline_scan import execute_deadline_scan

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("niyamsetu.worker")


def daily_deadline_and_reminder_scan():
    """
    Executes the deadline scan and reminder/escalation processing.
    """
    logger.info("Executing scheduled deadline, reminder, and escalation scan...")
    try:
        res = execute_deadline_scan()
        logger.info(f"Scan completed: {res}")
    except Exception as exc:
        logger.error(f"Error during scheduled scan: {exc}", exc_info=True)


def main():
    parser = argparse.ArgumentParser(description="NiyamSetu Background Worker Process")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Execute a single deadline scan and exit immediately (useful for testing and CLI cron jobs).",
    )
    args = parser.parse_args()

    if args.once:
        logger.info("Running single deadline scan via --once flag...")
        res = execute_deadline_scan()
        logger.info(f"Single scan finished: {res}")
        sys.exit(0 if res.get("status") == "success" else 1)

    logger.info("Starting NiyamSetu background worker daemon (APScheduler)...")
    scheduler = BlockingScheduler(timezone="UTC")

    # Add scheduled scan job (every 60 minutes)
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
