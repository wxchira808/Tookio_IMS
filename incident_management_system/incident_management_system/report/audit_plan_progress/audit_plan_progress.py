# pyright: reportMissingImports=false

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def get_columns():
    return [
        {
            "fieldname": "name",
            "label": _("Audit Plan"),
            "fieldtype": "Link",
            "options": "IMS Audit Plan",
            "width": 160,
        },
        {
            "fieldname": "plan_title",
            "label": _("Plan Title"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "plan_year",
            "label": _("Year"),
            "fieldtype": "Int",
            "width": 70,
        },
        {
            "fieldname": "plan_type",
            "label": _("Type"),
            "fieldtype": "Data",
            "width": 90,
        },
        {
            "fieldname": "department",
            "label": _("Department"),
            "fieldtype": "Link",
            "options": "Department",
            "width": 160,
        },
        {
            "fieldname": "status",
            "label": _("Plan Status"),
            "fieldtype": "Data",
            "width": 110,
        },
        {
            "fieldname": "total_engagements",
            "label": _("Total Engagements"),
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "fieldname": "completed_engagements",
            "label": _("Completed"),
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "fieldname": "in_progress_engagements",
            "label": _("In Progress"),
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "fieldname": "planned_engagements",
            "label": _("Planned"),
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "fieldname": "completion_pct",
            "label": _("Completion (%)"),
            "fieldtype": "Percent",
            "width": 120,
        },
        {
            "fieldname": "budget_amount",
            "label": _("Budget (KES)"),
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "fieldname": "schedule_start",
            "label": _("Schedule Start"),
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "fieldname": "schedule_end",
            "label": _("Schedule End"),
            "fieldtype": "Date",
            "width": 110,
        },
    ]


def get_data(filters):
    conditions = _build_conditions(filters)

    plans = frappe.db.sql(
        f"""
        SELECT
            ap.name,
            ap.plan_title,
            ap.plan_year,
            ap.plan_type,
            ap.department,
            ap.status,
            ap.budget_amount,
            ap.schedule_start,
            ap.schedule_end
        FROM `tabIMS Audit Plan` ap
        WHERE ap.docstatus = 0 {conditions}
        ORDER BY ap.plan_year DESC, ap.schedule_start ASC
        """,
        filters,
        as_dict=1,
    )

    for plan in plans:
        engagement_counts = frappe.db.sql(
            """
            SELECT
                COUNT(name) AS total,
                SUM(CASE WHEN status IN ('Closed', 'Review') THEN 1 ELSE 0 END)  AS completed,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN status = 'Planned' THEN 1 ELSE 0 END)     AS planned
            FROM `tabIMS Audit Engagement`
            WHERE audit_plan = %s AND docstatus = 0
            """,
            plan.name,
            as_dict=1,
        )

        counts = engagement_counts[0] if engagement_counts else {}
        plan.total_engagements = counts.get("total") or 0
        plan.completed_engagements = counts.get("completed") or 0
        plan.in_progress_engagements = counts.get("in_progress") or 0
        plan.planned_engagements = counts.get("planned") or 0

        total = plan.total_engagements
        completed = plan.completed_engagements
        plan.completion_pct = round((completed / total) * 100, 1) if total else 0.0

    return plans


def _build_conditions(filters):
    conditions = ""
    if filters.get("plan_year"):
        conditions += " AND ap.plan_year = %(plan_year)s"
    if filters.get("plan_type"):
        conditions += " AND ap.plan_type = %(plan_type)s"
    if filters.get("department"):
        conditions += " AND ap.department = %(department)s"
    if filters.get("status"):
        conditions += " AND ap.status = %(status)s"
    return conditions


def get_chart(data):
    if not data:
        return None

    labels = [row.get("plan_title") or row.get("name") for row in data]
    completed = [row.get("completed_engagements", 0) for row in data]
    in_progress = [row.get("in_progress_engagements", 0) for row in data]
    planned = [row.get("planned_engagements", 0) for row in data]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("Completed"), "values": completed},
                {"name": _("In Progress"), "values": in_progress},
                {"name": _("Planned"), "values": planned},
            ],
        },
        "type": "bar",
        "barOptions": {"stacked": True},
        "colors": ["#2ecc71", "#f39c12", "#3498db"],
    }
