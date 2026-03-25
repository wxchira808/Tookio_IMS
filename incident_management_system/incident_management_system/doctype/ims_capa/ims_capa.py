# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt
# pyright: reportMissingImports=false

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class IMSCAPA(Document):
    def validate(self):
        self.auto_set_overdue_status()

    def auto_set_overdue_status(self):
        if (
            self.due_date
            and self.status in ("Open", "In Progress")
            and getdate(self.due_date) < getdate(nowdate())
        ):
            self.status = "Overdue"

    def on_submit(self):
        self._notify_assigned_to()

    def _notify_assigned_to(self):
        if not self.assigned_to:
            return
        frappe.sendmail(
            recipients=[self.assigned_to],
            subject=_("CAPA Assigned: {0}").format(self.capa_title),
            message=_(
                "A CAPA action has been assigned to you: <b>{0}</b>.<br>"
                "Due Date: {1}<br>Please log in to review and take action."
            ).format(self.capa_title, self.due_date or _("Not set")),
        )
