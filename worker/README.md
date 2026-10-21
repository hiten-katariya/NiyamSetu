# NiyamSetu Background Worker

The NiyamSetu background worker is an independent Python process running APScheduler.

## Design Principles
1. **Isolated Execution**: The worker runs in a separate process, completely isolated from FastAPI API startup. A heavy report generation, daily scan, or notification batch does not impact API responsiveness.
2. **One Clock**: All date calculations use the centralized clock service (supporting simulated dates during testing).
3. **Idempotence**: Every notification, reminder, and escalation check uses database-level deduplication keys (`dedupe_key`) to ensure that re-running jobs or catching up on missed jobs never generates duplicate notifications or escalations.
4. **Auditability**: Every run is logged in the `scheduler_runs` table with items scanned, items processed, and error summaries.

## Running the Worker

From the repository root with the Python virtual environment activated:

```powershell
python worker/run.py
```

Or on Linux/macOS:
```bash
python worker/run.py
```
