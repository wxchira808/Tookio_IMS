# pyright: reportMissingImports=false

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class IMSAuditFinding(Document):
    def validate(self):
        self._auto_set_overdue()

    def _auto_set_overdue(self):
        if (
            self.status in ("Open", "In Progress")
            and self.target_closure_date
            and getdate(self.target_closure_date) < getdate(nowdate())
        ):
            self.status = "In Progress"

    def on_update(self):
        if self.capa_required and not self.linked_capa:
            self._create_capa()

    def _create_capa(self):
        """Auto-create an IMS CAPA record when a finding requires one."""
        if not self.finding_title:
            return

        existing = frappe.db.get_value(
            "IMS CAPA",
            {
                "source_doctype": "IMS Audit Finding",
                "source_reference": self.name,
            },
            "name",
        )
        if existing:
            frappe.db.set_value(self.doctype, self.name, "linked_capa", existing)
            return

        capa = frappe.get_doc(
            {
                "doctype": "IMS CAPA",
                "capa_title": f"Finding: {self.finding_title}",
                "capa_type": "Corrective Action",
                "source_doctype": "IMS Audit Finding",
                "source_reference": self.name,
                "description": self.finding_description or self.finding_title,
                "root_cause": self.root_cause or "",
                "root_cause_analysis_method": self.root_cause_analysis_method or "",
                "corrective_action_description": self.recommendation or "",
                "assigned_to": self.finding_owner or frappe.session.user,
                "department": self.department or "",
                "due_date": self.target_closure_date,
                "status": "Open",
                "priority": _severity_to_priority(self.severity),
            }
        )
        capa.insert(ignore_permissions=True)
        frappe.db.set_value(self.doctype, self.name, "linked_capa", capa.name)


def _severity_to_priority(severity):
    mapping = {
        "Critical": "Critical",
        "Major": "High",
        "Minor": "Medium",
        "Advisory": "Low",
    }
    return mapping.get(severity, "Medium")
