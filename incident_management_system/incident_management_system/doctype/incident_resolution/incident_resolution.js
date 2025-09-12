// Copyright (c) 2025, Brian Wachira and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Incident Resolution", {
// 	refresh(frm) {

// 	},
// });
// 
frappe.ui.form.on('Incident Resolution', {
    incident: function(frm) {
        if(frm.doc.incident) {
            frappe.db.get_value('Incident', frm.doc.incident, 'investigation_id')
                .then(r => {
                    if(!r.message.investigation_id) {
                        frappe.msgprint(__('Cannot create Resolution without an Investigation. Please create an Investigation first.'));
                        frm.set_value('incident', '');
                    }
                });
        }
    },
    
    validate: function(frm) {
        if(frm.doc.incident) {
            frappe.db.get_value('Incident', frm.doc.incident, 'investigation_id')
                .then(r => {
                    if(!r.message.investigation_id) {
                        frappe.throw(__('Cannot save Resolution without an Investigation. Please create an Investigation first.'));
                    }
                });
        }
    },

    after_submit: function(frm) {
        // Update parent incident status to Resolved
        if(frm.doc.incident) {
            frappe.db.set_value('Incident', frm.doc.incident, {
                'status': 'Resolved',
                'resolution_id': frm.doc.name
            });
        }
    }
});