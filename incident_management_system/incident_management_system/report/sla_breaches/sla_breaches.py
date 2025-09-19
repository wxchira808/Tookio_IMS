import frappe
from frappe.utils import getdate, today

def execute(filters=None):
    if not filters:
        filters = {}
    columns = [
        {"fieldname":"name","label":_("Incident"),"fieldtype":"Link","options":"Incident","width":140},
        {"fieldname":"title","label":_("Title"),"fieldtype":"Data","width":200},
        {"fieldname":"assigned_responder","label":_("Assigned To"),"fieldtype":"Link","options":"User","width":140},
        {"fieldname":"due_date","label":_("Due Date"),"fieldtype":"Datetime","width":140},
        {"fieldname":"sla_breach_time","label":_("SLA Breach Time"),"fieldtype":"Datetime","width":160},
        {"fieldname":"status","label":_("Status"),"fieldtype":"Data","width":100}
    ]

    data = frappe.db.sql("""
        SELECT name, title1 as title, assigned_responder, due_date, sla_breach_time, status
        FROM `tabIncident`
        WHERE sla_breach_time IS NOT NULL
        ORDER BY sla_breach_time DESC
    """, as_dict=1)

    return columns, data
