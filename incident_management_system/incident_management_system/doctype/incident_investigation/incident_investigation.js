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
    },
    
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.docstatus === 1) {
            // Button to create action items
            frm.add_custom_button(__('Create Action Item'), function() {
                let d = new frappe.ui.Dialog({
                    title: 'Create Action Item',
                    fields: [
                        {
                            label: 'Action Title',
                            fieldname: 'action_title',
                            fieldtype: 'Data',
                            reqd: 1
                        },
                        {
                            label: 'Action Description',
                            fieldname: 'action_description',
                            fieldtype: 'Text Editor',
                            reqd: 1
                        },
                        {
                            label: 'Priority',
                            fieldname: 'priority',
                            fieldtype: 'Select',
                            options: 'Urgent\nHigh\nNormal\nLow',
                            default: 'Normal'
                        }
                    ],
                    primary_action_label: 'Create',
                    primary_action(values) {
                        frappe.call({
                            method: 'incident_management_system.incident_management_system.doctype.incident_investigation.incident_investigation.create_action_item_from_investigation',
                            args: {
                                investigation_name: frm.doc.name,
                                action_title: values.action_title,
                                action_description: values.action_description,
                                priority: values.priority
                            },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.msgprint('Action Item created successfully');
                                    d.hide();
                                }
                            }
                        });
                    }
                });
                d.show();
            }, __('Actions'));
            
            // Button to generate investigation report
            frm.add_custom_button(__('Generate Report'), function() {
                // Generate a comprehensive investigation report
                let report_content = generate_investigation_report(frm.doc);
                frm.set_value('investigation_report', report_content);
                frm.save();
            }, __('Actions'));
        }
        
        // Show overdue indicator
        if (frm.doc.target_completion_date && !frm.doc.actual_completion_date) {
            let today = frappe.datetime.get_today();
            if (frappe.datetime.get_diff(today, frm.doc.target_completion_date) > 0) {
                frm.dashboard.add_indicator(__('Overdue'), 'red');
            }
        }
        
        // Show progress indicator
        if (frm.doc.investigation_status) {
            let progress_map = {
                'Not Started': 0,
                'In Progress': 25,
                'Evidence Collection': 40,
                'Analysis Phase': 60,
                'Report Writing': 80,
                'Review Pending': 90,
                'Completed': 100,
                'Closed': 100
            };
            
            let progress = progress_map[frm.doc.investigation_status] || 0;
            frm.dashboard.add_progress(__('Investigation Progress'), progress, __(`${progress}% Complete`));
        }
    }
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