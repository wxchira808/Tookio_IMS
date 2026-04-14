import frappe


DEMO_PREFIX = "DEMO 2026"


def _upsert(doctype: str, lookup: dict, payload: dict) -> str:
    existing = frappe.db.exists(doctype, lookup)
    if existing:
        doc = frappe.get_doc(doctype, existing)
        for key, value in payload.items():
            doc.set(key, value)
        doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc({"doctype": doctype, **payload})
    doc.insert(ignore_permissions=True)
    return doc.name


def seed_demo_data() -> dict:
    created = {}

    # 1) Taxonomy and risk core
    tax_ops = _upsert(
        "Risk Taxonomy",
        {"taxonomy_name": f"{DEMO_PREFIX} Operational Risk"},
        {
            "taxonomy_name": f"{DEMO_PREFIX} Operational Risk",
            "taxonomy_code": "DEMO-OPS-RISK",
            "risk_domain": "Operational",
            "description": "Demo taxonomy for operations-related risks.",
            "is_active": 1,
            "review_frequency": "Quarterly",
        },
    )

    tax_comp = _upsert(
        "Risk Taxonomy",
        {"taxonomy_name": f"{DEMO_PREFIX} Compliance Risk"},
        {
            "taxonomy_name": f"{DEMO_PREFIX} Compliance Risk",
            "taxonomy_code": "DEMO-COMP-RISK",
            "risk_domain": "Compliance",
            "description": "Demo taxonomy for compliance-related risks.",
            "is_active": 1,
            "review_frequency": "Quarterly",
        },
    )

    risk_1 = _upsert(
        "IMS Risk Register",
        {"risk_title": f"{DEMO_PREFIX} Supplier Outage"},
        {
            "risk_title": f"{DEMO_PREFIX} Supplier Outage",
            "risk_taxonomy": tax_ops,
            "risk_description": "Critical supplier disruption affecting service delivery.",
            "source_type": "Incident",
            "likelihood": 4,
            "impact": 5,
            "velocity": 4,
            "control_effectiveness": 2,
            "status": "Active",
            "mitigation_status": "In Progress",
            "risk_treatment_strategy": "Mitigate",
            "capa_status": "Open",
        },
    )

    # NOTE: some IMS doctypes currently use format autoname patterns that
    # produce duplicate names for multiple inserts. Keep one demo record here.
    risk_2 = None
    risk_3 = None

    # 2) Audit lifecycle
    audit_plan = _upsert(
        "IMS Audit Plan",
        {"plan_title": f"{DEMO_PREFIX} Q2 Internal Audit Plan"},
        {
            "plan_title": f"{DEMO_PREFIX} Q2 Internal Audit Plan",
            "plan_year": 2026,
            "plan_type": "Annual",
            "recurring_frequency": "Quarterly",
            "schedule_start": "2026-04-01",
            "schedule_end": "2026-06-30",
            "risk_reference": risk_1,
            "status": "Approved",
            "audit_scope": "Procurement and vendor management controls.",
            "audit_objectives": "Validate control design and operating effectiveness.",
        },
    )

    audit_program = _upsert(
        "IMS Audit Program",
        {"program_name": f"{DEMO_PREFIX} Vendor Control Testing Program"},
        {
            "program_name": f"{DEMO_PREFIX} Vendor Control Testing Program",
            "audit_plan": audit_plan,
            "audit_standard": "GIAS",
            "objective": "Assess adherence to approved vendor control standards.",
            "scope": "High-value vendor onboarding and performance monitoring.",
            "frequency": "Quarterly",
            "status": "Active",
            "is_template": 0,
        },
    )

    engagement = _upsert(
        "IMS Audit Engagement",
        {"engagement_title": f"{DEMO_PREFIX} Vendor Governance Engagement"},
        {
            "engagement_title": f"{DEMO_PREFIX} Vendor Governance Engagement",
            "audit_plan": audit_plan,
            "audit_program": audit_program,
            "status": "In Progress",
            "risk_rating": "High",
            "findings_summary": "Control weaknesses observed in approval trail completeness.",
        },
    )

    _upsert(
        "IMS Audit Finding",
        {"finding_title": f"{DEMO_PREFIX} Missing Approval Evidence"},
        {
            "finding_title": f"{DEMO_PREFIX} Missing Approval Evidence",
            "audit_engagement": engagement,
            "finding_type": "Non-Conformity",
            "severity": "Major",
            "finding_description": "Approval artifacts missing for selected transactions.",
            "status": "Open",
            "capa_required": 0,
            "recommendation": "Enforce mandatory document attachment controls.",
        },
    )

    # 3) Compliance and mappings
    compliance_reg = _upsert(
        "IMS Compliance Register",
        {"obligation_title": f"{DEMO_PREFIX} Data Retention Control"},
        {
            "obligation_title": f"{DEMO_PREFIX} Data Retention Control",
            "standard_framework": "ISO 27001",
            "requirement_description": "Retention and disposal controls must be enforced.",
            "compliance_status": "Partially Compliant",
            "risk_rating": "High",
            "applicable_article": "A.8.3",
            "penalty_exposure": "Potential regulatory penalty and reputational impact.",
        },
    )

    _upsert(
        "IMS Compliance Standard Mapping",
        {"mapping_title": f"{DEMO_PREFIX} ISO27001-A8.3 Mapping"},
        {
            "mapping_title": f"{DEMO_PREFIX} ISO27001-A8.3 Mapping",
            "compliance_register": compliance_reg,
            "framework": "ISO 27001",
            "requirement_clause": "A.8.3",
            "control_reference": "CTRL-DATA-RET-01",
            "attestation_status": "In Progress",
        },
    )

    # 4) CAPA and KRI monitoring
    _upsert(
        "IMS CAPA",
        {"capa_title": f"{DEMO_PREFIX} Vendor Approval Control Fix"},
        {
            "capa_title": f"{DEMO_PREFIX} Vendor Approval Control Fix",
            "capa_type": "Corrective Action",
            "source_doctype": "IMS Audit Engagement",
            "source_reference": engagement,
            "risk_register_ref": risk_1,
            "description": "Remediate missing approval checkpoints in workflow.",
            "status": "In Progress",
            "priority": "High",
            "corrective_action_description": "Deploy mandatory approval step in workflow.",
        },
    )

    _upsert(
        "IMS KRI Definition",
        {"kri_name": f"{DEMO_PREFIX} Open Critical Findings Ratio"},
        {
            "kri_name": f"{DEMO_PREFIX} Open Critical Findings Ratio",
            "risk_taxonomy": tax_comp,
            "unit": "Percentage",
            "threshold_direction": "Higher Is Worse",
            "threshold_green": 5,
            "threshold_yellow": 10,
            "threshold_red": 15,
            "current_value": 12,
            "status": "Active",
        },
    )

    _upsert(
        "IMS KRI Definition",
        {"kri_name": f"{DEMO_PREFIX} Overdue CAPA Count"},
        {
            "kri_name": f"{DEMO_PREFIX} Overdue CAPA Count",
            "risk_taxonomy": tax_ops,
            "unit": "Count",
            "threshold_direction": "Higher Is Worse",
            "threshold_green": 2,
            "threshold_yellow": 4,
            "threshold_red": 6,
            "current_value": 3,
            "status": "Paused",
        },
    )

    _upsert(
        "IMS Lessons Learned Repository",
        {"title": f"{DEMO_PREFIX} Approval Trail Lesson"},
        {
            "title": f"{DEMO_PREFIX} Approval Trail Lesson",
            "source_type": "Audit Engagement",
            "ims_audit_engagement": engagement,
            "summary": "Approval trail controls must be embedded in workflow design.",
            "root_cause_theme": "Control Design Gap",
            "corrective_pattern": "Mandatory checkpoints and evidence capture.",
            "preventive_pattern": "Quarterly control walk-through and sampling.",
            "reusability_rating": "High",
            "status": "Published",
        },
    )

    _upsert(
        "IMS Document Repository",
        {"document_title": f"{DEMO_PREFIX} Q2 Audit Evidence Pack"},
        {
            "document_title": f"{DEMO_PREFIX} Q2 Audit Evidence Pack",
            "document_type": "Evidence",
            "status": "Approved",
            "linked_audit_engagement": engagement,
            "linked_risk_register": risk_1,
            "document_category": "Audit",
            "description": "Compiled evidence for demo audit engagement.",
            "document_file": "/files/demo-q2-audit-evidence-pack.pdf",
            "retention_period_years": 7,
        },
    )

    created["risk_taxonomy"] = [tax_ops, tax_comp]
    created["risk_register"] = [risk_1]
    created["audit"] = [audit_plan, audit_program, engagement]
    created["compliance"] = [compliance_reg]

    frappe.db.commit()
    return {"ok": True, "seed": created}


def demo_status_snapshot() -> dict:
    status_doctypes = [
        "IMS Audit Plan",
        "IMS Audit Engagement",
        "IMS Audit Finding",
        "IMS CAPA",
        "IMS Compliance Register",
        "IMS Risk Register",
        "IMS KRI Definition",
        "IMS Lessons Learned Repository",
        "IMS Document Repository",
    ]

    out = {}
    for dt in status_doctypes:
        if not frappe.get_meta(dt).has_field("status"):
            continue
        rows = frappe.db.sql(
            f"""
            select status, count(*) as count
            from `tab{dt}`
            group by status
            order by count desc
            """,
            as_dict=True,
        )
        out[dt] = rows

    return out


def fix_bad_hash_names() -> dict:
    """Rename legacy names that include the literal '.#####' suffix."""
    from frappe.model.rename_doc import rename_doc

    doctypes = [
        "IMS Document Repository",
        "IMS Compliance Standard Mapping",
        "IMS Audit Engagement",
        "IMS Risk Maturity Snapshot",
        "IMS Lessons Learned Repository",
        "IMS Audit Program",
        "IMS Audit Plan",
        "IMS Audit Finding",
        "IMS Workpaper",
        "IMS Compliance Register",
        "IMS Risk Register",
        "IMS CAPA",
    ]

    renamed = []
    for dt in doctypes:
        bad_names = frappe.get_all(dt, filters={"name": ["like", "%.#####"]}, pluck="name")
        for old_name in bad_names:
            base = old_name.replace(".#####", "")
            candidate = f"{base}00001"
            i = 1
            while frappe.db.exists(dt, candidate):
                i += 1
                candidate = f"{base}{i:05d}"
            rename_doc(dt, old_name, candidate, force=True, ignore_permissions=True, show_alert=False)
            renamed.append({"doctype": dt, "old": old_name, "new": candidate})

    if renamed:
        frappe.db.commit()

    return {"renamed": renamed, "count": len(renamed)}
