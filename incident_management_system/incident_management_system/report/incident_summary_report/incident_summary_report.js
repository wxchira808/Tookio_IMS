// Copyright (c) 2025, Tookio and contributors
// For license information, please see license.txt

frappe.query_reports["Incident Summary Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": "\nOpen\nIn Progress\nResolved\nClosed\nCancelled",
            "reqd": 0
        },
        {
            "fieldname": "severity",
            "label": __("Severity"),
            "fieldtype": "Select",
            "options": "\nLow\nMedium\nHigh\nCritical",
            "reqd": 0
        },
        {
            "fieldname": "incident_type",
            "label": __("Incident Type"),
            "fieldtype": "Link",
            "options": "Incident Type",
            "reqd": 0
        },
        {
            "fieldname": "assigned_responder",
            "label": __("Assigned Responder"),
            "fieldtype": "Link",
            "options": "User",
            "reqd": 0
        }
    ]
};
