from incident_management_system.utils.action_item_automation import sweep_overdue_action_items
from incident_management_system.utils.arc_automation import run_daily_arc_automation, sweep_capa_overdue_task


def daily():
    sweep_overdue_action_items()
    run_daily_arc_automation()


def sweep_capa_overdue():
    """Scheduled task: mark overdue CAPAs and notify owners."""
    sweep_capa_overdue_task()
