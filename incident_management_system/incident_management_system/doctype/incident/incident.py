# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class Incident(Document):
    def validate(self):
        # ...existing code...
        if self.docstatus == 1 and not self.status:
            frappe.throw("Status is required for submitted incidents")

    def on_submit(self):
        """Set initial status when document is submitted"""
        if not self.status:
            self.status = "Open"
            self.db_set('status', self.status)

@frappe.whitelist()
def make_investigation(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.incident = source.name
        
    doclist = get_mapped_doc("Incident", source_name, {
        "Incident": {
            "doctype": "Incident Investigation",
            "field_map": {
                "name": "incident"
            }
        }
    }, target_doc, set_missing_values)
    
    return doclist

@frappe.whitelist()
def make_resolution(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.incident = source.name
        
    doclist = get_mapped_doc("Incident", source_name, {
        "Incident": {
            "doctype": "Incident Resolution",
            "field_map": {
                "name": "incident"
            }
        }
    }, target_doc, set_missing_values)
    
    return doclist


def get_status(self):
        """Override the default status display"""
        if self.docstatus == 0:
            return "Draft"
        if self.docstatus == 1:
            return "Open"
        elif self.docstatus == 2:
            return "Cancelled"
        else:
            # Use your custom status field instead of "Submitted"
            return self.status or "Submitted"
    
  