# pyright: reportMissingImports=false

import frappe


def create_lesson_from_resolution(doc, method=None):
    if not doc.get("lessons_learned"):
        return

    existing = frappe.db.exists(
        "IMS Lessons Learned Repository",
        {
            "incident_resolution": doc.name,
            "status": ["in", ["Draft", "Published"]],
        },
    )
    if existing:
        return

    lesson = frappe.get_doc(
        {
            "doctype": "IMS Lessons Learned Repository",
            "title": f"Lesson from {doc.name}",
            "source_type": "Incident Resolution",
            "incident_resolution": doc.name,
            "department": doc.get("department"),
            "owner_user": frappe.session.user,
            "summary": doc.get("lessons_learned"),
            "root_cause_theme": doc.get("root_cause_category"),
            "corrective_pattern": doc.get("corrective_actions"),
            "preventive_pattern": doc.get("preventive_actions"),
            "reusability_rating": "High" if doc.get("best_practices_documented") else "Medium",
            "status": "Published",
        }
    )
    lesson.insert(ignore_permissions=True)
