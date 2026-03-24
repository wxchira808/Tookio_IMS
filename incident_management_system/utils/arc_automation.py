# pyright: reportMissingImports=false

import frappe
from frappe.utils import getdate, nowdate


def run_daily_arc_automation():
    sweep_risk_review_overdue()
    sweep_compliance_assessment_overdue()
    sweep_kri_alerts()
    generate_daily_maturity_snapshots()


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


def generate_daily_maturity_snapshots():
    today = getdate(nowdate())
    departments = _get_departments_for_snapshot()
    if not departments:
        departments = [None]

    for department in departments:
        exists = frappe.db.exists(
            "IMS Risk Maturity Snapshot",
            {"snapshot_date": today, "department": department},
        )
        if exists:
            continue

        metrics = _collect_maturity_metrics(department)
        score = _calculate_maturity_score(metrics)

        snapshot = frappe.get_doc(
            {
                "doctype": "IMS Risk Maturity Snapshot",
                "snapshot_date": today,
                "department": department,
                "open_risks": metrics["open_risks"],
                "overdue_reviews": metrics["overdue_reviews"],
                "open_action_items": metrics["open_actions"],
                "overdue_action_items": metrics["overdue_actions"],
                "kri_red_count": metrics["kri_red"],
                "maturity_score": score,
                "notes": "Auto-generated daily ARC maturity snapshot.",
            }
        )
        snapshot.insert(ignore_permissions=True)


def _get_departments_for_snapshot():
    rows = frappe.get_all(
        "IMS Risk Register",
        filters={"status": ["!=", "Closed"], "department": ["is", "set"]},
        fields=["department"],
        distinct=True,
        limit_page_length=2000,
    )
    return [row.department for row in rows if row.department]


def _collect_maturity_metrics(department=None):
    risk_filters = {"status": ["!=", "Closed"]}
    action_filters = {"status": ["in", ["Open", "In Progress", "Overdue"]]}
    kri_filters = {"status": "Active", "alert_level": "Red"}

    if department:
        risk_filters["department"] = department
        action_filters["department"] = department

    return {
        "open_risks": frappe.db.count("IMS Risk Register", risk_filters),
        "overdue_reviews": frappe.db.count(
            "IMS Risk Register", {**risk_filters, "mitigation_status": "Overdue"}
        ),
        "open_actions": frappe.db.count("Action Item", action_filters),
        "overdue_actions": frappe.db.count("Action Item", {**action_filters, "status": "Overdue"}),
        "kri_red": frappe.db.count("IMS KRI Definition", kri_filters),
    }


def _calculate_maturity_score(metrics):
    open_risks = metrics["open_risks"]
    overdue_reviews = metrics["overdue_reviews"]
    open_actions = metrics["open_actions"]
    overdue_actions = metrics["overdue_actions"]
    kri_red = metrics["kri_red"]

    base = 100.0
    deductions = (
        min(overdue_reviews * 8, 40)
        + min(overdue_actions * 5, 30)
        + min(kri_red * 4, 20)
        + (5 if open_risks > 0 and open_actions == 0 else 0)
    )

    return max(0, round(base - deductions, 2))


# ---------------------------------------------------------------------------
# CAPA Automation
# ---------------------------------------------------------------------------

def sweep_capa_overdue_task():
    """
    Scheduled daily task: mark IMS CAPA records as Overdue when past due date
    and create ToDo notifications for assigned owners.
    """
    from frappe.utils import getdate, nowdate

    open_capas = frappe.get_all(
        "IMS CAPA",
        filters={
            "status": ["in", ["Open", "In Progress"]],
            "due_date": ["<", nowdate()],
        },
        fields=["name", "capa_title", "assigned_to", "due_date", "priority"],
        limit_page_length=1000,
    )

    for capa in open_capas:
        frappe.db.set_value("IMS CAPA", capa.name, "status", "Overdue")
        message = f"CAPA overdue: {capa.capa_title or capa.name} (due {capa.due_date})"
        _create_todo_if_missing(
            owner=capa.assigned_to,
            description=message,
            reference_type="IMS CAPA",
            reference_name=capa.name,
        )

    frappe.db.commit()


def on_risk_register_update(doc, method=None):
    """
    doc_event hook: when a risk is saved, auto-sync CAPA status
    if capa_status is Overdue but CAPA due date is still in future.
    """
    if not doc.capa_due_date:
        return
    from frappe.utils import getdate, nowdate

    if (
        doc.capa_status in ("Open", "In Progress")
        and getdate(doc.capa_due_date) < getdate(nowdate())
    ):
        doc.capa_status = "Overdue"


def on_capa_validate(doc, method=None):
    """
    doc_event hook: auto-set CAPA status to Overdue when past due date.
    """
    if not doc.due_date:
        return
    from frappe.utils import getdate, nowdate

    if (
        doc.status in ("Open", "In Progress")
        and getdate(doc.due_date) < getdate(nowdate())
    ):
        doc.status = "Overdue"
