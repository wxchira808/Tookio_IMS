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
        
    def update_resolution_status(self):
        """Auto-update resolution status based on progress and key milestones"""
        if self.docstatus == 0:  # Draft state
            if self.resolution_status == "Draft":
                if self.resolved_by and self.resolution_date:
                    self.resolution_status = "Planning"
                    
            if self.resolution_status == "Planning":
                if self.resolution_approach and self.resolution_type:
                    self.resolution_status = "Root Cause Analysis"
                    
            if self.resolution_status == "Root Cause Analysis":
                if self.primary_root_cause and self.detailed_root_cause_analysis:
                    self.resolution_status = "Solution Design"
                    
            if self.resolution_status == "Solution Design":
                if self.temporary_solution or self.permanent_solution:
                    self.resolution_status = "Implementation"
                    
            if self.resolution_status == "Implementation":
                if len(self.get("resolution_steps", [])) > 0:
                    self.resolution_status = "Testing"
                    
            if self.resolution_status == "Testing":
                if self.testing_results and self.quality_assurance_notes:
                    self.resolution_status = "Verification"
                    
            if self.resolution_status == "Verification":
                if self.effectiveness_verification and self.verification_status == "Passed":
                    self.resolution_status = "Approval Pending"
                    
            if self.resolution_status == "Approval Pending":
                if self.management_approval and self.approved_by:
                    self.resolution_status = "Deployed"
                elif self.approval_comments and not self.management_approval:
                    self.resolution_status = "Rejected"
                    
            if self.resolution_status == "Deployed":
                if self.post_implementation_review:
                    self.resolution_status = "Monitoring"
                    
            if self.resolution_status == "Monitoring":
                if self.closure_criteria_met and self.final_resolution_report:
                    self.resolution_status = "Completed"
                    
        elif self.docstatus == 1:  # Submitted
            self.resolution_status = "Completed"
        
    def before_save(self):
        """Before saving the resolution"""
        self.update_incident_details()
        self.set_default_values()
        self.calculate_resolution_time()
        self.update_resolution_status()
        
    def after_insert(self):
        """After creating the resolution"""
        # Update parent incident status to "Resolved" when resolution is created
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            # Only update if incident is not already in a "higher" state
            if incident.status not in ["Resolved", "Closed", "Cancelled"]:
                incident.status = "Resolved"
                incident.resolution_id = self.name
                incident.flags.ignore_permissions = True
                incident.save()
        
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
        """Ensure investigation exists before resolution"""
        if not self.incident:
            frappe.throw("Incident is required")
            
        investigation = frappe.db.exists("Incident Investigation", {
            "incident": self.incident
        })
        
        if not investigation:
            frappe.throw("Cannot create Resolution without an Investigation for this incident")
            
    def validate_required_fields(self):
        """Validate required fields based on resolution status - Progressive validation"""
        status = self.resolution_status
        
        # Draft: No mandatory fields beyond basic info
        if status == "Draft":
            pass
            
        # Planning: Need resolver and basic planning
        if status in ["Planning", "Root Cause Analysis", "Solution Design", "Implementation", 
                     "Testing", "Verification", "Approval Pending", "Deployed", "Monitoring", "Completed"]:
            if not self.resolved_by:
                frappe.throw("Resolved By is required when resolution is in planning phase")
            if not self.resolution_date:
                frappe.throw("Resolution Date is required when resolution is in planning phase")
                
        # Root Cause Analysis: Need approach and analysis method
        if status in ["Root Cause Analysis", "Solution Design", "Implementation", "Testing", 
                     "Verification", "Approval Pending", "Deployed", "Monitoring", "Completed"]:
            if not self.resolution_approach:
                frappe.throw("Resolution Approach is required for root cause analysis phase")
            if not self.root_cause_analysis_method:
                frappe.throw("Root Cause Analysis Method is required for analysis phase")
                
        # Solution Design: Need root cause and analysis
        if status in ["Solution Design", "Implementation", "Testing", "Verification", 
                     "Approval Pending", "Deployed", "Monitoring", "Completed"]:
            if not self.primary_root_cause:
                frappe.throw("Primary Root Cause is required for solution design phase")
            if not self.detailed_root_cause_analysis:
                frappe.throw("Detailed Root Cause Analysis is required for solution design phase")
                
        # Implementation: Need solution details
        if status in ["Implementation", "Testing", "Verification", "Approval Pending", 
                     "Deployed", "Monitoring", "Completed"]:
            if not self.permanent_solution and not self.temporary_solution:
                frappe.throw("Either Temporary or Permanent Solution is required for implementation phase")
                
        # Testing: Need implementation steps
        if status in ["Testing", "Verification", "Approval Pending", "Deployed", "Monitoring", "Completed"]:
            if not len(self.get("resolution_steps", [])):
                frappe.throw("Resolution Steps are required for testing phase")
                
        # Verification: Need testing results
        if status in ["Verification", "Approval Pending", "Deployed", "Monitoring", "Completed"]:
            if not self.testing_results:
                frappe.throw("Testing Results are required for verification phase")
            if not self.effectiveness_verification:
                frappe.throw("Effectiveness Verification is required for verification phase")
                
        # Approval Pending: Need verification passed
        if status in ["Approval Pending", "Deployed", "Monitoring", "Completed"]:
            if self.verification_status != "Passed":
                frappe.throw("Verification must be Passed before seeking approval")
                
        # Deployed: Need management approval
        if status in ["Deployed", "Monitoring", "Completed"]:
            if not self.management_approval or not self.approved_by:
                frappe.throw("Management Approval is required before deployment")
                
        # Monitoring: Need post-implementation review
        if status in ["Monitoring", "Completed"]:
            if not self.post_implementation_review:
                frappe.throw("Post Implementation Review is required for monitoring phase")
                
        # Completed: Need final report and closure criteria
        if status == "Completed":
            if not self.final_resolution_report:
                frappe.throw("Final Resolution Report is required for completion")
            if not self.closure_criteria_met:
                frappe.throw("All Closure Criteria must be met for completion")
                
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
            self.incident_title = incident.title1
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
                # Create resolution datetime
                if self.resolution_time:
                    resolution_datetime = datetime.combine(
                        frappe.utils.getdate(self.resolution_date),
                        frappe.utils.get_time(self.resolution_time)
                    )
                else:
                    resolution_datetime = frappe.utils.get_datetime(self.resolution_date)
                
                # Get incident datetime (incident_date is already a datetime field)
                incident_datetime = frappe.utils.get_datetime(incident.incident_date)
                
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