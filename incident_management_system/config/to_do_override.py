import frappe

def todo_after_insert(doc, method):
    if doc.reference_type == "Incident":
        frappe.share.add(
            doc.reference_type,
            doc.reference_name,
            doc.owner,
            read=1,
            write=1,
            notify=1
        )