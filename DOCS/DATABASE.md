# NiyamSetu Database Architecture & Schema Specification

This document details the PostgreSQL relational schema, entity relationships, indexing strategy, and migration management for NiyamSetu.

---

## 1. Design Conventions

1. **UUID Primary Keys**: All business entities use RFC 4122 version 4 UUIDs to prevent sequential ID guessing and enable seamless distributed generation.
2. **UTC Timezone-Aware Timestamps**: All timestamp columns (`created_at`, `updated_at`, `occurred_at`, `stage_entered_at`) store timezone information (`TIMESTAMP WITH TIME ZONE`).
3. **Structured Metadata via JSONB**: Extensible fields (e.g. audit metadata, stage transition payloads, recipient role lists) use PostgreSQL `JSONB` for indexing and queryability.
4. **Versioned Route Workflows**: Route types and ordered stages are versioned (`route_version`). In-progress applications preserve the exact route version assigned at creation time.
5. **Decoupled File Storage**: Uploaded files and physical payloads are never stored as database blobs; the database only retains metadata (`storage_key`, `size_bytes`, `mime_type`, `checksum`) in `files` and `documents`.
6. **Append-Only Tamper-Evident Audit Trail**: The `audit_log` table contains `previous_hash` and `entry_hash` forming a cryptographic SHA-256 hash chain verified by the application service.

---

## 2. Entity Summary (25 Entities)

| Table | Purpose | Primary Key | Key Foreign Keys |
|---|---|---|---|
| `regions` | Administrative regional offices | UUID | None |
| `institutions` | Managed institutions | UUID | `region_id -> regions.id` |
| `users` | Authenticated system users | UUID | `region_id`, `institution_id` |
| `user_sessions` | Server-managed authenticated sessions | UUID | `user_id -> users.id` |
| `route_types` | Configurable workflow routes | UUID | None |
| `route_stages` | Ordered stages for a route version | UUID | `route_type_id -> route_types.id` |
| `applications` | Approval applications & active state | UUID | `institution_id`, `route_type_id`, `current_stage_id`, `assigned_to_user_id` |
| `stage_history` | Complete stage transition history | UUID | `application_id`, `from_stage_id`, `to_stage_id`, `performed_by_user_id` |
| `files` | Stored file object metadata | UUID | `uploaded_by_user_id -> users.id` |
| `evcs` | Expert Visit Committee inspections | UUID | `application_id`, `assigned_region_id` |
| `evc_members` | Assigned committee members | UUID | `evc_id`, `user_id` |
| `evc_reports` | Inspection report metadata | UUID | `evc_id`, `file_id`, `submitted_by_user_id` |
| `undertakings` | Time-bound obligations & conditions | UUID | `application_id`, `assigned_institution_id`, `verified_by_user_id` |
| `undertaking_submissions` | Evidence submitted against conditions | UUID | `undertaking_id`, `submitted_by_user_id`, `file_id` |
| `documents` | Institutional document registry | UUID | `institution_id`, `application_id`, `verified_by_user_id` |
| `document_renewals` | Lease & document expiry tracking | UUID | `document_id`, `replacement_document_id`, `reviewed_by_user_id` |
| `reminder_rules` | Configurable pre-due reminder offsets | UUID | None |
| `escalation_rules` | Multi-tier SLA breach escalation rules | UUID | None |
| `message_templates` | Standardized notification templates | UUID | None |
| `notifications` | In-app and dispatched notifications | UUID | `recipient_user_id`, `application_id` |
| `escalations` | Escalated overdue items | UUID | `application_id`, `assigned_to_user_id` |
| `scheduler_runs` | Background scan execution logs | UUID | None |
| `holidays` | Configured working-day calendar | UUID | `region_id -> regions.id` |
| `config_versions` | Versioned config change snapshots | UUID | `changed_by_user_id -> users.id` |
| `audit_log` | Tamper-evident append-only audit log | UUID | `actor_user_id -> users.id` |

---

## 3. Indexes & Constraints

- **Unique Constraints**:
  - `regions(code)`
  - `institutions(institution_code)`
  - `users(email)`
  - `user_sessions(session_token_hash)` (never stores raw unhashed tokens)
  - `route_types(code)`
  - `route_stages(route_type_id, route_version, stage_code)`
  - `route_stages(route_type_id, route_version, sequence)`
  - `applications(reference_no)`
  - `files(storage_key)`
  - `documents(storage_key)`
  - `notifications(dedupe_key)` (enforces idempotent alert delivery)
  - `message_templates(code)`
- **Performance Indexes**:
  - `user_sessions(user_id)`
  - `user_sessions(expires_at)`
  - `user_sessions(revoked_at)`
  - `applications(status)`
  - `applications(institution_id)`
  - `applications(route_type_id, route_version)`
  - `stage_history(application_id, performed_at)`
  - `evcs(status, due_by)`
  - `undertakings(status, due_date)`
  - `documents(institution_id, valid_to)`
  - `audit_log(entity_type, entity_id)`
  - `audit_log(occurred_at)`
  - `audit_log(entry_hash)`

---

## 4. Alembic Migration Management

Alembic migrations reside in `backend/migrations/`.

### Applying Migrations to `niyamsetu_dev`
```powershell
cd backend
python -m alembic upgrade head
```

### Checking Migration Status
```powershell
python -m alembic current
```

### Downgrading / Rollback
```powershell
python -m alembic downgrade -1
```
