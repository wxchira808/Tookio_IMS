import frappe
from frappe.utils import getdate, today


def execute(filters=None):
    if not filters:
        filters = {}

    columns = [
        {"fieldname":"period","label":_("Period"),"fieldtype":"Data","width":120},
        {"fieldname":"total_incidents","label":_("Total Incidents"),"fieldtype":"Int","width":120},
        {"fieldname":"resolved","label":_("Resolved"),"fieldtype":"Int","width":100},
        {"fieldname":"open","label":_("Open"),"fieldtype":"Int","width":100}
    ]

    # Build last 12 months aggregation
    data = frappe.db.sql("""
        SELECT DATE_FORMAT(incident.incident_date, '%%Y-%%m') as period,
            COUNT(*) as total_incidents,
            SUM(CASE WHEN incident.status IN ('Resolved','Closed') THEN 1 ELSE 0 END) as resolved,
            SUM(CASE WHEN incident.status NOT IN ('Resolved','Closed') THEN 1 ELSE 0 END) as open
        FROM `tabIncident` incident
        WHERE incident.incident_date IS NOT NULL
        GROUP BY DATE_FORMAT(incident.incident_date, '%%Y-%%m')
        ORDER BY DATE_FORMAT(incident.incident_date, '%%Y-%%m') DESC
        LIMIT 12
    """, as_dict=1)

    return columns, data
