# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate, add_days

class IncidentInvestigation(Document):
    def validate(self):
        # Set start date if not provided
        if not self.start_date:
            self.start_date = getdate()
        
        # Set target completion date if not provided (default 30 days from start)
        if not self.target_completion_date and self.start_date:
            self.target_completion_date = add_days(self.start_date, 30)
        
        # Validate completion date
        if self.actual_completion_date and self.start_date:
            if getdate(self.actual_completion_date) < getdate(self.start_date):
                frappe.throw("Actual completion date cannot be before start date")
    
    def before_save(self):
        # Auto-set completion date when status changes to completed
        if self.investigation_status == "Completed" and not self.actual_completion_date:
            self.actual_completion_date = getdate()
        
        # Clear completion date if status is not completed
        if self.investigation_status != "Completed" and self.actual_completion_date:
            self.actual_completion_date = None
    
    def on_submit(self):
        # Update parent incident status when investigation is submitted
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            # Only update status if incident is not already in a "higher" state
            if incident.status not in ["Resolved", "Closed", "Cancelled"]:
                # Set status based on investigation status
                if self.investigation_status == "Completed":
                    incident.status = "Investigation Complete"
                else:
                    incident.status = "Investigating"
                incident.investigation_id = self.name
                incident.save(ignore_permissions=True)
    
    def after_insert(self):
        # Create initial timeline entry
        self.add_timeline_entry("Investigation Started", "Investigation has been initiated")
    
    def add_timeline_entry(self, event_type, description, responsible_party=None):
        """Helper method to add timeline entries"""
        if not responsible_party:
            responsible_party = frappe.session.user
        
        timeline_entry = {
            "event_date": getdate(),
            "event_time": now_datetime().time(),
            "event_description": description,
            "event_type": event_type,
            "responsible_party": responsible_party
        }
        
        # Add to timeline table
        self.append("investigation_timeline", timeline_entry)
        
    def get_investigation_duration(self):
        """Calculate investigation duration in days"""
        if self.start_date and self.actual_completion_date:
            return (getdate(self.actual_completion_date) - getdate(self.start_date)).days
        elif self.start_date:
            return (getdate() - getdate(self.start_date)).days
        return 0
    
    def get_overdue_status(self):
        """Check if investigation is overdue"""
        if self.target_completion_date and not self.actual_completion_date:
            return getdate() > getdate(self.target_completion_date)
        return False

@frappe.whitelist()
def create_action_item_from_investigation(investigation_name, action_title, action_description, priority="Medium"):
    """Create an action item linked to this investigation"""
    action_item = frappe.new_doc("Action Item")
    action_item.action_title = action_title
    action_item.action_description = action_description
    action_item.priority = priority
    action_item.action_type = "Investigation"
    
    # Link to the incident from investigation
    investigation = frappe.get_doc("Incident Investigation", investigation_name)
    if investigation.incident:
        action_item.incident = investigation.incident
    
    action_item.save()
    return action_item