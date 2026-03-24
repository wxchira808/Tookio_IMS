# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from incident_management_system.utils.action_item_automation import enforce_action_item_escalation


class ActionItem(Document):
	def validate(self):
		enforce_action_item_escalation(self)
