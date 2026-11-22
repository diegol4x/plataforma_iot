"""Gestió de grups de treball, membres i dispositius."""

from nicegui import ui

from gui import client
from gui.layout import profile

COLUMNS = [
    {"name": "name", "label": "Nom", "field": "name", "sortable": True, "align": "left", "style": "width: 25%"},
    {"name": "description", "label": "Descripció", "field": "description", "align": "left", "style": "width: 35%"},
    {"name": "members", "label": "Membres", "field": "member_count", "sortable": True, "align": "left", "style": "width: 15%"},
    {"name": "devices", "label": "Dispositius", "field": "device_count", "sortable": True, "align": "left", "style": "width: 15%"},
    {"name": "actions", "label": "", "field": "actions", "align": "right", "style": "width: 10%"},
]

ACTIONS_SLOT = """
<q-td :props="props">
    <q-btn flat dense icon="edit" @click="() => $parent.$emit('edit', props.row)" />
</q-td>
"""


def content() -> None:
    if profile() is None:
        return

    def load() -> None:
        try:
            table.rows = client.get("/workgroups")
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        table.selected = []
        table.update()
        _refresh_delete()

    def _refresh_delete() -> None:
        """El botó d'esborrar només s'activa amb alguna fila marcada."""
        delete_button.set_enabled(bool(table.selected))

    def create() -> None:
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Nou grup").classes("text-lg")

            name = ui.input("Nom").classes("w-full")
            description = ui.input("Descripció").classes("w-full")

            def confirm() -> None:
                submit.disable()
                try:
                    client.post(
                        "/workgroups",
                        {"name": name.value, "description": description.value or None},
                    )
                    dialog.close()
                    ui.notify("Grup creat")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")
                    submit.enable()

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                submit = ui.button("Crear", on_click=confirm)

            dialog.on("hide", load)

        dialog.open()

    def remove_selected() -> None:
        chosen = list(table.selected)

        with ui.dialog() as dialog, ui.card():
            ui.label(
                f"Esborrar {len(chosen)} grup(s)? Els que tinguen projectes no "
                "es podran esborrar."
            )

            def confirm() -> None:
                failed = []
                for group in chosen:
                    try:
                        client.delete(f"/workgroups/{group['id']}")
                    except client.ApiError as error:
                        failed.append(f"{group['name']}: {error.detail}")

                dialog.close()

                if failed:
                    ui.notify(" / ".join(failed), color="negative")
                else:
                    ui.notify("Grups esborrats")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                ui.button("Esborrar", on_click=confirm).props("color=negative")

            dialog.on("hide", load)

        dialog.open()

    def edit(group: dict) -> None:
        with ui.dialog() as dialog, ui.card().classes("w-[32rem]"):
            ui.label(group["name"]).classes("text-lg")

            with ui.tabs().classes("w-full") as tabs:
                ui.tab("Dades")
                ui.tab("Membres")
                ui.tab("Dispositius")

            with ui.tab_panels(tabs, value="Dades").classes("w-full"):
                with ui.tab_panel("Dades"):
                    name = ui.input("Nom", value=group["name"]).classes("w-full")
                    description = ui.input(
                        "Descripció", value=group["description"] or ""
                    ).classes("w-full")

                    def save() -> None:
                        try:
                            client.patch(
                                f"/workgroups/{group['id']}",
                                {
                                    "name": name.value,
                                    "description": description.value or None,
                                },
                            )
                            dialog.close()
                            ui.notify("Grup actualitzat")
                        except client.ApiError as error:
                            ui.notify(error.detail, color="negative")

                    with ui.row().classes("w-full justify-end mt-4"):
                        ui.button("Guardar", on_click=save)

                with ui.tab_panel("Membres"):
                    ui.label(
                        "Qui està en el grup veu tots els seus projectes i "
                        "dispositius."
                    ).classes("text-xs text-grey mb-2")
                    members = ui.column().classes("w-full")
                    _refresh_members(group["id"], members)

                with ui.tab_panel("Dispositius"):
                    devices = ui.column().classes("w-full")
                    _refresh_devices(group["id"], devices)

            dialog.on("hide", load)

        dialog.open()

    with ui.row().classes("items-center mx-6 mt-4 gap-3"):
        ui.button("Nou grup", on_click=create)
        delete_button = ui.button(
            "Esborrar", icon="delete", on_click=remove_selected
        ).props("flat dense color=negative")
        delete_button.set_enabled(False)

    with ui.card().classes("w-full mt-4 p-0 overflow-hidden"):
        table = ui.table(
            columns=COLUMNS, rows=[], row_key="id", selection="multiple"
        ).classes("w-full").props('flat table-header-class="bg-primary text-white"')

        table.add_slot("body-cell-actions", ACTIONS_SLOT)
        table.on("edit", lambda event: edit(event.args))
        table.on("selection", _refresh_delete)

    load()


def _refresh_members(group_id: int, container) -> None:
    """Llista els membres del grup amb els botons per a afegir-ne i traure'n."""
    container.clear()

    try:
        members = client.get(f"/workgroups/{group_id}/members")
        users = client.get("/users")
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")
        return

    current = {u["id"] for u in members}

    with container:
        if not members:
            ui.label("Cap membre").classes("text-grey")

        for member in members:
            with ui.row().classes("w-full items-center gap-2"):
                ui.label(member["username"])
                ui.label(f"({member['role']})").classes("text-xs text-grey")
                ui.space()
                ui.button(
                    icon="close",
                    on_click=lambda m=member: _remove_member(
                        group_id, m["id"], container
                    ),
                ).props("flat dense")

        available = {u["id"]: u["username"] for u in users if u["id"] not in current}

        if available:
            ui.separator().classes("my-2")
            with ui.row().classes("w-full items-center gap-2"):
                choice = ui.select(available, label="Usuari").classes("flex-grow")
                ui.button(
                    "Afegir",
                    on_click=lambda: _add_member(group_id, choice.value, container),
                ).props("outline dense")


def _add_member(group_id: int, user_id: int | None, container) -> None:
    if user_id is None:
        return

    try:
        client.put(f"/workgroups/{group_id}/members/{user_id}")
        _refresh_members(group_id, container)
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")


def _remove_member(group_id: int, user_id: int, container) -> None:
    try:
        client.delete(f"/workgroups/{group_id}/members/{user_id}")
        _refresh_members(group_id, container)
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")


def _refresh_devices(group_id: int, container) -> None:
    """Llista els dispositius del grup, amb els mateixos botons que els membres."""
    container.clear()

    try:
        assigned = client.get(f"/workgroups/{group_id}/devices")
        every = client.get("/devices", limit=200)
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")
        return

    current = {(d["source"], d["device_id"]) for d in assigned}

    with container:
        if not assigned:
            ui.label("Cap dispositiu").classes("text-grey")

        for device in assigned:
            with ui.row().classes("w-full items-center gap-2"):
                ui.label(f"{device['source']} / {device['device_id']}").classes(
                    "font-mono text-sm"
                )
                ui.space()
                ui.button(
                    icon="close",
                    on_click=lambda d=device: _remove_device(group_id, d, container),
                ).props("flat dense")

        available = {
            f"{d['source']}/{d['device_id']}": f"{d['source']} / {d['device_id']}"
            for d in every
            if (d["source"], d["device_id"]) not in current
        }

        if available:
            ui.separator().classes("my-2")
            with ui.row().classes("w-full items-center gap-2"):
                choice = ui.select(available, label="Dispositiu").classes("flex-grow")
                ui.button(
                    "Afegir",
                    on_click=lambda: _add_device(group_id, choice.value, container),
                ).props("outline dense")


def _add_device(group_id: int, identity: str | None, container) -> None:
    if identity is None:
        return

    try:
        client.put(f"/workgroups/{group_id}/devices/{identity}")
        _refresh_devices(group_id, container)
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")


def _remove_device(group_id: int, device: dict, container) -> None:
    try:
        client.delete(
            f"/workgroups/{group_id}/devices/{device['source']}/{device['device_id']}"
        )
        _refresh_devices(group_id, container)
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")