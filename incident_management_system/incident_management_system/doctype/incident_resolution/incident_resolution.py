# Copyright (c) 2025, Brian Wachira and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate, add_days, flt

class IncidentResolution(Document):
    def validate(self):
        # Set resolution date if not provided
        if not self.resolution_date:
            self.resolution_date = getdate()
        
        # Set target completion date if not provided (default 7 days from resolution start)
        if not self.target_completion_date and self.resolution_date:
            self.target_completion_date = add_days(self.resolution_date, 7)
        
        # Validate actual completion date
        if self.actual_completion_date and self.resolution_date:
            if getdate(self.actual_completion_date) < getdate(self.resolution_date):
                frappe.throw("Actual completion date cannot be before resolution date")
        
        # Calculate and update progress
        self.update_resolution_progress()
        
        # Auto-update status based on progress and validation
        self.update_resolution_status()
        
        # Validate required fields based on status
        self.validate_required_fields()
        
    def before_save(self):
        # Update status based on approval - when approved, mark as Completed
        if self.docstatus == 0:  # Draft
            if self.resolution_approved and self.approved_by:
                self.resolution_status = "Completed"
                # Auto-set completion date when approved
                if not self.actual_completion_date:
                    self.actual_completion_date = getdate()
            elif self.peer_review_required and self.peer_review_comments:
                self.resolution_status = "Review"
                
    def before_submit(self):
        # Can only submit if status is "Completed"
        if self.resolution_status != "Completed":
            frappe.throw("Resolution must be completed before submission")
            
        if not self.resolution_approved or not self.approved_by:
            frappe.throw("Resolution must be approved before submission")
            
        # Set status to Completed on submission
        self.resolution_status = "Completed"
        
    def on_submit(self):
        # Update incident status
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            incident.status = "Resolved"
            incident.resolution_id = self.name
            incident.save(ignore_permissions=True)
            
    def validate_required_fields(self):
        """Validate required fields based on status - Progressive requirements"""
        
        # Planning phase requirements
        if self.resolution_status in ["Planning", "Implementation", "Testing", "Review", "Completed"]:
            if not self.resolution_type:
                frappe.throw("Resolution Type is required to move beyond Draft status")
            if not self.resolved_by:
                frappe.throw("Resolved By is required to move beyond Draft status")
                
        # Implementation requirements
        if self.resolution_status in ["Implementation", "Testing", "Review", "Completed"]:
            if not self.resolution_approach:
                frappe.throw("Resolution Approach is required for Implementation phase")
                
        # Testing phase requirements
        if self.resolution_status in ["Testing", "Review", "Completed"]:
            if not self.resolution_summary:
                frappe.throw("Resolution Summary is required for Testing phase")
                
        # Review phase requirements
        if self.resolution_status in ["Review", "Completed"]:
            if not self.corrective_actions:
                frappe.throw("Corrective Actions are required for Review phase")
                
        # Completion requirements
        if self.resolution_status == "Completed":
            if not self.resolution_approved:
                frappe.throw("Resolution must be approved to mark as Completed")
            if not self.approved_by:
                frappe.throw("Approver must be specified when resolution is approved")
                
    def update_resolution_progress(self):
        """Calculate resolution progress based on completed sections"""
        progress_weights = {
            'basic_info': 20,    # Basic information
            'solution': 30,      # Solution design and implementation
            'testing': 20,       # Testing and verification
            'documentation': 15, # Documentation
            'approval': 15       # Review and approval
        }
        
        total_progress = 0
        
        # Basic Information (20%)
        basic_info_score = 0
        if self.get("resolution_type"):
            basic_info_score += 0.25
        if self.get("resolution_approach"):
            basic_info_score += 0.25
        if self.get("resolved_by"):
            basic_info_score += 0.25
        if self.get("resolution_date"):
            basic_info_score += 0.25
        total_progress += progress_weights['basic_info'] * basic_info_score
            
        # Solution (30%)
        solution_score = 0
        if self.get("resolution_summary"):
            solution_score += 0.4
        if len(self.get("resolution_steps", [])) > 0:
            solution_score += 0.3
        if self.get("technical_details"):
            solution_score += 0.3
        total_progress += progress_weights['solution'] * solution_score
            
        # Testing (20%)
        testing_score = 0
        if self.get("testing_results"):
            testing_score += 0.5
        if len(self.get("validation_criteria", [])) > 0:
            testing_score += 0.5
        total_progress += progress_weights['testing'] * testing_score
            
        # Documentation (15%)
        documentation_score = 0
        if self.get("corrective_actions"):
            documentation_score += 0.5
        if self.get("preventive_actions"):
            documentation_score += 0.5
        total_progress += progress_weights['documentation'] * documentation_score
            
        # Approval (15%)
        approval_score = 0
        if self.peer_review_required:
            if self.peer_review_comments:
                approval_score += 0.5
            if self.resolution_approved:
                approval_score += 0.5
        else:
            if self.resolution_approved:
                approval_score = 1.0
        total_progress += progress_weights['approval'] * approval_score
                
        # Set the progress
        self.resolution_progress = min(round(total_progress), 100)
        
    def update_resolution_status(self):
        """Auto-update resolution status based on progress and key milestones"""
        if self.docstatus == 0:  # Draft state
            if self.resolution_status == "Draft":
                if self.resolution_type and self.resolved_by:
                    self.resolution_status = "Planning"
                    
            if self.resolution_status == "Planning":
                if self.resolution_summary and self.resolution_approach:
                    self.resolution_status = "Implementation"
                    
            if self.resolution_status == "Implementation":
                if self.testing_results or len(self.get("validation_criteria", [])) > 0:
                    self.resolution_status = "Testing"
                    
            if self.resolution_status == "Testing":
                if self.corrective_actions:
                    if self.peer_review_required:
                        if self.peer_review_comments:
                            self.resolution_status = "Review"
                    else:
                        self.resolution_status = "Completed" if self.resolution_approved else "Draft"
                        
            if self.resolution_status == "Review" and self.peer_review_comments:
                self.resolution_status = "Completed" if self.resolution_approved else "Draft"
                
        elif self.docstatus == 1:  # Submitted
            self.resolution_status = "Completed"
            
    def after_insert(self):
        # Update parent incident status to "Under Resolution" when resolution is created
        if self.incident:
            try:
                incident = frappe.get_doc("Incident", self.incident)
                # Only update if incident is not already in a "higher" state
                if incident.status not in ["Resolved", "Closed", "Cancelled"]:
                    incident.status = "Under Resolution"
                    incident.resolution_id = self.name
                    incident.flags.ignore_permissions = True
                    incident.save()
                    
                    frappe.msgprint(f"Resolution created successfully. Incident status updated to 'Under Resolution'.", 
                                  indicator='green', alert=True)
                    
            except Exception as e:
                frappe.log_error(f"Error updating incident status on resolution creation: {str(e)}")
                frappe.msgprint(f"Resolution created, but failed to update incident status: {str(e)}", 
                              indicator='orange', alert=True)
        
        # Create default validation criteria
        self.create_default_validation_criteria()
        
    def on_cancel(self):
        # Revert incident status when resolution is cancelled
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            incident.status = "Investigation Complete"
            incident.resolution_id = None
            incident.save(ignore_permissions=True)
        
    def create_default_validation_criteria(self):
        """Create default validation criteria"""
        if not len(self.get("validation_criteria", [])):
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
                }
            ]
            
            for criteria in default_criteria:
                self.append("validation_criteria", criteria)
                
    def get_resolution_duration(self):
        """Calculate resolution duration in days"""
        if self.resolution_date and self.actual_completion_date:
            return (getdate(self.actual_completion_date) - getdate(self.resolution_date)).days
        elif self.resolution_date:
            return (getdate() - getdate(self.resolution_date)).days
        return 0
    
    def get_overdue_status(self):
        """Check if resolution is overdue"""
        if self.target_completion_date and not self.actual_completion_date:
            return getdate() > getdate(self.target_completion_date)
        return False

@frappe.whitelist()
def create_action_item_from_resolution(resolution_name, action_title, action_description, priority="Medium"):
    """Create an action item linked to this resolution"""
    action_item = frappe.new_doc("Action Item")
    action_item.action_title = action_title
    action_item.action_description = action_description
    action_item.priority = priority
    action_item.action_type = "Resolution"
    
    # Link to the incident from resolution
    resolution = frappe.get_doc("Incident Resolution", resolution_name)
    if resolution.incident:
        action_item.incident = resolution.incident
    
    action_item.save()
    return action_item
