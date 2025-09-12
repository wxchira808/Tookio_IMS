// Copyright (c) 2025, Brian Wachira and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Incident Investigation", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on('Incident Investigation', {
    after_save: function(frm) {
        // Update parent incident status to "Investigation"
        if(frm.doc.incident) {
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: 'Incident',
                    name: frm.doc.incident,
                    fieldname: 'status',
                    value: 'Investigation'
                }
            });
        }
    }
});