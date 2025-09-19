import frappe

def todo_after_insert(doc, method):
    if doc.reference_type == "Incident":
        # Share the incident with the assigned user
        frappe.share.add(
            doc.reference_type,
            doc.reference_name,
            doc.allocated_to,
            read=1,
            write=1,
            notify=1
        )
        
        # Update incident status to "In Progress" when assigned
        incident = frappe.get_doc("Incident", doc.reference_name)
        # Temporarily commented out auto-status change
        # if incident.status == "Open":
        #     incident.status = "In Progress"
        incident.assigned_responder = doc.allocated_to
        
        # Add timeline entry
        assigned_user = frappe.get_value("User", doc.allocated_to, "full_name") or doc.allocated_to
        incident.append("incident_timeline", {
            "timestamp": frappe.utils.now_datetime(),
            "event_type": "Assignment",
            "event_description": f"Incident assigned to: {assigned_user}",
            "updated_by": frappe.session.user,
            "status_before": incident.status,  # Keep current status
            "status_after": incident.status   # No status change
        })
        
        incident.flags.ignore_permissions = True
        incident.save()