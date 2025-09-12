# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

#import frappe
#from frappe.model.document import Document


import frappe
from frappe.model.document import Document

class IncidentInvestigation(Document):
    def on_submit(self):
        # Update parent incident status when investigation is submitted
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            incident.status = "Investigation"
            incident.investigation_id = self.name
            incident.save()

    def validate(self):
        # Add any validation logic here
        pass