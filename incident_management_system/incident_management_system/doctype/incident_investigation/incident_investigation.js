// Copyright (c) 2025, Brian Wachira and contributors
// For license information, please see license.txt

frappe.ui.form.on('Incident Investigation', {
    incident: function(frm) {
        // Auto-populate investigation fields when incident is selected
        if (frm.doc.incident) {
            frappe.db.get_doc('Incident', frm.doc.incident).then(incident => {
                // Set investigation priority based on incident severity
                if (incident.severity === 'Critical') {
                    frm.set_value('investigation_priority', 'Critical');
                } else if (incident.severity === 'High') {
                    frm.set_value('investigation_priority', 'High');
                } else {
                    frm.set_value('investigation_priority', 'Medium');
                }
                
                // Set preliminary assessment
                if (!frm.doc.preliminary_assessment) {
                    frm.set_value('preliminary_assessment', 
                        `Preliminary investigation for incident: ${incident.title1}\n` +
                        `Severity: ${incident.severity}\n` +
                        `Reported: ${incident.reported_date}\n` +
                        `Description: ${incident.description}`
                    );
                }
            });
        }
    },
    
    investigation_status: function(frm) {
        // Auto-set completion date when status changes to completed
        if (frm.doc.investigation_status === 'Completed' && !frm.doc.actual_completion_date) {
            frm.set_value('actual_completion_date', frappe.datetime.get_today());
        }
        
        // Add timeline entry for status changes
        if (frm.doc.investigation_status && frm.doc.name) {
            frm.add_child('investigation_timeline', {
                event_date: frappe.datetime.get_today(),
                event_time: frappe.datetime.get_time(),
                event_description: `Investigation status changed to: ${frm.doc.investigation_status}`,
                event_type: 'Status Change',
                responsible_party: frappe.session.user
            });
            frm.refresh_field('investigation_timeline');
        }
        
        // Update dashboard with a slight delay to ensure progress is calculated
        setTimeout(() => {
            update_investigation_dashboard(frm);
        }, 100);
    },
    
    investigation_progress: function(frm) {
        // Update dashboard when progress field changes
        update_investigation_dashboard(frm);
    },
    
    onload: function(frm) {
        // Set up initial field requirements and dashboard
        update_investigation_dashboard(frm);
    },
    
    refresh: function(frm) {
        // Update dashboard
        update_investigation_dashboard(frm);
        
        // Auto-set start date for new documents
        if (frm.is_new() && !frm.doc.start_date) {
            frm.set_value('start_date', frappe.datetime.get_today());
        }
        
        // Custom buttons removed to reduce interface clutter
    },
    
    onload: function(frm) {
        // Set default status for new documents
        if (frm.is_new() && !frm.doc.investigation_status) {
            frm.set_value('investigation_status', 'Draft');
        }
    },
});

// Helper function to generate investigation report
function generate_investigation_report(doc) {
    let report = `# Investigation Report\n\n`;
    report += `**Investigation ID:** ${doc.name}\n`;
    report += `**Incident:** ${doc.incident}\n`;
    report += `**Investigation Type:** ${doc.investigation_type}\n`;
    report += `**Priority:** ${doc.investigation_priority}\n`;
    report += `**Status:** ${doc.investigation_status}\n`;
    report += `**Duration:** ${doc.start_date} to ${doc.actual_completion_date || 'Ongoing'}\n\n`;
    
    if (doc.investigation_objective) {
        report += `## Investigation Objective\n${doc.investigation_objective}\n\n`;
    }
    
    if (doc.investigation_findings) {
        report += `## Key Findings\n${doc.investigation_findings}\n\n`;
    }
    
    if (doc.root_cause_description) {
        report += `## Root Cause Analysis\n`;
        report += `**Category:** ${doc.root_cause_category}\n`;
        report += `**Description:** ${doc.root_cause_description}\n\n`;
    }
    
    if (doc.investigation_recommendations) {
        report += `## Recommendations\n${doc.investigation_recommendations}\n\n`;
    }
    
    if (doc.lessons_learned) {
        report += `## Lessons Learned\n${doc.lessons_learned}\n\n`;
    }
    
    report += `---\n*Report generated on ${frappe.datetime.get_today()}*`;
    
    return report;
}

// Child table events
frappe.ui.form.on('Investigation Evidence', {
    evidence_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.collection_date) {
            frappe.model.set_value(cdt, cdn, 'collection_date', frappe.datetime.now_datetime());
        }
        if (!row.collected_by) {
            frappe.model.set_value(cdt, cdn, 'collected_by', frappe.session.user);
        }
    }
});

frappe.ui.form.on('Investigation Witness', {
    witness_name: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.interview_date) {
            frappe.model.set_value(cdt, cdn, 'interview_date', frappe.datetime.now_datetime());
        }
    }
});

// Consolidated dashboard update function
function update_investigation_dashboard(frm) {
    // Clear existing dashboard content first to prevent duplicates
    clear_investigation_dashboard(frm);
    
    // Add progress bar and status indicators
    add_investigation_progress(frm);
    add_investigation_status_indicators(frm);
    
    // Handle progressive mandatory fields
    handle_progressive_mandatory_fields(frm);
}

// Helper function to clear dashboard content
function clear_investigation_dashboard(frm) {
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

// Handle progressive mandatory fields based on investigation status
function handle_progressive_mandatory_fields(frm) {
    // Reset all fields to non-mandatory first
    const all_fields = [
        'investigation_type', 'investigation_priority', 'investigation_method',
        'root_cause_description', 'investigation_findings', 'preventive_measures', 
        'corrective_actions_required', 'peer_review_comments'
    ];
    
    all_fields.forEach(field => {
        if (frm.get_field(field)) {
            frm.toggle_reqd(field, false);
        }
    });
    
    // Set mandatory fields based on current status
    const status = frm.doc.investigation_status;
    
    if (status && status !== 'Draft') {
        // Planning phase requirements
        frm.toggle_reqd('investigation_type', true);
        frm.toggle_reqd('investigation_priority', true);
    }
    
    if (status === 'Evidence Collection' || ['Analysis', 'Review', 'Approval Pending', 'Completed'].includes(status)) {
        // Evidence Collection requirements
        frm.toggle_reqd('investigation_method', true);
    }
    
    if (['Analysis', 'Review', 'Approval Pending', 'Completed'].includes(status)) {
        // Analysis phase requirements
        frm.toggle_reqd('root_cause_description', true);
        frm.toggle_reqd('investigation_findings', true);
    }
    
    if (['Review', 'Approval Pending', 'Completed'].includes(status)) {
        // Review phase requirements
        frm.toggle_reqd('preventive_measures', true);
        frm.toggle_reqd('corrective_actions_required', true);
    }
    
    if (['Approval Pending', 'Completed'].includes(status) && frm.doc.peer_review_required) {
        // Peer review requirements
        frm.toggle_reqd('peer_review_comments', true);
    }
}

function add_investigation_progress(frm) {
    // Show investigation progress based on status and actual progress field
    if (frm.doc.investigation_status) {
        // Use the calculated progress from the backend if available
        let progress = frm.doc.investigation_progress || 0;
        
        // If no calculated progress, use status-based progress
        if (progress === 0) {
            let progress_map = {
                'Draft': 0,
                'Planning': 15,
                'Evidence Collection': 35,
                'Analysis': 60,
                'Review': 80,
                'Approval Pending': 90,
                'Completed': 100,
                'Rejected': 0
            };
            progress = progress_map[frm.doc.investigation_status] || 0;
        }
        
        let status_color_map = {
            'Draft': 'grey',
            'Planning': 'blue',
            'Evidence Collection': 'orange',
            'Analysis': 'purple',
            'Review': 'yellow',
            'Approval Pending': 'cyan',
            'Completed': 'green',
            'Rejected': 'red'
        };
        
        let color = status_color_map[frm.doc.investigation_status] || 'blue';
        
        // Add main investigation progress bar
        frm.dashboard.add_progress(
            __('Investigation Progress'), 
            progress, 
            __(`${frm.doc.investigation_status} - ${progress}% Complete`),
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

function add_investigation_status_indicators(frm) {
    // Add status-specific indicators and styling (dashboard already cleared in refresh)
    if (frm.doc.investigation_status) {        
        // Add status-specific headlines
        if (frm.doc.investigation_status === 'Completed') {
            frm.dashboard.set_headline(__('Investigation Completed Successfully'));
        } else if (frm.doc.investigation_status === 'Rejected') {
            frm.dashboard.set_headline(__('Investigation Rejected - Requires Revision'));
        } else if (frm.doc.investigation_status === 'Approval Pending') {
            frm.dashboard.set_headline(__('Investigation Pending Approval'));
        }
        
        // Highlight important fields based on status
        let highlight_fields = [];
        if (frm.doc.investigation_status === 'Evidence Collection') {
            highlight_fields = ['evidence_collected', 'key_witnesses'];
        } else if (frm.doc.investigation_status === 'Analysis') {
            highlight_fields = ['root_cause_description', 'investigation_findings', 'contributing_factors'];
        } else if (frm.doc.investigation_status === 'Review') {
            highlight_fields = ['preventive_measures', 'corrective_actions_required'];
        } else if (frm.doc.investigation_status === 'Approval Pending') {
            highlight_fields = ['investigation_approved', 'approved_by'];
        }
        
        // Apply highlighting
        highlight_fields.forEach(field => {
            if (frm.get_field(field)) {
                frm.get_field(field).df.bold = 1;
                frm.refresh_field(field);
            }
        });
    }
}

frappe.ui.form.on('Investigation Timeline', {
    event_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.event_date) {
            frappe.model.set_value(cdt, cdn, 'event_date', frappe.datetime.get_today());
        }
        if (!row.event_time) {
            frappe.model.set_value(cdt, cdn, 'event_time', frappe.datetime.get_time());
        }
        if (!row.responsible_party) {
            frappe.model.set_value(cdt, cdn, 'responsible_party', frappe.session.user);
        }
    }
});