# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, add_days, getdate


FREQUENCY_TO_MONTHS = {
    "Monthly": 1,
    "Quarterly": 3,
    "Semi-Annual": 6,
    "Annual": 12,
}


class IMSAuditPlan(Document):
    def validate(self):
        self.validate_schedule_dates()
        self.validate_recurring_frequency()

    def validate_schedule_dates(self):
        if self.schedule_start and self.schedule_end and self.schedule_start > self.schedule_end:
            frappe.throw(_("Schedule End must be after Schedule Start"))

    def validate_recurring_frequency(self):
        """For recurring plans (non-One-time), schedule_start must be set."""
        if (
            self.recurring_frequency
            and self.recurring_frequency != "One-time"
            and not self.schedule_start
        ):
            frappe.throw(
                _("Schedule Start is required for recurring audit plans (Frequency: {0})").format(
                    self.recurring_frequency
                )
            )

    def get_next_occurrence_date(self):
        """
        Calculate the next scheduled occurrence date based on recurring_frequency
        and the current schedule_end date.
        """
        if not self.recurring_frequency or self.recurring_frequency == "One-time":
            return None
        if not self.schedule_end:
            return None

        months = FREQUENCY_TO_MONTHS.get(self.recurring_frequency)
        if months:
            return add_months(getdate(self.schedule_end), months)
        return None

