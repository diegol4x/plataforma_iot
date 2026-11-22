"""Llistat i provisionament de dispositius."""

from nicegui import ui

from gui import client
from gui.layout import format_moment, profile

COLUMNS = [
    {"name": "source", "label": "Font", "field": "source", "sortable": True, "align": "left", "style": "width: 10%"},
    {"name": "device_id", "label": "Identificador", "field": "device_id", "sortable": True, "align": "left", "style": "width: 18%"},
    {"name": "name", "label": "Nom", "field": "name", "align": "left", "style": "width: 16%"},
    {"name": "type", "label": "Tipus", "field": "type", "align": "left", "style": "width: 10%"},
    {"name": "status", "label": "Estat", "field": "status", "sortable": True, "align": "left", "style": "width: 13%"},
    {"name": "battery_level", "label": "Bateria", "field": "battery_level", "sortable": True, "align": "left", "style": "width: 8%"},
    {"name": "last_seen", "label": "Vist per últim cop", "field": "last_seen", "sortable": True, "align": "left", "style": "width: 15%"},
    {"name": "actions", "label": "", "field": "actions", "align": "right", "style": "width: 10%"},
]

STATE_OPTIONS = {
    "": "Tots",
    "unprovisioned": "Sense provisionar",
    "active": "Actiu",
    "silent": "Silenciós",
    "retired": "Retirat",
}

STATUS_SLOT = '<q-td :props="props">{{ props.row.status_label }}</q-td>'

ACTIONS_SLOT = """
<q-td :props="props">
    <q-btn v-if="props.row.status === 'unprovisioned'" flat dense icon="add_task"
           color="primary" @click="() => $parent.$emit('provision', props.row)">
        <q-tooltip>Provisionar</q-tooltip>
    </q-btn>
    <q-btn v-else flat dense icon="edit"
           @click="() => $parent.$emit('edit', props.row)">
        <q-tooltip>Modificar</q-tooltip>
    </q-btn>
    <q-btn v-if="['active', 'silent'].includes(props.row.status)" flat dense
           icon="block" color="negative"
           @click="() => $parent.$emit('retire', props.row)">
        <q-tooltip>Retirar</q-tooltip>
    </q-btn>
</q-td>
"""

BATTERY_SLOT = """
<q-td :props="props"
      :class="props.row.battery_level != null && props.row.battery_level < 20 ? 'text-negative' : ''">
    {{ props.row.battery_level == null ? '-' : props.row.battery_level + ' %' }}
</q-td>
"""


async def content() -> None:
    me = profile()
    if me is None:
        return

    is_admin = me["role"] == "admin"
    originals: dict = {}

    def load() -> None:
        try:
            devices = client.get("/devices", status=state.value or None, limit=200)
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        originals.clear()
        originals.update({(d["source"], d["device_id"]): d for d in devices})

        table.rows = [
            d
            | {
                "key": f"{d['source']}/{d['device_id']}",
                "status_label": STATE_OPTIONS.get(d["status"], d["status"]),
                "last_seen": format_moment(d["last_seen"]),
            }
            for d in devices
        ]
        table.update()

    def _patch(device: dict, payload: dict, message: str) -> bool:
        try:
            client.patch(f"/devices/{device['source']}/{device['device_id']}", payload)
            load()
            ui.notify(message)
            return True
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return False

    def provision(row: dict) -> None:
        """L'alta d'un dispositiu descobert: li posa nom i el deixa actiu."""
        device = originals[(row["source"], row["device_id"])]

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Provisionar dispositiu").classes("text-lg")
            ui.label(f"{device['source']} / {device['device_id']}").classes(
                "font-mono text-sm text-grey"
            )

            name = ui.input("Nom").classes("w-full")
            kind = ui.input("Tipus").classes("w-full")
            ui.label(
                "En provisionar-lo passa a actiu i les seues dades deixen de ser "
                "d'un aparell sense reclamar."
            ).classes("text-xs text-grey")

            def confirm() -> None:
                if not name.value:
                    ui.notify("Cal posar-li un nom", color="warning")
                    return

                submit.disable()
                if _patch(
                    device,
                    {"name": name.value, "type": kind.value or None},
                    "Dispositiu provisionat",
                ):
                    dialog.close()
                else:
                    submit.enable()

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                submit = ui.button("Provisionar", on_click=confirm)

        dialog.open()

    def edit(row: dict) -> None:
        device = originals[(row["source"], row["device_id"])]

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label(f"{device['source']} / {device['device_id']}").classes("text-lg")

            name = ui.input("Nom", value=device["name"] or "").classes("w-full")
            kind = ui.input("Tipus", value=device["type"] or "").classes("w-full")

            def save() -> None:
                if _patch(
                    device,
                    {"name": name.value, "type": kind.value or None},
                    "Dispositiu actualitzat",
                ):
                    dialog.close()

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                ui.button("Guardar", on_click=save)

        dialog.open()

    def retire(row: dict) -> None:
        device = originals[(row["source"], row["device_id"])]

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Retirar dispositiu").classes("text-lg")
            ui.label(f"{device['source']} / {device['device_id']}").classes(
                "font-mono text-sm text-grey"
            )
            ui.label(
                "La retirada no té tornada: si el dispositiu torna a servici, "
                "caldrà provisionar-lo de nou. Les seues lectures es conserven."
            ).classes("text-sm mt-2")

            def confirm() -> None:
                if _patch(
                    device,
                    {"name": device["name"], "status": "retired"},
                    "Dispositiu retirat",
                ):
                    dialog.close()

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                ui.button("Retirar", on_click=confirm).props("color=negative")

        dialog.open()

    with ui.row().classes("items-end mx-6 mt-4 gap-4"):
        state = ui.select(STATE_OPTIONS, value="").props(
            'dense outlined placeholder="Estat"'
        ).classes("w-56").on_value_change(lambda: load())
        ui.button("Refrescar", icon="refresh", on_click=load).props("flat dense")

    with ui.card().classes("w-full mt-4 p-0 overflow-hidden"):
        table = ui.table(columns=COLUMNS, rows=[], row_key="key").classes(
            "w-full"
        ).props('flat table-header-class="bg-primary text-white"')

        table.add_slot("body-cell-status", STATUS_SLOT)
        table.add_slot("body-cell-battery_level", BATTERY_SLOT)

        if is_admin:
            table.add_slot("body-cell-actions", ACTIONS_SLOT)
            table.on("provision", lambda event: provision(event.args))
            table.on("edit", lambda event: edit(event.args))
            table.on("retire", lambda event: retire(event.args))

    load()