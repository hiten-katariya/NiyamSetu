# NiyamSetu Local Development Setup (No Docker)

This guide provides step-by-step instructions for running NiyamSetu completely on your local machine using standard runtimes.

> [!CAUTION]
> **Strict Non-Interference Policy**: If you have existing databases or applications running on your local PostgreSQL server, NiyamSetu must strictly run in its own dedicated database (`niyamsetu_dev`). Never run NiyamSetu migrations against an existing project's database or alter existing users.

---

## 1. System Requirements

| Tool | Minimum Version | Tested Version | Verification Command |
|---|---|---|---|
| **Python** | 3.12+ | 3.13.5 | `python --version` |
| **Node.js** | 20+ | v22.17.1 | `node --version` |
| **npm** | 10+ | 10.9.2 | `npm --version` |
| **PostgreSQL** | 15+ | 16.15 | `psql --version` |

---

## 2. PostgreSQL Configuration

NiyamSetu requires a locally running PostgreSQL instance.

### A. Verify Local PostgreSQL Service
**Windows (PowerShell)**:
```powershell
Get-Service -Name *postgres*
```
If not running, start the service:
```powershell
Start-Service -Name postgresql-x64-16
```

### B. Create Dedicated User and Database
Open a PostgreSQL administrative shell using `psql`:
```powershell
psql -h localhost -p 5432 -U postgres
```
Run the following SQL commands to safely isolate NiyamSetu:
```sql
-- Create dedicated database user (replace with a secure local password)
CREATE USER niyamsetu_user WITH ENCRYPTED PASSWORD 'your_secure_local_password';

-- Create isolated database
CREATE DATABASE niyamsetu_dev OWNER niyamsetu_user;

-- Grant permissions strictly on the target database
GRANT ALL PRIVILEGES ON DATABASE niyamsetu_dev TO niyamsetu_user;
\c niyamsetu_dev
GRANT ALL ON SCHEMA public TO niyamsetu_user;
```

---

## 3. Repository Configuration

1. Copy the configuration template:
   ```powershell
   # Windows PowerShell
   Copy-Item .env.example .env

   # Linux / macOS
   cp .env.example .env
   ```

2. Edit `.env` to update `DATABASE_URL`:
   ```ini
   DATABASE_URL=postgresql+psycopg2://niyamsetu_user:your_secure_local_password@localhost:5432/niyamsetu_dev
   ```

---

## 4. Backend Setup

### A. Python Environment Setup
From the repository root:
```powershell
# Optional: Create a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1    # Linux/macOS: source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### B. Apply Database Migrations
Run Alembic from the `backend/` directory to construct all 24 schema tables:
```powershell
cd backend
python -m alembic upgrade head
cd ..
```

### C. Seed Synthetic Demonstration Data
Load synthetic regions, institutions, demo role accounts, sample routes, and mock applications:
```powershell
python backend/seed/seed_data.py
```

### D. Bootstrap Administrative User (CLI)
Create a dedicated system administrator safely via CLI with interactive password prompt or random generation:
```powershell
# Interactive prompt:
python backend/app/commands/create_admin.py --email admin.ops@niyamsetu.local --name "Operations Lead"

# Or with specified password:
python backend/app/commands/create_admin.py --email admin.ops@niyamsetu.local --name "Operations Lead" --password "YourStrongPassword123!"
```

### E. Start Backend API Server
```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```
Verify the API:
- **API Status**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Database Readiness**: [http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 5. Background Worker Setup

The background worker runs APScheduler as a detached independent process:
```powershell
# Open a new terminal with the Python environment active
python worker/run.py
```
The worker executes scheduled scans every hour, records execution history in `scheduler_runs`, and guarantees deduplicated notification delivery.

---

## 6. Frontend Setup

From the repository root:
```powershell
cd frontend
npm install
npm run dev
```
The React development server runs at:
- **Web App**: [http://localhost:5173](http://localhost:5173)

---

## 7. Running Tests

### Backend Unit & Integration Tests
```powershell
python -m pytest backend/tests -v
```

### Frontend Type Checking & Production Build
```powershell
cd frontend
npm run lint
npm run build
```
