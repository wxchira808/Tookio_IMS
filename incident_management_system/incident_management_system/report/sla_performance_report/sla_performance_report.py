import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, get_datetime

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
            "fieldname": "sla_deadline",
            "label": _("SLA Deadline"),
            "fieldtype": "Datetime",
            "width": 150
        },
        {
            "fieldname": "closure_date",
            "label": _("Closure Date"),
            "fieldtype": "Datetime",
            "width": 150
        },
        {
            "fieldname": "sla_status",
            "label": _("SLA Status"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "time_remaining",
            "label": _("Time Remaining (Hours)"),
            "fieldtype": "Float",
            "width": 150
        },
        {
            "fieldname": "overdue_hours",
            "label": _("Overdue Hours"),
            "fieldtype": "Float",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT 
            i.name,
            i.title1 AS title,
            i.severity,
            i.status,
            i.sla_deadline,
            i.closure_date,
            i.creation
        FROM `tabIncident` i
        WHERE i.docstatus = 0 {conditions}
        ORDER BY i.sla_deadline ASC
    """, filters, as_dict=1)
    
    # Calculate SLA metrics
    for row in data:
        if row.sla_deadline:
            deadline = get_datetime(row.sla_deadline)
            current_time = now_datetime()
            
            if row.closure_date:
                # Incident is closed, check if it was closed on time
                closure_time = get_datetime(row.closure_date)
                if closure_time <= deadline:
                    row.sla_status = "Met"
                    row.time_remaining = 0
                    row.overdue_hours = 0
                else:
                    row.sla_status = "Breached"
                    row.time_remaining = 0
                    row.overdue_hours = (closure_time - deadline).total_seconds() / 3600
            else:
                # Incident is still open
                if current_time <= deadline:
                    row.sla_status = "On Track"
                    row.time_remaining = (deadline - current_time).total_seconds() / 3600
                    row.overdue_hours = 0
                else:
                    row.sla_status = "Overdue"
                    row.time_remaining = 0
                    row.overdue_hours = (current_time - deadline).total_seconds() / 3600
        else:
            row.sla_status = "No SLA"
            row.time_remaining = 0
            row.overdue_hours = 0
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND DATE(i.creation) >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND DATE(i.creation) <= %(to_date)s"
    
    if filters.get("severity"):
        conditions += " AND i.severity = %(severity)s"
    
    if filters.get("sla_status"):
        if filters.get("sla_status") == "Overdue":
            conditions += " AND i.sla_deadline < NOW() AND i.status NOT IN ('Closed', 'Cancelled')"
        elif filters.get("sla_status") == "No SLA":
            conditions += " AND i.sla_deadline IS NULL"
    
    return conditions
