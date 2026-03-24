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
        
        // Add AI-powered buttons for non-new documents
        if (!frm.is_new()) {
            add_ai_buttons(frm);
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
        
        // Update progress indicators when status changes
        add_status_indicators(frm);
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
    
    // Create and Notify buttons removed per user request
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

// Create Dispatch
function create_dispatch(frm) {
    frappe.new_doc('Dispatch', {
        incident: frm.doc.name
    });
}

// Helper Functions
function add_status_indicators(frm) {
    // Clear existing dashboard content first to prevent duplicates
    clear_dashboard_content(frm);
    
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
    
    // Show incident progress bar (only once)
    add_incident_progress(frm);
}

// Helper function to clear dashboard content
function clear_dashboard_content(frm) {
    // Clear indicators
    if (frm.dashboard && frm.dashboard.clear_indicators) {
        frm.dashboard.clear_indicators();
    }
    
    // Clear progress bars by removing existing progress chart elements
    if (frm.dashboard && frm.dashboard.wrapper) {
        $(frm.dashboard.wrapper).find('.progress-chart').remove();
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
        const partyDoctypeMap = {
            'Employee': 'Employee',
            'Customer': 'Customer',
            'Vendor': 'Supplier',
            'Partner': 'Customer',
            'Regulator': 'Contact',
            'Public': 'Contact',
            'Other': 'Contact'
        };

        const mappedDoctype = partyDoctypeMap[row.party_type] || 'Contact';
        frappe.model.set_value(cdt, cdn, 'party_reference_doctype', mappedDoctype);

        // Avoid saving stale identifiers when the target doctype changes.
        if (row.party_name) {
            frappe.model.set_value(cdt, cdn, 'party_name', '');
        }

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
        
        // Show only reporter-relevant fields
        show_reporter_relevant_fields(frm);
        
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
    // Reporters should only see: Reporter Details, Incident Details, Time & Location
    const tabs_to_hide = [
        'impact_assessment_tab',        // Impact Assessment (management level)
        'assignment_and_escalation_tab', // Assignment & Escalation
        'investigation_tab',            // Investigation
        'resolution_tab',              // Resolution
        'communication_tab',           // Communication (internal/external)
        'closure_and_review_tab'       // Closure & Review
    ];
    
    tabs_to_hide.forEach(tab => {
        if (frm.get_field(tab)) {
            frm.toggle_display(tab, false);
        }
    });
}

function hide_advanced_fields_for_reporter(frm) {
    // Hide advanced fields in the basic incident info section that reporters don't need
    const fields_to_hide = [
        // Status management fields (auto-managed)
        'status',
        
        // Assignment and escalation fields
        'escalation_level',
        'escalated_to', 
        'escalation_date',
        'assigned_responder',
        'response_team',
        'due_date',
        'sla_breach_time',
        'sla_deadline',
        'estimated_resolution_time',
        
        // Investigation fields
        'investigation_required',
        'investigation_priority',
        'investigation_type',
        'investigation_id',
        
        // Advanced operational fields
        'regulatory_reporting_required',
        'external_support_required',
        'vendor_involved',
        'detection_method',
        'response_team_deployed',
        'initial_response_time',
        
        // Resolution and closure fields
        'closure_reason',
        'closure_date',
        'final_report_completed',
        'resolution_id',
        
        // Advanced system fields
        'route',
        'published'
    ];
    
    fields_to_hide.forEach(field => {
        if (frm.get_field(field)) {
            frm.toggle_display(field, false);
        }
    });
    
    // Also hide some sections that contain only advanced fields
    const sections_to_hide = [
        'affected_parties_section',  // This might contain sensitive information
        'timeline_and_updates_section' // Timeline is auto-managed
    ];
    
    sections_to_hide.forEach(section => {
        if (frm.get_field(section)) {
            frm.toggle_display(section, false);
        }
    });
    
    // Show a helpful message about what reporters can do
    if (frm.is_new()) {
        frm.set_intro(__('As an Incident Reporter, you can create new incidents and provide initial details. Your report will be reviewed and assigned by the incident management team.'), 'blue');
    }
}

function show_reporter_relevant_fields(frm) {
    // Explicitly ensure that essential reporter fields are visible
    const reporter_essential_fields = [
        // Reporter Details Tab - all fields should be visible
        'full_name',
        'email', 
        'phone_number',
        'address',
        'organization',
        'role',
        'reporter_department',
        'reporter_manager',
        'reporter_employee_id',
        'witness_present',
        'witness_contact',
        
        // Incident Details Tab - core reporting fields
        'title1',
        'description',
        'attachments',
        'incident_type',
        'severity',
        'priority',
        'department',
        'incident_category',
        'immediate_action_taken',
        'injuries_involved',
        'property_damage',
        
        // Time and Location Tab - essential incident facts
        'incident_date',
        'reported_date',
        'location',
        'affected_systems'
    ];
    
    reporter_essential_fields.forEach(field => {
        if (frm.get_field(field)) {
            frm.toggle_display(field, true);
            // Make required fields more prominent for reporters
            if (['title1', 'description', 'incident_type', 'severity', 'priority', 'incident_date'].includes(field)) {
                frm.get_field(field).df.bold = 1;
                frm.refresh_field(field);
            }
        }
    });
}

function add_incident_progress(frm) {
    // Show incident progress based on status - only the main progress bar
    if (frm.doc.status) {
        let progress_map = {
            'Open': 10,
            'In Progress': 30,
            'Investigating': 50,
            'Resolved': 80,
            'Closed': 100,
            'Cancelled': 0
        };
        
        let progress = progress_map[frm.doc.status] || 0;
        let status_color_map = {
            'Open': 'orange',
            'In Progress': 'blue', 
            'Investigating': 'purple',
            'Resolved': 'green',
            'Closed': 'green',
            'Cancelled': 'red'
        };
        
        let color = status_color_map[frm.doc.status] || 'blue';
        
        // Add only the main incident progress bar
        frm.dashboard.add_progress(
            __('Incident Progress'), 
            progress, 
            __(`${frm.doc.status} - ${progress}% Complete`),
            color
        );
        
        // Removed investigation and resolution progress bars to prevent duplicates
        // Only show the main incident progress which is working correctly
    }
}

// AI-powered functionality
function add_ai_buttons(frm) {
    // Add AI Assistant button - conversational help
    frm.add_custom_button(__('🤖 Ask AI Assistant'), function() {
        show_ai_assistant_dialog(frm);
    }, __('AI Tools')).addClass('btn-primary');
    
    // Add AI Summary button with smart loading and caching
    frm.add_custom_button(__('Generate AI Summary'), function() {
        generate_smart_ai_summary(frm);
    }, __('AI Tools'));
    
    // Add AI Investigation Suggestions button
    frm.add_custom_button(__('AI Investigation Steps'), function() {
        frappe.call({
            method: 'incident_management_system.incident_management_system.doctype.incident.incident.get_incident_ai_suggestions',
            args: {
                incident_name: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    // Show AI suggestions in a dialog
                    let d = new frappe.ui.Dialog({
                        title: 'AI Investigation Suggestions',
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'ai_suggestions',
                                options: `<div style="max-height: 400px; overflow-y: auto; padding: 10px; border: 1px solid #fff3cd; border-radius: 4px; background-color: #fefefe;">
                                    <h5 style="color: #856404;">🔍 AI Investigation Recommendations</h5>
                                    <div style="white-space: pre-wrap; line-height: 1.6;">${r.message}</div>
                                </div>`
                            }
                        ],
                        primary_action_label: 'Create Investigation',
                        primary_action: function() {
                            // Auto-create investigation with AI suggestions
                            frappe.new_doc('Incident Investigation', {
                                incident: frm.doc.name,
                                preliminary_assessment: r.message
                            });
                            d.hide();
                        }
                    });
                    d.show();
                } else {
                    frappe.msgprint('Failed to generate AI investigation suggestions');
                }
            }
        });
    }, __('AI Tools'));
    
    // Add Trend Analysis button (for managers)
    if (frappe.user.has_role(['System Manager', 'Incident Manager'])) {
        frm.add_custom_button(__('AI Trend Analysis'), function() {
            frappe.call({
                method: 'incident_management_system.incident_management_system.doctype.incident.incident.analyze_incident_trends',
                callback: function(r) {
                    if (r.message) {
                        // Show trend analysis in a dialog
                        let d = new frappe.ui.Dialog({
                            title: 'AI Incident Trend Analysis',
                            size: 'large',
                            fields: [
                                {
                                    fieldtype: 'HTML',
                                    fieldname: 'ai_trends',
                                    options: `<div style="max-height: 500px; overflow-y: auto; padding: 15px; border: 1px solid #d4edda; border-radius: 4px; background-color: #f8fff8;">
                                        <h5 style="color: #155724;">📊 AI Trend Analysis (Last 30 Days)</h5>
                                        <div style="white-space: pre-wrap; line-height: 1.6;">${r.message}</div>
                                    </div>`
                                }
                            ],
                            primary_action_label: 'Export Report',
                            primary_action: function() {
                                // Create downloadable report
                                let content = `INCIDENT TREND ANALYSIS REPORT\n\nGenerated: ${new Date().toLocaleString()}\n\n${r.message}`;
                                let blob = new Blob([content], {type: 'text/plain'});
                                let url = URL.createObjectURL(blob);
                                let a = document.createElement('a');
                                a.href = url;
                                a.download = `incident_trends_${new Date().toISOString().split('T')[0]}.txt`;
                                a.click();
                                URL.revokeObjectURL(url);
                            }
                        });
                        d.show();
                    } else {
                        frappe.msgprint('Failed to generate trend analysis');
                    }
                }
            });
        }, __('AI Tools'));
    }
}

// Smart AI Summary with loading, caching, and professional display
function generate_smart_ai_summary(frm) {
    // Show loading indicator
    let loading_msg = frappe.msgprint({
        message: '🤖 Checking for existing AI summary...',
        indicator: 'blue',
        title: 'AI Processing'
    });
    
    // First check if summary already exists
    frappe.call({
        method: 'incident_management_system.incident_management_system.doctype.ai_incident_summary.ai_incident_summary.get_incident_ai_summary',
        args: {
            incident_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.exists) {
                // Show existing summary
                loading_msg.hide();
                show_ai_summary_dialog(frm, r.message.summary, true);
            } else {
                // Generate new summary
                loading_msg.set_message('🔄 Generating new AI summary... This may take 10-30 seconds');
                loading_msg.set_indicator('orange');
                
                let start_time = Date.now();
                
                frappe.call({
                    method: 'incident_management_system.incident_management_system.doctype.incident.incident.generate_incident_ai_summary',
                    args: {
                        incident_name: frm.doc.name
                    },
                    callback: function(ai_response) {
                        loading_msg.hide();
                        
                        if (ai_response.message) {
                            let generation_time = (Date.now() - start_time) / 1000;
                            
                            // Save the AI response to our DocType
                            frappe.call({
                                method: 'incident_management_system.incident_management_system.doctype.ai_incident_summary.ai_incident_summary.create_ai_summary',
                                args: {
                                    incident_name: frm.doc.name,
                                    ai_response: ai_response.message,
                                    model_used: 'gpt-3.5-turbo',
                                    tokens_used: 0, // We'll update this later when we track tokens
                                    generation_time: generation_time
                                },
                                callback: function(save_response) {
                                    if (save_response.message && save_response.message.success) {
                                        // Show the formatted summary
                                        show_ai_summary_dialog(frm, save_response.message, false);
                                        
                                        frappe.show_alert({
                                            message: `AI summary generated and saved in ${generation_time.toFixed(1)}s`,
                                            indicator: 'green'
                                        });
                                    } else {
                                        // Fallback to showing raw response
                                        show_simple_ai_dialog(frm, ai_response.message, 'AI-Generated Summary');
                                    }
                                }
                            });
                        } else {
                            frappe.msgprint('Failed to generate AI summary. Please try again.');
                        }
                    },
                    error: function() {
                        loading_msg.hide();
                        frappe.msgprint('Error generating AI summary. Please check your connection and try again.');
                    }
                });
            }
        },
        error: function() {
            loading_msg.hide();
            frappe.msgprint('Error checking for existing summary. Please try again.');
        }
    });
}

// Professional AI Summary Dialog with print functionality
function show_ai_summary_dialog(frm, summary_data, is_existing) {
    let title = is_existing ? 
        `AI Summary (Generated: ${frappe.datetime.str_to_user(summary_data.generated_on)})` : 
        'AI Summary - Just Generated';
    
    let content = summary_data.summary_content || summary_data.raw_ai_response || 'No content available';
    
    let d = new frappe.ui.Dialog({
        title: title,
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'summary_display',
                options: `
                <div class="ai-summary-container" style="max-height: 500px; overflow-y: auto;">
                    ${content}
                </div>
                <style>
                .ai-summary-container {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    padding: 20px;
                    background: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .ai-summary-container h4 {
                    color: #2490ef;
                    border-bottom: 2px solid #e9ecef;
                    padding-bottom: 8px;
                    margin-bottom: 15px;
                }
                .ai-summary-container p {
                    margin-bottom: 12px;
                    text-align: justify;
                }
                .ai-summary-container ul, .ai-summary-container ol {
                    margin-left: 20px;
                    margin-bottom: 15px;
                }
                .ai-summary-container li {
                    margin-bottom: 6px;
                }
                </style>
                `
            }
        ],
        primary_action_label: 'Print Report',
        primary_action: function() {
            if (summary_data.name) {
                // Open the AI Summary DocType for printing
                frappe.set_route('Form', 'AI Incident Summary', summary_data.name);
            } else {
                // Fallback to browser print
                let printWindow = window.open('', '_blank');
                printWindow.document.write(`
                    <html>
                    <head>
                        <title>AI Incident Summary - ${frm.doc.name}</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 40px; }
                            h1 { color: #2490ef; }
                            h4 { color: #333; margin-top: 25px; }
                            p { line-height: 1.6; }
                            .header { border-bottom: 2px solid #2490ef; padding-bottom: 10px; margin-bottom: 30px; }
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>AI-Generated Incident Summary</h1>
                            <p><strong>Incident:</strong> ${frm.doc.name} | <strong>Generated:</strong> ${new Date().toLocaleString()}</p>
                        </div>
                        ${content}
                    </body>
                    </html>
                `);
                printWindow.document.close();
                printWindow.print();
            }
            d.hide();
        },
        secondary_action_label: 'Copy Text',
        secondary_action: function() {
            // Create plain text version for copying
            let plainText = content.replace(/<[^>]*>/g, '').replace(/&bull;/g, '•').replace(/&nbsp;/g, ' ');
            navigator.clipboard.writeText(plainText);
            frappe.show_alert({message: 'Summary copied to clipboard!', indicator: 'green'});
        }
    });
    
    d.show();
    
    // Add view all summaries button if this is an existing summary
    if (is_existing) {
        d.add_custom_action('View All Summaries', function() {
            frappe.set_route('List', 'AI Incident Summary', {incident: frm.doc.name});
            d.hide();
        });
    }
}

// Simple fallback dialog for raw AI responses
function show_simple_ai_dialog(frm, content, title) {
    let d = new frappe.ui.Dialog({
        title: title,
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'ai_content',
                options: `<div style="max-height: 400px; overflow-y: auto; padding: 15px; white-space: pre-wrap; font-family: monospace; background: #f8f9fa; border-radius: 4px;">${content}</div>`
            }
        ],
        primary_action_label: 'Copy to Clipboard',
        primary_action: function() {
            navigator.clipboard.writeText(content);
            frappe.show_alert('Content copied to clipboard!');
        }
    });
    d.show();
}

// AI Assistant Dialog - Conversational help for incident management
function show_ai_assistant_dialog(frm) {
    let conversation_history = [];
    
    let d = new frappe.ui.Dialog({
        title: '🤖 AI Assistant - Incident Help',
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'chat_area',
                options: `
                <div id="ai-chat-container" style="border: 1px solid #e3e6ea; border-radius: 8px; background: #fefefe; min-height: 400px; max-height: 500px; overflow-y: auto; padding: 15px; margin-bottom: 15px;">
                    <div class="ai-message" style="background: #e3f2fd; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196f3;">
                        <strong>🤖 AI Assistant:</strong><br>
                        Hello! I'm here to help you with this incident. You can ask me questions like:<br><br>
                        • "What are the next steps for this incident?"<br>
                        • "What similar incidents have we had?"<br>
                        • "How should I prioritize this incident?"<br>
                        • "What resources might help resolve this?"<br>
                        • "Are there any risks I should be aware of?"<br><br>
                        <strong>Incident Details:</strong> ${frm.doc.title1 || 'New Incident'} (${frm.doc.severity || 'Unknown'} severity)
                    </div>
                </div>
                `
            },
            {
                fieldtype: 'Small Text',
                fieldname: 'user_question',
                label: 'Ask the AI Assistant',
                placeholder: 'Type your question about this incident...'
            }
        ],
        primary_action_label: 'Ask AI',
        primary_action: function(values) {
            if (!values.user_question.trim()) {
                frappe.msgprint('Please enter a question first');
                return;
            }
            
            // Add user message to chat
            add_message_to_chat('user', values.user_question);
            
            // Clear input
            d.set_value('user_question', '');
            
            // Show loading message
            add_message_to_chat('ai', 'Thinking... 🤔');
            
            // Call AI API
            frappe.call({
                method: 'incident_management_system.utils.ai_helper.get_incident_assistance',
                args: {
                    incident_name: frm.doc.name,
                    user_question: values.user_question,
                    incident_data: {
                        title: frm.doc.title1,
                        description: frm.doc.description,
                        severity: frm.doc.severity,
                        priority: frm.doc.priority,
                        status: frm.doc.status,
                        incident_type: frm.doc.incident_type,
                        reported_date: frm.doc.reported_date
                    },
                    conversation_history: conversation_history
                },
                callback: function(r) {
                    // Remove loading message
                    let chatContainer = document.getElementById('ai-chat-container');
                    let loadingMsg = chatContainer.lastElementChild;
                    if (loadingMsg && loadingMsg.textContent.includes('Thinking...')) {
                        chatContainer.removeChild(loadingMsg);
                    }
                    
                    if (r.message) {
                        add_message_to_chat('ai', r.message);
                        conversation_history.push({
                            question: values.user_question,
                            answer: r.message
                        });
                    } else {
                        add_message_to_chat('ai', 'I apologize, but I encountered an error. Please try asking your question differently.');
                    }
                }
            });
        }
    });
    
    // Helper function to add messages to chat
    function add_message_to_chat(sender, message) {
        let chatContainer = document.getElementById('ai-chat-container');
        if (!chatContainer) return;
        
        let messageDiv = document.createElement('div');
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="user-message" style="background: #f0f8e7; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #4caf50; text-align: right;">
                    <strong>👤 You:</strong><br>
                    ${message}
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="ai-message" style="background: #e3f2fd; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196f3;">
                    <strong>🤖 AI Assistant:</strong><br>
                    ${message.replace(/\n/g, '<br>')}
                </div>
            `;
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    d.show();
}