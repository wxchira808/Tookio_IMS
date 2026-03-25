// Copyright (c) 2026, Tookio and contributors
// For license information, please see license.txt

frappe.query_reports["Audit Plan Progress"] = {
    "filters": [
        {
            "fieldname": "plan_year",
            "label": __("Plan Year"),
            "fieldtype": "Int",
            "default": new Date().getFullYear(),
            "reqd": 0
        },
        {
            "fieldname": "plan_type",
            "label": __("Plan Type"),
            "fieldtype": "Select",
            "options": "\nAnnual\nAd-hoc",
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
            "label": __("Plan Status"),
            "fieldtype": "Select",
            "options": "\nDraft\nSubmitted\nApproved\nIn Progress\nCompleted",
            "reqd": 0
        }
    ]
};
