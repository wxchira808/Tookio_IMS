# pyright: reportMissingImports=false

import frappe
from frappe import _


@frappe.whitelist()
def get_arc_dashboard_summary():
    summary = {
        "open_risks": frappe.db.count("IMS Risk Register", {"status": ["!=", "Closed"]}),
        "high_or_very_high_risks": frappe.db.count(
            "IMS Risk Register", {"risk_level": ["in", ["High", "Very High"]], "status": ["!=", "Closed"]}
        ),
        "overdue_risk_reviews": frappe.db.count(
            "IMS Risk Register", {"mitigation_status": "Overdue", "status": ["!=", "Closed"]}
        ),
        "non_compliant_items": frappe.db.count(
            "IMS Compliance Register", {"compliance_status": ["in", ["Non-Compliant", "Partially Compliant"]]}
        ),
        "kri_red_count": frappe.db.count("IMS KRI Definition", {"status": "Active", "alert_level": "Red"}),
        "open_action_items": frappe.db.count("Action Item", {"status": ["in", ["Open", "In Progress", "Overdue"]]}),
        "open_audit_findings": _safe_count(
            "IMS Audit Finding", {"status": ["not in", ["Closed", "Accepted Risk"]]}
        ),
        "critical_audit_findings": _safe_count(
            "IMS Audit Finding", {"severity": "Critical", "status": ["not in", ["Closed", "Accepted Risk"]]}
        ),
    }

    summary["executive_summary"] = _build_executive_summary(summary)
    return summary


def _safe_count(doctype, filters):
    """Count records only if the table exists (graceful for fresh installs)."""
    try:
        if frappe.db.table_exists(doctype):
            return frappe.db.count(doctype, filters)
    except Exception:
        pass
    return 0


@frappe.whitelist()
def nlq_arc_query(question=None):
    text = (question or "").strip().lower()
    if not text:
        return {"message": _("Please provide a question.")}

    # --- Risk patterns ---
    if "high" in text and "risk" in text and ("pending" in text or "mitigation" in text):
        return {
            "query": question,
            "results": frappe.get_all(
                "IMS Risk Register",
                filters={
                    "risk_level": ["in", ["High", "Very High"]],
                    "mitigation_status": ["!=", "Completed"],
                    "status": ["!=", "Closed"],
                },
                fields=["name", "risk_title", "risk_owner", "risk_level", "mitigation_status", "next_review_date"],
                limit_page_length=200,
            ),
        }

    if "overdue" in text and "risk" in text:
        return {
            "query": question,
            "results": frappe.get_all(
                "IMS Risk Register",
                filters={"mitigation_status": "Overdue", "status": ["!=", "Closed"]},
                fields=["name", "risk_title", "risk_owner", "risk_level", "next_review_date", "department"],
                limit_page_length=200,
            ),
        }

    # --- CAPA / Action patterns ---
    if "overdue" in text and ("action" in text or "capa" in text):
        return {
            "query": question,
            "results": frappe.get_all(
                "Action Item",
                filters={"status": "Overdue"},
                fields=["name", "action_title", "priority", "completion_date", "escalated_to"],
                limit_page_length=200,
            ),
        }

    if "open" in text and "capa" in text:
        return {
            "query": question,
            "results": frappe.get_all(
                "IMS CAPA",
                filters={"status": ["in", ["Open", "In Progress", "Overdue"]]},
                fields=["name", "capa_title", "capa_type", "assigned_to", "due_date", "status", "priority"],
                limit_page_length=200,
            ),
        }

    # --- Compliance patterns ---
    if "non-compliant" in text or "non compliant" in text:
        return {
            "query": question,
            "results": frappe.get_all(
                "IMS Compliance Register",
                filters={"compliance_status": ["in", ["Non-Compliant", "Partially Compliant"]]},
                fields=["name", "obligation_title", "standard_framework", "control_owner", "next_assessment_date"],
                limit_page_length=200,
            ),
        }

    if "compliance" in text and ("overdue" in text or "assessment" in text):
        return {
            "query": question,
            "results": frappe.get_all(
                "IMS Compliance Register",
                filters={
                    "compliance_status": ["!=", "Compliant"],
                    "next_assessment_date": ["<", frappe.utils.nowdate()],
                },
                fields=["name", "obligation_title", "standard_framework", "control_owner", "next_assessment_date", "compliance_status"],
                limit_page_length=200,
            ),
        }

    # --- Audit patterns ---
    if "open" in text and "finding" in text:
        if frappe.db.table_exists("IMS Audit Finding"):
            return {
                "query": question,
                "results": frappe.get_all(
                    "IMS Audit Finding",
                    filters={"status": ["not in", ["Closed", "Accepted Risk"]]},
                    fields=["name", "finding_title", "audit_engagement", "finding_type", "severity", "status", "target_closure_date"],
                    limit_page_length=200,
                ),
            }

    if "critical" in text and "finding" in text:
        if frappe.db.table_exists("IMS Audit Finding"):
            return {
                "query": question,
                "results": frappe.get_all(
                    "IMS Audit Finding",
                    filters={
                        "severity": "Critical",
                        "status": ["not in", ["Closed", "Accepted Risk"]],
                    },
                    fields=["name", "finding_title", "audit_engagement", "finding_owner", "status", "target_closure_date"],
                    limit_page_length=200,
                ),
            }

    if ("audit" in text and "plan" in text) or "audit plan" in text:
        return {
            "query": question,
            "results": frappe.get_all(
                "IMS Audit Plan",
                filters={"status": ["in", ["Approved", "In Progress"]]},
                fields=["name", "plan_title", "plan_year", "department", "status", "schedule_start", "schedule_end"],
                limit_page_length=200,
            ),
        }

    # --- KRI patterns ---
    if "kri" in text and "red" in text:
        return {
            "query": question,
            "results": frappe.get_all(
                "IMS KRI Definition",
                filters={"status": "Active", "alert_level": "Red"},
                fields=["name", "kri_name", "alert_level", "current_value", "threshold_red"],
                limit_page_length=200,
            ),
        }

    return {
        "query": question,
        "message": _(
            "Supported NLQ patterns: high-impact pending risks, overdue risks, overdue CAPA/actions, "
            "open CAPA, non-compliant obligations, overdue compliance assessments, "
            "open/critical audit findings, active audit plans, red KRIs."
        ),
    }


@frappe.whitelist()
def get_department_maturity_trend(department=None, limit=12):
    filters = {}
    if department:
        filters["department"] = department

    rows = frappe.get_all(
        "IMS Risk Maturity Snapshot",
        filters=filters,
        fields=["name", "snapshot_date", "department", "maturity_score", "maturity_band"],
        order_by="snapshot_date desc",
        limit_page_length=max(1, min(int(limit), 120)),
    )
    return list(reversed(rows))


@frappe.whitelist()
def get_risk_heatmap_data(department=None):
    """
    Return risk data structured for a 5x5 risk heatmap.
    Each cell (likelihood x impact) contains the count and list of risks.
    """
    filters = {"status": ["!=", "Closed"]}
    if department:
        filters["department"] = department

    risks = frappe.get_all(
        "IMS Risk Register",
        filters=filters,
        fields=["name", "risk_title", "likelihood", "impact", "risk_level", "department", "risk_owner"],
        limit_page_length=2000,
    )

    # Build a 5x5 matrix (likelihood 1-5, impact 1-5)
    matrix = {}
    for l in range(1, 6):
        for i in range(1, 6):
            matrix[f"{l}_{i}"] = {"likelihood": l, "impact": i, "count": 0, "risks": []}

    for risk in risks:
        l = int(risk.get("likelihood") or 3)
        i = int(risk.get("impact") or 3)
        l = max(1, min(5, l))
        i = max(1, min(5, i))
        key = f"{l}_{i}"
        matrix[key]["count"] += 1
        matrix[key]["risks"].append(
            {
                "name": risk.name,
                "risk_title": risk.risk_title,
                "risk_level": risk.risk_level,
                "department": risk.department,
            }
        )

    # Flatten to list, ordered by likelihood asc, impact asc
    cells = sorted(matrix.values(), key=lambda c: (c["likelihood"], c["impact"]))

    return {
        "cells": cells,
        "total_risks": len(risks),
        "department": department,
    }


@frappe.whitelist()
def get_audit_findings_summary(audit_engagement=None):
    """
    Return a summary of audit findings, optionally filtered by engagement.
    Used for the ARC dashboard and board reports.
    """
    if not frappe.db.table_exists("IMS Audit Finding"):
        return {"message": _("IMS Audit Finding module not yet installed.")}

    filters = {}
    if audit_engagement:
        filters["audit_engagement"] = audit_engagement

    findings = frappe.get_all(
        "IMS Audit Finding",
        filters=filters,
        fields=["name", "finding_title", "finding_type", "severity", "status", "audit_engagement", "department"],
        limit_page_length=2000,
    )

    summary = {
        "total": len(findings),
        "by_severity": {},
        "by_type": {},
        "by_status": {},
        "open": 0,
        "closed": 0,
    }

    for f in findings:
        sev = f.severity or "Unknown"
        ftype = f.finding_type or "Unknown"
        st = f.status or "Unknown"

        summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1
        summary["by_type"][ftype] = summary["by_type"].get(ftype, 0) + 1
        summary["by_status"][st] = summary["by_status"].get(st, 0) + 1

        if st in ("Closed", "Accepted Risk"):
            summary["closed"] += 1
        else:
            summary["open"] += 1

    return summary


def _build_executive_summary(summary):
    findings_text = ""
    if summary.get("open_audit_findings") is not None:
        findings_text = (
            f" open audit findings: {summary['open_audit_findings']} "
            f"(critical: {summary.get('critical_audit_findings', 0)});"
        )

    return (
        f"Open risks: {summary['open_risks']}; "
        f"high/very-high risks: {summary['high_or_very_high_risks']}; "
        f"overdue reviews: {summary['overdue_risk_reviews']}; "
        f"non-compliant obligations: {summary['non_compliant_items']}; "
        f"red KRIs: {summary['kri_red_count']}; "
        f"open actions: {summary['open_action_items']};{findings_text}"
    )
