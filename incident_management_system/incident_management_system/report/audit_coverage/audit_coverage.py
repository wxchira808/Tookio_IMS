# pyright: reportMissingImports=false

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def get_columns():
    return [
        {
            "fieldname": "department",
            "label": _("Department"),
            "fieldtype": "Link",
            "options": "Department",
            "width": 180,
        },
        {
            "fieldname": "planned",
            "label": _("Planned"),
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "fieldname": "in_progress",
            "label": _("In Progress"),
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "fieldname": "closed",
            "label": _("Closed"),
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "fieldname": "cancelled",
            "label": _("Cancelled"),
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "fieldname": "total",
            "label": _("Total Engagements"),
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "fieldname": "open_findings",
            "label": _("Open Findings"),
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "fieldname": "critical_findings",
            "label": _("Critical Findings"),
            "fieldtype": "Int",
            "width": 130,
        },
        {
            "fieldname": "coverage_pct",
            "label": _("Closure Rate (%)"),
            "fieldtype": "Percent",
            "width": 130,
        },
    ]


def get_data(filters):
    conditions = _build_conditions(filters)

    rows = frappe.db.sql(
        f"""
        SELECT
            ae.auditee_department AS department,
            SUM(CASE WHEN ae.status = 'Planned' THEN 1 ELSE 0 END)       AS planned,
            SUM(CASE WHEN ae.status = 'In Progress' THEN 1 ELSE 0 END)   AS in_progress,
            SUM(CASE WHEN ae.status IN ('Closed', 'Review') THEN 1 ELSE 0 END) AS closed,
            SUM(CASE WHEN ae.status = 'Cancelled' THEN 1 ELSE 0 END)     AS cancelled,
            COUNT(ae.name)                                                AS total
        FROM `tabIMS Audit Engagement` ae
        WHERE ae.docstatus = 0 {conditions}
        GROUP BY ae.auditee_department
        ORDER BY ae.auditee_department
        """,
        filters,
        as_dict=1,
    )

    # Annotate with finding counts if IMS Audit Finding exists
    finding_table_exists = frappe.db.table_exists("IMS Audit Finding")
    for row in rows:
        row.open_findings = 0
        row.critical_findings = 0
        if finding_table_exists and row.department:
            row.open_findings = frappe.db.sql(
                """
                SELECT COUNT(af.name)
                FROM `tabIMS Audit Finding` af
                JOIN `tabIMS Audit Engagement` ae ON ae.name = af.audit_engagement
                WHERE ae.auditee_department = %s
                  AND af.status NOT IN ('Closed', 'Accepted Risk')
                  AND af.docstatus = 0
                """,
                row.department,
            )[0][0] or 0

            row.critical_findings = frappe.db.sql(
                """
                SELECT COUNT(af.name)
                FROM `tabIMS Audit Finding` af
                JOIN `tabIMS Audit Engagement` ae ON ae.name = af.audit_engagement
                WHERE ae.auditee_department = %s
                  AND af.severity = 'Critical'
                  AND af.status NOT IN ('Closed', 'Accepted Risk')
                  AND af.docstatus = 0
                """,
                row.department,
            )[0][0] or 0

        total = row.total or 0
        closed = row.closed or 0
        row.coverage_pct = round((closed / total) * 100, 1) if total else 0.0

    return rows


def _build_conditions(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += " AND ae.planned_start >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND ae.planned_start <= %(to_date)s"
    if filters.get("department"):
        conditions += " AND ae.auditee_department = %(department)s"
    if filters.get("status"):
        conditions += " AND ae.status = %(status)s"
    return conditions


def get_chart(data):
    if not data:
        return None

    labels = [row.get("department") or _("Unknown") for row in data]
    planned = [row.get("planned", 0) for row in data]
    closed = [row.get("closed", 0) for row in data]
    open_findings = [row.get("open_findings", 0) for row in data]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("Planned"), "values": planned},
                {"name": _("Closed"), "values": closed},
                {"name": _("Open Findings"), "values": open_findings},
            ],
        },
        "type": "bar",
        "colors": ["#5E64FF", "#2ecc71", "#e74c3c"],
    }
