# NiyamSetu — API Specification (`api.md`)

Version: 1.0 Status: Prototype specification Base path: `/api/v1` Architecture: REST API using FastAPI, PostgreSQL, SQLAlchemy, and Pydantic Authentication: JWT in secure, HttpOnly cookies, with optional OTP verification.

## 1. Purpose

This document defines the API endpoints, request and response formats, authentication, role-based permissions, validation, and error handling for NiyamSetu.

The API supports application workflow routing, pendency monitoring, EVC scheduling, institutional compliance, document validity tracking, notifications, escalations, reports, and audit logging.

The prototype uses seeded dummy data and mock/CSV integrations. It does not connect to live AICTE production systems. Statutory scrutiny, verification, and approval or rejection decisions remain the responsibility of authorised officials.

## 2. API Conventions

### 2.1 Base URL

```
http://localhost:8000/api/v1
```

FastAPI interactive documentation is available at `/docs` during development.

### 2.2 Request and response formats

- JSON for standard API requests and responses.
- `multipart/form-data` for document uploads.
- Dates use `YYYY-MM-DD`.
- Timestamps use ISO 8601 with timezone information.
- All endpoints require authentication unless explicitly marked public.
- Every request is validated by Pydantic schemas.
- Access permissions are enforced on the backend.
- Pagination is supported for list endpoints.
- Sensitive information must not be exposed in API errors or logs.

### 2.3 Standard success response

```
{
  "data": {
    "id": "app_1001",
    "reference_no": "NS-2026-001001",
    "status": "in_progress"
  }
}
```

### 2.4 Standard paginated response

```
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### 2.5 Standard error response

```
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "A reason is required for this action.",
    "details": [
      {
        "field": "reason",
        "message": "This field is required."
      }
    ]
  }
}
```

### 2.6 HTTP status codes

| Status                       | Description                                                   |
| ---------------------------- | ------------------------------------------------------------- |
| `200 OK`                     | Request completed successfully                                |
| `201 Created`                | Resource created successfully                                 |
| `202 Accepted`               | Additional authentication or asynchronous processing required |
| `204 No Content`             | Request completed without a response body                     |
| `400 Bad Request`            | Invalid action or malformed request                           |
| `401 Unauthorized`           | Authentication required or invalid                            |
| `403 Forbidden`              | Insufficient permissions                                      |
| `404 Not Found`              | Resource not found or inaccessible                            |
| `409 Conflict`               | Conflicting state or duplicate operation                      |
| `413 Payload Too Large`      | File exceeds the configured limit                             |
| `415 Unsupported Media Type` | Unsupported file type                                         |
| `422 Unprocessable Entity`   | Request validation failed                                     |
| `429 Too Many Requests`      | Rate limit exceeded                                           |
| `500 Internal Server Error`  | Unexpected server error                                       |

## 3. Authentication APIs

### 3.1 Login

`POST /auth/login`

Authenticates a user using email and password.

Request

```
{
  "email": "officer@example.test",
  "password": "demo-password"
}
```

Response: `200 OK`

```
{
  "data": {
    "user": {
      "id": "user_101",
      "name": "Demo Officer",
      "email": "officer@example.test",
      "role": "regional_officer",
      "region_id": "region_01"
    },
    "otp_required": false
  }
}
```

The JWT is issued through a secure, HttpOnly cookie.

For accounts requiring OTP, the API returns `202 Accepted` with an authentication challenge. It must not issue a fully authenticated session until verification succeeds.

### 3.2 Logout

`POST /auth/logout`

Invalidates the active session and clears the authentication cookie.

Response: `204 No Content`

### 3.3 Verify OTP

`POST /auth/otp/verify`

Request

```
{
  "challenge_id": "challenge_101",
  "otp": "123456"
}
```

Response: `200 OK`

```
{
  "data": {
    "message": "OTP verified successfully."
  }
}
```

### 3.4 Get current user

`GET /me`

Returns the authenticated user's profile and permissions.

Response

```
{
  "data": {
    "id": "user_101",
    "name": "Demo Officer",
    "email": "officer@example.test",
    "role": "regional_officer",
    "region_id": "region_01",
    "institution_id": null,
    "permissions": [
      "applications.read",
      "applications.advance",
      "evcs.schedule",
      "reports.region.read"
    ]
  }
}
```

### 3.5 Update profile

`PATCH /me`

Updates permitted profile fields, such as display name or contact details.

Users cannot modify their own role, region assignment, or administrative permissions through this endpoint.

## 4. Application Management APIs

### 4.1 List applications

`GET /applications`

Returns applications accessible to the authenticated user.

Query parameters

- `page`
- `page_size`
- `region_id`
- `stage`
- `route_type`
- `status`
- `institution_id`
- `assigned_to`
- `from_date`
- `to_date`
- `q`
- `sort_by`
- `sort_order`

Example

```
GET /api/v1/applications?region_id=region_01&status=in_progress&page=1&page_size=20
```

### 4.2 Create application

`POST /applications`

Creates an application record for an authorised user or an approved integration process.

Request

```
{
  "institution_id": "inst_101",
  "route_type_id": "route_scrutiny_evc",
  "submitted_at": "2026-10-21T10:00:00+05:30"
}
```

The server assigns the reference number, route version, initial stage, and initial stage history.

Response: `201 Created`

### 4.3 Get application details

`GET /applications/{application_id}`

Returns the application summary, institution details, current stage, assigned officer, timeline, route, and status.

### 4.4 Update application metadata

`PATCH /applications/{application_id}`

Updates permitted administrative fields. Changes to workflow stage or statutory decision must not be made through this endpoint; dedicated actions must be used.

### 4.5 Advance application

`POST /applications/{application_id}/advance`

Moves the application to the next configured stage after validating the user's role and the current application state.

Request

```
{
  "remarks": "Scrutiny completed."
}
```

Response

```
{
  "data": {
    "message": "Application advanced successfully.",
    "previous_stage": "SCRUTINY",
    "current_stage": "EVC_QUEUE"
  }
}
```

### 4.6 Return application

`POST /applications/{application_id}/return`

Returns the application to a previous stage or to the institution for deficiency or clarification.

Request

```
{
  "target_stage": "INSTITUTION_RESPONSE",
  "reason": "Required supporting documents are missing."
}
```

The reason is mandatory. The API records the transition and audit entry in the same database transaction.

### 4.7 Place application on hold

`POST /applications/{application_id}/hold`

Request

```
{
  "reason": "Awaiting institutional clarification."
}
```

### 4.8 Resume application

`POST /applications/{application_id}/resume`

Resumes a held application according to the configured timeline rules.

### 4.9 Get application history

`GET /applications/{application_id}/history`

Returns stage transitions, actors, timestamps, actions, reasons, and remarks in chronological order.

### 4.10 Record competent authority decision

`POST /applications/{application_id}/decision`

Records a decision made by an authorised competent authority.

Request

```
{
  "decision": "approved_with_conditions",
  "remarks": "Approval subject to the listed undertakings.",
  "conditions": [
    {
      "description": "Submit the required compliance evidence.",
      "due_date": "2026-12-31"
    }
  ]
}
```

The API records the human decision and creates applicable compliance records. It does not independently determine approval or rejection.

## 5. Dashboard APIs

### 5.1 Dashboard summary

`GET /dashboard/summary`

Returns role-scoped summary statistics.

Response

```
{
  "data": {
    "open_applications": 120,
    "due_soon": 18,
    "overdue": 12,
    "evcs_pending": 9,
    "documents_expiring": 7
  }
}
```

Values are illustrative and must be calculated from database records.

### 5.2 Application ageing

`GET /dashboard/ageing`

Returns application counts grouped by stage-ageing bands and status.

Query parameters: `region_id`, `stage`, `route_type`, `from_date`, `to_date`.

### 5.3 Workload distribution

`GET /dashboard/workload`

Returns open items grouped by assigned officer or committee.

### 5.4 Stage bottlenecks

`GET /dashboard/bottlenecks`

Returns stage-wise pendency, average dwell time, and configured stage timelines.

### 5.5 Regional performance

`GET /dashboard/regions`

Returns region-level performance metrics for users authorised to access cross-region data.

### 5.6 Dashboard filters

All dashboard endpoints enforce role-based data scoping. Institutions can access only their own records, and regional users are limited to their authorised scope.

## 6. EVC Management APIs

### 6.1 List EVC records

`GET /evcs`

Query parameters

- `region_id`
- `status`
- `priority`
- `from_date`
- `to_date`
- `page`
- `page_size`

### 6.2 Get EVC details

`GET /evcs/{evc_id}`

Returns the associated application, status, deadlines, scheduled date, committee members, and report status.

### 6.3 Schedule EVC

`POST /evcs/{evc_id}/schedule`

Request

```
{
  "scheduled_date": "2026-11-05T10:00:00+05:30",
  "member_ids": [
    "user_201",
    "user_202"
  ],
  "notes": "Visit scheduled by the Regional Office."
}
```

Only authorised officials can schedule EVCs. Scheduling and assignment changes are audited.

### 6.4 Assign committee members

`POST /evcs/{evc_id}/members`

Request

```
{
  "members": [
    {
      "user_id": "user_201",
      "role_in_committee": "member"
    },
    {
      "user_id": "user_202",
      "role_in_committee": "chair"
    }
  ]
}
```

### 6.5 Mark EVC as conducted

`POST /evcs/{evc_id}/conducted`

Request

```
{
  "conducted_on": "2026-11-05T10:00:00+05:30",
  "remarks": "Visit completed."
}
```

### 6.6 Submit EVC report

`POST /evcs/{evc_id}/report`

Accepts report metadata and an authorised file reference or multipart file upload, according to the implementation.

Example metadata

```
{
  "remarks": "Report submitted for review."
}
```

### 6.7 Close EVC

`POST /evcs/{evc_id}/close`

Closes the EVC record after required report and review steps are completed. Closure does not itself constitute an approval decision.

## 7. Undertaking and Compliance APIs

### 7.1 List undertakings

`GET /undertakings`

Query parameters: `status`, `institution_id`, `application_id`, `due_before`, `due_after`, `region_id`, `page`, `page_size`.

### 7.2 Get undertaking details

`GET /undertakings/{undertaking_id}`

Returns the undertaking condition, due date, status, submissions, review history, and assigned verifier.

### 7.3 Create undertaking

`POST /undertakings`

Request

```
{
  "application_id": "app_1001",
  "description": "Submit the required compliance evidence.",
  "due_date": "2026-12-31"
}
```

Creation is restricted to authorised users and applicable workflow events.

### 7.4 Submit compliance evidence

`POST /undertakings/{undertaking_id}/submissions`

Uses `multipart/form-data` for file uploads.

Fields

- `file`: supporting document
- `remarks`: optional submission remarks

The API records the submitting user and submission timestamp.

### 7.5 Review compliance evidence

`POST /submissions/{submission_id}/review`

Request

```
{
  "decision": "rejected",
  "remarks": "The submitted evidence does not demonstrate the required condition."
}
```

Allowed review decisions are `accepted` and `rejected`.

The reviewer must be authorised. Rejection requires remarks. If resubmission is permitted, the system applies the configured revised-deadline rule.

### 7.6 Close undertaking

`POST /undertakings/{undertaking_id}/close`

Closes the undertaking after the required verification and closure conditions are satisfied.

### 7.7 Undertaking history

`GET /undertakings/{undertaking_id}/history`

Returns status changes, submissions, reviews, remarks, and escalation events.

## 8. Document Validity APIs

### 8.1 List documents

`GET /documents`

Query parameters

- `institution_id`
- `application_id`
- `doc_type`
- `status`
- `expires_before`
- `expires_after`
- `region_id`
- `page`
- `page_size`

### 8.2 Get document details

`GET /documents/{document_id}`

Returns document metadata, validity dates, current status, renewal history, and alert history.

### 8.3 Register document

`POST /documents`

Request

```
{
  "institution_id": "inst_101",
  "application_id": "app_1001",
  "doc_type": "lease",
  "valid_from": "2024-01-01",
  "valid_to": "2027-01-01"
}
```

The system derives validity status from configured rules and dates.

### 8.4 Upload renewed document

`POST /documents/{document_id}/renewals`

Uses `multipart/form-data`.

Fields

- `file`: renewed document
- `new_valid_from`: validity start date
- `new_valid_to`: expiry date
- `remarks`: optional remarks

The renewal remains under verification until reviewed by an authorised official.

### 8.5 Review document renewal

`POST /renewals/{renewal_id}/review`

Request

```
{
  "decision": "accepted",
  "remarks": "Renewed lease verified."
}
```

Allowed decisions are `accepted` and `rejected`. Rejected renewals require remarks.

### 8.6 Document validity summary

`GET /documents/summary`

Returns counts of valid, expiring soon, expired, and renewals under verification, scoped to the user's permissions.

## 9. Notifications APIs

### 9.1 List notifications

`GET /notifications`

Query parameters: `status`, `event_type`, `from_date`, `to_date`, `page`, `page_size`.

Returns only notifications available to the authenticated recipient.

### 9.2 Get notification details

`GET /notifications/{notification_id}`

### 9.3 Acknowledge notification

`POST /notifications/{notification_id}/ack`

Marks a notification as acknowledged.

### 9.4 Snooze notification

`POST /notifications/{notification_id}/snooze`

Request

```
{
  "snoozed_until": "2026-10-24T09:00:00+05:30",
  "reason": "Follow-up is scheduled for the next working day."
}
```

A reason is mandatory. Snoozing does not erase the notification or suppress mandatory escalations unless the applicable rule explicitly permits it.

### 9.5 Notification preferences

`GET /notifications/preferences`

Returns configurable notification preferences available to the user.

`PATCH /notifications/preferences`

Updates permitted preferences. Users cannot disable mandatory regulatory alerts if policy requires their delivery.

## 10. Escalation APIs

### 10.1 List escalations

`GET /escalations`

Query parameters: `level`, `status`, `event_type`, `region_id`, `from_date`, `to_date`, `page`, `page_size`.

### 10.2 Get escalation details

`GET /escalations/{escalation_id}`

Returns the underlying item, escalation level, reason, recipient, raised timestamp, and resolution status.

### 10.3 Resolve escalation

`POST /escalations/{escalation_id}/resolve`

Request

```
{
  "resolution_note": "The pending evidence has been verified and the case is now up to date."
}
```

A resolution note is mandatory. When the underlying item is resolved, associated open escalations may be closed automatically according to configured rules.

## 11. Reports APIs

### 11.1 Generate report

`GET /reports/{report_type}`

Supported report types:

- `application-pendency`
- `evc-status`
- `undertaking-compliance`
- `document-validity`
- `overdue-cases`
- `region-performance`

Query parameters

- `region_id`
- `stage`
- `status`
- `from_date`
- `to_date`
- `format`: `json`, `csv`, or `pdf`

Example:

```
GET /api/v1/reports/application-pendency?region_id=region_01&format=csv
```

The same query logic must be used for dashboards and reports so figures remain consistent.

### 11.2 Get report job status

`GET /reports/jobs/{job_id}`

Optional endpoint for deployments where large report exports are processed asynchronously.

### 11.3 Export audit report

`GET /reports/audit`

Returns an authorised, filterable audit export. Sensitive fields must be minimised according to access policy.

## 12. Audit APIs

### 12.1 List audit entries

`GET /audit`

Query parameters

- `entity_type`
- `entity_id`
- `actor_id`
- `action`
- `from_date`
- `to_date`
- `region_id`
- `page`
- `page_size`

Access is limited to authorised audit viewers.

### 12.2 Get audit entry

`GET /audit/{audit_id}`

Returns the event metadata, actor, timestamp, before/after snapshots where permitted, reason, and hash-chain fields appropriate to the viewer's role.

### 12.3 Verify audit hash chain

`POST /audit/verify`

Checks the integrity of the audit hash chain.

Response

```
{
  "data": {
    "valid": true,
    "entries_checked": 1200,
    "first_invalid_sequence": null
  }
}
```

Audit records are append-only. Normal application endpoints must not allow users to edit or delete audit entries.

## 13. Administration APIs

All endpoints in this section require the appropriate administrative permissions.

### 13.1 User management

- `GET /admin/users`
- `POST /admin/users`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}`
- `POST /admin/users/{user_id}/deactivate`

Role changes and region/institution assignments must be validated and audited.

### 13.2 Region management

- `GET /admin/regions`
- `POST /admin/regions`
- `PATCH /admin/regions/{region_id}`

### 13.3 Institution management

- `GET /admin/institutions`
- `POST /admin/institutions`
- `GET /admin/institutions/{institution_id}`
- `PATCH /admin/institutions/{institution_id}`

### 13.4 Route type management

- `GET /admin/route-types`
- `POST /admin/route-types`
- `GET /admin/route-types/{route_type_id}`
- `PATCH /admin/route-types/{route_type_id}`
- `POST /admin/route-types/{route_type_id}/versions`

Route configuration contains an ordered stage sequence, required role, timeline, day type, and applicable stage-entry behaviour. Route changes are versioned. Existing applications retain the route version with which they started unless an authorised migration process is explicitly applied.

### 13.5 Reminder rules

- `GET /admin/reminder-rules`
- `POST /admin/reminder-rules`
- `PATCH /admin/reminder-rules/{rule_id}`
- `DELETE /admin/reminder-rules/{rule_id}`

Deletion should be soft deletion or deactivation where historical traceability is required.

### 13.6 Escalation rules

- `GET /admin/escalation-rules`
- `POST /admin/escalation-rules`
- `PATCH /admin/escalation-rules/{rule_id}`
- `DELETE /admin/escalation-rules/{rule_id}`

Rules define event type, escalation level, deadline offset, recipient role, and region scope.

### 13.7 Message templates

- `GET /admin/templates`
- `POST /admin/templates`
- `GET /admin/templates/{template_id}`
- `PATCH /admin/templates/{template_id}`

Template variables are validated against an approved variable list. Generated communications must not imply a statutory decision that has not been made.

### 13.8 Configuration history

`GET /admin/config-versions`

Returns version history for routes, timelines, reminders, escalation rules, and templates.

### 13.9 Run scheduler manually

`POST /admin/scheduler/run`

Triggers a deadline scan on demand.

Request

```
{
  "process_date": "2026-10-21"
}
```

The requested date must be resolved through the central clock service and must obey environment restrictions.

### 13.10 Simulate date

`POST /admin/clock`

Available only outside production.

Request

```
{
  "simulated_date": "2026-12-01"
}
```

### 13.11 Clear simulated date

`DELETE /admin/clock`

Restores the real system date. Both setting and clearing simulated dates are audit events.

### 13.12 Scheduler run history

`GET /admin/scheduler/runs`

Returns run date, start/end times, status, items scanned, alerts generated, and error details appropriate for the administrator.

## 14. Integration APIs

### 14.1 Import data

`POST /integration/import`

Accepts CSV or JSON batches through the configured adapter.

Supported import entities may include:

- Institutions
- Applications
- Users and role mappings
- Application updates

The importer validates records, uses stable external identifiers such as `aicte_id` and `reference_no` for matching, avoids duplicate records, and logs each import.

### 14.2 Get import status

`GET /integration/imports/{import_id}`

Returns counts of accepted, rejected, and skipped records, along with validation errors.

### 14.3 Download import template

`GET /integration/templates/{entity_type}`

Returns a documented CSV template for supported entity types.

Prototype restriction: Only mock and CSV adapters are implemented. A live AICTE API adapter is future work and requires authorised access and confirmed interface specifications.

## 15. File APIs

### 15.1 Upload file

`POST /files`

Uses `multipart/form-data`.

Fields

- `file`: PDF, JPG, or PNG
- `entity_type`: associated entity type
- `entity_id`: associated entity identifier

Default maximum file size is 10 MB and is configurable.

The API validates file content, not only the extension. Files are stored under random storage keys and are not publicly accessible.

### 15.2 Get file metadata

`GET /files/{file_id}`

Returns permitted metadata, such as file name, MIME type, size, upload timestamp, and checksum.

### 15.3 Download file

`GET /files/{file_id}/download`

Requires authentication and record-level access. The API must verify permission before streaming the file.

### 15.4 Delete or replace file

Files linked to submissions, decisions, or audit history must not be silently removed. Any permitted replacement or removal must follow retention rules, preserve the historical record, and be audited.

## 16. Role-Based Access Control

The following is the baseline access model. Actual permissions are enforced by the backend and must be configured to match authorised AICTE procedures.

| Capability                 | Institution           | Scrutiny officer  | Regional officer | Bureau officer    | Committee member | Senior authority | Admin                  |
| -------------------------- | --------------------- | ----------------- | ---------------- | ----------------- | ---------------- | ---------------- | ---------------------- |
| View own applications      | Yes                   | Assigned cases    | Region           | Cross-region read | Assigned cases   | Authorised scope | System scope           |
| Advance/return application | No                    | At scrutiny stage | Assigned stages  | As configured     | Committee stages | As configured    | No automatic authority |
| Submit compliance evidence | Own institution       | No                | No               | No                | No               | No               | No                     |
| Verify evidence/documents  | No                    | As configured     | Yes              | Yes               | No               | As configured    | No by default          |
| Schedule EVC               | No                    | No                | Yes              | Yes               | No               | As configured    | No by default          |
| View reports               | Own data              | Assigned scope    | Region           | Cross-region      | Assigned scope   | Cross-region     | System scope           |
| Manage configuration       | No                    | No                | No               | No                | No               | No               | Yes                    |
| View audit trail           | Own permitted history | Assigned scope    | Region           | Cross-region      | Assigned scope   | Cross-region     | System scope           |

A user's region and institution scope must be applied at query level. A valid identifier alone must never grant access to a record.

## 17. Validation and Business Rules

1. A stage transition is allowed only when the current application state and actor permissions permit it.
2. Returning an application requires a non-empty reason.
3. Rejecting evidence or a document renewal requires review remarks.
4. Resolving an escalation requires a resolution note.
5. Route stages, timelines, reminder intervals, and escalation chains are data-driven and configurable.
6. Changing a route configuration must not silently change the route version of applications already in progress.
7. Deadline processing uses a central clock service and respects configured calendar-day or working-day rules, including applicable holidays.
8. Re-running a scheduler must not create duplicate notifications or escalations.
9. Every state change, configuration change, submission, review, notification, escalation, and closure must create an audit event.
10. The state change and its audit entry must commit in the same database transaction.
11. Approval and rejection decisions are entered by authorised humans, not inferred by the workflow engine.
12. A simulated date is forbidden in production.
13. Document downloads and all sensitive endpoints must enforce resource-level permissions.
14. Reports and dashboard figures must use consistent query logic.
15. Automated communications and case summaries must be labelled as drafts or system-generated where applicable.

## 18. Notifications and Scheduler Behaviour

The worker evaluates due dates daily and on demand.

For each eligible application stage, EVC, undertaking, and document, it:

1. Reads the processing date from the central clock service.
2. Calculates time remaining or overdue duration.
3. Matches configured reminder and escalation rules.
4. Creates notifications and escalations using a unique deduplication key.
5. Updates derived statuses where required.
6. Records scheduler run results and errors.
7. Retries failed notification delivery according to configured retry limits.
8. Processes missed dates after a service interruption.

The scheduler must not make statutory decisions or change a decision made by an authorised official.

## 19. Security Requirements

- Hash passwords using bcrypt or an approved secure password-hashing configuration.
- Store JWTs in secure, HttpOnly, SameSite cookies.
- Apply login rate limiting and temporary lockout after repeated failures.
- Use OTP for configured officer accounts.
- Validate all request bodies, query parameters, and uploaded files.
- Use parameterised database operations through SQLAlchemy.
- Apply CSRF protections to cookie-authenticated state-changing endpoints.
- Restrict CORS to approved frontend origins.
- Enforce TLS in deployed environments.
- Store secrets in environment variables or an approved secrets manager.
- Encrypt sensitive data in transit and at rest.
- Keep uploaded files outside public web directories.
- Enforce role, region, institution, and record-level access on every relevant request.
- Do not permit ordinary application database credentials to update or delete audit rows.
- Minimise personal data in logs and error responses.
- Record security-relevant events in the audit trail.

## 20. Audit Event Requirements

Audit entries should include:

- Unique sequence or event identifier
- Timestamp
- Actor ID and role
- Action
- Entity type and ID
- Before and after snapshots, where applicable
- Reason or remarks
- Previous hash and current hash for hash-chain verification

Audit records are append-only. The application must not expose ordinary update or delete operations for audit entries.

## 21. API Testing Requirements

### Authentication and access

- Unauthenticated requests receive `401`.
- Users cannot access another institution's records.
- Regional officers cannot access unauthorised regions.
- Users cannot perform actions outside their role.
- OTP-protected accounts cannot access protected resources before verification.

### Workflow

- Every configured route advances in the correct order.
- Returning an application without a reason is rejected.
- Invalid or concurrent transitions are safely rejected.
- Holds and resumes affect ageing according to configured rules.
- Each state transition produces a corresponding audit event.

### Deadlines and notifications

- Reminder and escalation rules trigger at configured offsets.
- Running the scheduler twice does not create duplicates.
- Missed scheduler dates are processed during catch-up.
- Working-day timelines skip configured weekends and holidays.
- Simulated-date controls are unavailable in production.

### Compliance and documents

- Evidence submission and review work end to end.
- Rejected submissions contain reviewer remarks.
- Document expiry alerts follow configured intervals.
- Renewal verification updates validity records only after authorised review.

### Reporting and audit

- Dashboard and report figures match.
- CSV and PDF exports work for authorised users.
- Audit hash verification detects modified historical entries.
- Audit entries cannot be updated or deleted through normal application credentials.

## 22. Prototype Scope and Future Work

### Included in the prototype

- Authentication and role-based access
- Application routing and stage history
- Role-specific dashboards
- EVC scheduling and tracking
- Undertaking submissions and verification
- Document validity and renewal tracking
- Notifications and escalations
- Reports and exports
- Audit logging and integrity verification
- Admin configuration
- Scheduler and simulated-date controls
- Seeded demo data and mock/CSV integration

### Future work

- Live AICTE system integration
- Production identity provider or SSO
- SMS gateway
- DigiLocker and e-sign integration, subject to authorisation
- Production-grade object storage and malware scanning
- Approved government hosting and security certification
- Advanced analytics and predictive delay indicators

## 23. Implementation Notes

- API routers should be versioned under `backend/app/api/v1/`.
- Business logic belongs in service modules rather than directly in route handlers.
- Use SQLAlchemy transactions for workflow transitions and audit writes.
- Use Pydantic request and response schemas for all endpoints.
- Keep route definitions, timelines, notification rules, and escalation rules in database configuration.
- Use a central clock service for all deadline calculations.
- Use unique database constraints and idempotency keys where duplicate processing is possible.
- Generate and maintain the interactive OpenAPI specification through FastAPI.
- Document any endpoint or permission change and cover it with automated tests.


## 24. Phase 6: Analytics, Reporting, Configurable Administration & Monitoring Endpoints

### 24.1 Role-Scoped Analytics (`/dashboard`)
- `GET /api/v1/dashboard/volume-trends`: Monthly application intake and resolution trends.
  - Query parameters: `start_date`, `end_date`, `region_id`, `institution_id`, `route_type_id`, `status`.
- `GET /api/v1/dashboard/regional-comparison`: Cross-region comparison of applications, approvals, pendencies, and overdue rates.
  - Scoping: Apex AICTE officials and administrators only. Rejects institution users with `403 Forbidden`.
- `GET /api/v1/dashboard/evc-analytics`: EVC scheduling status, outcome distribution, and visit metrics.
- `GET /api/v1/dashboard/undertaking-analytics`: Undertaking compliance rates, verification rates, and overdue counts.
- `GET /api/v1/dashboard/document-analytics`: Document health, expiry horizons (30d, 60d, 90d), and renewal queue.
- `GET /api/v1/dashboard/operational-summary`: High-level operational summary with pending actions and SLA breach counts.

### 24.2 Standard Statutory Reporting (`/reports`)
- `GET /api/v1/reports/types`: List available report types with required scopes and metadata.
- `POST /api/v1/reports/preview`: Live paginated preview of report data with total count and column schemas.
- `POST /api/v1/reports/export`: Direct streaming CSV export.
  - Supported report codes: `application_pendency`, `application_ageing`, `evc_status`, `undertaking_compliance`, `document_validity`, `escalations_audit`.
  - Security protections: Max 2000 rows limit, Formula Injection sanitization (`=`, `+`, `-`, `@`, `\t`, `\r` escaped with `'`), UTF-8 BOM encoding (`\ufeff`), and audit log record generation on every export.

### 24.3 Configurable Administration (`/admin`)
- `PATCH /api/v1/admin/stages/{stage_id}`: Update stage parameters (`timeline_days`, `grace_period_days`, `is_active`). Requires `change_reason`. Pinned versions of active applications are preserved.
- `GET|POST|PUT|DELETE /api/v1/admin/rules/reminders`: Full CRUD for automated reminder rules with mandatory change reason.
- `GET|POST|PUT|DELETE /api/v1/admin/rules/escalations`: Full CRUD for multi-tier escalation rules with mandatory change reason.
- `GET|POST|DELETE /api/v1/admin/holidays`: Manage regional/national holiday calendar with duplicate prevention.
- `GET|PUT /api/v1/admin/message-templates`: Manage notification and escalation notification message templates.
- `GET /api/v1/admin/config/versions`: Query historical configuration snapshots and change reason audits.

### 24.4 Cryptographic Audit Trail Explorer (`/audit`)
- `GET /api/v1/audit/logs`: Filtered, paginated audit log entries with previous/current hash verification.
- `GET /api/v1/audit/verify-integrity`: Validates the complete SHA-256 hash chain from genesis to head.

### 24.5 Operational Worker & Notification Monitoring (`/monitoring`)
- `GET /api/v1/monitoring/worker`: Inspect scheduler run history, job execution status, and next scheduled runs.
- `GET /api/v1/monitoring/notifications`: Inspect pending notification queues, delivery logs, and retry attempts.
- `GET /api/v1/health/readiness`: Alias for container/system readiness probes.


End of API Specification