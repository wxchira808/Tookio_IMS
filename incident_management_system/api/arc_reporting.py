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
    }

    summary["executive_summary"] = _build_executive_summary(summary)
    return summary


@frappe.whitelist()
def nlq_arc_query(question=None):
    text = (question or "").strip().lower()
    if not text:
        return {"message": _("Please provide a question.")}

    if "high" in text and "risk" in text and "pending" in text:
        return {
            "query": question,
            "results": frappe.get_all(
                "IMS Risk Register",
                filters={
                    "risk_level": ["in", ["High", "Very High"]],
                    "mitigation_status": ["!", "Completed"],
                    "status": ["!=", "Closed"],
                },
                fields=["name", "risk_title", "risk_owner", "risk_level", "mitigation_status", "next_review_date"],
                limit_page_length=200,
            ),
        }

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

    return {
        "query": question,
        "message": _(
            "Supported NLQ patterns: high-impact pending risks, overdue CAPA/actions, non-compliant obligations."
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


def _build_executive_summary(summary):
    return (
        f"Open risks: {summary['open_risks']}; "
        f"high/very-high risks: {summary['high_or_very_high_risks']}; "
        f"overdue reviews: {summary['overdue_risk_reviews']}; "
        f"non-compliant obligations: {summary['non_compliant_items']}; "
        f"red KRIs: {summary['kri_red_count']}; "
        f"open actions: {summary['open_action_items']}."
    )
