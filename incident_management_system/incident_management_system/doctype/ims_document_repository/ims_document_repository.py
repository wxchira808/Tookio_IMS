# pyright: reportMissingImports=false

import frappe
from frappe.model.document import Document
from frappe.utils import add_years, getdate, nowdate


class IMSDocumentRepository(Document):
    def before_save(self):
        self._set_author_if_missing()
        self._set_expiry_from_retention()
        self._auto_link_workpaper()

    def _set_author_if_missing(self):
        if not self.author:
            self.author = frappe.session.user

    def _set_expiry_from_retention(self):
        if self.retention_period_years and self.document_date and not self.expiry_date:
            self.expiry_date = add_years(getdate(self.document_date), self.retention_period_years)

    def _auto_link_workpaper(self):
        """If a workpaper is linked, propagate the audit engagement reference."""
        if self.linked_workpaper and not self.linked_audit_engagement:
            engagement = frappe.db.get_value(
                "IMS Workpaper", self.linked_workpaper, "audit_engagement"
            )
            if engagement:
                self.linked_audit_engagement = engagement
