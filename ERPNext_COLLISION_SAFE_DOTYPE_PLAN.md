# ERPNext Collision-Safe Doctype Plan

This project integrates with ERPNext. Use ERPNext master doctypes where possible and avoid custom doctype names that are likely to collide now or later.

## Rules

1. Do not prefix every custom doctype.
2. Prefix only high-collision names with `IMS`.
3. Reuse ERPNext masters via Link fields instead of duplicating entities.
4. Before adding a new doctype, check bench metadata for conflicts.

## Reuse ERPNext Masters (Preferred)

- Employee
- Department
- Customer
- Supplier
- Project
- Task
- Company
- Cost Center
- User
- ToDo
- Communication

## Naming Guidance

Use unprefixed names for incident-domain entities that are clearly unique:

- Incident
- Incident Investigation
- Incident Resolution
- Incident Timeline
- Incident Notification

Use scoped names for likely collisions in ARC expansion:

- `IMS Audit Plan`
- `IMS Audit Program`
- `IMS Audit Engagement`
- `IMS Workpaper`
- `IMS Audit Finding`
- `IMS Document Repository`
- `IMS Compliance Register`
- `IMS Compliance Standard Mapping`
- `IMS Risk Taxonomy`
- `IMS Risk Register`
- `IMS KRI Definition`
- `IMS Risk Maturity Snapshot`
- `IMS Lessons Learned Repository`

## First Implemented ERPNext-Compatibility Changes

- Incident reporter fields now support ERPNext masters:
  - `reporter_employee_id` -> Link(Employee)
  - `reporter_department` -> Link(Department)
- Incident contextual links added:
  - `related_customer` -> Link(Customer)
  - `related_project` -> Link(Project)
- Affected parties now use dynamic linking:
  - `party_name` -> Dynamic Link via hidden `party_reference_doctype`
  - mapped from party type to Employee/Customer/Supplier/Contact

## ARC Slice Implemented

- Added `Risk Taxonomy` doctype for hierarchical risk classification.
- Added `IMS Risk Register` doctype (scoped naming to reduce ERPNext collision risk).
- Linked `Risk Assessment` to both taxonomy and risk register entries.
- Added server-side risk score calculation and register-to-assessment field synchronization.
- Added audit/compliance scaffolding doctypes:
  - `IMS Audit Plan`
  - `IMS Audit Program`
  - `IMS Audit Engagement`
  - `IMS Workpaper`
  - `IMS Compliance Register`
  - `IMS KRI Definition`
- Added `IMS Compliance Standard Mapping` for framework control mappings to concrete records.
- Added daily ARC automation for overdue risk/compliance reviews and KRI red-alert task generation.
- Added ARC maturity analytics through daily `IMS Risk Maturity Snapshot` generation.
- Added knowledge management through `IMS Lessons Learned Repository` with auto-capture from submitted Incident Resolutions.
- Added ARC API endpoints for executive summaries, NLQ-style risk/compliance queries, and maturity trend retrieval.
- Added Local AI service (Ollama-based, data sovereignty compliant) for NLP text mining, NLG narratives, and compliance classification.
- Added Monte Carlo simulation and scikit-learn risk ML service for predictive risk scoring.

## Second ARC Slice – Tender Gap Closure (KTNA/OT/04/2025-2026)

Implemented after analysis of the KenTrade ARC tender document to close remaining functional gaps:

### New Doctypes
- `IMS Audit Finding` – structured logging of non-conformities and observations from audit engagements.
  - Fields: finding type, severity (Critical/Major/Minor/Advisory), condition/cause/effect, root cause with RCA method,
    auditor recommendation, management response, CAPA linkage (auto-creates IMS CAPA on save when required),
    effectiveness testing, target/actual closure dates.
- `IMS Document Repository` – central repository for all ARC-related documents.
  - Fields: document type, version number, status, tagging, linked engagement/plan/risk/workpaper, version history
    (supersedes link + change summary), retention period with auto-expiry calculation.
  - Auto-propagates audit engagement from linked workpaper.

### New Reports
- `Audit Coverage` (Script Report on IMS Audit Engagement) – shows planned vs. in-progress vs. closed engagements
  by department, with open/critical finding counts and closure rate. Includes bar chart.
- `Audit Plan Progress` (Script Report on IMS Audit Plan) – shows total/completed/in-progress/planned engagements
  per plan with completion percentage and budget. Includes stacked bar chart.

### API Enhancements (`arc_reporting.py`)
- `get_arc_dashboard_summary` – now also counts open and critical audit findings.
- `nlq_arc_query` – expanded NLQ patterns:
  - Overdue risks, open/critical audit findings, active audit plans, open CAPAs, red KRIs, overdue compliance assessments.
- `get_risk_heatmap_data` – new endpoint returning 5×5 likelihood×impact matrix with risk counts per cell
  for interactive risk heatmap visualisation.
- `get_audit_findings_summary` – new endpoint summarising findings by severity, type, and status
  (optionally filtered by engagement), used for board reports.

### Workspace
- ARC Command Center updated to include `IMS Audit Finding`, `IMS Document Repository`,
  `Audit Coverage` report, and `Audit Plan Progress` report.

## Verification Checklist

- New doctype name checked against ERPNext doctype list.
- New Link fields validated against live ERPNext masters.
- Existing reports and print formats still render after schema updates.
- Assignment and permissions workflows still pass smoke tests.
