"""Descarts i uplinks: què arriba i què es rebutja. Només per a administradors."""

from nicegui import ui

from gui import client
from gui.layout import format_moment, profile

DISCARD_COLUMNS = [
    {"name": "received_at", "label": "Rebut", "field": "received_at", "sortable": True, "align": "left", "style": "width: 18%"},
    {"name": "topic", "label": "Topic", "field": "topic", "align": "left", "style": "width: 32%"},
    {"name": "source", "label": "Font", "field": "source", "align": "left", "style": "width: 15%"},
    {"name": "device_id", "label": "Dispositiu", "field": "device_id", "align": "left", "style": "width: 20%"},
    {"name": "reason", "label": "Motiu", "field": "reason", "sortable": True, "align": "left", "style": "width: 15%"},
]

UPLINK_COLUMNS = [
    {"name": "time", "label": "Instant", "field": "time", "sortable": True, "align": "left", "style": "width: 25%"},
    {"name": "received_at", "label": "Rebut", "field": "received_at", "align": "left", "style": "width: 25%"},
    {"name": "source", "label": "Font", "field": "source", "align": "left", "style": "width: 20%"},
    {"name": "device_id", "label": "Dispositiu", "field": "device_id", "align": "left", "style": "width: 30%"},
]

TABLE_PROPS = 'flat table-header-class="bg-primary text-white"'


async def content() -> None:
    me = profile()
    if me is None:
        return

    if me["role"] != "admin":
        ui.label("Aquesta pàgina és només per a administradors.").classes("m-4")
        return

    async def load() -> None:
        answers = await client.gather(["/discards?limit=200", "/uplinks?limit=200"])

        discards.rows = [
            d | {"received_at": format_moment(d["received_at"])}
            for d in (answers[0] or [])
        ]
        uplinks.rows = [
            u
            | {
                "time": format_moment(u["time"]),
                "received_at": format_moment(u["received_at"]),
            }
            for u in (answers[1] or [])
        ]
        discards.update()
        uplinks.update()

    def show_discard(row: dict) -> None:
        """El detall porta el payload cru, que és el que serveix per a diagnosticar."""
        try:
            detail = client.get(f"/discards/{row['id']}")
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        with ui.dialog() as dialog, ui.card().classes("w-[40rem]"):
            ui.label(detail["reason"]).classes("text-lg")
            ui.label(detail["topic"]).classes("text-grey text-sm")
            ui.code(detail["raw_payload"]).classes("w-full")
            if detail["detail"]:
                ui.code(str(detail["detail"])).classes("w-full")
            with ui.row().classes("w-full justify-end"):
                ui.button("Tancar", on_click=dialog.close).props("flat")

        dialog.open()

    def show_uplink(row: dict) -> None:
        with ui.dialog() as dialog, ui.card().classes("w-[40rem]"):
            ui.label(f"{row['source']} / {row['device_id']}").classes("text-lg")
            ui.label(row["time"]).classes("text-grey text-sm")
            ui.code(str(row["uplink_metadata"])).classes("w-full")
            with ui.row().classes("w-full justify-end"):
                ui.button("Tancar", on_click=dialog.close).props("flat")

        dialog.open()

    with ui.row().classes("items-center mx-6 mt-4 gap-3"):
        ui.button("Refrescar", icon="refresh", on_click=load).props("flat dense")

    with ui.tabs().classes("w-full") as tabs:
        ui.tab("Descarts")
        ui.tab("Uplinks")

    with ui.tab_panels(tabs, value="Descarts").classes("w-full p-0"):
        with ui.tab_panel("Descarts").classes("p-0"):
            with ui.card().classes("w-full mt-4 p-0 overflow-hidden"):
                discards = ui.table(
                    columns=DISCARD_COLUMNS, rows=[], row_key="id"
                ).classes("w-full").props(TABLE_PROPS)
                discards.on("rowClick", lambda event: show_discard(event.args[1]))

        with ui.tab_panel("Uplinks").classes("p-0"):
            with ui.card().classes("w-full mt-4 p-0 overflow-hidden"):
                uplinks = ui.table(
                    columns=UPLINK_COLUMNS, rows=[], row_key="id"
                ).classes("w-full").props(TABLE_PROPS)
                uplinks.on("rowClick", lambda event: show_uplink(event.args[1]))

    await load()