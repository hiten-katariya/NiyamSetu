"""
NiyamSetu Combined Local Service Runner.

Spawns and manages both:
1. The FastAPI Backend API server (uvicorn on port 8000)
2. The Background Worker process (worker/run.py with APScheduler)

Maintains architectural decoupling: each runs in its own separate operating system
process, without executing background jobs inside API startup.
Pressing CTRL+C shuts down both processes gracefully.
"""
import os
import signal
import subprocess
import sys
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def start_services():
    print("=" * 65)
    print("  Starting NiyamSetu Local Services (Backend API + Worker)")
    print("=" * 65)
    print(f"Working Directory: {ROOT_DIR}")
    print("API Server:        http://localhost:8000")
    print("Interactive Docs:  http://localhost:8000/docs")
    print("Readiness Probe:   http://localhost:8000/api/v1/health/ready")
    print("-" * 65)
    print("Press CTRL+C at any time to shut down both processes.")
    print("-" * 65)

    # 1. Start Backend API server process
    api_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--reload",
        "--port",
        "8000",
    ]
    api_proc = subprocess.Popen(api_cmd, cwd=ROOT_DIR)
    print(f"[PROCESS] Started FastAPI Backend (PID: {api_proc.pid})")

    # Give API a moment to initialize ports before worker connects
    time.sleep(1)

    # 2. Start Background Worker process
    worker_cmd = [
        sys.executable,
        os.path.join(ROOT_DIR, "worker", "run.py"),
    ]
    worker_proc = subprocess.Popen(worker_cmd, cwd=ROOT_DIR)
    print(f"[PROCESS] Started Background Worker (PID: {worker_proc.pid})")
    print("-" * 65)

    processes = [("API", api_proc), ("Worker", worker_proc)]

    def shutdown(signum=None, frame=None):
        print("\n[STOPPING] Shutting down NiyamSetu services gracefully...")
        for name, proc in processes:
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
        # Wait up to 5 seconds for termination
        for name, proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("[STOPPED] All services terminated.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    # Monitor processes
    try:
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"\n[ALERT] {name} process exited with code {ret}.")
                    shutdown()
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    start_services()
