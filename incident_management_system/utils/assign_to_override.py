import frappe
from frappe.share import add

def assign_to_overrride(doc, method):
    """Override assign_to.add to include custom sharing logic"""

    # Check if the ToDo is related to an Incident
    if doc.reference_type == "Incident" and doc.reference_name and doc.allocated_to:
        # Add enhanced permissions
        add(
            doctype=doc.reference_type,
            name=doc.reference_name,
            user=doc.allocated_to,
            read=1,
            write=1,
            submit=0,
            notify=1
        )