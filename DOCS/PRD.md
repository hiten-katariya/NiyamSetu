# NiyamSetu: Product Requirements Document (PRD)
---

## 1. Product Overview

NiyamSetu is an integrated, secure and configurable digital platform that automates and monitors AICTE approval-related workflows. It covers application routing, scrutiny stages, EVC scheduling, pendency monitoring, time-bound undertakings, institutional compliance and validity of prescribed documents such as leases. It produces real-time dashboards, automated notifications, deadline reminders and escalations for institutions and authorised AICTE officials.

NiyamSetu supports the approval process. It does not replace statutory scrutiny, verification, inspection or decisions that belong to the competent authority.

## 2. Problem Statement

AICTE processes applications through multiple stages (scrutiny/re-scrutiny, EVC, SAC/SHC and others under the APH). Some approvals are granted subject to time-bound undertakings and document submissions. Today, monitoring application movement, stage-wise pendency, EVC scheduling, undertakings and document validity across Regions and officials relies on manual coordination and follow-up. This causes:

- Missed or delayed deadlines
- Expired documents (for example leases) going unnoticed
- Poor visibility of bottlenecks and workload
- Weak accountability and incomplete audit trails
- Repetitive manual follow-up by officers

## 3. Goals and Non-Goals

### Goals
1. Automate routing of applications through the applicable stage combinations.
2. Give real-time visibility of pendency, ageing and workload across Regions.
3. Ensure EVCs are queued, scheduled and completed within prescribed timelines.
4. Track undertakings and compliance evidence through to verification and closure.
5. Monitor document validity and trigger timely renewal alerts.
6. Deliver configurable notifications and automatic escalation.
7. Maintain a complete, tamper-evident audit trail.

### Non-Goals
- Replacing scrutiny, inspection, verification or approval decisions by competent authorities
- Making autonomous approval or rejection decisions
- Replacing AICTE's core systems (NiyamSetu integrates with or sits alongside them)
- Hardcoding APH rules (all rules are configurable)

## 4. Users and Roles

| Role | Description | Key needs |
|---|---|---|
| **Institution User** | Authorised representative of a technical institution | See application status, receive deadline alerts, submit undertakings and renewed documents, respond to deficiencies |
| **Scrutiny Officer** | Processes applications at scrutiny/re-scrutiny stage | Work queue, return/revert with reasons, case summary |
| **Regional Officer** | Regional office official | Region-wise dashboard, pendency, EVC scheduling, compliance follow-up |
| **Bureau Officer** | Bureau-level official | Cross-region view, bottlenecks, escalated cases |
| **Committee Member (EVC / SAC / SHC)** | Expert and approval committee members | Assigned cases, EVC schedule, record observations |
| **Senior Authority** | Designated escalation authorities | Escalated and overdue cases, performance reports |
| **System Administrator** | Technical and configuration admin | Manage users, roles, rules, timelines, templates |

## 5. Scope

### In scope (Prototype)
Application routing, role-based dashboards, stage-wise pendency monitoring, EVC queue and alerts, undertaking tracking, lease/document expiry monitoring, compliance submission and verification, notifications, escalation, reports and audit trail, all on seeded dummy data.

### Out of scope for prototype (described as future roadmap)
Live integration with AICTE production systems, production hosting and security certification, mobile apps, AI-based document analysis.

## 6. Functional Requirements

### 6.1 Approval Workflow Automation

| ID | Requirement | Priority |
|---|---|---|
| WF-01 | Each application is assigned a route type (Only Scrutiny, Scrutiny + EVC, EVC + SAC/SHC, Only EVC, and other combinations) defined in configuration. | Must |
| WF-02 | Route types are defined as ordered stage sequences, editable by admin without code changes. | Must |
| WF-03 | On completion of a stage by an authorised user, the application moves automatically to the next stage in its route. | Must |
| WF-04 | Authorised users can return/revert an application to a previous stage or to the institution for deficiency, clarification or further verification. A reason is mandatory. | Must |
| WF-05 | Stage transitions are permitted only for users holding the required role for that stage. | Must |
| WF-06 | The system generates standardised communications (deficiency letters, acknowledgements) from templates. | Should |
| WF-07 | The system generates an electronic case summary for each application, for officer review. | Should |
| WF-08 | Automated actions are limited to routing and communication. Decisions are always taken manually by the competent authority. | Must |

### 6.2 Integrated Dashboard and Pendency Monitoring

| ID | Requirement | Priority |
|---|---|---|
| DB-01 | Consolidated real-time dashboard showing applications by Region, stage, institution, officer and committee. | Must |
| DB-02 | Ageing view: days in current stage and total days against prescribed timelines. | Must |
| DB-03 | Workload distribution per officer and committee. | Must |
| DB-04 | Bottleneck view: stages with the highest pendency or longest average dwell time. | Should |
| DB-05 | Visual alerts for applications approaching (amber) and exceeding (red) timelines. | Must |
| DB-06 | Role-based dashboards for Institution, Regional Officer, Bureau Officer, Committee and Senior Authority. | Must |
| DB-07 | Drill-down from summary tiles to the application list to the full application history. | Must |
| DB-08 | Filters by Region, stage, route type, date range, institution type and status. | Must |

### 6.3 EVC Scheduling and Alerts

| ID | Requirement | Priority |
|---|---|---|
| EV-01 | Applications requiring an EVC are placed automatically in the EVC queue after preliminary processing is complete. | Must |
| EV-02 | Track EVC status: queued, scheduled, conducted, report submitted, closed. | Must |
| EV-03 | Track scheduling and completion timelines, with priority tracking for new institutions. | Must |
| EV-04 | Authorised officials schedule EVCs and assign committee members. | Must |
| EV-05 | Reminders for EVCs due or approaching their timeline. | Must |
| EV-06 | Delayed EVCs escalate to designated authorities. | Must |
| EV-07 | EVC calendar view by Region. | Should |

### 6.4 Time-Bound Undertakings and Institutional Compliance

| ID | Requirement | Priority |
|---|---|---|
| UT-01 | Maintain a digital record of each approval granted subject to undertakings: conditions, due dates, supporting evidence and status. | Must |
| UT-02 | Notify institutions of upcoming compliance deadlines at configurable intervals. | Must |
| UT-03 | Institutions upload supporting documents online. | Must |
| UT-04 | Authorised officials verify, accept or reject evidence with remarks. | Must |
| UT-05 | Rejected evidence returns to the institution with a revised deadline, if permitted. | Should |
| UT-06 | Unfulfilled undertakings beyond the stipulated timeline trigger reminders and then escalation. | Must |
| UT-07 | Each undertaking shows a status timeline: pending, submitted, under verification, verified, overdue, closed. | Must |

### 6.5 Lease and Document Validity Monitoring

| ID | Requirement | Priority |
|---|---|---|
| LD-01 | Track document type, validity start and expiry dates for leases and other prescribed documents. | Must |
| LD-02 | Advance alerts at configurable intervals before expiry (for example 180, 90, 60, 30 and 15 days). | Must |
| LD-03 | Institutions upload renewed documents online. | Must |
| LD-04 | Officials verify renewed documents and update the validity record. | Must |
| LD-05 | Overdue alerts and escalation for expired documents or missing renewals. | Must |
| LD-06 | Document validity dashboard: valid, expiring soon, expired, renewal under verification. | Must |

### 6.6 Notifications, Escalation and Reporting

| ID | Requirement | Priority |
|---|---|---|
| NE-01 | Configurable notification rules by event type, recipient role, timing and channel. | Must |
| NE-02 | Channels: in-app notifications and email. SMS is optional. | Must |
| NE-03 | Notification templates editable by admin. | Should |
| NE-04 | Multi-level escalation matrix by event type and Region (see Section 8). | Must |
| NE-05 | A scheduler evaluates all due dates daily and on demand. | Must |
| NE-06 | Reports: application pendency, EVC status, undertaking compliance, document validity, overdue cases, Region-wise performance. | Must |
| NE-07 | Export reports to CSV and PDF. | Should |
| NE-08 | Alerts are de-duplicated and acknowledged or snoozed with a reason. | Should |

### 6.7 Audit Trail

| ID | Requirement | Priority |
|---|---|---|
| AU-01 | Log every action: who, role, what, when, from and to state, reason and remarks. | Must |
| AU-02 | Log all alerts sent, submissions, verifications, escalations and case closures. | Must |
| AU-03 | Audit records are append-only and cannot be edited or deleted by any user. | Must |
| AU-04 | Searchable and filterable audit view with export. | Must |

### 6.8 Administration and Configuration

| ID | Requirement | Priority |
|---|---|---|
| AD-01 | Manage users, roles, Regions and officer mappings. | Must |
| AD-02 | Configure route types, stage timelines, reminder intervals and escalation chains. | Must |
| AD-03 | Version configuration changes and log them in the audit trail. | Should |
| AD-04 | "Simulate date" control (non-production) to demonstrate time-based alerts. | Must (prototype) |

## 7. Application Lifecycle (Reference Flow)

1. Application received and registered, route type assigned
2. Scrutiny (and re-scrutiny if returned)
3. If the route includes an EVC: EVC queue, scheduling, visit, report
4. If the route includes SAC/SHC: committee review
5. Decision recorded by the competent authority (manual)
6. If approved with undertakings: undertakings and document validity records created
7. Ongoing compliance and document monitoring until closure

At every step, return/revert is available to authorised users with a mandatory reason.

*Stage names, order and timelines are illustrative defaults. The actual values must be loaded from the APH into configuration.*

## 8. Escalation Model (Illustrative, Configurable)

| Level | Trigger | Action |
|---|---|---|
| L0 | X days before deadline | Reminder to responsible user or institution |
| L1 | Deadline reached | Alert to assigned officer and supervisor |
| L2 | Deadline + N days | Escalate to Regional Officer |
| L3 | Deadline + M days | Escalate to Bureau Officer or Senior Authority |

Thresholds differ by event type (application stage, EVC, undertaking, document expiry) and are admin-configurable.

## 9. Data Model (High Level)

- **Institution:** id, name, type, Region, contact details
- **Application:** id, institution, route type, current stage, status, created date
- **Route Type / Stage Config:** ordered stages, timeline per stage
- **Stage History:** application, stage, entered, exited, actor, outcome, reason
- **EVC:** application, status, scheduled date, members, report
- **Undertaking:** application, condition, due date, status, evidence, verifier
- **Document (Lease etc.):** institution, type, validity start, expiry, status, file
- **Notification:** recipient, event, channel, sent time, acknowledged flag
- **Escalation:** source item, level, escalated to, time, resolved flag
- **User / Role / Region mapping**
- **Audit Log:** append-only event records
- **Rules Config:** timelines, reminder intervals, escalation chains, templates

## 10. Non-Functional Requirements

| Area | Requirement |
|---|---|
| **Security** | Role-based access control, least privilege, encrypted data in transit and at rest, secure session handling, optional OTP/MFA |
| **Confidentiality** | Institutions see only their own data. Officers see only assigned Regions or cases unless authorised. |
| **Auditability** | Immutable, timestamped logs of all actions |
| **Reliability** | Scheduler must not miss deadlines. Missed runs are detected and re-run. |
| **Performance** | Dashboards load in under 3 seconds for typical data volumes |
| **Scalability** | Supports tens of thousands of applications and documents |
| **Configurability** | Rules, timelines and templates changeable without code deployment |
| **Usability** | Simple, accessible interface. Responsive on desktop and tablet. |
| **Interoperability** | API-based adapter layer for AICTE systems, plus CSV import as a fallback |
| **Data retention** | Document and audit retention policy configurable per AICTE norms |
| **Accessibility** | Aligned with applicable government accessibility guidelines |

## 11. Integration

- **Adapter layer:** a defined interface for applications, institutions and user data from existing AICTE systems.
- **Fallback:** bulk CSV/Excel import for data when APIs are unavailable.
- **Prototype:** mock adapter with seeded dummy data.
- **Future:** SSO, e-sign, DigiLocker or other authorised services, as permitted.

## 12. Human Oversight and Regulatory Safeguards

- The system functions according to applicable AICTE regulations, the APH and authorised procedures.
- Automated alerts, recommendations and workflow actions support the process only.
- Scrutiny outcomes, verification, inspections and approval or rejection decisions are taken only by authorised humans.
- Every system-generated communication or summary is reviewable before it is treated as final, where required.
- All overrides and manual interventions are logged with reasons.

## 13. Success Metrics

| Metric | Target (illustrative) |
|---|---|
| Reduction in manual follow-up effort | 50% or more |
| Applications processed within prescribed timelines | Measurable increase against baseline |
| Alerts delivered on schedule | 99% or more |
| Expired documents without prior alert | Zero |
| Overdue cases escalated automatically | 100% |
| Audit trail completeness | 100% of actions logged |
| Dashboard adoption by officers | High and trending upward |

## 14. Prototype Acceptance Criteria

1. An application with each route type moves correctly through its stages.
2. Return/revert requires a reason and appears in the history.
3. Each role sees only its authorised dashboard and data.
4. Ageing and pendency numbers match the underlying data.
5. EVC queue entries, reminders and escalations fire at configured times (demonstrated with simulated dates).
6. Undertaking lifecycle works end to end: notify, submit, verify, close or escalate.
7. Lease expiry alerts fire at each configured interval, and overdue cases escalate.
8. Reports match dashboard figures and export correctly.
9. Every action above appears in the audit trail.
10. Changing a timeline in configuration changes system behaviour without code changes.

## 15. Assumptions and Dependencies

- APH stage definitions and timelines will be provided or confirmed by AICTE.
- Officer, Region and escalation mappings will be available.
- Email or notification gateway access is available for the deployment.
- Existing system data can be shared via API or file export.

## 16. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| APH rules misinterpreted | Rules fully configurable, reviewed by domain experts |
| No API access to existing systems | CSV import and adapter layer |
| Alert fatigue | De-duplication, snooze, tunable thresholds |
| Data security concerns | RBAC, encryption, audit logging, approved hosting |
| User adoption | Simple UI, role-specific views, training material |
| Scheduler failure | Monitoring, retry and catch-up runs |

## 17. Phased Roadmap

| Phase | Content |
|---|---|
| **Phase 1 (Prototype)** | Workflow engine, dashboards, EVC, undertakings, lease tracking, alerts and escalation, audit trail, seeded data |
| **Phase 2 (Pilot)** | Integration with AICTE systems, real user onboarding, SMS, hardened security |
| **Phase 3 (Rollout)** | All Regions, advanced analytics, predictive delay indicators, mobile access, e-sign and other integrations |

## 18. Open Questions

1. What is the exact list of route types and stage sequences in the current APH?
2. What are the prescribed timelines for each stage, EVC and compliance type?
3. Who are the designated escalation authorities for each Region and event?
4. Which document types besides leases require validity tracking?
5. Which authorised systems can be integrated, and through what interfaces?
6. What are the hosting, data localisation and retention requirements?

