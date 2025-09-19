import frappe
from frappe import _
from frappe.utils import getdate, add_days

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "name",
            "label": _("Incident ID"),
            "fieldtype": "Link",
            "options": "Incident",
            "width": 120
        },
        {
            "fieldname": "title",
            "label": _("Title"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "incident_type",
            "label": _("Type"),
            "fieldtype": "Link",
            "options": "Incident Type",
            "width": 120
        },
        {
            "fieldname": "severity",
            "label": _("Severity"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "assigned_responder",
            "label": _("Assigned To"),
            "fieldtype": "Link",
            "options": "User",
            "width": 150
        },
        {
            "fieldname": "created_date",
            "label": _("Created Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "sla_deadline",
            "label": _("SLA Deadline"),
            "fieldtype": "Datetime",
            "width": 150
        },
        {
            "fieldname": "closure_date",
            "label": _("Closure Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "days_to_resolve",
            "label": _("Days to Resolve"),
            "fieldtype": "Int",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT 
            i.name,
            i.title1 AS title,
            i.incident_type,
            i.severity,
            i.status,
            i.assigned_responder,
            DATE(i.creation) as created_date,
            i.sla_deadline,
            i.closure_date,
            CASE 
                WHEN i.closure_date IS NOT NULL 
                THEN DATEDIFF(i.closure_date, DATE(i.creation))
                ELSE NULL
            END as days_to_resolve
        FROM `tabIncident` i
        WHERE i.docstatus = 0 {conditions}
        ORDER BY i.creation DESC
    """, filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND DATE(i.creation) >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND DATE(i.creation) <= %(to_date)s"
    
    if filters.get("status"):
        conditions += " AND i.status = %(status)s"
    
    if filters.get("severity"):
        conditions += " AND i.severity = %(severity)s"
    
    if filters.get("incident_type"):
        conditions += " AND i.incident_type = %(incident_type)s"
    
    if filters.get("assigned_responder"):
        conditions += " AND i.assigned_responder = %(assigned_responder)s"
    
    return conditions
