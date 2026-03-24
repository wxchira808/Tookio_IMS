# pyright: reportMissingImports=false

import frappe
from frappe.utils import getdate, nowdate


def run_daily_arc_automation():
    sweep_risk_review_overdue()
    sweep_compliance_assessment_overdue()
    sweep_kri_alerts()


def sweep_risk_review_overdue():
    overdue_risks = frappe.get_all(
        "IMS Risk Register",
        filters={
            "next_review_date": ["<", nowdate()],
            "status": ["!=", "Closed"],
        },
        fields=["name", "risk_title", "risk_owner", "mitigation_status"],
        limit_page_length=1000,
    )

    for risk in overdue_risks:
        if risk.mitigation_status != "Completed":
            frappe.db.set_value("IMS Risk Register", risk.name, "mitigation_status", "Overdue")

        message = f"Risk review overdue: {risk.risk_title or risk.name}"
        _create_todo_if_missing(
            owner=risk.risk_owner,
            description=message,
            reference_type="IMS Risk Register",
            reference_name=risk.name,
        )


def sweep_compliance_assessment_overdue():
    overdue_items = frappe.get_all(
        "IMS Compliance Register",
        filters={
            "next_assessment_date": ["<", nowdate()],
            "compliance_status": ["!=", "Compliant"],
        },
        fields=["name", "obligation_title", "control_owner"],
        limit_page_length=1000,
    )

    for item in overdue_items:
        message = f"Compliance assessment overdue: {item.obligation_title or item.name}"
        _create_todo_if_missing(
            owner=item.control_owner,
            description=message,
            reference_type="IMS Compliance Register",
            reference_name=item.name,
        )


def sweep_kri_alerts():
    active_kri_list = frappe.get_all(
        "IMS KRI Definition",
        filters={"status": "Active"},
        fields=["name", "owner", "kri_name", "alert_level", "last_updated_on"],
        limit_page_length=1000,
    )

    for row in active_kri_list:
        kri_doc = frappe.get_doc("IMS KRI Definition", row.name)
        kri_doc.update_alert_level()
        kri_doc.last_updated_on = frappe.utils.now_datetime()
        kri_doc.save(ignore_permissions=True)

        if kri_doc.alert_level == "Red":
            message = f"KRI in red zone: {kri_doc.kri_name or kri_doc.name}"
            _create_todo_if_missing(
                owner=kri_doc.owner,
                description=message,
                reference_type="IMS KRI Definition",
                reference_name=kri_doc.name,
            )


def _create_todo_if_missing(owner, description, reference_type, reference_name):
    allocated_to = owner or _get_fallback_owner()
    if not allocated_to:
        return

    existing = frappe.db.exists(
        "ToDo",
        {
            "allocated_to": allocated_to,
            "reference_type": reference_type,
            "reference_name": reference_name,
            "status": ["in", ["Open", "Pending"]],
            "description": ["like", f"%{description[:40]}%"],
        },
    )
    if existing:
        return

    todo = frappe.get_doc(
        {
            "doctype": "ToDo",
            "allocated_to": allocated_to,
            "description": description,
            "date": getdate(nowdate()),
            "reference_type": reference_type,
            "reference_name": reference_name,
            "status": "Open",
        }
    )
    todo.insert(ignore_permissions=True)


def _get_fallback_owner():
    managers = frappe.get_all(
        "Has Role",
        filters={"role": "Incident Manager", "parenttype": "User"},
        fields=["parent"],
        limit_page_length=1,
    )
    if managers:
        return managers[0].parent

    admins = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name"],
        limit_page_length=1,
    )
    return admins[0].name if admins else None
