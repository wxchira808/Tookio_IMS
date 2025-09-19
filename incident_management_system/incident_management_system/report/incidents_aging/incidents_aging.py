import frappe
from frappe.utils import getdate, today


def execute(filters=None):
    if not filters:
        filters = {}

    columns = [
        {"fieldname":"name","label":_("Incident"),"fieldtype":"Link","options":"Incident","width":140},
        {"fieldname":"title","label":_("Title"),"fieldtype":"Data","width":200},
        {"fieldname":"assigned_responder","label":_("Assigned To"),"fieldtype":"Link","options":"User","width":140},
        {"fieldname":"status","label":_("Status"),"fieldtype":"Data","width":100},
        {"fieldname":"days_open","label":_("Days Open"),"fieldtype":"Int","width":100}
    ]

    data = frappe.db.sql("""
        SELECT i.name, i.title1 as title, i.assigned_responder, i.status,
            DATEDIFF(CURDATE(), DATE(i.incident_date)) as days_open
        FROM `tabIncident` i
        WHERE i.status NOT IN ('Resolved','Closed','Cancelled')
        ORDER BY days_open DESC
    """, as_dict=1)

    return columns, data
