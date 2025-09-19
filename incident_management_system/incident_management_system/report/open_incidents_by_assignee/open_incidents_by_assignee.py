import frappe


def execute(filters=None):
    if not filters:
        filters = {}
    columns = [
        {"fieldname":"assigned_responder","label":_("Assigned To"),"fieldtype":"Link","options":"User","width":160},
        {"fieldname":"open_count","label":_("Open Incidents"),"fieldtype":"Int","width":120}
    ]

    data = frappe.db.sql("""
        SELECT assigned_responder, COUNT(*) as open_count
        FROM `tabIncident`
        WHERE status NOT IN ('Resolved','Closed','Cancelled')
        GROUP BY assigned_responder
        ORDER BY open_count DESC
    """, as_dict=1)

    return columns, data
