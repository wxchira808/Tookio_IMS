// Copyright (c) 2025, Tookio and contributors
// For license information, please see license.txt

frappe.query_reports["Action Items Tracking"] = {
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
            "options": "\nOpen\nIn Progress\nCompleted\nCancelled",
            "reqd": 0
        },
        {
            "fieldname": "priority",
            "label": __("Priority"),
            "fieldtype": "Select",
            "options": "\nLow\nMedium\nHigh\nCritical",
            "reqd": 0
        },
        {
            "fieldname": "assigned_to",
            "label": __("Assigned To"),
            "fieldtype": "Link",
            "options": "User",
            "reqd": 0
        },
        {
            "fieldname": "related_incident",
            "label": __("Related Incident"),
            "fieldtype": "Link",
            "options": "Incident",
            "reqd": 0
        },
        {
            "fieldname": "overdue_only",
            "label": __("Show Overdue Only"),
            "fieldtype": "Check",
            "default": 0
        }
    ]
};
