"""Gestió de projectes."""

from nicegui import ui

from gui import client
from gui.layout import profile

COLUMNS = [
    {"name": "name", "label": "Nom", "field": "name", "sortable": True, "align": "left", "style": "width: 30%"},
    {"name": "description", "label": "Descripció", "field": "description", "align": "left", "style": "width: 35%"},
    {"name": "workgroup", "label": "Grup", "field": "workgroup_name", "sortable": True, "align": "left", "style": "width: 13%"},
    {"name": "owner", "label": "Propietari", "field": "owner_name", "sortable": True, "align": "left", "style": "width: 12%"},
    {"name": "actions", "label": "", "field": "actions", "align": "right", "style": "width: 10%"},
]

ACTIONS_SLOT = """
<q-td :props="props">
    <q-btn flat dense icon="edit" @click="() => $parent.$emit('edit', props.row)" />
</q-td>
"""


async def content() -> None:
    me = profile()
    if me is None:
        return

    is_admin = me["role"] == "admin"

    def load() -> None:
        try:
            table.rows = client.get("/projects")
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
        available = me["workgroups"]

        if is_admin:
            try:
                available = client.get("/workgroups")
            except client.ApiError as error:
                ui.notify(error.detail, color="negative")
                return

        if not available:
            ui.notify("No pertanys a cap grup de treball", color="warning")
            return

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Nou projecte").classes("text-lg")

            name = ui.input("Nom").classes("w-full")
            description = ui.input("Descripció").classes("w-full")
            group = ui.select(
                {g["id"]: g["name"] for g in available}, label="Grup de treball"
            ).classes("w-full")

            def confirm() -> None:
                submit.disable()
                try:
                    client.post(
                        "/projects",
                        {
                            "name": name.value,
                            "description": description.value or None,
                            "workgroup_id": group.value,
                        },
                    )
                    dialog.close()
                    load()
                    ui.notify("Projecte creat")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")
                    submit.enable()

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                submit = ui.button("Crear", on_click=confirm)

        dialog.open()

    def remove_selected() -> None:
        chosen = list(table.selected)

        with ui.dialog() as dialog, ui.card():
            ui.label(
                f"Esborrar {len(chosen)} projecte(s)? Els que tinguen espais no "
                "es podran esborrar."
            )

            def confirm() -> None:
                failed = []
                for project in chosen:
                    try:
                        client.delete(f"/projects/{project['id']}")
                    except client.ApiError as error:
                        failed.append(f"{project['name']}: {error.detail}")

                dialog.close()
                load()

                if failed:
                    ui.notify(" / ".join(failed), color="negative")
                else:
                    ui.notify("Projectes esborrats")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                ui.button("Esborrar", on_click=confirm).props("color=negative")

        dialog.open()

    def edit(project: dict) -> None:
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label(project["name"]).classes("text-lg")

            name = ui.input("Nom", value=project["name"]).classes("w-full")
            description = ui.input(
                "Descripció", value=project["description"] or ""
            ).classes("w-full")

            def save() -> None:
                try:
                    client.patch(
                        f"/projects/{project['id']}",
                        {"name": name.value, "description": description.value or None},
                    )
                    dialog.close()
                    load()
                    ui.notify("Projecte actualitzat")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                ui.button("Guardar", on_click=save)

        dialog.open()

    with ui.row().classes("items-center mx-6 mt-4 gap-3"):
        ui.button("Nou projecte", on_click=create)
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