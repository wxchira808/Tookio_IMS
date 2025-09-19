# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import now_datetime, getdate, add_to_date, get_datetime

class Incident(Document):
    def validate(self):
        # Set status to Open when creating if not already set
        if not self.status:
            self.status = "Open"
        
        # Auto-set investigation priority based on severity
        if self.severity and not self.investigation_priority:
            severity_priority_map = {
                "Critical": "Critical",
                "High": "High", 
                "Medium": "Medium",
                "Low": "Low"
            }
            self.investigation_priority = severity_priority_map.get(self.severity, "Medium")
        
        # Auto-set due dates based on severity
        if self.severity and self.reported_date and not self.due_date:
            self.set_sla_dates()
        
        # Auto-set investigation requirement for critical incidents
        if self.severity in ["Critical", "High"] and not self.investigation_required:
            self.investigation_required = 1
    
    def before_save(self):
        # Add timeline entry for status changes
        if self.has_value_changed("status") and self.status:
            self.add_timeline_entry("Status Change", f"Status changed to: {self.status}")
        
        # Auto-set closure date when status changes to closed
        if self.status == "Closed" and not self.closure_date:
            self.closure_date = getdate()
        
        # Clear closure date if status is not closed
        if self.status != "Closed" and self.closure_date:
            self.closure_date = None
    
    def after_insert(self):
        """Add initial timeline entry after incident creation"""
        # Add initial timeline entry
        self.add_timeline_entry("Incident Created", "Incident has been created")
        
        # Create automatic notifications for critical incidents
        if self.severity == "Critical":
            self.send_critical_incident_alerts()
        
        # Auto-assign if department is specified
        if self.department:
            self.auto_assign_to_department()

    def on_update(self):
        """Handle updates to incident"""
        # Track significant changes
        if self.has_value_changed("status"):
            self.add_timeline_entry("Status Change", f"Status updated to: {self.status}")
        
        if self.has_value_changed("escalation_level"):
            self.add_timeline_entry("Escalation", f"Escalated to: {self.escalation_level}")
        
        if self.has_value_changed("assigned_responder"):
            self.handle_assignment_change()

    def handle_assignment_change(self):
        """Handle assignment changes"""
        if self.assigned_responder:
            # Temporarily commented out auto-status change
            # Set status to In Progress when assigned
            # if self.status == "Open":
            #     self.status = "In Progress"
            
            # Add timeline entry
            assigned_user = frappe.get_value("User", self.assigned_responder, "full_name") or self.assigned_responder
            self.add_timeline_entry("Assignment", f"Incident assigned to: {assigned_user}")
            
            # Share the document with the assigned user
            frappe.share.add(
                doctype="Incident",
                name=self.name,
                user=self.assigned_responder,
                read=1,
                write=1
            )

    def get_status(self):
        """Override the default status display"""
        if self.docstatus == 2:
            return "Cancelled"
        # For non-submittable documents, return the custom status
        return self.status if self.status else "Open"
    
    def set_sla_dates(self):
        """Set SLA dates based on severity"""
        if not self.reported_date:
            return
        
        # SLA hours based on severity
        sla_hours = {
            "Critical": 4,    # 4 hours
            "High": 24,       # 1 day
            "Medium": 72,     # 3 days  
            "Low": 168        # 1 week
        }
        
        hours = sla_hours.get(self.severity, 72)
        
        # Set due date
        self.due_date = add_to_date(self.reported_date, hours=hours)
        
        # Set SLA breach time (80% of SLA)
        breach_hours = int(hours * 0.8)
        self.sla_breach_time = add_to_date(self.reported_date, hours=breach_hours)
    
    def add_timeline_entry(self, event_type, description):
        """Add entry to incident timeline"""
        timeline_entry = {
            "timestamp": now_datetime(),
            "event_type": event_type,
            "event_description": description,
            "updated_by": frappe.session.user,
            "status_before": self.get_db_value("status") if self.name else "",
            "status_after": self.status
        }
        
        self.append("incident_timeline", timeline_entry)
    
    def send_critical_incident_alerts(self):
        """Send alerts for critical incidents"""
        # Get all incident managers
        managers = frappe.get_all("User", filters={
            "role_profile_name": ["like", "%Incident Manager%"],
            "enabled": 1
        }, fields=["email", "full_name"])
        
        for manager in managers:
            # Create email notification (simplified)
            frappe.sendmail(
                recipients=[manager.email],
                subject=f"CRITICAL INCIDENT: {self.title1}",
                message=f"A critical incident has been reported: {self.description[:200]}...",
                reference_doctype="Incident",
                reference_name=self.name
            )
    
    def auto_assign_to_department(self):
        """Auto-assign incident to department head"""
        if not self.department:
            return
        
        # Find department head or manager
        dept_doc = frappe.get_doc("Department", self.department)
        if hasattr(dept_doc, 'department_head') and dept_doc.department_head:
            frappe.share.add(
                doctype="Incident",
                name=self.name,
                user=dept_doc.department_head,
                read=1,
                write=1
            )
    
    def get_duration_since_reported(self):
        """Calculate duration since incident was reported"""
        if self.reported_date:
            return get_datetime() - get_datetime(self.reported_date)
        return None
    
    def is_overdue(self):
        """Check if incident is overdue"""
        if self.due_date and self.status not in ["Resolved", "Closed"]:
            return get_datetime() > get_datetime(self.due_date)
        return False
    
    def is_sla_breached(self):
        """Check if SLA is breached"""
        if self.sla_breach_time and self.status not in ["Resolved", "Closed"]:
            return get_datetime() > get_datetime(self.sla_breach_time)
        return False

@frappe.whitelist()
def make_investigation(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.incident = source.name
        
    doclist = get_mapped_doc("Incident", source_name, {
        "Incident": {
            "doctype": "Incident Investigation",
            "field_map": {
                "name": "incident"
            }
        }
    }, target_doc, set_missing_values)
    
    return doclist

@frappe.whitelist()
def make_resolution(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.incident = source.name
        
    doclist = get_mapped_doc("Incident", source_name, {
        "Incident": {
            "doctype": "Incident Resolution",
            "field_map": {
                "name": "incident"
            }
        }
    }, target_doc, set_missing_values)
    
    return doclist
    
  