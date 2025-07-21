# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class IncidentResolution(Document):
    def on_submit(self):
        if self.incident:
            frappe.db.set_value("Incident", self.incident, "status", "Resolved")
            frappe.msgprint(f"Incident {self.incident} marked as Resolved.")
