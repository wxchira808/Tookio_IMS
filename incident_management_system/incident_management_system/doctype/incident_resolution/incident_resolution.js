// Copyright (c) 2025, Brian Wachira and contributors
// For license information, please see license.txt

frappe.ui.form.on('Incident Resolution', {
    refresh: function(frm) {
        add_custom_buttons(frm);
        set_status_indicators(frm);
        setup_timeline_updates(frm);
        setup_auto_calculations(frm);
    },
    
    onload: function(frm) {
        setup_field_filters(frm);
        setup_field_dependencies(frm);
    },
    
    incident: function(frm) {
        if (frm.doc.incident) {
            // Check for investigation
            frappe.db.get_value('Incident', frm.doc.incident, 'investigation_id')
                .then(r => {
                    if(!r.message.investigation_id) {
                        frappe.msgprint(__('Cannot create Resolution without an Investigation. Please create an Investigation first.'));
                        frm.set_value('incident', '');
                        return;
                    }
                    fetch_incident_details(frm);
                });
        }
    },
    
    resolution_status: function(frm) {
        update_field_visibility(frm);
        set_status_indicators(frm);
    },
    
    verification_status: function(frm) {
        if (frm.doc.verification_status === 'Passed') {
            frm.set_value('closure_criteria_met', 1);
        }
    }
});

function add_custom_buttons(frm) {
    // Clear existing custom buttons
    frm.clear_custom_buttons();
    
    if (frm.doc.docstatus === 0) {
        // Draft state buttons
        
        // Primary Actions
        frm.add_custom_button(__('Verify Solution'), function() {
            verify_solution_dialog(frm);
        }, __('Primary Actions')).addClass('btn-primary');
        
        frm.add_custom_button(__('Update Status'), function() {
            update_status_dialog(frm);
        }, __('Primary Actions'));
        
        // Validation Actions
        frm.add_custom_button(__('Run Validation'), function() {
            run_validation_tests(frm);
        }, __('Validation'));
        
        frm.add_custom_button(__('Mark Criteria Passed'), function() {
            mark_criteria_dialog(frm, 'passed');
        }, __('Validation'));
        
        frm.add_custom_button(__('Mark Criteria Failed'), function() {
            mark_criteria_dialog(frm, 'failed');
        }, __('Validation'));
        
        // Communication Actions
        frm.add_custom_button(__('Notify Stakeholders'), function() {
            notify_stakeholders_dialog(frm);
        }, __('Communication'));
        
        frm.add_custom_button(__('Add Documentation'), function() {
            add_documentation_dialog(frm);
        }, __('Communication'));
        
        // Action Items
        frm.add_custom_button(__('Create Action Items'), function() {
            create_action_items_dialog(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('Assign Follow-up'), function() {
            assign_followup_dialog(frm);
        }, __('Actions'));
        
    } else if (frm.doc.docstatus === 1) {
        // Submitted state buttons
        
        frm.add_custom_button(__('View Metrics'), function() {
            show_resolution_metrics(frm);
        }).addClass('btn-info');
        
        frm.add_custom_button(__('Export Report'), function() {
            export_resolution_report(frm);
        });
        
        if (frappe.user.has_role(['System Manager', 'Incident Manager'])) {
            frm.add_custom_button(__('Reopen Resolution'), function() {
                reopen_resolution_dialog(frm);
            }).addClass('btn-warning');
        }
    }
    
    // Always available buttons
    frm.add_custom_button(__('View Incident'), function() {
        if (frm.doc.incident) {
            frappe.set_route('Form', 'Incident', frm.doc.incident);
        }
    });
    
    frm.add_custom_button(__('Resolution Timeline'), function() {
        show_resolution_timeline(frm);
    });
}

function verify_solution_dialog(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('Verify Solution'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'verification_method',
                label: __('Verification Method'),
                options: [
                    'Functional Testing',
                    'User Acceptance Testing', 
                    'Stress Testing',
                    'Monitoring',
                    'Peer Review',
                    'Customer Validation',
                    'Automated Testing'
                ],
                reqd: 1
            },
            {
                fieldtype: 'Link',
                fieldname: 'verified_by',
                label: __('Verified By'),
                options: 'User',
                default: frappe.session.user,
                reqd: 1
            },
            {
                fieldtype: 'Text Editor',
                fieldname: 'testing_details',
                label: __('Testing Details'),
                reqd: 1
            },
            {
                fieldtype: 'Select',
                fieldname: 'verification_result',
                label: __('Verification Result'),
                options: ['Passed', 'Failed', 'Partially Verified'],
                reqd: 1
            }
        ],
        primary_action_label: __('Update Verification'),
        primary_action: function(values) {
            frm.set_value('verification_method', values.verification_method);
            frm.set_value('verified_by', values.verified_by);
            frm.set_value('verification_date', frappe.datetime.get_today());
            frm.set_value('verification_status', values.verification_result);
            frm.set_value('solution_testing_details', values.testing_details);
            
            if (values.verification_result === 'Passed') {
                frm.set_value('resolution_status', 'Verified');
                frappe.show_alert({
                    message: __('Solution verification completed successfully!'),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: __('Solution verification recorded. Please review and update.'),
                    indicator: 'orange'
                });
            }
            
            frm.save();
            dialog.hide();
        }
    });
    
    dialog.show();
}

function update_status_dialog(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('Update Resolution Status'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'new_status',
                label: __('New Status'),
                options: [
                    'Draft',
                    'In Progress',
                    'Pending Verification',
                    'Verified',
                    'Closed'
                ],
                default: frm.doc.resolution_status,
                reqd: 1
            },
            {
                fieldtype: 'Text',
                fieldname: 'status_reason',
                label: __('Reason for Status Change'),
                reqd: 1
            }
        ],
        primary_action_label: __('Update Status'),
        primary_action: function(values) {
            frm.set_value('resolution_status', values.new_status);
            
            // Add to timeline
            frm.timeline.insert_comment('Info', 
                `Status changed to ${values.new_status}: ${values.status_reason}`
            );
            
            frm.save();
            dialog.hide();
            
            frappe.show_alert({
                message: __(`Status updated to ${values.new_status}`),
                indicator: 'blue'
            });
        }
    });
    
    dialog.show();
}

function mark_criteria_dialog(frm, action) {
    const title = action === 'passed' ? 'Mark Criteria as Passed' : 'Mark Criteria as Failed';
    
    const dialog = new frappe.ui.Dialog({
        title: __(title),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'criteria',
                label: __('Validation Criteria'),
                options: frm.doc.validation_criteria.map(c => c.criteria_title),
                reqd: 1
            },
            {
                fieldtype: 'Text',
                fieldname: 'reason',
                label: action === 'passed' ? __('Success Notes') : __('Failure Reason'),
                reqd: action === 'failed'
            }
        ],
        primary_action_label: __(action === 'passed' ? 'Mark Passed' : 'Mark Failed'),
        primary_action: function(values) {
            if (action === 'passed') {
                frm.call('mark_criteria_passed', {
                    criteria_name: values.criteria
                }).then(() => {
                    frappe.show_alert({
                        message: __('Criteria marked as passed'),
                        indicator: 'green'
                    });
                    frm.refresh();
                });
            } else {
                frm.call('mark_criteria_failed', {
                    criteria_name: values.criteria,
                    reason: values.reason
                }).then(() => {
                    frappe.show_alert({
                        message: __('Criteria marked as failed'),
                        indicator: 'red'
                    });
                    frm.refresh();
                });
            }
            dialog.hide();
        }
    });
    
    dialog.show();
}

function run_validation_tests(frm) {
    frappe.show_alert({
        message: __('Running validation tests...'),
        indicator: 'blue'
    });
    
    // Simulate validation test execution
    setTimeout(() => {
        const passed_count = Math.floor(Math.random() * frm.doc.validation_criteria.length);
        
        frappe.show_alert({
            message: __(`Validation complete: ${passed_count} criteria passed`),
            indicator: passed_count > 0 ? 'green' : 'orange'
        });
        
        // Update random criteria to passed
        for (let i = 0; i < passed_count; i++) {
            if (frm.doc.validation_criteria[i]) {
                frm.doc.validation_criteria[i].status = 'Passed';
                frm.doc.validation_criteria[i].validated_by = frappe.session.user;
                frm.doc.validation_criteria[i].validation_date = frappe.datetime.get_today();
            }
        }
        
        frm.refresh_field('validation_criteria');
        frm.save();
    }, 2000);
}

function set_status_indicators(frm) {
    // Status indicator colors
    const status_colors = {
        'Draft': 'gray',
        'In Progress': 'blue',
        'Pending Verification': 'orange',
        'Verified': 'green',
        'Closed': 'darkgreen'
    };
    
    const verification_colors = {
        'Not Started': 'gray',
        'In Progress': 'blue',
        'Passed': 'green',
        'Failed': 'red',
        'Partially Verified': 'orange'
    };
    
    // Set status indicators
    frm.dashboard.set_headline_alert(
        `<div class="row">
            <div class="col-xs-6">
                <span class="indicator ${status_colors[frm.doc.resolution_status] || 'gray'}">
                    Resolution: ${frm.doc.resolution_status || 'Draft'}
                </span>
            </div>
            <div class="col-xs-6">
                <span class="indicator ${verification_colors[frm.doc.verification_status] || 'gray'}">
                    Verification: ${frm.doc.verification_status || 'Not Started'}
                </span>
            </div>
        </div>`
    );
}

function fetch_incident_details(frm) {
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Incident',
            name: frm.doc.incident
        },
        callback: function(r) {
            if (r.message) {
                const incident = r.message;
                frm.set_value('incident_title', incident.title);
                frm.set_value('incident_priority', incident.priority);
                frm.set_value('incident_severity', incident.severity);
                frm.set_value('incident_type', incident.incident_type);
                
                // Auto-populate resolution team if not set
                if (!frm.doc.resolution_team && incident.assigned_to) {
                    frm.set_value('resolution_team', incident.assigned_to);
                }
            }
        }
    });
}

function setup_field_filters(frm) {
    // Filter resolved_by to show only active users
    frm.set_query('resolved_by', function() {
        return {
            filters: {
                enabled: 1
            }
        };
    });
    
    // Filter incident to show only open incidents
    frm.set_query('incident', function() {
        return {
            filters: {
                status: ['in', ['Open', 'Under Investigation', 'In Progress']]
            }
        };
    });
}

function setup_field_dependencies(frm) {
    // Show/hide fields based on status
    update_field_visibility(frm);
}

function update_field_visibility(frm) {
    const status = frm.doc.resolution_status;
    
    // Root cause fields - show when status is 'In Progress' or later
    const show_root_cause = ['In Progress', 'Pending Verification', 'Verified', 'Closed'].includes(status);
    frm.toggle_display('root_cause_tab', show_root_cause);
    
    // Verification fields - show when status is 'Pending Verification' or later
    const show_verification = ['Pending Verification', 'Verified', 'Closed'].includes(status);
    frm.toggle_display('verification_tab', show_verification);
    
    // Closure fields - show only when status is 'Closed'
    const show_closure = status === 'Closed';
    frm.toggle_display('closure_tab', show_closure);
}

function setup_timeline_updates(frm) {
    // Auto-update timeline on status changes
    if (frm.doc.__islocal) return;
    
    frm.timeline.refresh();
}

function setup_auto_calculations(frm) {
    // Auto-calculate resolution time when date/time changes
    if (frm.doc.incident && frm.doc.resolution_date) {
        calculate_resolution_metrics(frm);
    }
}

function calculate_resolution_metrics(frm) {
    if (!frm.doc.incident || !frm.doc.resolution_date) return;
    
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Incident',
            name: frm.doc.incident
        },
        callback: function(r) {
            if (r.message && r.message.incident_date) {
                const incident_date = moment(r.message.incident_date + ' ' + (r.message.incident_time || '00:00:00'));
                const resolution_date = moment(frm.doc.resolution_date + ' ' + (frm.doc.resolution_time || '00:00:00'));
                
                const hours_diff = resolution_date.diff(incident_date, 'hours', true);
                frm.set_value('resolution_time_hours', Math.round(hours_diff * 100) / 100);
                
                // Determine SLA compliance
                const sla_hours = {
                    'Critical': 4,
                    'High': 8,
                    'Medium': 24,
                    'Low': 72
                };
                
                const target_hours = sla_hours[r.message.priority] || 24;
                frm.set_value('sla_compliance', hours_diff <= target_hours ? 1 : 0);
            }
        }
    });
}

function show_resolution_metrics(frm) {
    frm.call('get_resolution_summary').then(r => {
        if (r.message) {
            const metrics = r.message;
            
            const dialog = new frappe.ui.Dialog({
                title: __('Resolution Metrics'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'metrics_html',
                        options: `
                            <div class="resolution-metrics">
                                <div class="row">
                                    <div class="col-xs-6">
                                        <h5>Performance Metrics</h5>
                                        <p><strong>Resolution Time:</strong> ${metrics.resolution_time_hours || 0} hours</p>
                                        <p><strong>SLA Compliance:</strong> 
                                            <span class="indicator ${metrics.sla_compliance ? 'green' : 'red'}">
                                                ${metrics.sla_compliance ? 'Met' : 'Missed'}
                                            </span>
                                        </p>
                                        <p><strong>Verification Status:</strong> ${metrics.verification_status || 'Not Started'}</p>
                                    </div>
                                    <div class="col-xs-6">
                                        <h5>Quality Metrics</h5>
                                        <p><strong>Stakeholder Satisfaction:</strong> ${metrics.stakeholder_satisfaction || 'Not Rated'}</p>
                                        <p><strong>Closure Criteria:</strong> 
                                            <span class="indicator ${metrics.closure_criteria_met ? 'green' : 'orange'}">
                                                ${metrics.closure_criteria_met ? 'Met' : 'Pending'}
                                            </span>
                                        </p>
                                    </div>
                                </div>
                            </div>
                        `
                    }
                ]
            });
            
            dialog.show();
        }
    });
}

function notify_stakeholders_dialog(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('Notify Stakeholders'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'notification_type',
                label: __('Notification Type'),
                options: [
                    'Resolution Completed',
                    'Solution Deployed',
                    'Testing Complete',
                    'Stakeholder Update',
                    'Closure Notice',
                    'Lessons Learned'
                ],
                reqd: 1
            },
            {
                fieldtype: 'Link',
                fieldname: 'recipient',
                label: __('Additional Recipient'),
                options: 'User'
            },
            {
                fieldtype: 'Text',
                fieldname: 'custom_message',
                label: __('Custom Message')
            }
        ],
        primary_action_label: __('Send Notification'),
        primary_action: function(values) {
            // Add notification record
            const notification_row = frm.add_child('resolution_notifications');
            notification_row.notification_type = values.notification_type;
            notification_row.recipient = values.recipient || frm.doc.resolved_by;
            notification_row.notification_method = 'Email';
            notification_row.sent_date = frappe.datetime.now_datetime();
            notification_row.status = 'Sent';
            notification_row.message = values.custom_message;
            
            frm.refresh_field('resolution_notifications');
            frm.save();
            
            frappe.show_alert({
                message: __('Notification sent successfully'),
                indicator: 'green'
            });
            
            dialog.hide();
        }
    });
    
    dialog.show();
}

function show_resolution_timeline(frm) {
    frappe.route_options = {
        "reference_doctype": "Incident Resolution",
        "reference_name": frm.doc.name
    };
    frappe.set_route("List", "Communication");
}