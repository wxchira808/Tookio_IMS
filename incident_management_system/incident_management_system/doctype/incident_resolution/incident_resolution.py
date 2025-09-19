# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, date_diff, flt
from datetime import datetime, timedelta

class IncidentResolution(Document):
    def validate(self):
        """Validate the resolution before saving"""
        self.validate_incident_investigation()
        self.validate_required_fields()
        self.calculate_resolution_metrics()
        self.validate_stakeholder_signoffs()
        
    def before_save(self):
        """Before saving the resolution"""
        self.update_incident_details()
        self.set_default_values()
        self.calculate_resolution_time()
        
    def after_insert(self):
        """After creating the resolution"""
        self.create_default_validation_criteria()
        self.notify_stakeholders("resolution_created")
        
    def on_submit(self):
        """When resolution is submitted"""
        self.validate_closure_criteria()
        self.update_incident_status()
        self.create_action_items()
        self.update_knowledge_base()
        self.notify_stakeholders("resolution_submitted")
        
    def on_cancel(self):
        """When resolution is cancelled"""
        self.revert_incident_status()
        self.notify_stakeholders("resolution_cancelled")
        
    def validate_incident_investigation(self):
        """Ensure investigation is completed before resolution"""
        if not self.incident:
            frappe.throw("Incident is required")
            
        investigation = frappe.db.exists("Incident Investigation", {
            "incident": self.incident, 
            "docstatus": 1
        })
        
        if not investigation:
            frappe.throw("Cannot create Resolution without a submitted Investigation for this incident")
            
    def validate_required_fields(self):
        """Validate required fields based on resolution status"""
        if self.resolution_status in ["Verified", "Closed"]:
            if not self.primary_root_cause:
                frappe.throw("Primary Root Cause is required for verified/closed resolutions")
            if not self.resolution_summary:
                frappe.throw("Resolution Summary is required for verified/closed resolutions")
                
    def validate_stakeholder_signoffs(self):
        """Validate required sign-offs for closure"""
        if self.resolution_status == "Closed":
            required_signoffs = ["Technical Approval", "Business Approval"]
            
            for signoff in self.stakeholder_sign_offs:
                if signoff.sign_off_type in required_signoffs and not signoff.signed_off:
                    frappe.throw(f"{signoff.sign_off_type} is required for closure")
                    
    def validate_closure_criteria(self):
        """Validate all closure criteria are met"""
        if not self.closure_criteria_met:
            frappe.throw("All closure criteria must be met before submitting resolution")
            
        # Check validation criteria
        failed_criteria = []
        for criteria in self.validation_criteria:
            if criteria.status == "Failed":
                failed_criteria.append(criteria.criteria_title)
                
        if failed_criteria:
            frappe.throw(f"The following validation criteria failed: {', '.join(failed_criteria)}")
            
    def update_incident_details(self):
        """Fetch incident details for display"""
        if self.incident and not self.incident_title:
            incident = frappe.get_doc("Incident", self.incident)
            self.incident_title = incident.title
            self.incident_priority = incident.priority
            self.incident_severity = incident.severity
            self.incident_type = incident.incident_type
            
    def set_default_values(self):
        """Set default values"""
        if not self.resolved_by:
            self.resolved_by = frappe.session.user
            
        if not self.resolution_date:
            self.resolution_date = frappe.utils.today()
            
        if not self.resolution_time:
            self.resolution_time = frappe.utils.nowtime()
            
    def calculate_resolution_time(self):
        """Calculate total resolution time"""
        if self.incident and self.resolution_date:
            incident = frappe.get_doc("Incident", self.incident)
            if incident.incident_date:
                resolution_datetime = datetime.combine(
                    frappe.utils.getdate(self.resolution_date),
                    frappe.utils.get_time(self.resolution_time or "00:00:00")
                )
                incident_datetime = datetime.combine(
                    frappe.utils.getdate(incident.incident_date),
                    frappe.utils.get_time(incident.incident_time or "00:00:00")
                )
                
                time_diff = resolution_datetime - incident_datetime
                self.resolution_time_hours = flt(time_diff.total_seconds() / 3600, 2)
                
    def calculate_resolution_metrics(self):
        """Calculate resolution metrics and SLA compliance"""
        if self.incident and self.resolution_time_hours:
            incident = frappe.get_doc("Incident", self.incident)
            
            # Determine SLA based on priority
            sla_hours = {
                "Critical": 4,
                "High": 8,
                "Medium": 24,
                "Low": 72
            }
            
            target_hours = sla_hours.get(incident.priority, 24)
            self.sla_compliance = self.resolution_time_hours <= target_hours
            
    def update_incident_status(self):
        """Update parent incident status when resolution is submitted"""
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            incident.status = "Resolved"
            incident.resolution_id = self.name
            incident.resolution_date = self.resolution_date
            incident.flags.ignore_permissions = True
            incident.save()
            
    def revert_incident_status(self):
        """Revert incident status when resolution is cancelled"""
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            incident.status = "Under Investigation"
            incident.resolution_id = None
            incident.resolution_date = None
            incident.flags.ignore_permissions = True
            incident.save()
            
    def create_default_validation_criteria(self):
        """Create default validation criteria"""
        default_criteria = [
            {
                "criteria_title": "Solution Tested",
                "criteria_description": "Solution has been tested and verified to work",
                "validation_method": "Manual Testing"
            },
            {
                "criteria_title": "Root Cause Addressed",
                "criteria_description": "Primary root cause has been properly addressed",
                "validation_method": "Peer Review"
            },
            {
                "criteria_title": "No Negative Impact",
                "criteria_description": "Solution does not introduce new issues",
                "validation_method": "Monitoring"
            }
        ]
        
        for criteria in default_criteria:
            self.append("validation_criteria", criteria)
            
    def create_action_items(self):
        """Create action items from corrective and preventive actions"""
        all_actions = []
        
        # Collect all action items
        for action in self.corrective_actions:
            all_actions.append(action)
        for action in self.preventive_actions:
            all_actions.append(action)
        for action in self.follow_up_actions:
            all_actions.append(action)
            
        # Create ToDo items for each action
        for action in all_actions:
            if action.assigned_to and action.due_date:
                todo = frappe.get_doc({
                    "doctype": "ToDo",
                    "description": f"{action.action_title}: {action.action_description}",
                    "allocated_to": action.assigned_to,
                    "date": action.due_date,
                    "priority": action.priority or "Medium",
                    "reference_type": "Incident Resolution",
                    "reference_name": self.name,
                    "status": "Open"
                })
                todo.insert(ignore_permissions=True)
                
    def update_knowledge_base(self):
        """Update knowledge base with resolution information"""
        if self.knowledge_base_updated and self.lessons_learned:
            # Create knowledge article (this would integrate with your KB system)
            kb_article = {
                "title": f"Resolution: {self.incident_title}",
                "content": self.lessons_learned,
                "category": "Incident Resolutions",
                "tags": [self.incident_type, self.root_cause_category],
                "resolution_id": self.name
            }
            
            # This would be implemented based on your knowledge base system
            frappe.publish_realtime(
                "knowledge_base_update",
                kb_article,
                user=frappe.session.user
            )
            
    def notify_stakeholders(self, event_type):
        """Send notifications to stakeholders"""
        notification_map = {
            "resolution_created": "Resolution Created",
            "resolution_submitted": "Resolution Completed",
            "resolution_cancelled": "Resolution Cancelled"
        }
        
        if event_type in notification_map:
            # Get incident details for notification
            incident = frappe.get_doc("Incident", self.incident) if self.incident else None
            
            recipients = []
            if incident:
                recipients.extend([incident.reported_by, incident.assigned_to])
            
            # Add resolution team
            if self.resolved_by:
                recipients.append(self.resolved_by)
                
            # Send notifications
            for recipient in set(recipients):  # Remove duplicates
                if recipient:
                    notification = frappe.get_doc({
                        "doctype": "Notification Log",
                        "subject": f"{notification_map[event_type]}: {self.incident_title or 'Incident Resolution'}",
                        "for_user": recipient,
                        "type": "Alert",
                        "document_type": "Incident Resolution",
                        "document_name": self.name,
                        "from_user": frappe.session.user
                    })
                    notification.insert(ignore_permissions=True)
                    
    @frappe.whitelist()
    def mark_criteria_passed(self, criteria_name):
        """Mark validation criteria as passed"""
        for criteria in self.validation_criteria:
            if criteria.criteria_title == criteria_name:
                criteria.status = "Passed"
                criteria.validated_by = frappe.session.user
                criteria.validation_date = frappe.utils.today()
                break
        self.save()
        
    @frappe.whitelist()
    def mark_criteria_failed(self, criteria_name, reason):
        """Mark validation criteria as failed"""
        for criteria in self.validation_criteria:
            if criteria.criteria_title == criteria_name:
                criteria.status = "Failed"
                criteria.validated_by = frappe.session.user
                criteria.validation_date = frappe.utils.today()
                criteria.criteria_description += f"\nFailure Reason: {reason}"
                break
        self.save()
        
    @frappe.whitelist()
    def get_resolution_summary(self):
        """Get summary of resolution for dashboards"""
        return {
            "resolution_id": self.name,
            "incident_title": self.incident_title,
            "resolution_status": self.resolution_status,
            "resolution_time_hours": self.resolution_time_hours,
            "sla_compliance": self.sla_compliance,
            "stakeholder_satisfaction": self.stakeholder_satisfaction,
            "verification_status": self.verification_status,
            "closure_criteria_met": self.closure_criteria_met
        }