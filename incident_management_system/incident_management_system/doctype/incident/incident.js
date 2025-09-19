// Copyright (c) 2025, Brian Wachira and contributors
// For license information, please see license.txt

frappe.ui.form.on('Incident', {
    refresh: function(frm) {
        // Apply role-based restrictions first
        apply_role_based_restrictions(frm);
        
        // Add ERPNext-style action buttons for non-submittable document (only for non-reporters)
        if (!frm.is_new() && !frappe.user.has_role('Incident Reporter')) {
            add_action_buttons(frm);
        }
        
        // Add status indicators (for all users)
        add_status_indicators(frm);
        
        // Auto-populate fields based on severity (for all users)
        if (frm.doc.severity && !frm.doc.investigation_priority) {
            set_investigation_priority_from_severity(frm);
        }
        
        // Set default status to Open if not set
        if (frm.is_new() && !frm.doc.status) {
            frm.set_value('status', 'Open');
        }
    },
    
    onload: function(frm) {
        // Set default status for new documents
        if (frm.is_new() && !frm.doc.status) {
            frm.set_value('status', 'Open');
        }
    },
    
    severity: function(frm) {
        set_investigation_priority_from_severity(frm);
        update_sla_based_on_severity(frm);
    },
    
    status: function(frm) {
        // Add timeline entry when status changes
        if (frm.doc.status && frm.doc.name) {
            add_timeline_entry(frm, 'Status Change', `Incident status changed to: ${frm.doc.status}`);
        }
        
        // Auto-set fields based on status
        if (frm.doc.status === 'Closed' && !frm.doc.closure_date) {
            frm.set_value('closure_date', frappe.datetime.get_today());
        }
    },
    
    incident_type: function(frm) {
        // Auto-set investigation requirements based on incident type
        if (frm.doc.incident_type) {
            frappe.db.get_doc('Incident Type', frm.doc.incident_type).then(doc => {
                if (doc.requires_investigation) {
                    frm.set_value('investigation_required', 1);
                }
            });
        }
    }
});

// ERPNext-style Action Buttons
function add_action_buttons(frm) {
    // Primary Action: Close Incident
    if (frm.doc.status !== 'Closed' && frm.doc.status !== 'Cancelled') {
        frm.add_custom_button(__('Close Incident'), function() {
            close_incident_dialog(frm);
        }, __('Actions')).addClass('btn-primary');
    }
    
    // Secondary Actions
    if (frm.doc.status === 'Open' || frm.doc.status === 'In Progress') {
        frm.add_custom_button(__('Escalate'), function() {
            escalate_incident_dialog(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('Create Investigation'), function() {
            create_investigation(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('Assign Response Team'), function() {
            assign_response_team_dialog(frm);
        }, __('Actions'));
    }
    
    if (frm.doc.status === 'Resolved') {
        frm.add_custom_button(__('Reopen'), function() {
            reopen_incident_dialog(frm);
        }, __('Actions'));
    }
    
    if (frm.doc.status === 'Closed') {
        frm.add_custom_button(__('Reopen'), function() {
            reopen_incident_dialog(frm);
        }, __('Actions'));
    }
    
    // Create linked documents
    frm.add_custom_button(__('Create Action Item'), function() {
        create_action_item(frm);
    }, __('Create'));
    
    frm.add_custom_button(__('Create Risk Assessment'), function() {
        create_risk_assessment(frm);
    }, __('Create'));
    
    // Notification actions
    frm.add_custom_button(__('Send Status Update'), function() {
        send_status_update_dialog(frm);
    }, __('Notify'));
    
    frm.add_custom_button(__('Notify Stakeholders'), function() {
        notify_stakeholders_dialog(frm);
    }, __('Notify'));
}

// Close Incident Dialog
function close_incident_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Close Incident'),
        fields: [
            {
                label: 'Closure Reason',
                fieldname: 'closure_reason',
                fieldtype: 'Select',
                options: 'Resolved\nDuplicate\nInvalid\nWithdrawn\nCannot Reproduce\nOther',
                reqd: 1
            },
            {
                label: 'Final Report Completed',
                fieldname: 'final_report_completed',
                fieldtype: 'Check'
            },
            {
                label: 'Closure Notes',
                fieldname: 'closure_notes',
                fieldtype: 'Text'
            }
        ],
        primary_action_label: __('Close Incident'),
        primary_action(values) {
            frm.set_value('status', 'Closed');
            frm.set_value('closure_date', frappe.datetime.get_today());
            frm.set_value('closure_reason', values.closure_reason);
            frm.set_value('final_report_completed', values.final_report_completed);
            
            add_timeline_entry(frm, 'Closure', `Incident closed. Reason: ${values.closure_reason}`);
            
            frm.save().then(() => {
                frappe.msgprint(__('Incident has been closed successfully'));
                d.hide();
            });
        }
    });
    d.show();
}

// Escalate Incident Dialog
function escalate_incident_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Escalate Incident'),
        fields: [
            {
                label: 'Escalation Level',
                fieldname: 'escalation_level',
                fieldtype: 'Select',
                options: 'Level 1\nLevel 2\nLevel 3\nLevel 4',
                reqd: 1
            },
            {
                label: 'Escalate To',
                fieldname: 'escalated_to',
                fieldtype: 'Link',
                options: 'User',
                reqd: 1
            },
            {
                label: 'Escalation Reason',
                fieldname: 'escalation_reason',
                fieldtype: 'Text',
                reqd: 1
            }
        ],
        primary_action_label: __('Escalate'),
        primary_action(values) {
            frm.set_value('escalation_level', values.escalation_level);
            frm.set_value('escalated_to', values.escalated_to);
            frm.set_value('escalation_date', frappe.datetime.now_datetime());
            
            // Also assign the incident to the escalated user
            frm.set_value('assigned_responder', values.escalated_to);
            
            add_timeline_entry(frm, 'Escalation', `Incident escalated to ${values.escalation_level}. Reason: ${values.escalation_reason}`);
            
            // Create a ToDo for the escalated user
            frappe.call({
                method: 'frappe.desk.form.assign_to.add',
                args: {
                    assign_to: [values.escalated_to],
                    doctype: frm.doc.doctype,
                    name: frm.doc.name,
                    description: `Escalated incident: ${values.escalation_reason}`
                },
                callback: function(r) {
                    if (!r.exc) {
                        frappe.show_alert({
                            message: __('Incident escalated and assigned successfully'),
                            indicator: 'green'
                        });
                    }
                }
            });
            
            frm.save().then(() => {
                frappe.msgprint(__('Incident has been escalated successfully'));
                d.hide();
            });
        }
    });
    d.show();
}

// Reopen Incident Dialog
function reopen_incident_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Reopen Incident'),
        fields: [
            {
                label: 'Reason for Reopening',
                fieldname: 'reopen_reason',
                fieldtype: 'Text',
                reqd: 1
            },
            {
                label: 'New Status',
                fieldname: 'new_status',
                fieldtype: 'Select',
                options: 'Open\nIn Progress\nInvestigating',
                default: 'Open',
                reqd: 1
            }
        ],
        primary_action_label: __('Reopen'),
        primary_action(values) {
            frm.set_value('status', values.new_status);
            frm.set_value('closure_date', '');
            frm.set_value('closure_reason', '');
            
            add_timeline_entry(frm, 'Reopened', `Incident reopened. Reason: ${values.reopen_reason}`);
            
            frm.save().then(() => {
                frappe.msgprint(__('Incident has been reopened successfully'));
                d.hide();
            });
        }
    });
    d.show();
}

// Create Investigation
function create_investigation(frm) {
    frappe.model.open_mapped_doc({
        method: "incident_management_system.incident_management_system.doctype.incident.incident.make_investigation",
        frm: frm
    });
}

// Create Action Item
function create_action_item(frm) {
    frappe.new_doc('Action Item', {
        incident: frm.doc.name,
        action_type: 'Corrective',
        priority: map_severity_to_priority(frm.doc.severity)
    });
}

// Create Risk Assessment
function create_risk_assessment(frm) {
    frappe.new_doc('Risk Assessment', {
        incident: frm.doc.name
    });
}

// Helper Functions
function add_status_indicators(frm) {
    // Show overdue indicator
    if (frm.doc.due_date && frm.doc.status !== 'Closed') {
        let today = frappe.datetime.get_today();
        if (frappe.datetime.get_diff(today, frm.doc.due_date) > 0) {
            frm.dashboard.add_indicator(__('Overdue'), 'red');
        }
    }
    
    // Show SLA breach indicator
    if (frm.doc.sla_breach_time && frm.doc.status !== 'Closed') {
        let now = frappe.datetime.now_datetime();
        if (frappe.datetime.get_diff(now, frm.doc.sla_breach_time) > 0) {
            frm.dashboard.add_indicator(__('SLA Breached'), 'red');
        }
    }
    
    // Show investigation indicator
    if (frm.doc.investigation_required && !frm.doc.investigation_id) {
        frm.dashboard.add_indicator(__('Investigation Pending'), 'orange');
    }
}

function set_investigation_priority_from_severity(frm) {
    if (frm.doc.severity && !frm.doc.investigation_priority) {
        let priority_map = {
            'Critical': 'Critical',
            'High': 'High',
            'Medium': 'Medium',
            'Low': 'Low'
        };
        frm.set_value('investigation_priority', priority_map[frm.doc.severity]);
    }
}

function update_sla_based_on_severity(frm) {
    if (frm.doc.severity && !frm.doc.due_date) {
        let hours_map = {
            'Critical': 4,
            'High': 24,
            'Medium': 72,
            'Low': 168
        };
        
        let hours = hours_map[frm.doc.severity] || 72;
        let due_date = frappe.datetime.add_to_date(frm.doc.reported_date, {'hours': hours});
        frm.set_value('due_date', due_date);
        
        // Set SLA breach time (80% of due date)
        let breach_hours = Math.floor(hours * 0.8);
        let breach_time = frappe.datetime.add_to_date(frm.doc.reported_date, {'hours': breach_hours});
        frm.set_value('sla_breach_time', breach_time);
    }
}

function add_timeline_entry(frm, event_type, description) {
    let timeline_entry = {
        timestamp: frappe.datetime.now_datetime(),
        event_type: event_type,
        event_description: description,
        updated_by: frappe.session.user,
        status_before: frm.doc.status,
        status_after: frm.doc.status
    };
    
    frm.add_child('incident_timeline', timeline_entry);
    frm.refresh_field('incident_timeline');
}

function map_severity_to_priority(severity) {
    let priority_map = {
        'Critical': 'Urgent',
        'High': 'High',
        'Medium': 'Normal',
        'Low': 'Low'
    };
    return priority_map[severity] || 'Normal';
}

function send_status_update_dialog(frm) {
    // Implementation for sending status updates
    frappe.msgprint(__('Status update functionality to be implemented'));
}

function notify_stakeholders_dialog(frm) {
    // Implementation for stakeholder notifications
    frappe.msgprint(__('Stakeholder notification functionality to be implemented'));
}

function assign_response_team_dialog(frm) {
    // Implementation for assigning response team
    frappe.msgprint(__('Response team assignment functionality to be implemented'));
}

// Child table events
frappe.ui.form.on('Incident Timeline', {
    timestamp: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.updated_by) {
            frappe.model.set_value(cdt, cdn, 'updated_by', frappe.session.user);
        }
    }
});

frappe.ui.form.on('Incident Affected Party', {
    party_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.party_type && !row.notification_sent) {
            // Auto-suggest notification based on party type
            if (['Customer', 'Regulator', 'Public'].includes(row.party_type)) {
                frappe.model.set_value(cdt, cdn, 'notification_sent', 1);
                frappe.model.set_value(cdt, cdn, 'notification_date', frappe.datetime.now_datetime());
            }
        }
    }
});

// Role-based UI restrictions
function apply_role_based_restrictions(frm) {
    // If user is only an Incident Reporter, hide complex functionality
    if (frappe.user.has_role('Incident Reporter') && 
        !frappe.user.has_role('Incident Manager') && 
        !frappe.user.has_role('Incident Responder')) {
        
        // Hide complex tabs - reporters only need basic incident details
        hide_tabs_for_reporter(frm);
        
        // Hide advanced fields in the basic info section
        hide_advanced_fields_for_reporter(frm);
        
        // Make the form read-only if not new and not created by current user
        if (!frm.is_new() && frm.doc.owner !== frappe.session.user) {
            frm.disable_form();
            frappe.msgprint({
                title: __('View Only Access'),
                message: __('You can only view this incident. Contact your manager for modifications.'),
                indicator: 'blue'
            });
        }
    }
}

function hide_tabs_for_reporter(frm) {
    // Hide advanced tabs that reporters don't need to see
    const tabs_to_hide = [
        'assignment_tab',           // Assignment & Escalation
        'investigation_tab',        // Investigation
        'resolution_tab',          // Resolution
        'closure_tab',             // Closure & Follow-up
        'timeline_tab',            // Timeline (they can see basic status)
        'affected_parties_tab'     // Affected Parties (sensitive info)
    ];
    
    tabs_to_hide.forEach(tab => {
        if (frm.get_field(tab)) {
            frm.toggle_display(tab, false);
        }
    });
}

function hide_advanced_fields_for_reporter(frm) {
    // Hide advanced fields in the basic incident info section
    const fields_to_hide = [
        'escalation_level',
        'escalated_to', 
        'escalation_date',
        'investigation_required',
        'investigation_priority',
        'regulatory_notification_required',
        'regulatory_notification_sent',
        'assigned_responder',
        'response_team',
        'sla_deadline',
        'closure_reason',
        'closure_date',
        'final_report_completed'
    ];
    
    fields_to_hide.forEach(field => {
        if (frm.get_field(field)) {
            frm.toggle_display(field, false);
        }
    });
    
    // Show a helpful message about what reporters can do
    if (frm.is_new()) {
        frm.set_intro(__('As an Incident Reporter, you can create new incidents and provide initial details. Your report will be reviewed and assigned by the incident management team.'), 'blue');
    }
}