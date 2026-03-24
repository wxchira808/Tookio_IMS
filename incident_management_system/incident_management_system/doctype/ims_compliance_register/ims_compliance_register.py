# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IMSComplianceRegister(Document):
    def validate(self):
        self.validate_assessment_dates()
        self.validate_attestation_dates()

    def validate_assessment_dates(self):
        if self.last_assessment_date and self.next_assessment_date and self.last_assessment_date > self.next_assessment_date:
            frappe.throw("Next Assessment Date must be after Last Assessment Date")

    def validate_attestation_dates(self):
        if self.attestation_required and self.attested_on and self.next_assessment_date and self.attested_on > self.next_assessment_date:
            frappe.throw("Attested On cannot be after Next Assessment Date")
