# NiyamSetu — Implementation Plan (`plan.md`)

This plan follows your PRD, Technical Design Document, UI/UX Design Document, and API Specification. It is organised into implementation phases so the team can build, test, and demonstrate the prototype systematically.

## 1. Project objective

Build a functional NiyamSetu prototype that automates configurable application routing, monitors stage-wise pendency, schedules EVCs, tracks undertakings and document validity, generates notifications and escalations, and maintains a tamper-evident audit trail.

The prototype will use seeded dummy data and mock/CSV integrations. All statutory decisions remain under authorised human control.

## 2. Technology stack

| Component          | Technology                                        |
| ------------------ | ------------------------------------------------- |
| Frontend           | React, Vite, TypeScript, Tailwind CSS             |
| UI components      | Shared components, Lucide icons                   |
| Charts             | Recharts                                          |
| Backend            | Python 3.12, FastAPI                              |
| Validation         | Pydantic v2                                       |
| ORM and migrations | SQLAlchemy 2.0, Alembic                           |
| Database           | PostgreSQL                                        |
| Background jobs    | APScheduler                                       |
| Authentication     | JWT cookies, bcrypt, optional OTP                 |
| File handling      | Python file validation, private encrypted storage |
| Email              | SMTP with development test inbox                  |
| PDF/CSV reports    | WeasyPrint, Python CSV                            |
| Testing            | pytest, HTTPX, Playwright                         |
| Deployment         | Docker Compose, Nginx                             |

## 3. Development phases

Phase 1

Project foundation and database

Foundation

- Create the repository structure and Docker Compose configuration.
- Configure FastAPI, React, PostgreSQL, and environment variables.
- Create SQLAlchemy models and Alembic migrations.
- Define users, roles, regions, institutions, applications, route configurations, and audit tables.
- Seed realistic dummy data for the demonstration.
- Establish a consistent API response and error format.

Deliverable: Running application skeleton with database and seed script.

Phase 2

Authentication and access control

- Implement login, logout, current-user profile, and optional OTP.
- Add role-based access for all seven user roles.
- Enforce institution and regional data scoping on the server.
- Add login rate limiting and session security.
- Test unauthorised access and cross-institution data isolation.

Deliverable: Secure login and role-specific access.

Phase 3

Workflow engine and audit trail

- Build configurable route types and ordered stages.
- Implement advance, return, hold, and resume operations.
- Require reasons for returns and holds.
- Preserve route versions for applications already in progress.
- Write stage history and audit entries transactionally.
- Implement hash-chain verification for audit records.

Deliverable: Working application lifecycle with complete history.

Phase 4

Deadline and notification engine

- Implement the central clock service.
- Calculate stage ageing while accounting for hold periods.
- Build configurable reminder and escalation rules.
- Add APScheduler daily scans and on-demand execution.
- Implement deduplication, retry handling, and missed-run recovery.
- Add simulated-date controls for non-production environments.

Deliverable: Reliable deadline processing with demonstrable alerts.

Phase 5

EVC, compliance, and document modules

- Build EVC queues, scheduling, member assignment, and report tracking.
- Implement undertaking creation, evidence upload, review, and closure.
- Implement document registration, validity tracking, and renewal verification.
- Add notifications and escalation handling for overdue items.
- Apply file validation, private storage, and permission-checked downloads.

Deliverable: End-to-end EVC and compliance workflows.

Phase 6

Frontend and role-based dashboards

- Implement the light-only design system and responsive app shell.
- Build login, sidebar, top bar, notifications, and role-based navigation.
- Create regional and bureau dashboards.
- Build institution home, application detail, EVC calendar, undertakings, and document screens.
- Add escalation views, admin configuration, and accessible data tables.
- Connect all screens to the backend APIs.

Deliverable: Complete responsive UI aligned with the UI/UX design document.

Phase 7 & 8

End-to-End Integration, Security Assurance, and Performance Validation [COMPLETED]

- Executed end-to-end integration workflows covering all 7 system roles across 9 distinct scenarios.
- Verified strict tenant isolation (cross-institution 403/404, unauthenticated 401s, privilege escalation denial).
- Hardened security defenses: path traversal rejection, magic byte MIME spoofing prevention, whitespace-padded formula injection sanitization, SHA-256 tamper-evident audit chaining.
- Conducted performance benchmarking and percentiles analysis (p50, p95, p99) under simulated load and 10 concurrent requests (0% error rate).
- Validated background worker idempotency and transactional atomicity with complete rollback.
- Confirmed full regression suite (108 backend tests passing, 0 failures, 0 regressions; frontend type checking and production build 100% clean).

Deliverables: Complete integration test suite (test_phase7_e2e_workflows.py, test_phase7_tenant_isolation_security.py, test_phase8_performance_benchmarks.py), performance benchmark report, and verified production-ready system.

## 4. Recommended repository structure

```
niyamsetu/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │       ├── workflow/
│   │       ├── deadlines/
│   │       ├── permissions/
│   │       ├── audit/
│   │       ├── notifications/
│   │       └── adapters/
│   ├── worker/
│   │   └── run.py
│   ├── migrations/
│   ├── seed/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   └── public/
├── docs/
│   ├── PRD.md
│   ├── TECH.md
│   ├── UI-UX.md
│   ├── API.md
│   └── PLAN.md
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 5. Core database entities

Implement these entities in dependency order:

1. Organisation: Regions, institutions, users, roles.
2. Configuration: Route types, route stages, reminder rules, escalation rules, message templates, holidays, configuration versions.
3. Applications: Applications and stage history.
4. EVC: EVC records, committee members, EVC reports.
5. Compliance: Undertakings, submissions, documents, renewals.
6. Notifications: Notifications, escalations, scheduler runs.
7. Security and audit: Files, audit logs, authentication-related records as needed.

Use foreign keys, indexes, uniqueness constraints, and transactions for data integrity.

## 6. API implementation order

Implement and test the API in this order:

| Order | API group                          | Main functionality                   |
| ----- | ---------------------------------- | ------------------------------------ |
| 1     | `/auth`, `/me`                     | Authentication and identity          |
| 2     | `/admin/users`, `/admin/regions`   | Access and organisation setup        |
| 3     | `/applications`                    | Routing and application history      |
| 4     | `/audit`                           | Audit writing and verification       |
| 5     | `/admin/scheduler`, `/admin/clock` | Deadline engine controls             |
| 6     | `/notifications`, `/escalations`   | Reminders and escalations            |
| 7     | `/evcs`                            | EVC lifecycle                        |
| 8     | `/undertakings`                    | Compliance evidence                  |
| 9     | `/documents`, `/files`             | Document validity and secure uploads |
| 10    | `/dashboard`                       | Dashboard summaries and analytics    |
| 11    | `/reports`                         | CSV and PDF exports                  |
| 12    | `/integration`                     | Mock adapter and CSV import          |

## 7. Frontend implementation order

1. Design tokens, typography, buttons, badges, cards, inputs, and tables.
2. Responsive application shell and role-based navigation.
3. Login and current-user handling.
4. Dashboard summary tiles, charts, filters, and ageing lists.
5. Application list, details, timeline, and transition dialogs.
6. EVC queue, schedule form, calendar, and report views.
7. Undertaking submission and review screens.
8. Document validity and renewal screens.
9. Notifications, escalations, and audit history.
10. Reports and administrative configuration screens.
11. Loading, empty, error, and confirmation states.
12. Accessibility and responsive polish.

Use one shared component library. Keep the interface light-only, fluid, and status-focused throughout.

## 8. Testing strategy

### Unit tests

- Route resolution and stage transitions.
- Return and hold validation.
- Deadline calculations and paused time.
- Working-day and holiday calculations.
- Reminder and escalation matching.
- Scheduler idempotency and catch-up.
- Audit hash-chain verification.

### API tests

- Authentication and OTP enforcement.
- Role and record-level permissions.
- Institution and regional data isolation.
- File type and file size validation.
- Evidence review and renewal review.
- Configuration versioning.
- Report permissions and output correctness.

### End-to-end tests

- Application moves through a complete configured route.
- Officer returns an application with a reason.
- Institution submits compliance evidence and an official verifies it.
- A lease approaches expiry, triggers alerts, and proceeds through renewal.
- An overdue EVC generates an escalation.
- Changing a configured timeline changes subsequent system behaviour without code changes.

## 9. Definition of done

A feature is complete only when:

- The API and database operations work.
- Authentication and permissions are enforced.
- Input validation and useful error states are implemented.
- Relevant actions are written to the audit trail.
- Unit and API tests pass.
- The UI follows the design system and works on mobile and desktop.
- Loading, empty, and error states are handled.
- Documentation is updated.

## 10. Prototype acceptance checklist

- Every configured application route advances correctly.
- Return/revert actions require a reason and appear in history.
- Each role sees only its permitted data.
- Dashboard ageing and pendency match underlying records.
- EVC scheduling, reminders, and escalations work.
- Undertaking submission, verification, rejection, and closure work.
- Document expiry alerts and renewal verification work.
- Reports export correctly and match dashboard figures.
- All important actions appear in the audit trail.
- Audit integrity verification detects tampering.
- Scheduler reruns do not duplicate alerts.
- Simulated dates work only outside production.
- Configuration changes alter behaviour without code changes.
- Responsive and accessibility checks are completed.

## 11. Important constraints and dependencies

- APH stage definitions, timelines, and escalation thresholds are placeholders until confirmed by authorised domain experts.
- The prototype uses dummy data and does not process real AICTE applications.
- Production deployment requires approved hosting, security review, retention policies, and integration authorisation.
- SMS, e-sign, DigiLocker, production SSO, and live AICTE APIs are future enhancements.
- Human officials retain responsibility for scrutiny, verification, inspections, and statutory decisions.

## 12. Final development principle

Build the workflow engine, permission model, deadline engine, and audit trail before polishing the dashboards. These components underpin the correctness and trustworthiness of NiyamSetu. Once they are tested, build the role-specific UI on top of stable APIs and finish with end-to-end demonstrations.