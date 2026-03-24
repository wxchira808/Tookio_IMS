# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt
# pyright: reportMissingImports=false

import frappe
from frappe.model.document import Document


class IMSRiskMaturitySnapshot(Document):
    def validate(self):
        self.compute_maturity_band()

    def compute_maturity_band(self):
        score = float(self.maturity_score or 0)

        if score >= 80:
            self.maturity_band = "Optimized"
        elif score >= 60:
            self.maturity_band = "Managed"
        elif score >= 40:
            self.maturity_band = "Defined"
        elif score >= 20:
            self.maturity_band = "Developing"
        else:
            self.maturity_band = "Initial"
