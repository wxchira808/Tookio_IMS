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
        
        # Calculate and update progress
        self.update_investigation_progress()
        
        # Auto-update status based on progress and validation
        self.update_investigation_status()
        
        # Validate required fields based on status
        self.validate_required_fields()
        
    def before_save(self):
        # Update status based on approval - FIX: When approved, mark as Completed
        if self.docstatus == 0:  # Draft
            if self.investigation_approved and self.approved_by:
                # If approved, mark as completed
                self.investigation_status = "Completed"
                # Auto-set completion date when approved
                if not self.actual_completion_date:
                    self.actual_completion_date = getdate()
            elif self.peer_review_required and self.peer_review_comments:
                self.investigation_status = "Review"
                

            
    def before_submit(self):
        # Can only submit if status is "Approval Pending" or "Completed"
        if self.investigation_status not in ["Approval Pending", "Completed"]:
            frappe.throw("Investigation must be approved before submission")
            
        if not self.investigation_approved or not self.approved_by:
            frappe.throw("Investigation must be approved before submission")
            
        # Set status to Completed on submission
        self.investigation_status = "Completed"
        
    def on_submit(self):
        # Update incident status
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            incident.status = "Investigation Complete"
            incident.save(ignore_permissions=True)
            
    def validate_required_fields(self):
        """Validate required fields based on status - Progressive requirements"""
        
        # Planning phase requirements
        if self.investigation_status in ["Planning", "Evidence Collection", "Analysis", "Review", "Approval Pending", "Completed"]:
            if not self.investigation_type:
                frappe.throw("Investigation Type is required to move beyond Draft status")
            if not self.investigation_priority:
                frappe.throw("Investigation Priority is required to move beyond Draft status")
                
        # Evidence Collection requirements
        if self.investigation_status in ["Evidence Collection", "Analysis", "Review", "Approval Pending", "Completed"]:
            if not self.investigation_method:
                frappe.throw("Investigation Method is required for Evidence Collection phase")
                
        # Analysis phase requirements
        if self.investigation_status in ["Analysis", "Review", "Approval Pending", "Completed"]:
            if not self.root_cause_description:
                frappe.throw("Root Cause Description is required for Analysis phase")
            if not self.investigation_findings:
                frappe.throw("Investigation Findings are required for Analysis phase")
                
        # Review phase requirements
        if self.investigation_status in ["Review", "Approval Pending", "Completed"]:
            if not self.preventive_measures:
                frappe.throw("Preventive Measures are required for Review phase")
            if not self.corrective_actions_required:
                frappe.throw("Corrective Actions are required for Review phase")
                
        # Approval requirements
        if self.investigation_status in ["Approval Pending", "Completed"]:
            if self.peer_review_required and not self.peer_review_comments:
                frappe.throw("Peer Review Comments are required when peer review is enabled")
            
        # Completion requirements
        if self.investigation_status == "Completed":
            if not self.investigation_approved:
                frappe.throw("Investigation must be approved to mark as Completed")
            if not self.approved_by:
                frappe.throw("Approver must be specified when investigation is approved")
            
    def update_investigation_progress(self):
        """Calculate investigation progress based on completed sections"""
        progress_weights = {
            'basic_info': 15,  # Basic information
            'evidence': 25,    # Evidence collection
            'timeline': 10,    # Timeline documentation
            'analysis': 25,    # Analysis and findings
            'recommendations': 15,  # Recommendations
            'review': 10      # Review and approval
        }
        
        total_progress = 0
        
        # Basic Information (15%)
        basic_info_score = 0
        if self.get("investigation_type"):
            basic_info_score += 0.25
        if self.get("investigation_method"):
            basic_info_score += 0.25
        if self.get("investigation_scope"):
            basic_info_score += 0.25
        if self.get("investigation_priority"):
            basic_info_score += 0.25
        total_progress += progress_weights['basic_info'] * basic_info_score
            
        # Evidence Collection (25%)
        evidence_score = 0
        if len(self.get("evidence_collected", [])) > 0:
            evidence_score += 0.5
        if len(self.get("key_witnesses", [])) > 0:
            evidence_score += 0.5
        total_progress += progress_weights['evidence'] * evidence_score
            
        # Timeline (10%)
        if len(self.get("investigation_timeline", [])) > 0:
            total_progress += progress_weights['timeline']
            
        # Analysis and Findings (25%)
        analysis_score = 0
        if self.get("root_cause_category"):
            analysis_score += 0.2
        if self.get("root_cause_description"):
            analysis_score += 0.3
        if self.get("investigation_findings"):
            analysis_score += 0.3
        if len(self.get("contributing_factors", [])) > 0:
            analysis_score += 0.2
        total_progress += progress_weights['analysis'] * analysis_score
            
        # Recommendations and Actions (15%)
        recommendations_score = 0
        if getattr(self, "preventive_measures", None):
            recommendations_score += 0.5
        if getattr(self, "corrective_actions_required", None):
            recommendations_score += 0.5
        total_progress += progress_weights['recommendations'] * recommendations_score
            
        # Review and Approval (10%)
        review_score = 0
        if self.peer_review_required:
            if self.peer_review_comments:
                review_score += 0.5
            if self.investigation_approved:
                review_score += 0.5
        else:
            if self.investigation_approved:
                review_score = 1.0
        total_progress += progress_weights['review'] * review_score
                
        # Set the progress
        self.investigation_progress = min(round(total_progress), 100)
        
        # Debug logging
        frappe.logger().info(f"Investigation {self.name} progress calculation:")
        frappe.logger().info(f"Basic Info: {basic_info_score} -> {progress_weights['basic_info'] * basic_info_score}")
        frappe.logger().info(f"Evidence: {evidence_score} -> {progress_weights['evidence'] * evidence_score}")
        frappe.logger().info(f"Analysis: {analysis_score} -> {progress_weights['analysis'] * analysis_score}")
        frappe.logger().info(f"Total Progress: {self.investigation_progress}%")
        
    def update_investigation_status(self):
        """Auto-update investigation status based on progress and key milestones"""
        if self.docstatus == 0:  # Draft state
            if self.investigation_status == "Draft":
                if self.investigation_type and self.investigation_method:
                    self.investigation_status = "Planning"
                    
            if self.investigation_status == "Planning":
                if len(self.get("evidence_collected", [])) > 0 or len(self.get("key_witnesses", [])) > 0:
                    self.investigation_status = "Evidence Collection"
                    
            if self.investigation_status == "Evidence Collection":
                if self.root_cause_description and self.investigation_findings:
                    self.investigation_status = "Analysis"
                    
            if self.investigation_status == "Analysis":
                if self.preventive_measures and self.corrective_actions_required:
                    if self.peer_review_required:
                        if self.peer_review_comments:
                            self.investigation_status = "Review"
                    else:
                        self.investigation_status = "Approval Pending"
                        
            if self.investigation_status == "Review" and self.peer_review_comments:
                self.investigation_status = "Approval Pending"
                
            # Handle approval/rejection - FIX: Check approval status correctly
            if self.investigation_status == "Approval Pending":
                if self.investigation_approved and self.approved_by:
                    self.investigation_status = "Completed"
                elif self.approval_comments and not self.investigation_approved:
                    self.investigation_status = "Rejected"
                    
        elif self.docstatus == 1:  # Submitted
            self.investigation_status = "Completed"
            
        # Handle overdue cases
        if self.get_overdue_status() and self.investigation_status not in ["Completed", "Rejected"]:
            frappe.msgprint("Investigation is overdue. Please update target completion date or expedite the investigation.")
    
    def on_submit(self):
        # Update parent incident status when investigation is submitted
        if self.incident:
            incident = frappe.get_doc("Incident", self.incident)
            # Only update status if incident is not already in a "higher" state
            if incident.status not in ["Resolved", "Closed", "Cancelled"]:
                # Set status based on investigation status
                if self.investigation_status == "Completed":
                    incident.status = "Resolved"
                else:
                    incident.status = "Investigating"
                incident.investigation_id = self.name
                incident.save(ignore_permissions=True)
    
    def after_insert(self):
        # Create initial timeline entry
        self.add_timeline_entry("Investigation Started", "Investigation has been initiated")
        
        # Update parent incident status to "Investigating" when investigation is created
        if self.incident:
            try:
                incident = frappe.get_doc("Incident", self.incident)
                # Store the previous status for timeline entry
                previous_status = incident.status
                
                # Only update if incident is not already in a "higher" state
                if incident.status not in ["Resolved", "Closed", "Cancelled"]:
                    incident.status = "Investigating"
                    incident.investigation_id = self.name
                    incident.flags.ignore_permissions = True
                    incident.save()
                    
                    # Add timeline entry to the incident for the status change
                    if hasattr(incident, 'incident_timeline'):
                        incident.append('incident_timeline', {
                            'timestamp': now_datetime(),
                            'event_type': 'Investigation Started',
                            'event_description': f'Investigation {self.name} created. Status changed from {previous_status} to Investigating.',
                            'updated_by': frappe.session.user,
                            'status_before': previous_status,
                            'status_after': 'Investigating'
                        })
                        incident.save(ignore_permissions=True)
                    
                    frappe.db.commit()
                    
                    # Show success message
                    frappe.msgprint(f"Investigation created successfully. Incident status updated to 'Investigating'.", 
                                  indicator='green', alert=True)
                    
            except Exception as e:
                frappe.log_error(f"Error updating incident status on investigation creation: {str(e)}")
                frappe.msgprint(f"Investigation created, but failed to update incident status: {str(e)}", 
                              indicator='orange', alert=True)
                
    def on_update(self):
        # Refresh progress calculation on every update
        if self.docstatus == 0:  # Only for draft documents
            self.update_investigation_progress()
            
        # Update parent incident status based on investigation status changes
        self.update_parent_incident_status()
        
    def update_parent_incident_status(self):
        """Update parent incident status based on investigation status"""
        if self.incident and self.docstatus == 0:  # Only for draft documents
            try:
                incident = frappe.get_doc("Incident", self.incident)
                previous_status = incident.status
                new_status = None
                
                # Don't override higher level statuses
                if incident.status in ["Resolved", "Closed", "Cancelled"]:
                    return
                    
                # Map investigation status to incident status
                if self.investigation_status == "Completed":
                    new_status = "Resolved"
                elif self.investigation_status == "Rejected":
                    # If investigation is rejected, revert to previous status or "Open"
                    new_status = "Open"
                elif self.investigation_status in ["Draft", "Planning", "Evidence Collection", "Analysis", "Review", "Approval Pending"]:
                    new_status = "Investigating"
                
                # Update incident status if it should change
                if new_status and new_status != previous_status:
                    incident.status = new_status
                    incident.investigation_id = self.name
                    incident.save(ignore_permissions=True)
                    
                    # Add timeline entry for the status change
                    if hasattr(incident, 'incident_timeline'):
                        incident.append('incident_timeline', {
                            'timestamp': now_datetime(),
                            'event_type': 'Investigation Update',
                            'event_description': f'Investigation {self.name} status: {self.investigation_status}. Incident status updated to {new_status}.',
                            'updated_by': frappe.session.user,
                            'status_before': previous_status,
                            'status_after': new_status
                        })
                        incident.save(ignore_permissions=True)
                        
            except Exception as e:
                frappe.log_error(f"Error updating parent incident status: {str(e)}")
                # Don't show error to user as this is a background operation
            self.update_investigation_status()
            
        # Update incident with current investigation status
        if self.incident:
            try:
                incident = frappe.get_doc("Incident", self.incident)
                if self.investigation_status == "Completed" and incident.status == "Investigating":
                    incident.status = "Investigation Complete"
                    incident.flags.ignore_permissions = True
                    incident.save()
            except Exception as e:
                frappe.log_error(f"Error updating incident status: {str(e)}")
    
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