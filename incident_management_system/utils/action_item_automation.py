# pyright: reportMissingImports=false

import frappe
from frappe.utils import nowdate, getdate


def enforce_action_item_escalation(doc, method=None):
    if doc.status in ["Completed", "Cancelled"]:
        return

    if not doc.completion_date:
        return

    due_date = getdate(doc.completion_date)
    if due_date >= getdate(nowdate()):
        return

    doc.status = "Overdue"

    if not doc.escalation_required:
        doc.escalation_required = 1

    if not doc.escalated_date:
        doc.escalated_date = nowdate()

    if not doc.escalated_reason:
        doc.escalated_reason = "Auto-escalated due to overdue action item."

    if not doc.escalated_level:
        doc.escalated_level = "Level 1"

    if not doc.escalated_to:
        doc.escalated_to = resolve_escalation_user(doc)


def sweep_overdue_action_items():
    overdue_actions = frappe.get_all(
        "Action Item",
        filters={
            "status": ["not in", ["Completed", "Cancelled", "Overdue"]],
            "completion_date": ["<", nowdate()],
        },
        fields=["name"],
        limit_page_length=1000,
    )

    for item in overdue_actions:
        action_doc = frappe.get_doc("Action Item", item.name)
        enforce_action_item_escalation(action_doc)
        action_doc.flags.ignore_permissions = True
        action_doc.save()


def resolve_escalation_user(action_item):
    if action_item.incident:
        incident = frappe.db.get_value(
            "Incident",
            action_item.incident,
            ["escalated_to", "assigned_responder", "reporter_manager"],
            as_dict=True,
        )
        if incident:
            for candidate in [incident.escalated_to, incident.assigned_responder, incident.reporter_manager]:
                if candidate:
                    return candidate

    managers = frappe.get_all(
        "Has Role",
        filters={"role": "Incident Manager", "parenttype": "User"},
        fields=["parent"],
        limit_page_length=1,
    )
    if managers:
        return managers[0].parent

    return None
