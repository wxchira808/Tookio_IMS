# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt
# pyright: reportMissingImports=false

from frappe.model.document import Document


class IMSWorkpaper(Document):
    def before_save(self):
        if not self.version_number:
            self.version_number = 1
            return

        if self.has_value_changed("document_file"):
            self.version_number = int(self.version_number) + 1
