# NiyamSetu — AICTE Workflow & Statutory Compliance Platform

NiyamSetu is a configurable digital platform for managing and monitoring AICTE approval-related workflows, institutional compliance, Expert Visit Committee (EVC) scheduling, time-bound undertakings, document validity, automated deadline notifications, multi-tier escalations, role-specific dashboards, and tamper-evident audit history.

> **Important Principles**:
> - **Human Decision-Making**: The system supports authorized human decision-makers and **never independently grants or rejects statutory approvals**.
> - **Rules in Data, Not Code**: Workflow routes, stage timelines, reminder intervals, and escalation chains are fully configurable database records.
> - **No Hardcoded Regulations**: The platform does not hardcode unconfirmed statutory regulations or approval timelines.
> - **Synthetic Demonstration Data**: All initial data, sample routes, and timelines are synthetic demonstration artifacts.
> - **Tamper-Evident Auditability**: Every important action is attributed to an authenticated user and recorded in an append-only, SHA-256 hash-chained audit log.

---

## Architecture Overview

NiyamSetu is architected as a clean, decoupled monorepo:

```
                      ┌────────────────────────────────────────┐
                      │    React + Vite + Tailwind Frontend     │
                      │    (Liquid, accessible, light theme)   │
                      └───────────────────┬────────────────────┘
                                          │  REST /api/v1
                                          ▼
                      ┌────────────────────────────────────────┐
                      │          FastAPI Backend Server         │
                      │  (Pydantic v2, SQLAlchemy 2, Alembic)   │
                      └───────────────┬────────────────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     PostgreSQL (Local Engine)   │       │   APScheduler Worker Process    │
│    (Target: niyamsetu_dev)      │◀──────│  (Independent detached runner)  │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

---

## Repository Structure

```
├── frontend/                     # React 18 + Vite + TypeScript + Tailwind CSS UI
│   ├── src/
│   │   ├── app/                  # Application router and root App component
│   │   ├── components/           # Reusable UI components (Button, Input, Badge, Card, Table)
│   │   │   └── layout/           # AppShell, Header, Sidebar
│   │   ├── features/             # Feature views (dashboard, applications, evc, compliance, etc.)
│   │   ├── lib/                  # Typed API client and utilities
│   │   ├── styles/               # Fluid liquid CSS & typography tokens
│   │   └── types/                # TypeScript interface definitions
│   ├── package.json
│   └── vite.config.ts
├── backend/                      # Python 3.12+ FastAPI backend
│   ├── app/
│   │   ├── api/v1/               # Versioned API endpoints (/health, /auth, /applications, etc.)
│   │   ├── core/                 # Config, security, sanitized logging, exception handlers
│   │   ├── db/                   # SQLAlchemy 2 base, session management, ping health
│   │   ├── models/               # Typed ORM models for all 24 schema entities
│   │   ├── permissions/          # RBAC roles, permission sets, and regional/inst scoping
│   │   ├── repositories/         # Data access repositories
│   │   ├── schemas/              # Pydantic v2 request/response schemas
│   │   ├── services/             # Audit hash-chain, health, auth services
│   │   └── main.py               # FastAPI application entrypoint
│   ├── migrations/               # Alembic database migrations
│   ├── seed/                     # Idempotent development seed data script
│   ├── tests/                    # Pytest test suite (health, security, rbac, audit hash)
│   ├── alembic.ini
│   ├── requirements.txt
│   └── pyproject.toml
├── worker/                       # APScheduler background worker process
│   ├── run.py                    # Worker entrypoint (decoupled from API startup)
│   └── README.md
├── docs/                         # Architecture, PRD, database, API, and setup documentation
│   ├── LOCAL_SETUP.md            # Step-by-step local setup guide (NO Docker)
│   ├── DATABASE.md               # Complete schema specification & index guide
│   ├── API.md                    # REST endpoint specifications & error formats
│   ├── TECH.md                   # Technical design document
│   ├── PLAN.md                   # Phased implementation roadmap
│   ├── PRD.md                    # Product requirements document
│   └── UI-UX.md                  # UI/UX design specifications & tokens
├── .env.example                  # Environment variable configuration template
├── .gitignore                    # Comprehensive ignore rules (no secrets committed)
└── README.md                     # Project overview and quick start guide
```

---

## Local Development Quick Start (No Docker)

### 1. Prerequisites
- **Python**: 3.12+ (Python 3.13 tested and verified)
- **Node.js**: 20+ (Node v22 tested and verified)
- **PostgreSQL**: Installed directly on the local machine (running on port 5432)

### 2. Environment Setup
Copy the template configuration:
```powershell
Copy-Item .env.example .env
```
Ensure `DATABASE_URL` in `.env` points to your target `niyamsetu_dev` database:
```ini
DATABASE_URL=postgresql+psycopg2://niyamsetu_user:your_password@localhost:5432/niyamsetu_dev
```

### 3. Database Initialization & Migrations
Create the target database and user using local `psql`:
```sql
CREATE DATABASE niyamsetu_dev;
CREATE USER niyamsetu_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE niyamsetu_dev TO niyamsetu_user;
```
Run Alembic migrations to build the schema:
```powershell
cd backend
python -m alembic upgrade head
```

### 4. Seed Demonstration Data
Seed synthetic regions, institutions, test users, demo routes, and sample applications:
```powershell
python backend/seed/seed_data.py
```

### 5. Running the Backend API and Background Worker (Unified Runner)
Start both the FastAPI backend and APScheduler worker together with a single command:
`powershell
python run_services.py
`
*(Or on Windows PowerShell: .\start_services.ps1)*

Both services run as separate decoupled processes. Pressing CTRL+C terminates both gracefully.
- **Swagger Documentation**: http://localhost:8000/docs
- **Health & Readiness Check**: http://localhost:8000/api/v1/health/ready

*(Alternatively, you can run them individually: python -m uvicorn backend.app.main:app --reload --port 8000 and python worker/run.py in separate terminals).*

### 6. Running the Frontend
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to access the portal.

---

## Testing & Verification

Run the backend automated test suite:
```powershell
python -m pytest backend/tests -v
```

Run frontend type checking and production build:
```powershell
cd frontend
npm run lint
npm run build
```
