import json
from pathlib import Path

import frappe


WORKSPACE_SLUGS = [
    "tookio_ims",
    "incident_management",
    "audit",
    "compliance",
    "risk",
    "arc_command_center",
]

DESKTOP_ICONS = [
    {
        "label": "Tookio IMS",
        "link_to": "",
        "parent_icon": "",
        "idx": 1,
        "icon": "shield-check",
        "icon_type": "Folder",
    },
    {
        "label": "Incident Management",
        "link_to": "Incident Management",
        "parent_icon": "Tookio IMS",
        "idx": 1,
        "icon": "badge-alert",
        "icon_type": "Link",
    },
    {
        "label": "Audit",
        "link_to": "Audit",
        "parent_icon": "Tookio IMS",
        "idx": 2,
        "icon": "clipboard-check",
        "icon_type": "Link",
    },
    {
        "label": "Compliance",
        "link_to": "Compliance",
        "parent_icon": "Tookio IMS",
        "idx": 3,
        "icon": "scroll-text",
        "icon_type": "Link",
    },
    {
        "label": "Risk",
        "link_to": "Risk",
        "parent_icon": "Tookio IMS",
        "idx": 4,
        "icon": "shield-alert",
        "icon_type": "Link",
    },
    {
        "label": "ARC Command Center",
        "link_to": "ARC Command Center",
        "parent_icon": "Tookio IMS",
        "idx": 5,
        "icon": "layout-dashboard",
        "icon_type": "Link",
    },
]

WORKSPACE_SIDEBARS = [
    {
        "name": "Tookio IMS",
        "workspace": "Tookio IMS",
        "header_icon": "shield-check",
    },
    {
        "name": "Incident Management",
        "workspace": "Incident Management",
        "header_icon": "badge-alert",
    },
    {
        "name": "Audit",
        "workspace": "Audit",
        "header_icon": "clipboard-check",
    },
    {
        "name": "Compliance",
        "workspace": "Compliance",
        "header_icon": "scroll-text",
    },
    {
        "name": "Risk",
        "workspace": "Risk",
        "header_icon": "shield-alert",
    },
    {
        "name": "ARC Command Center",
        "workspace": "ARC Command Center",
        "header_icon": "layout-dashboard",
    },
]

ROOT_WORKSPACE = "Tookio IMS"

MODULE_WORKSPACES = [
    "Incident Management",
    "Audit",
    "Compliance",
    "Risk",
    "ARC Command Center",
]


def _workspace_json_path(slug: str) -> Path:
    return Path(
        frappe.get_app_path(
            "incident_management_system",
            "incident_management_system",
            "workspace",
            slug,
            f"{slug}.json",
        )
    )


def _load_workspace_payload(slug: str) -> dict:
    with _workspace_json_path(slug).open("r", encoding="utf-8") as f:
        return json.load(f)


def _sync_workspace(payload: dict) -> None:
    name = payload["name"]
    existing = frappe.db.exists("Workspace", name)

    if existing:
        doc = frappe.get_doc("Workspace", name)
    else:
        doc = frappe.new_doc("Workspace")
        doc.name = name

    # Update scalar fields first.
    scalar_fields = [
        "app",
        "module",
        "label",
        "title",
        "icon",
        "content",
        "public",
        "is_hidden",
        "hide_custom",
        "for_user",
        "sequence_id",
        "indicator_color",
        "parent_page",
        "restrict_to_domain",
        "type",
    ]

    for fieldname in scalar_fields:
        if fieldname in payload:
            doc.set(fieldname, payload.get(fieldname))

    # Replace child tables so workspace sidebar/cards are exactly as defined in JSON.
    for table_field in ("links", "roles", "shortcuts", "charts", "number_cards", "quick_lists", "custom_blocks"):
        doc.set(table_field, [])
        for row in payload.get(table_field, []) or []:
            doc.append(table_field, row)

    if existing:
        doc.flags.ignore_mandatory = True
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)


def _get_desktop_icon(label: str, parent_icon: str):
    filters = {"label": label}
    if parent_icon:
        filters["parent_icon"] = parent_icon
        names = frappe.get_all("Desktop Icon", filters=filters, pluck="name", limit=1)
    else:
        names = frappe.get_all(
            "Desktop Icon",
            filters={"label": label, "parent_icon": ["in", ["", None]]},
            pluck="name",
            limit=1,
        )

    return names[0] if names else None


def _sync_desktop_icons() -> None:
    for icon in DESKTOP_ICONS:
        existing_name = frappe.db.exists("Desktop Icon", icon["label"]) or _get_desktop_icon(
            icon["label"], icon["parent_icon"]
        )

        if existing_name:
            doc = frappe.get_doc("Desktop Icon", existing_name)
        else:
            doc = frappe.new_doc("Desktop Icon")

        doc.label = icon["label"]
        doc.link_type = "Workspace Sidebar"
        doc.link_to = icon["link_to"]
        doc.parent_icon = icon["parent_icon"]
        doc.icon = icon["icon"]
        doc.icon_type = icon["icon_type"]
        doc.logo_url = ""
        doc.icon_image = ""
        doc.app = "incident_management_system"
        doc.standard = 1
        doc.hidden = 0
        doc.idx = icon["idx"]

        if existing_name:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)


def _sync_workspace_sidebars() -> None:
    payload_by_name = {}
    for slug in WORKSPACE_SLUGS:
        payload = _load_workspace_payload(slug)
        payload_by_name[payload["name"]] = payload

    for sidebar in WORKSPACE_SIDEBARS:
        existing = frappe.db.exists("Workspace Sidebar", sidebar["name"])
        if existing:
            doc = frappe.get_doc("Workspace Sidebar", sidebar["name"])
        else:
            doc = frappe.new_doc("Workspace Sidebar")
            doc.name = sidebar["name"]

        doc.title = sidebar["name"]
        doc.header_icon = sidebar["header_icon"]
        doc.for_user = ""
        doc.module = "Incident Management System"
        doc.standard = 1
        doc.app = "incident_management_system"

        doc.set("items", _build_sidebar_items(sidebar["workspace"], payload_by_name))

        if existing:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)


def _build_sidebar_items(workspace_name: str, payload_by_name: dict[str, dict]) -> list[dict]:
    items = [
        {
            "label": "Home",
            "type": "Link",
            "link_type": "Workspace",
            "link_to": workspace_name,
            "icon": "home",
            "child": 0,
            "indent": 0,
            "collapsible": 1,
            "keep_closed": 0,
            "show_arrow": 0,
        }
    ]

    if workspace_name == ROOT_WORKSPACE:
        items.append(
            {
                "label": "Modules",
                "type": "Section Break",
                "link_type": "Workspace",
                "icon": "list",
                "child": 0,
                "indent": 1,
                "collapsible": 1,
                "keep_closed": 0,
                "show_arrow": 0,
            }
        )
        for module_ws in MODULE_WORKSPACES:
            items.append(
                {
                    "label": module_ws,
                    "type": "Link",
                    "link_type": "Workspace",
                    "link_to": module_ws,
                    "child": 1,
                    "indent": 0,
                    "collapsible": 1,
                    "keep_closed": 0,
                    "show_arrow": 0,
                }
            )
        return items

    payload = payload_by_name.get(workspace_name, {})
    in_section = False

    doctype_navigable_cache: dict[str, bool] = {}

    for row in payload.get("links", []) or []:
        row_type = row.get("type")
        if row_type == "Card Break":
            items.append(
                {
                    "label": row.get("label") or "Section",
                    "type": "Section Break",
                    "link_type": row.get("link_type") or "DocType",
                    "icon": "list",
                    "child": 0,
                    "indent": 1,
                    "collapsible": 1,
                    "keep_closed": 0,
                    "show_arrow": 0,
                }
            )
            in_section = True
            continue

        if row_type != "Link":
            continue

        if not row.get("link_to") and row.get("link_type") != "Workspace":
            continue

        if row.get("link_type") == "DocType" and not _is_navigable_doctype(
            row.get("link_to"), doctype_navigable_cache
        ):
            continue

        items.append(
            {
                "label": row.get("label") or row.get("link_to"),
                "type": "Link",
                "link_type": row.get("link_type") or "DocType",
                "link_to": row.get("link_to"),
                "child": 1 if in_section else 0,
                "indent": 0,
                "collapsible": 1,
                "keep_closed": 0,
                "show_arrow": 0,
            }
        )

    return items


def _is_navigable_doctype(doctype_name: str | None, cache: dict[str, bool]) -> bool:
    if not doctype_name:
        return False

    if doctype_name in cache:
        return cache[doctype_name]

    meta = frappe.db.get_value("DocType", doctype_name, ["name", "istable"], as_dict=True)
    navigable = bool(meta and not int(meta.get("istable") or 0))
    cache[doctype_name] = navigable
    return navigable


def execute():
    for slug in WORKSPACE_SLUGS:
        payload = _load_workspace_payload(slug)
        _sync_workspace(payload)

    _sync_workspace_sidebars()
    _sync_desktop_icons()

    frappe.clear_cache(doctype="Workspace")
    frappe.clear_cache(doctype="Workspace Sidebar")
    frappe.clear_cache(doctype="Desktop Icon")
