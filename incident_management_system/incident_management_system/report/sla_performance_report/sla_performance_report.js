// Copyright (c) 2025, Tookio and contributors
// For license information, please see license.txt

frappe.query_reports["SLA Performance Report"] = {
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
            "fieldname": "severity",
            "label": __("Severity"),
            "fieldtype": "Select",
            "options": "\nLow\nMedium\nHigh\nCritical",
            "reqd": 0
        },
        {
            "fieldname": "sla_status",
            "label": __("SLA Status"),
            "fieldtype": "Select",
            "options": "\nOverdue\nNo SLA",
            "reqd": 0
        }
    ]
};
