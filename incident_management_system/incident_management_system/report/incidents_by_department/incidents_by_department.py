import frappe
from frappe.utils import getdate, today

def execute(filters=None):
    if not filters:
        filters = {}
    columns = [
        {"fieldname":"name","label":_("Incident"),"fieldtype":"Link","options":"Incident","width":140},
        {"fieldname":"title","label":_("Title"),"fieldtype":"Data","width":200},
        {"fieldname":"department","label":_("Department"),"fieldtype":"Data","width":140},
        {"fieldname":"severity","label":_("Severity"),"fieldtype":"Data","width":90},
        {"fieldname":"priority","label":_("Priority"),"fieldtype":"Data","width":90},
        {"fieldname":"status","label":_("Status"),"fieldtype":"Data","width":100},
        {"fieldname":"assigned_responder","label":_("Assigned To"),"fieldtype":"Link","options":"User","width":140},
        {"fieldname":"incident_date","label":_("Incident Date"),"fieldtype":"Datetime","width":160}
    ]

    conditions = []
    values = {}

    if filters.get('from_date'):
        conditions.append("DATE(incident.incident_date) >= %(from_date)s")
        values['from_date'] = filters.get('from_date')
    if filters.get('to_date'):
        conditions.append("DATE(incident.incident_date) <= %(to_date)s")
        values['to_date'] = filters.get('to_date')
    if filters.get('department'):
        conditions.append("incident.department = %(department)s")
        values['department'] = filters.get('department')

    where = (' WHERE ' + ' AND '.join(conditions)) if conditions else ''

    data = frappe.db.sql(f"""
        SELECT
            incident.name,
            incident.title1 as title,
            incident.department,
            incident.severity,
            incident.priority,
            incident.status,
            incident.assigned_responder,
            incident.incident_date
        FROM `tabIncident` incident
        {where}
        ORDER BY incident.department, incident.incident_date DESC
    """, values, as_dict=1)

    return columns, data
