import frappe
from frappe import _
from frappe.utils import getdate, today, add_days

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
            "label": _("Action Item ID"),
            "fieldtype": "Link",
            "options": "Action Item",
            "width": 140
        },
        {
            "fieldname": "title",
            "label": _("Title"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "related_incident",
            "label": _("Related Incident"),
            "fieldtype": "Link",
            "options": "Incident",
            "width": 140
        },
        {
            "fieldname": "assigned_to",
            "label": _("Assigned To"),
            "fieldtype": "Link",
            "options": "User",
            "width": 150
        },
        {
            "fieldname": "priority",
            "label": _("Priority"),
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
            "fieldname": "due_date",
            "label": _("Due Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "completion_date",
            "label": _("Completion Date"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "days_overdue",
            "label": _("Days Overdue"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "progress_percentage",
            "label": _("Progress %"),
            "fieldtype": "Percent",
            "width": 100
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT 
            ai.name,
            ai.action_title AS title,
            ai.incident AS related_incident,
            ai.owner AS assigned_to,
            ai.priority,
            ai.status,
            ai.start_date AS due_date,
            ai.completion_date,
            ai.progress_percentage,
            ai.creation
        FROM `tabAction Item` ai
        WHERE ai.docstatus = 0 {conditions}
        ORDER BY 
            CASE ai.priority 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                WHEN 'Medium' THEN 3 
                WHEN 'Low' THEN 4 
                ELSE 5 
            END,
            ai.start_date ASC
    """, filters, as_dict=1)
    
    # Calculate days overdue
    for row in data:
        if row.due_date and row.status != 'Completed':
            due_date = getdate(row.due_date)
            current_date = getdate(today())
            if current_date > due_date:
                row.days_overdue = (current_date - due_date).days
            else:
                row.days_overdue = 0
        else:
            row.days_overdue = 0
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND DATE(ai.creation) >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND DATE(ai.creation) <= %(to_date)s"
    
    if filters.get("status"):
        conditions += " AND ai.status = %(status)s"
    
    if filters.get("priority"):
        conditions += " AND ai.priority = %(priority)s"
    
    if filters.get("assigned_to"):
        conditions += " AND ai.owner = %(assigned_to)s"
    
    if filters.get("related_incident"):
        conditions += " AND ai.incident = %(related_incident)s"
    
    if filters.get("overdue_only"):
        conditions += " AND ai.start_date < CURDATE() AND ai.status != 'Completed'"
    
    return conditions
