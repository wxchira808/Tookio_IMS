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

## Verification Checklist

- New doctype name checked against ERPNext doctype list.
- New Link fields validated against live ERPNext masters.
- Existing reports and print formats still render after schema updates.
- Assignment and permissions workflows still pass smoke tests.
