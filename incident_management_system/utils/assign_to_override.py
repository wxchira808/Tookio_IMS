import frappe
from frappe.share import add


def assign_to_override(doc, method):
    """Override assign_to.add to include custom sharing logic"""

    # Check if the ToDo is related to an Incident
    if doc.reference_type == "Incident" and doc.reference_name and doc.allocated_to:
        # Add enhanced permissions - giving write access for non-submittable document
        add(
            doctype=doc.reference_type,
            name=doc.reference_name,
            user=doc.allocated_to,
            read=1,
            write=1,
            notify=1
        )
        
        # Update incident status to "In Progress" when assigned
        try:
            incident = frappe.get_doc("Incident", doc.reference_name)
            status_before = incident.status
            
            # Change status to "In Progress" when assigned
            if incident.status == "Open":
                incident.status = "In Progress"
            
            incident.assigned_responder = doc.allocated_to
            
            # Add timeline entry
            assigned_user = frappe.get_value("User", doc.allocated_to, "full_name") or doc.allocated_to
            incident.append("incident_timeline", {
                "timestamp": frappe.utils.now_datetime(),
                "event_type": "Assignment",
                "event_description": f"Incident assigned to: {assigned_user}",
                "updated_by": frappe.session.user,
                "status_before": status_before,
                "status_after": incident.status
            })
            
            incident.flags.ignore_permissions = True
            incident.save()
        except Exception as e:
            frappe.log_error(f"Error updating incident status on assignment: {str(e)}")


# Backward-compatible alias for older hooks/custom scripts that used the typo.
assign_to_overrride = assign_to_override
