// Copyright (c) 2025, Brian Wachira and contributors
// For license information, please see license.txt

frappe.ui.form.on('Incident Resolution', {
    incident: function(frm) {
        // Auto-populate resolution fields when incident is selected
        if (frm.doc.incident) {
            frappe.db.get_doc('Incident', frm.doc.incident).then(incident => {
             
                
                // Set basic incident details if not already set
                if (!frm.doc.incident_title) {
                    frm.set_value('incident_title', incident.title1);
                }
                if (!frm.doc.incident_priority) {
                    frm.set_value('incident_priority', incident.priority);
                }
                if (!frm.doc.incident_severity) {
                    frm.set_value('incident_severity', incident.severity);
                }
                if (!frm.doc.incident_type) {
                    frm.set_value('incident_type', incident.incident_type);
                }
            });
        }
    },
    
    resolution_status: function(frm) {
        // Auto-set completion date when status changes to completed
        if (frm.doc.resolution_status === 'Completed' && !frm.doc.actual_completion_date) {
            frm.set_value('actual_completion_date', frappe.datetime.get_today());
        }
        
        // Update dashboard
        update_resolution_dashboard(frm);
    },
    
    resolution_progress: function(frm) {
        // Update dashboard when progress field changes
        update_resolution_dashboard(frm);
    },
    
    resolution_approved: function(frm) {
        // Auto-set approved by when approved
        if (frm.doc.resolution_approved && !frm.doc.approved_by) {
            frm.set_value('approved_by', frappe.session.user);
        }
        
        // Update dashboard
        update_resolution_dashboard(frm);
    },
    
    refresh: function(frm) {
        // Update dashboard
        update_resolution_dashboard(frm);
        
        // Auto-set resolution date for new documents
        if (frm.is_new() && !frm.doc.resolution_date) {
            frm.set_value('resolution_date', frappe.datetime.get_today());
        }
        
        // Auto-set default status for new documents
        if (frm.is_new() && !frm.doc.resolution_status) {
            frm.set_value('resolution_status', 'Draft');
        }
        
        // Auto-set resolved by for new documents
        if (frm.is_new() && !frm.doc.resolved_by) {
            frm.set_value('resolved_by', frappe.session.user);
        }
    }
});

// Consolidated dashboard update function
function update_resolution_dashboard(frm) {
    // Clear existing dashboard content first to prevent duplicates
    clear_resolution_dashboard(frm);
    
    // Add progress bar and status indicators
    add_resolution_progress(frm);
    add_resolution_status_indicators(frm);
}

// Helper function to clear dashboard content
function clear_resolution_dashboard(frm) {
    // Clear indicators
    if (frm.dashboard && frm.dashboard.clear_indicators) {
        frm.dashboard.clear_indicators();
    }
    
    // Clear progress bars by removing existing progress chart elements
    if (frm.dashboard && frm.dashboard.wrapper) {
        $(frm.dashboard.wrapper).find('.progress-chart').remove();
    }
    
    // Clear headlines
    if (frm.dashboard && frm.dashboard.clear_headline) {
        frm.dashboard.clear_headline();
    }
}

function add_resolution_progress(frm) {
    // Show resolution progress based on status and actual progress field
    if (frm.doc.resolution_status) {
        // Use the calculated progress from the backend if available
        let progress = frm.doc.resolution_progress || 0;
        
        // If no calculated progress, use status-based progress
        if (progress === 0) {
            let progress_map = {
                'Draft': 0,
                'Planning': 8,
                'Root Cause Analysis': 16,
                'Solution Design': 25,
                'Implementation': 35,
                'Testing': 45,
                'Verification': 60,
                'Approval Pending': 75,
                'Deployed': 85,
                'Monitoring': 92,
                'Completed': 100,
                'Rejected': 0
            };
            progress = progress_map[frm.doc.resolution_status] || 0;
        }
        
        let status_color_map = {
            'Draft': 'grey',
            'Planning': 'blue',
            'Root Cause Analysis': 'orange',
            'Solution Design': 'purple',
            'Implementation': 'cyan',
            'Testing': 'yellow',
            'Verification': 'light-blue',
            'Approval Pending': 'orange',
            'Deployed': 'green',
            'Monitoring': 'dark-green',
            'Completed': 'green',
            'Rejected': 'red'
        };
        
        let color = status_color_map[frm.doc.resolution_status] || 'blue';
        
        // Add main resolution progress bar
        frm.dashboard.add_progress(
            __('Resolution Progress'), 
            progress, 
            __(`${frm.doc.resolution_status} - ${progress}% Complete`),
            color
        );
        
        // Add overdue indicator if applicable
        if (frm.doc.target_completion_date && !frm.doc.actual_completion_date) {
            let today = frappe.datetime.get_today();
            if (frappe.datetime.get_diff(today, frm.doc.target_completion_date) > 0) {
                let overdue_days = frappe.datetime.get_diff(today, frm.doc.target_completion_date);
                frm.dashboard.add_indicator(__(`Overdue by ${overdue_days} days`), 'red');
            }
        }
    }
}

function add_resolution_status_indicators(frm) {
    // Show resolution-specific indicators
    if (frm.doc.resolution_approved) {
        frm.dashboard.add_indicator(__('Resolution Approved'), 'green');
    } else if (frm.doc.resolution_status !== 'Draft') {
        frm.dashboard.add_indicator(__('Approval Pending'), 'orange');
    }
    
    // Show closure criteria status
    if (frm.doc.closure_criteria_met) {
        frm.dashboard.add_indicator(__('Closure Criteria Met'), 'green');
    } else if (frm.doc.resolution_status !== 'Draft') {
        frm.dashboard.add_indicator(__('Closure Criteria Pending'), 'orange');
    }
}
