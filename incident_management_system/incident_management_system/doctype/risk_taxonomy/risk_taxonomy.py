# Copyright (c) 2026, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RiskTaxonomy(Document):
    def validate(self):
        self.set_taxonomy_level()
        self.validate_parent_reference()

    def set_taxonomy_level(self):
        if not self.parent_taxonomy:
            self.level = 1
            return

        parent_level = frappe.db.get_value("Risk Taxonomy", self.parent_taxonomy, "level") or 1
        self.level = int(parent_level) + 1

    def validate_parent_reference(self):
        if not self.parent_taxonomy:
            return

        if self.parent_taxonomy == self.name:
            frappe.throw("A taxonomy node cannot reference itself as parent.")

        current = self.parent_taxonomy
        visited = {self.name}

        while current:
            if current in visited:
                frappe.throw("Circular taxonomy hierarchy detected.")
            visited.add(current)
            current = frappe.db.get_value("Risk Taxonomy", current, "parent_taxonomy")
