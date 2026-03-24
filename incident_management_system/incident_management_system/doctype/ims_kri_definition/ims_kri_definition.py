# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt
# pyright: reportMissingImports=false

import frappe
from frappe.model.document import Document


class IMSKRIDefinition(Document):
    def validate(self):
        self.last_updated_on = frappe.utils.now_datetime()
        self.update_alert_level()

    def update_alert_level(self):
        if self.current_value is None:
            self.alert_level = "Unknown"
            return

        value = float(self.current_value)
        red = float(self.threshold_red or 0)
        yellow = float(self.threshold_yellow or 0)

        higher_is_worse = self.threshold_direction != "Lower Is Worse"

        if higher_is_worse:
            if red and value >= red:
                self.alert_level = "Red"
            elif yellow and value >= yellow:
                self.alert_level = "Amber"
            else:
                self.alert_level = "Green"
        else:
            if red and value <= red:
                self.alert_level = "Red"
            elif yellow and value <= yellow:
                self.alert_level = "Amber"
            else:
                self.alert_level = "Green"
