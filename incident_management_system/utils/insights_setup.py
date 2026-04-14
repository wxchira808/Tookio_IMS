import frappe


WORKBOOK_TITLE = "Tookio IMS Executive Analytics"


def _source_op(table_name: str) -> dict:
    return {
        "type": "source",
        "table": {
            "type": "table",
            "data_source": "Site DB",
            "table_name": table_name,
        },
    }


def _measure_count_name(label: str = "count_of_records") -> dict:
    return {
        "aggregation": "count",
        "column_name": "name",
        "data_type": "String",
        "label": label,
        "measure_name": label,
        "value": label,
    }


def _dimension(column_name: str, data_type: str = "String", granularity: str | None = None) -> dict:
    d = {
        "column_name": column_name,
        "data_type": data_type,
        "dimension_name": column_name,
        "label": column_name,
        "value": column_name,
    }
    if granularity:
        d["granularity"] = granularity
    return d


def _chart_bar_by_month(title: str, query: str, date_col: str, measure_col: str = "name") -> dict:
    return {
        "name": f"ch_{title.lower().replace(' ', '_')}",
        "title": title,
        "workbook": "ims_workbook",
        "query": query,
        "chart_type": "Bar",
        "config": {
            "filters": {"filters": [], "logical_operator": "And"},
            "grouping": "grouped",
            "limit": 100,
            "normalize": False,
            "order_by": [{"column": {"column_name": date_col, "type": "column"}, "direction": "asc"}],
            "show_data_labels": False,
            "split_by": {"column_name": "", "data_type": "String", "dimension_name": ""},
            "stack": False,
            "swap_axes": False,
            "x_axis": {"dimension": _dimension(date_col, "Datetime", "month")},
            "y2_axis": None,
            "y2_axis_type": "line",
            "y_axis": {
                "normalize": False,
                "series": [
                    {
                        "measure": {
                            "aggregation": "count",
                            "column_name": measure_col,
                            "data_type": "String",
                            "label": "count_of_records",
                            "measure_name": "count_of_records",
                            "value": "count_of_records",
                        }
                    }
                ],
                "show_axis_label": False,
                "show_data_labels": False,
                "stack": False,
            },
        },
    }


def _chart_donut(title: str, query: str, label_col: str) -> dict:
    return {
        "name": f"ch_{title.lower().replace(' ', '_')}",
        "title": title,
        "workbook": "ims_workbook",
        "query": query,
        "chart_type": "Donut",
        "config": {
            "filters": {"filters": [], "logical_operator": "And"},
            "label_column": _dimension(label_col),
            "limit": 100,
            "order_by": [],
            "value_column": {
                "aggregation": "count",
                "column_name": "name",
                "data_type": "String",
                "measure_name": "count_of_records",
            },
        },
    }


def _chart_number(title: str, query: str, date_col: str, measures: list[dict]) -> dict:
    return {
        "name": f"ch_{title.lower().replace(' ', '_')}",
        "title": title,
        "workbook": "ims_workbook",
        "query": query,
        "chart_type": "Number",
        "config": {
            "comparison": True,
            "date_column": _dimension(date_col, "Datetime", "month"),
            "decimal": "2",
            "filters": {"filters": [], "logical_operator": "And"},
            "limit": 100,
            "negative_is_better": False,
            "number_columns": measures,
            "order_by": [{"column": {"column_name": date_col, "type": "column"}, "direction": "desc"}],
            "shorten_numbers": True,
            "sparkline": True,
        },
    }


def _chart_table(title: str, query: str, row_col: str, date_col: str) -> dict:
    return {
        "name": f"ch_{title.lower().replace(' ', '_')}",
        "title": title,
        "workbook": "ims_workbook",
        "query": query,
        "chart_type": "Table",
        "config": {
            "columns": [_dimension(date_col, "Datetime", "month")],
            "filters": {"filters": [], "logical_operator": "And"},
            "limit": 100,
            "order_by": [
                {"column": {"column_name": date_col, "type": "column"}, "direction": "asc"},
                {"column": {"column_name": row_col, "type": "column"}, "direction": "asc"},
            ],
            "rows": [_dimension(row_col)],
            "show_column_totals": False,
            "show_filter_row": True,
            "show_row_totals": False,
            "values": [{"aggregation": "count", "column_name": "name", "data_type": "String", "measure_name": "count_of_records"}],
        },
    }


def _dashboard(name: str, title: str, charts: list[str]) -> dict:
    y = 0
    items = []
    for i, chart in enumerate(charts):
        if i == 0:
            items.append({"type": "chart", "chart": chart, "layout": {"x": 0, "y": y, "w": 20, "h": 4, "i": f"{name}_{i}"}})
            y += 4
            continue
        if i % 2 == 1:
            items.append({"type": "chart", "chart": chart, "layout": {"x": 0, "y": y, "w": 10, "h": 8, "i": f"{name}_{i}"}})
        else:
            items.append({"type": "chart", "chart": chart, "layout": {"x": 10, "y": y, "w": 10, "h": 8, "i": f"{name}_{i}"}})
            y += 8

    return {
        "name": name,
        "title": title,
        "workbook": "ims_workbook",
        "items": items,
    }


@frappe.whitelist()
def create_ims_insights_workbook(replace_existing: int = 1) -> dict:
    if not frappe.db.exists("DocType", "Insights Workbook"):
        frappe.throw("Insights app is not installed on this site.")

    if not frappe.db.exists("Insights Data Source v3", "Site DB"):
        frappe.throw("Insights Site DB data source is missing. Open Insights once to finish setup.")

    if int(replace_existing):
        existing = frappe.get_all("Insights Workbook", filters={"title": WORKBOOK_TITLE}, pluck="name")
        for wb in existing:
            frappe.delete_doc("Insights Workbook", wb, force=True, ignore_permissions=True)

    queries = {
        "q_incidents": {
            "name": "q_incidents",
            "title": "IMS Incidents",
            "workbook": "ims_workbook",
            "use_live_connection": 1,
            "is_script_query": 0,
            "is_builder_query": 1,
            "is_native_query": 0,
            "operations": [_source_op("tabIncident")],
        },
        "q_audit_findings": {
            "name": "q_audit_findings",
            "title": "IMS Audit Findings",
            "workbook": "ims_workbook",
            "use_live_connection": 1,
            "is_script_query": 0,
            "is_builder_query": 1,
            "is_native_query": 0,
            "operations": [_source_op("tabIMS Audit Finding")],
        },
        "q_compliance": {
            "name": "q_compliance",
            "title": "IMS Compliance Register",
            "workbook": "ims_workbook",
            "use_live_connection": 1,
            "is_script_query": 0,
            "is_builder_query": 1,
            "is_native_query": 0,
            "operations": [_source_op("tabIMS Compliance Register")],
        },
        "q_risk": {
            "name": "q_risk",
            "title": "IMS Risk Register",
            "workbook": "ims_workbook",
            "use_live_connection": 1,
            "is_script_query": 0,
            "is_builder_query": 1,
            "is_native_query": 0,
            "operations": [_source_op("tabIMS Risk Register")],
        },
    }

    charts = {
        "ch_incident_kpi": _chart_number(
            "Incident KPI",
            "q_incidents",
            "creation",
            [
                _measure_count_name("incidents_count"),
                {
                    "aggregation": "avg",
                    "column_name": "risk_score",
                    "data_type": "Float",
                    "label": "avg_risk_score",
                    "measure_name": "avg_risk_score",
                    "value": "avg_risk_score",
                },
            ],
        ),
        "ch_incident_status": _chart_donut("Incident Status Distribution", "q_incidents", "status"),
        "ch_incident_severity": _chart_donut("Incident Severity Distribution", "q_incidents", "severity"),
        "ch_incident_monthly": _chart_bar_by_month("Incidents by Month", "q_incidents", "creation"),
        "ch_audit_kpi": _chart_number(
            "Audit KPI",
            "q_audit_findings",
            "creation",
            [_measure_count_name("findings_count")],
        ),
        "ch_audit_severity": _chart_donut("Audit Findings by Severity", "q_audit_findings", "severity"),
        "ch_audit_status": _chart_donut("Audit Findings by Status", "q_audit_findings", "status"),
        "ch_audit_monthly": _chart_bar_by_month("Audit Findings by Month", "q_audit_findings", "creation"),
        "ch_compliance_kpi": _chart_number(
            "Compliance KPI",
            "q_compliance",
            "creation",
            [_measure_count_name("obligations_count")],
        ),
        "ch_compliance_status": _chart_donut("Compliance Status Mix", "q_compliance", "compliance_status"),
        "ch_compliance_risk": _chart_donut("Compliance Risk Rating Mix", "q_compliance", "risk_rating"),
        "ch_compliance_framework": _chart_table("Framework Breakdown", "q_compliance", "standard_framework", "creation"),
        "ch_risk_kpi": _chart_number(
            "Risk KPI",
            "q_risk",
            "creation",
            [
                _measure_count_name("risks_count"),
                {
                    "aggregation": "avg",
                    "column_name": "residual_risk_score",
                    "data_type": "Float",
                    "label": "avg_residual_risk_score",
                    "measure_name": "avg_residual_risk_score",
                    "value": "avg_residual_risk_score",
                },
            ],
        ),
        "ch_risk_level": _chart_donut("Risk Level Distribution", "q_risk", "risk_level"),
        "ch_risk_status": _chart_donut("Risk Status Distribution", "q_risk", "status"),
        "ch_risk_monthly": _chart_bar_by_month("Risk Entries by Month", "q_risk", "creation"),
    }

    dashboards = {
        "db_incident": _dashboard(
            "db_incident",
            "Incident Management Dashboard",
            ["ch_incident_kpi", "ch_incident_status", "ch_incident_severity", "ch_incident_monthly"],
        ),
        "db_audit": _dashboard(
            "db_audit",
            "Audit Dashboard",
            ["ch_audit_kpi", "ch_audit_status", "ch_audit_severity", "ch_audit_monthly"],
        ),
        "db_compliance": _dashboard(
            "db_compliance",
            "Compliance Dashboard",
            ["ch_compliance_kpi", "ch_compliance_status", "ch_compliance_risk", "ch_compliance_framework"],
        ),
        "db_risk": _dashboard(
            "db_risk",
            "Risk Dashboard",
            ["ch_risk_kpi", "ch_risk_level", "ch_risk_status", "ch_risk_monthly"],
        ),
    }

    workbook_payload = {
        "version": "1.0",
        "timestamp": frappe.utils.now(),
        "type": "Workbook",
        "name": "ims_workbook",
        "doc": {"name": "ims_workbook", "title": WORKBOOK_TITLE},
        "dependencies": {
            "queries": queries,
            "charts": charts,
            "dashboards": dashboards,
        },
    }

    from insights.insights.doctype.insights_workbook.insights_workbook import import_workbook

    new_workbook = import_workbook(workbook_payload)
    frappe.db.commit()

    created_dashboards = frappe.get_all(
        "Insights Dashboard v3",
        filters={"workbook": new_workbook},
        fields=["name", "title"],
        order_by="creation asc",
    )

    return {
        "ok": True,
        "workbook": new_workbook,
        "title": WORKBOOK_TITLE,
        "dashboard_count": len(created_dashboards),
        "dashboards": created_dashboards,
    }