# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt
# pyright: reportMissingImports=false

import frappe
from frappe.model.document import Document


class IMSAuditEngagement(Document):
    def validate(self):
        self.validate_planned_dates()
        self.validate_actual_dates()

    def validate_planned_dates(self):
        if self.planned_start and self.planned_end and self.planned_start > self.planned_end:
            frappe.throw("Planned End must be after Planned Start")

    def validate_actual_dates(self):
        if self.actual_start and self.actual_end and self.actual_start > self.actual_end:
            frappe.throw("Actual End must be after Actual Start")
