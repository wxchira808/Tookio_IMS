app_name = "incident_management_system"
app_title = "Tookio ARC"
app_publisher = "Brian Wachira"
app_description = "Enterprise incident, audit, risk, and compliance command suite for risk registers, KRIs, compliance obligations, audits, CAPA, investigations, and executive oversight."
app_email = "bwkinyua01@gmail.com"
app_license = "mit"




fixtures = [
    {
        "dt": "Custom DocPerm"
    },
    { "dt": "Role" },
    { "dt": "Role Profile" },
    {"dt": "Client Script"},
    {"dt": "Server Script"}
]


doc_events = {
    "ToDo": {
        "on_update": "incident_management_system.utils.assign_to_override.assign_to_override"
    },
    "Incident Resolution": {
        "on_submit": "incident_management_system.utils.knowledge_automation.create_lesson_from_resolution"
    },
    "IMS Risk Register": {
        "on_update": "incident_management_system.utils.arc_automation.on_risk_register_update"
    },
    "IMS CAPA": {
        "validate": "incident_management_system.utils.arc_automation.on_capa_validate"
    },
}

scheduler_events = {
    "daily": [
        "incident_management_system.tasks.daily",
        "incident_management_system.tasks.sweep_capa_overdue",
    ]
}

# Whitelisted API methods (callable from client-side or external scripts)
override_whitelisted_methods = {
    # Local AI Service (Ollama - data sovereignty compliant)
    "incident_management_system.utils.local_ai_service.identify_risks_from_text": "incident_management_system.utils.local_ai_service.identify_risks_from_text",
    "incident_management_system.utils.local_ai_service.generate_executive_summary": "incident_management_system.utils.local_ai_service.generate_executive_summary",
    "incident_management_system.utils.local_ai_service.generate_risk_narrative": "incident_management_system.utils.local_ai_service.generate_risk_narrative",
    "incident_management_system.utils.local_ai_service.generate_audit_finding_narrative": "incident_management_system.utils.local_ai_service.generate_audit_finding_narrative",
    "incident_management_system.utils.local_ai_service.classify_compliance_obligation": "incident_management_system.utils.local_ai_service.classify_compliance_obligation",
    # Risk ML Service (Monte Carlo & scikit-learn)
    "incident_management_system.utils.risk_ml_service.run_monte_carlo_simulation": "incident_management_system.utils.risk_ml_service.run_monte_carlo_simulation",
    "incident_management_system.utils.risk_ml_service.run_portfolio_simulation": "incident_management_system.utils.risk_ml_service.run_portfolio_simulation",
    "incident_management_system.utils.risk_ml_service.get_risk_probability_summary": "incident_management_system.utils.risk_ml_service.get_risk_probability_summary",
    # ARC Reporting API
    "incident_management_system.api.arc_reporting.get_arc_dashboard_summary": "incident_management_system.api.arc_reporting.get_arc_dashboard_summary",
    "incident_management_system.api.arc_reporting.nlq_arc_query": "incident_management_system.api.arc_reporting.nlq_arc_query",
    "incident_management_system.api.arc_reporting.get_department_maturity_trend": "incident_management_system.api.arc_reporting.get_department_maturity_trend",
    "incident_management_system.api.arc_reporting.get_risk_heatmap_data": "incident_management_system.api.arc_reporting.get_risk_heatmap_data",
    "incident_management_system.api.arc_reporting.get_audit_findings_summary": "incident_management_system.api.arc_reporting.get_audit_findings_summary",
}

app_include_css = "/assets/incident_management_system/css/incident_management_system.css"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "incident_management_system",
		"title": "Tookio ARC",
		"route": "/app/tookio-ims",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/incident_management_system/css/incident_management_system.css"
# app_include_js = "/assets/incident_management_system/js/incident_management_system.js"

# include js, css files in header of web template
# web_include_css = "/assets/incident_management_system/css/incident_management_system.css"
# web_include_js = "/assets/incident_management_system/js/incident_management_system.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "incident_management_system/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "incident_management_system/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "incident_management_system.utils.jinja_methods",
# 	"filters": "incident_management_system.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "incident_management_system.install.before_install"
# after_install = "incident_management_system.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "incident_management_system.uninstall.before_uninstall"
# after_uninstall = "incident_management_system.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "incident_management_system.utils.before_app_install"
# after_app_install = "incident_management_system.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "incident_management_system.utils.before_app_uninstall"
# after_app_uninstall = "incident_management_system.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "incident_management_system.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"incident_management_system.tasks.all"
# 	],
# 	"daily": [
# 		"incident_management_system.tasks.daily"
# 	],
# 	"hourly": [
# 		"incident_management_system.tasks.hourly"
# 	],
# 	"weekly": [
# 		"incident_management_system.tasks.weekly"
# 	],
# 	"monthly": [
# 		"incident_management_system.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "incident_management_system.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "incident_management_system.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "incident_management_system.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["incident_management_system.utils.before_request"]
# after_request = ["incident_management_system.utils.after_request"]

# Job Events
# ----------
# before_job = ["incident_management_system.utils.before_job"]
# after_job = ["incident_management_system.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"incident_management_system.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }




#doc_events = {
 #   "ToDo": {
  #      "after_insert": "incident_management_system.config.to_do_override.todo_after_insert"
   # }
#}
