# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IMSComplianceRegister(Document):
    def validate(self):
        self.validate_assessment_dates()
        self.validate_attestation_dates()
        self.calculate_assessment_score()

    def validate_assessment_dates(self):
        if self.last_assessment_date and self.next_assessment_date and self.last_assessment_date > self.next_assessment_date:
            frappe.throw("Next Assessment Date must be after Last Assessment Date")

    def validate_attestation_dates(self):
        if self.attestation_required and self.attested_on and self.next_assessment_date and self.attested_on > self.next_assessment_date:
            frappe.throw("Attested On cannot be after Next Assessment Date")

    def calculate_assessment_score(self):
        """Auto-calculate overall assessment score from self-assessment checklist items."""
        items = self.get("self_assessment_items") or []
        scoreable = [item for item in items if item.get("compliance_response") not in ("Not Applicable", None, "")]
        if not scoreable:
            self.overall_assessment_score = 0.0
            return
        total = sum(float(item.get("score") or 0) for item in scoreable)
        self.overall_assessment_score = round(total / len(scoreable), 2)
