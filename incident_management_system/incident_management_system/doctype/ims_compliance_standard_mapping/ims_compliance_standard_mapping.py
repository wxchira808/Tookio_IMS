# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt
# pyright: reportMissingImports=false

import frappe
from frappe.model.document import Document


class IMSComplianceStandardMapping(Document):
    def validate(self):
        self.validate_reference_pair()
        self.validate_review_dates()

    def validate_reference_pair(self):
        has_type = bool(self.applies_to_doctype)
        has_name = bool(self.applies_to_name)

        if has_type != has_name:
            frappe.throw("Both Applies To DocType and Applies To Name must be set together.")

    def validate_review_dates(self):
        if self.last_review_date and self.next_review_date and self.last_review_date > self.next_review_date:
            frappe.throw("Next Review Date must be after Last Review Date")
