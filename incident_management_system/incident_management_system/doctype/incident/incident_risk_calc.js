frappe.ui.form.on('Incident', {
    likelihood_score: function(frm) {
        calculate_risk_score(frm);
    },
    
    impact_score: function(frm) {
        calculate_risk_score(frm);
    }
});

function calculate_risk_score(frm) {
    // Extract numeric values from the select options
    var likelihood = parseInt(frm.doc.likelihood_score ? frm.doc.likelihood_score.split(' ')[0] : 0);
    var impact = parseInt(frm.doc.impact_score ? frm.doc.impact_score.split(' ')[0] : 0);
    
    if (likelihood && impact) {
        var risk_score = likelihood * impact;
        frm.set_value('risk_score', risk_score);
    }
}
