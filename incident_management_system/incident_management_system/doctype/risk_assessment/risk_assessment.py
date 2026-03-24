# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RiskAssessment(Document):
	def validate(self):
		self.sync_from_risk_register()
		self.calculate_risk_scores()

	def sync_from_risk_register(self):
		if not self.ims_risk_register:
			return

		register_values = frappe.db.get_value(
			"IMS Risk Register",
			self.ims_risk_register,
			["risk_taxonomy", "risk_owner"],
			as_dict=True,
		)

		if not register_values:
			return

		self.risk_taxonomy = register_values.risk_taxonomy
		if register_values.risk_owner and not self.risk_owner:
			self.risk_owner = register_values.risk_owner

		if self.risk_taxonomy and not self.risk_category:
			domain = frappe.db.get_value("Risk Taxonomy", self.risk_taxonomy, "risk_domain")
			if domain in {"Strategic", "Operational", "Financial", "Compliance", "Reputational"}:
				self.risk_category = domain
			elif domain:
				self.risk_category = "Technical"

	def calculate_risk_scores(self):
		likelihood = parse_scale_value(self.likelihood)
		impact = parse_scale_value(self.impact_severity)

		if not likelihood or not impact:
			return

		score = likelihood * impact
		self.risk_score = score

		if score <= 4:
			self.risk_level = "Very Low"
		elif score <= 8:
			self.risk_level = "Low"
		elif score <= 12:
			self.risk_level = "Medium"
		elif score <= 18:
			self.risk_level = "High"
		else:
			self.risk_level = "Very High"


def parse_scale_value(raw_value):
	if raw_value is None:
		return None

	if isinstance(raw_value, int):
		return raw_value

	value = str(raw_value).strip()
	if not value:
		return None

	first_token = value.split(" ", 1)[0]
	if first_token.isdigit():
		return int(first_token)

	return None
