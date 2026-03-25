// Copyright (c) 2026, Tookio and contributors
// For license information, please see license.txt

frappe.query_reports["Audit Coverage"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.year_start(),
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
            "fieldname": "department",
            "label": __("Department"),
            "fieldtype": "Link",
            "options": "Department",
            "reqd": 0
        },
        {
            "fieldname": "status",
            "label": __("Engagement Status"),
            "fieldtype": "Select",
            "options": "\nPlanned\nIn Progress\nReview\nClosed\nCancelled",
            "reqd": 0
        }
    ]
};
