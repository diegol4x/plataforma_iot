"""Gestió d'usuaris. Només per a administradors."""

from nicegui import ui

from gui import client
from gui.layout import profile

COLUMNS = [
    {"name": "username", "label": "Usuari", "field": "username", "sortable": True, "align": "left", "style": "width: 40%"},
    {"name": "role", "label": "Rol", "field": "role", "sortable": True, "align": "left", "style": "width: 25%"},
    {"name": "active", "label": "Actiu", "field": "active", "sortable": True, "align": "left", "style": "width: 25%"},
    {"name": "actions", "label": "", "field": "actions", "align": "right", "style": "width: 10%"},
]

ROLES = {"viewer": "Lector", "admin": "Administrador"}

ACTIONS_SLOT = """
<q-td :props="props">
    <q-btn flat dense icon="edit" @click="() => $parent.$emit('edit', props.row)" />
</q-td>
"""


async def content() -> None:
    me = profile()
    if me is None:
        return

    if me["role"] != "admin":
        ui.label("Aquesta pàgina és només per a administradors.").classes("m-4")
        return

    originals: dict = {}

    def load() -> None:
        try:
            users = client.get("/users")
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        originals.clear()
        originals.update({u["id"]: u for u in users})

        table.rows = [
            u
            | {
                "role": ROLES.get(u["role"], u["role"]),
                "active": "Sí" if u["active"] else "No",
            }
            for u in users
        ]
        table.selected = []
        table.update()
        _refresh_delete()

    def _refresh_delete() -> None:
        """El botó d'esborrar només s'activa amb alguna fila marcada."""
        delete_button.set_enabled(bool(table.selected))

    def create() -> None:
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Nou usuari").classes("text-lg")

            username = ui.input("Usuari").classes("w-full")
            password = ui.input("Contrasenya", password=True).classes("w-full")
            ui.label("Mínim 8 caràcters").classes("text-grey text-xs")
            role = ui.select(ROLES, label="Rol", value="viewer").classes("w-full")

            def confirm() -> None:
                submit.disable()
                try:
                    client.post(
                        "/users",
                        {
                            "username": username.value,
                            "password": password.value,
                            "role": role.value,
                        },
                    )
                    dialog.close()
                    load()
                    ui.notify("Usuari creat")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")
                    submit.enable()

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                submit = ui.button("Crear", on_click=confirm)

        dialog.open()

    def remove_selected() -> None:
        chosen = list(table.selected)

        if any(u["id"] == me["id"] for u in chosen):
            ui.notify("No et pots esborrar a tu mateix", color="negative")
            return

        with ui.dialog() as dialog, ui.card():
            ui.label(
                f"Esborrar {len(chosen)} usuari(s)? Els que siguen propietaris "
                "d'algun projecte no es podran esborrar."
            )

            def confirm() -> None:
                failed = []
                for user in chosen:
                    try:
                        client.delete(f"/users/{user['id']}")
                    except client.ApiError as error:
                        failed.append(f"{user['username']}: {error.detail}")

                dialog.close()
                load()

                if failed:
                    ui.notify(" / ".join(failed), color="negative")
                else:
                    ui.notify("Usuaris esborrats")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                ui.button("Esborrar", on_click=confirm).props("color=negative")

        dialog.open()

    def edit(row: dict) -> None:
        user = originals[row["id"]]
        is_me = user["id"] == me["id"]

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label(user["username"]).classes("text-lg")

            role = ui.select(ROLES, label="Rol", value=user["role"]).classes("w-full")
            active = ui.checkbox("Actiu", value=user["active"])

            if is_me:
                role.disable()
                active.disable()
                ui.label("No pots canviar-te el rol ni desactivar-te").classes(
                    "text-xs text-grey"
                )

            ui.separator()
            password = ui.input("Nova contrasenya", password=True).classes("w-full")
            ui.label("Deixar en blanc per a no canviar-la").classes("text-grey text-xs")

            def save() -> None:
                payload = {}
                if not is_me:
                    payload |= {"role": role.value, "active": active.value}
                if password.value:
                    payload["password"] = password.value

                if not payload:
                    dialog.close()
                    return

                try:
                    client.patch(f"/users/{user['id']}", payload)
                    dialog.close()
                    load()
                    ui.notify("Usuari actualitzat")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                ui.button("Guardar", on_click=save)

        dialog.open()

    with ui.row().classes("items-center mx-6 mt-4 gap-3"):
        ui.button("Nou usuari", on_click=create)
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