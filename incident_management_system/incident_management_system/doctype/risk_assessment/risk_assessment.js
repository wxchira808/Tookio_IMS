// Copyright (c) 2025, Brian Wachira and contributors
// For license information, please see license.txt

frappe.ui.form.on("Risk Assessment", {
	refresh(frm) {
		frm.set_query("risk_taxonomy", () => {
			return {
				filters: {
					is_active: 1
				}
			};
		});

		frm.set_query("ims_risk_register", () => {
			const filters = {};
			if (frm.doc.risk_taxonomy) {
				filters.risk_taxonomy = frm.doc.risk_taxonomy;
			}

			return { filters };
		});
	},

	likelihood(frm) {
		update_risk_score_preview(frm);
	},

	impact_severity(frm) {
		update_risk_score_preview(frm);
	}
});

function update_risk_score_preview(frm) {
	const likelihood = parseScaleValue(frm.doc.likelihood);
	const impact = parseScaleValue(frm.doc.impact_severity);

	if (!likelihood || !impact) {
		return;
	}

	const score = likelihood * impact;
	frm.set_value("risk_score", score);
}

function parseScaleValue(rawValue) {
	if (!rawValue) {
		return null;
	}

	const token = String(rawValue).trim().split(" ", 1)[0];
	if (/^\d+$/.test(token)) {
		return Number(token);
	}

	return null;
}
