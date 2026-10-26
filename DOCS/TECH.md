# NiyamSetu: Technical Design Document

## 1. Purpose

This document describes how NiyamSetu will be built to meet the PRD: architecture, data model, the workflow and deadline engines, security, APIs and the testing approach. Where the APH or AICTE has not given us a figure, we describe how it is configured.

## 2. Design principles

1. **Rules live in data, not code.** Route types, stage timelines, reminder intervals and escalation chains are database records edited through the admin panel.
2. **One clock.** All code gets "today" from a single clock service. This lets us demonstrate deadline behaviour by simulating dates.
3. **Everything is logged.** No state change happens without an audit entry written in the same database transaction.
4. **The system recommends, people decide.** Automation is limited to routing, reminders, drafts and reports. Decisions are always a manual action by an authorised user.
5. **Idempotent jobs.** Re-running the scheduler never produces duplicate alerts or escalations.

## 3. Architecture

The system has four parts:

- **Web app:** React user interface for all roles.
- **API server:** FastAPI application holding business logic, authentication, role checks and the workflow engine.
- **Worker:** a separate Python process running APScheduler for the daily deadline scan, notification sending and escalations.
- **PostgreSQL and file storage:** the system of record, plus encrypted storage for uploaded documents.

```
Browser (React) -> FastAPI (REST /api/v1) -> PostgreSQL
                          |                      ^
                          v                      |
                    File storage        Worker (APScheduler)
                                                 |
                                                 v
                                      Email / in-app notifications

AICTE systems -> Adapter layer (mock, CSV import) -> FastAPI
```

The API and worker share one codebase and one database. Keeping the worker as its own process means a slow report or a busy dashboard cannot delay deadline processing.

## 4. Technology choices

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | Team familiarity, strong date and data handling |
| API framework | FastAPI | Typed request validation, automatic API docs, async support |
| Validation | Pydantic v2 | Request and response schemas |
| ORM and migrations | SQLAlchemy 2.0 and Alembic | Mature, explicit control over transactions and row locking |
| Database | PostgreSQL | Transactions, constraints, strong date handling |
| Scheduler | APScheduler in a separate worker process | Enough for a daily scan plus on-demand runs. Celery with Redis is the upgrade path if volume grows |
| Auth | bcrypt (passlib), JWT via PyJWT in httpOnly cookies, optional OTP (pyotp) | Simple and demonstrable |
| Rate limiting | slowapi | Login throttling |
| File handling | python-magic for content-type checks, local encrypted directory (prototype) | S3-compatible storage later behind the same interface |
| Email | SMTP through fastapi-mail, test inbox in development | No external dependency for the demo |
| PDF and CSV export | WeasyPrint for PDF, standard csv module | Reports and letters |
| Frontend | React with Vite, Tailwind CSS, Recharts | Fast to build, good dashboard charts |
| Tests | pytest, httpx test client, Playwright | Engine logic, API role checks, end-to-end flows |
| Linting and typing | Ruff and mypy | Keeps the codebase consistent |

If the team prefers a single language, the UI can instead be server-rendered with Jinja2 and HTMX, with Chart.js for charts. That removes the separate frontend build but gives less interactive dashboards.

## 5. Data model

All tables carry `id`, `created_at` and `updated_at` unless stated otherwise.

**Organisation and access**
- `regions`: name, code
- `users`: name, email, password_hash, role, region_id (nullable), institution_id (nullable), is_active
- `institutions`: name, aicte_id, type, region_id, is_new (boolean), contact_email, contact_phone

**Configuration**
- `route_types`: code, name, version, is_active
- `route_stages`: route_type_id, sequence, stage_code, required_role, timeline_days, day_type (calendar or working)
- `escalation_rules`: event_type, level, offset_days (relative to deadline), notify_role, region_scope
- `reminder_rules`: event_type, offset_days_before, channel, template_id
- `message_templates`: code, subject, body, variables
- `holidays`: date, region_id (nullable), used when working days are configured
- `config_versions`: entity, entity_id, snapshot (JSON), changed_by, changed_at

**Applications**
- `applications`: reference_no, institution_id, route_type_id, route_version, current_stage_id, status, assigned_to, submitted_at, stage_entered_at, closed_at
- `stage_history`: application_id, stage_code, entered_at, exited_at, actor_id, action (advance, return, hold), from_stage, to_stage, reason

**EVC**
- `evcs`: application_id, status (queued, scheduled, conducted, report_submitted, closed), queued_at, due_by, scheduled_date, conducted_on, report_due_by, priority
- `evc_members`: evc_id, user_id, role_in_committee
- `evc_reports`: evc_id, file_id, submitted_at

**Compliance**
- `undertakings`: application_id, description, due_date, status (pending, submitted, under_verification, verified, rejected, overdue, closed), verified_by, verified_at
- `undertaking_submissions`: undertaking_id, file_id, submitted_by, submitted_at, review_status, reviewer_remarks
- `documents`: institution_id, application_id (nullable), doc_type, valid_from, valid_to, status (valid, expiring, expired, renewal_submitted, renewal_verified), current_file_id
- `document_renewals`: document_id, file_id, new_valid_from, new_valid_to, submitted_at, review_status, reviewer_id

**Alerts**
- `notifications`: recipient_id, event_type, entity_type, entity_id, channel, dedupe_key (unique), status, sent_at, read_at, acknowledged_at, snoozed_until, snooze_reason
- `escalations`: entity_type, entity_id, level, escalated_to, raised_at, resolved_at, resolution_note
- `scheduler_runs`: run_for_date, started_at, finished_at, status, items_scanned, items_alerted, error

**Files and audit**
- `files`: storage_key, original_name, mime_type, size, checksum, uploaded_by
- `audit_log`: sequence_no, occurred_at, actor_id, actor_role, action, entity_type, entity_id, before (JSON), after (JSON), reason, prev_hash, hash

Important constraints:
- `notifications.dedupe_key` is unique, which makes the scheduler idempotent.
- `applications` stores `route_type_id` and `route_version`, so changing a route type does not alter applications already in progress. They keep the version they started on.
- The application database user has no UPDATE or DELETE permission on `audit_log`.

## 6. Workflow engine

### 6.1 Route definition

A route type is an ordered set of `route_stages`. For example, Scrutiny + EVC could be `SCRUTINY -> EVC_QUEUE -> EVC_VISIT -> EVC_REPORT_REVIEW -> DECISION`. The real sequences will be loaded from the APH. Nothing in the engine refers to a specific stage name.

### 6.2 Transitions

There are three actions on an application:

- **advance:** moves to the next stage in the route. Allowed only if the caller's role matches the stage's `required_role` and the application is in that stage.
- **return:** moves to a named earlier stage or to the institution. A reason is mandatory, and the stage timeline resets or continues according to configuration.
- **hold:** pauses the timeline clock for a reason such as waiting for the institution's reply. Time on hold does not count towards ageing.

Each transition runs in a single database transaction that checks permission, updates the application, writes `stage_history` and writes `audit_log`. If any step fails, all of them are rolled back.

```python
def transition(session, app_id, action, actor, payload):
    with session.begin():
        app = session.execute(
            select(Application).where(Application.id == app_id).with_for_update()
        ).scalar_one()

        ensure_actor_allowed(actor, action, app.current_stage)
        if action == "return" and not payload.reason.strip():
            raise ValidationError("Reason is mandatory for a return")

        target = resolve_target_stage(app, action, payload)
        before = snapshot(app)
        close_stage_history(session, app, actor)
        open_stage_history(session, app, target, actor, payload.reason)

        app.current_stage_id = target.id
        app.stage_entered_at = clock.now()
        app.assigned_to = pick_assignee(app, target)

        run_stage_entry_hooks(session, app, target)
        write_audit(session, actor, action, app, before, snapshot(app), payload.reason)
```

`with_for_update()` locks the row so two officers cannot act on the same application at once. Everything inside `session.begin()` commits or rolls back together, including the audit entry.

### 6.3 Stage entry hooks

Entering certain stages triggers side effects, also configured per stage:
- `EVC_QUEUE`: creates an `evcs` row with `due_by` calculated from configuration.
- `DECISION` followed by an approval with conditions: creates `undertakings` and `documents` records from the conditions the official enters.

The decision itself is entered by the competent authority. The system only records it.

## 7. Deadline, reminder and escalation engine

### 7.1 Deadline sources

| Item | Deadline field |
|---|---|
| Application stage | `stage_entered_at` + `timeline_days` (excluding hold periods) |
| EVC scheduling | `evcs.due_by` |
| EVC report | `evcs.report_due_by` |
| Undertaking | `undertakings.due_date` |
| Document | `documents.valid_to` |

### 7.2 Daily scan

The worker runs once a day and also on demand from the admin panel. For the date being processed (taken from the clock service):

1. Record a `scheduler_runs` row.
2. For each item type, load open items with a deadline.
3. Compute `days_to_deadline = deadline - today`.
4. Match against `reminder_rules` (upcoming items) and `escalation_rules` (overdue items).
5. For each match, build a `dedupe_key` such as `EVC_DUE:{evc_id}:L0:{rule_id}` and insert the notification or escalation only if that key does not already exist.
6. Update derived statuses, for example `documents.status` to expiring or expired.
7. Close the run row with counts.

Because of the unique `dedupe_key`, running the scan twice for the same date has no extra effect.

### 7.3 Catch-up

At startup and before each scan, the worker checks `scheduler_runs` for any date between the last successful run and today with no run recorded, and processes those dates in order. A server outage therefore does not cause a missed alert.

### 7.4 Escalation

Escalation levels come from `escalation_rules`. At each level the target is resolved from the item's region and the configured role, for example the Regional Officer of the institution's region. An escalation stays open until the underlying item is resolved or an official records a resolution note. Resolving an item automatically closes its open escalations.

### 7.5 Working days

Where a timeline is in working days, the engine skips weekends and any dates in `holidays`. Calendar days are the default unless a stage is configured otherwise.

### 7.6 Simulated date

The clock service returns the real date unless an admin sets a simulated date. This is allowed only when `ENV` is not production. Setting a simulated date writes an audit entry and shows a visible banner in the UI. After moving the date, the admin triggers a scan to show reminders and escalations firing.

## 8. Roles and access control

Roles: `institution`, `scrutiny_officer`, `regional_officer`, `bureau_officer`, `committee_member`, `senior_authority`, `admin`.

Access is enforced in the API on every request, never only in the UI. Each endpoint uses a FastAPI dependency that checks the user, the action and the target record.

| Resource | Institution | Scrutiny | Regional | Bureau | Committee | Senior | Admin |
|---|---|---|---|---|---|---|---|
| Own applications | Read | | | | | | |
| Applications in region | | Assigned | Read, act | Read | Assigned | Read | Read |
| All regions | | | | Read | | Read | Read |
| Advance or return | | At scrutiny stage | At assigned stages | | At committee stages | | |
| Schedule EVC | | | Yes | Yes | | | |
| Verify undertaking or document | | | Yes | Yes | | | |
| Submit evidence | Own only | | | | | | |
| Reports | Own only | | Region | All | | All | All |
| Configuration | | | | | | | Yes |
| Audit log | | | Region | All | | All | All |

Data scoping is applied in queries by adding the user's region or institution to the filter, so a missing check cannot return other people's rows.

## 9. API outline

REST, JSON, versioned under `/api/v1`. Every endpoint validates input with Pydantic and returns consistent error objects. FastAPI also exposes interactive API documentation at `/docs`, which we will use during the demo.

**Auth**
- `POST /auth/login`, `POST /auth/logout`, `POST /auth/otp/verify`, `GET /me`

**Applications**
- `GET /applications` with filters (region, stage, route, status, date range, page)
- `GET /applications/{id}` (details, history, case summary)
- `POST /applications/{id}/advance`
- `POST /applications/{id}/return` (reason required)
- `POST /applications/{id}/hold` and `/resume`

**EVC**
- `GET /evcs`, `POST /evcs/{id}/schedule`, `POST /evcs/{id}/members`, `POST /evcs/{id}/conducted`, `POST /evcs/{id}/report`

**Undertakings**
- `GET /undertakings`, `POST /undertakings/{id}/submissions` (file upload), `POST /submissions/{id}/review` (accept or reject with remarks)

**Documents**
- `GET /documents`, `POST /documents/{id}/renewals`, `POST /renewals/{id}/review`

**Notifications and escalations**
- `GET /notifications`, `POST /notifications/{id}/ack`, `POST /notifications/{id}/snooze`
- `GET /escalations`, `POST /escalations/{id}/resolve`

**Dashboards and reports**
- `GET /dashboard/summary`, `/dashboard/ageing`, `/dashboard/workload`, `/dashboard/bottlenecks`
- `GET /reports/{type}` with `?format=csv|pdf`

**Admin**
- CRUD for `/admin/users`, `/admin/regions`, `/admin/route-types`, `/admin/escalation-rules`, `/admin/reminder-rules`, `/admin/templates`
- `POST /admin/scheduler/run`, `POST /admin/clock` (non-production only)

**Integration**
- `POST /integration/import` (CSV or JSON batch through the adapter)

## 10. Dashboards: how the numbers are computed

Dashboards use SQL queries or views over `applications`, `stage_history`, `evcs`, `undertakings` and `documents`, scoped by role.

- **Ageing:** `today - stage_entered_at - hold_days`.
- **Status colour:** green when under 75% of the timeline is used, amber from 75% to 100%, red beyond. The 75% value is configurable.
- **Bottlenecks:** average dwell time per stage over a selectable period, compared with the stage timeline.
- **Workload:** open items per assigned user.
- **Region performance:** share of applications completed within timeline, and average days per stage.

Reports reuse the same query functions as the dashboards so the figures always match.

## 11. Notifications

An event creates a `notifications` row per recipient and channel. In-app notifications appear in a bell menu with an unread count. Email is sent from a queue by the worker, with up to three retries before the notification is marked failed and an entry is written to the audit log. Templates use named variables such as `{institution}`, `{due_date}` and `{days_left}`. Administrators edit the template text but not the variable names.

## 12. Audit log

Each audit entry stores a hash computed over its own content and the hash of the previous entry. This makes tampering detectable, because changing any past row breaks every hash after it. A verification endpoint recomputes the chain and reports the first break, if any. Entries are written inside the same transaction as the change they describe, so there is no state change without a log entry and no log entry for a change that did not happen.

Logged events include logins, transitions, configuration edits, uploads, reviews, alerts sent, escalations raised and resolved, snoozes, simulated date changes and report exports.

## 13. Document handling

- Accepted types: PDF, JPG, PNG. Size limit is configurable, default 10 MB.
- File type is checked by content using python-magic, not only by extension.
- Files are stored under a random key, encrypted at rest, and never served from a public path. Downloads go through an authenticated endpoint that checks the user's right to see the record.
- A checksum is stored for each file so tampering after upload is detectable.
- A virus scan hook is provided but only mocked in the prototype.

## 14. Security

- Passwords hashed with bcrypt. Login rate limiting with slowapi and temporary lockout after repeated failures.
- JWT in httpOnly, secure, same-site cookies. Short-lived access token with refresh.
- Optional OTP for officer logins.
- All input validated on the server with Pydantic. Parameterised queries through SQLAlchemy.
- CORS limited to the frontend origin. CSRF protection on state-changing routes. Strict Content Security Policy.
- Secrets in environment variables, never in the repository.
- TLS everywhere in deployment.
- The application database user has no rights to modify or delete audit rows.
- Personal data in logs is minimised.

## 15. Integration with AICTE systems

An adapter interface defines the methods the platform needs: `get_institutions`, `get_applications`, `get_users` and `get_application_updates`. Two implementations will exist:

- **MockAdapter:** reads seed data. Used for the prototype.
- **CsvAdapter:** imports files in a documented format. Used as the fallback.

A real API adapter would implement the same interface once AICTE specifies how to connect. Imports are idempotent, matched on `aicte_id` or `reference_no`, and each import is logged.

## 16. Seed data for the demo

- Two or three Regions with a few officers each
- About 40 institutions, a share of them new
- Around 150 applications across all route types and stages, with some near their timelines and some already overdue
- EVCs in each status, including delayed ones
- Undertakings in each status
- Leases expiring at different intervals, plus some already expired
- A user for every role with a documented demo login

## 17. Testing

Unit tests for the engine are the priority, since evaluation depends on workflow accuracy and alert timing.

**Unit tests (pytest):**
- Every route type advances in the correct order.
- A return without a reason is rejected.
- A wrong-role transition is rejected.
- Deadline calculation with hold periods, weekends and holidays.
- Reminder and escalation selection for each offset.
- Running the scheduler twice produces no duplicates.
- Catch-up processes missed dates in order.
- Audit chain verification detects a modified row.

The deadline tests use a fake clock object, which is why the single clock service matters.

**API tests (pytest and httpx):** role scoping, for example an institution requesting another institution's application receives a 403.

**End-to-end tests (Playwright for Python):** the PRD acceptance criteria, including an application through a full route, an undertaking from notification to closure, a lease from first alert to escalation, and a configuration change altering behaviour with no code change.

## 18. Deployment

Development and demo run with Docker Compose and four services: `api` (FastAPI served by Uvicorn), `worker` (APScheduler), `web` (React build served by Nginx) and `db` (PostgreSQL). Configuration comes from `.env` files, and Alembic migrations run at startup.

Production would additionally need approved government hosting, Gunicorn with Uvicorn workers behind a reverse proxy, managed PostgreSQL with backups, an object store for files, centralised logging and monitoring, and a security audit. These are described but not built in the prototype.

## 19. Repository layout

```
niyamsetu/
  backend/
    app/
      main.py              FastAPI entry point
      api/v1/              routers: auth, applications, evc, undertakings,
                           documents, notifications, dashboard, reports, admin
      core/                settings, security, dependencies
      models/              SQLAlchemy models
      schemas/             Pydantic schemas
      services/
        workflow/          transition logic, route resolution
        deadlines/         scan, reminders, escalation
        permissions/       role and scope checks
        audit/             writer and chain verifier
        notifications/     queue, email, templates
        adapters/          mock, csv
        clock.py           single source of "today"
    worker/
      run.py               scheduler entry point
    migrations/            Alembic
    seed/                  seed data script
    tests/                 unit, api, e2e
  frontend/
    src/                   pages per role, components, charts
  docs/                    PRD, this document
  docker-compose.yml
```

## 20. Build order

1. SQLAlchemy models, Alembic migrations, seed script
2. Authentication and permission layer
3. Workflow engine with tests
4. Audit log writer and verifier
5. Deadline engine, scheduler, clock service, with tests
6. Notifications and escalation
7. EVC, undertaking and document modules
8. Role dashboards and reports
9. Admin panel for configuration
10. End-to-end tests, polish and demo script

## 21. Known limitations

- The prototype uses dummy data and a mock adapter, so no live AICTE data is involved.
- Route types, timelines and escalation chains are placeholders until confirmed from the APH.
- SMS, e-sign, DigiLocker and real virus scanning are not included.
- Performance is designed for tens of thousands of records but only tested at seed data volume.

## 22. Open technical questions

1. Does AICTE expose any API or data export we can match against, and in what format?
2. Which authentication method will a real deployment require: SSO, OTP or something else?
3. Are timelines counted in calendar days or working days, and which holiday calendar applies?
4. What are the retention and data localisation requirements for stored documents?
5. Are there size or format rules for uploaded evidence?

