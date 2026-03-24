# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IMSAuditPlan(Document):
    def validate(self):
        self.validate_schedule_dates()

    def validate_schedule_dates(self):
        if self.schedule_start and self.schedule_end and self.schedule_start > self.schedule_end:
            frappe.throw("Schedule End must be after Schedule Start")
