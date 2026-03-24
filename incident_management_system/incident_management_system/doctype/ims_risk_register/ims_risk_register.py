# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt
# pyright: reportMissingImports=false

from frappe.model.document import Document


class IMSRiskRegister(Document):
    def validate(self):
        self.normalize_scores()
        self.calculate_risk_scores()

    def normalize_scores(self):
        self.likelihood = clamp_score(self.likelihood)
        self.impact = clamp_score(self.impact)
        self.velocity = clamp_score(self.velocity)
        self.control_effectiveness = clamp_score(self.control_effectiveness)

    def calculate_risk_scores(self):
        inherent_score = self.likelihood * self.impact * self.velocity
        control_modifier = (6 - self.control_effectiveness) / 5
        residual_score = inherent_score * control_modifier

        self.inherent_risk_score = round(inherent_score, 2)
        self.residual_risk_score = round(residual_score, 2)
        self.risk_level = get_risk_level(self.residual_risk_score)


def clamp_score(value):
    try:
        score = int(value or 1)
    except (TypeError, ValueError):
        score = 1
    return max(1, min(score, 5))


def get_risk_level(score):
    if score >= 80:
        return "Very High"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Medium"
    if score >= 10:
        return "Low"
    return "Very Low"
