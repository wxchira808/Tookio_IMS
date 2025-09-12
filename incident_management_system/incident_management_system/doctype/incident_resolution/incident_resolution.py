# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class IncidentResolution(Document):
    def validate(self):
        if not frappe.db.exists("Incident Investigation", {"incident": self.incident, "docstatus": 1}):
            frappe.throw("Cannot create Resolution without a submitted Investigation")

    def on_submit(self):
        # Update parent incident status when resolution is submitted
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            incident.status = "Resolved"
            incident.resolution_id = self.name
            incident.save()