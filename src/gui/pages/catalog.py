"""Catàleg d'unitats i magnituds."""

from nicegui import ui

from gui import client
from gui.layout import profile

UNIT_COLUMNS = [
    {"name": "symbol", "label": "Símbol", "field": "symbol", "sortable": True, "align": "left", "style": "width: 25%"},
    {"name": "name", "label": "Nom", "field": "name", "align": "left", "style": "width: 65%"},
    {"name": "actions", "label": "", "field": "actions", "align": "right", "style": "width: 10%"},
]

TYPE_COLUMNS = [
    {"name": "code", "label": "Codi", "field": "code", "sortable": True, "align": "left", "style": "width: 20%"},
    {"name": "name", "label": "Nom", "field": "name", "align": "left", "style": "width: 30%"},
    {"name": "unit", "label": "Unitat", "field": "unit", "align": "left", "style": "width: 15%"},
    {"name": "range_min", "label": "Mínim", "field": "range_min", "align": "left", "style": "width: 12%"},
    {"name": "range_max", "label": "Màxim", "field": "range_max", "align": "left", "style": "width: 13%"},
    {"name": "actions", "label": "", "field": "actions", "align": "right", "style": "width: 10%"},
]

PENDING_COLUMNS = [
    {"name": "source", "label": "Font", "field": "source", "align": "left", "style": "width: 25%"},
    {"name": "device_id", "label": "Dispositiu", "field": "device_id", "align": "left", "style": "width: 40%"},
    {"name": "name", "label": "Magnitud rebuda", "field": "name", "align": "left", "style": "width: 35%"},
]

EDIT_SLOT = """
<q-td :props="props">
    <q-btn flat dense icon="edit" @click="() => $parent.$emit('edit', props.row)" />
</q-td>
"""

TABLE_PROPS = 'flat table-header-class="bg-primary text-white"'


async def content() -> None:
    me = profile()
    if me is None:
        return

    is_admin = me["role"] == "admin"

    async def load() -> None:
        answers = await client.gather(
            ["/units", "/sensor_types", "/sensors?pending=true"]
        )

        units.rows = answers[0] or []
        types.rows = answers[1] or []
        pending.rows = answers[2] or []
        units.update()
        types.update()
        pending.update()

    def new_unit() -> None:
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Nova unitat").classes("text-lg")
            name = ui.input("Nom").classes("w-full")
            symbol = ui.input("Símbol").classes("w-full")

            def confirm() -> None:
                submit.disable()
                try:
                    client.post("/units", {"name": name.value, "symbol": symbol.value})
                    dialog.close()
                    ui.notify("Unitat creada")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")
                    submit.enable()

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                submit = ui.button("Crear", on_click=confirm)

            dialog.on("hide", load)

        dialog.open()

    def edit_unit(unit: dict) -> None:
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label(unit["symbol"]).classes("text-lg")
            ui.label(
                "El símbol no es pot canviar: és la clau que referencien les "
                "magnituds."
            ).classes("text-xs text-grey")

            name = ui.input("Nom", value=unit["name"]).classes("w-full")

            def save() -> None:
                try:
                    client.patch(f"/units/{unit['id']}", {"name": name.value})
                    dialog.close()
                    ui.notify("Unitat actualitzada")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                ui.button("Guardar", on_click=save)

            dialog.on("hide", load)

        dialog.open()

    def new_type(code: str = "") -> None:
        """Dona d'alta una magnitud. El codi ve omplit si es cataloga una pendent."""
        try:
            available = client.get("/units")
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Nova magnitud").classes("text-lg")

            code_input = ui.input("Codi", value=code).classes("w-full")
            name = ui.input("Nom").classes("w-full")
            unit = ui.select(
                {u["symbol"]: f"{u['symbol']} ({u['name']})" for u in available},
                label="Unitat",
            ).classes("w-full")
            minimum = ui.number("Mínim").classes("w-full")
            maximum = ui.number("Màxim").classes("w-full")

            def confirm() -> None:
                submit.disable()
                try:
                    client.post(
                        "/sensor_types",
                        {
                            "code": code_input.value,
                            "name": name.value,
                            "unit_symbol": unit.value,
                            "range_min": minimum.value,
                            "range_max": maximum.value,
                        },
                    )
                    dialog.close()
                    ui.notify("Magnitud catalogada")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")
                    submit.enable()

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                submit = ui.button("Crear", on_click=confirm)

            dialog.on("hide", load)

        dialog.open()

    def edit_type(sensor_type: dict) -> None:
        try:
            available = client.get("/units")
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label(sensor_type["code"]).classes("text-lg")

            name = ui.input("Nom", value=sensor_type["name"]).classes("w-full")
            unit = ui.select(
                {u["symbol"]: f"{u['symbol']} ({u['name']})" for u in available},
                label="Unitat",
                value=sensor_type["unit"],
            ).classes("w-full")
            ui.label(
                "Canviar la unitat reinterpreta tot l'històric: els valors "
                "guardats no es converteixen."
            ).classes("text-xs text-orange")

            minimum = ui.number("Mínim", value=sensor_type["range_min"]).classes(
                "w-full"
            )
            maximum = ui.number("Màxim", value=sensor_type["range_max"]).classes(
                "w-full"
            )

            def save() -> None:
                try:
                    client.patch(
                        f"/sensor_types/{sensor_type['id']}",
                        {
                            "name": name.value,
                            "unit_symbol": unit.value,
                            "range_min": minimum.value,
                            "range_max": maximum.value,
                        },
                    )
                    dialog.close()
                    ui.notify("Magnitud actualitzada")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                ui.button("Guardar", on_click=save)

            dialog.on("hide", load)

        dialog.open()

    with ui.tabs().classes("w-full") as tabs:
        ui.tab("Magnituds")
        ui.tab("Unitats")
        ui.tab("Pendents")

    with ui.tab_panels(tabs, value="Magnituds").classes("w-full p-0"):
        with ui.tab_panel("Magnituds").classes("p-0"):
            if is_admin:
                with ui.row().classes("mx-6 mt-4"):
                    ui.button("Nova magnitud", on_click=lambda: new_type())

            with ui.card().classes("w-full mt-4 p-0 overflow-hidden"):
                types = ui.table(columns=TYPE_COLUMNS, rows=[], row_key="id").classes(
                    "w-full"
                ).props(TABLE_PROPS)
                if is_admin:
                    types.add_slot("body-cell-actions", EDIT_SLOT)
                    types.on("edit", lambda event: edit_type(event.args))

        with ui.tab_panel("Unitats").classes("p-0"):
            if is_admin:
                with ui.row().classes("mx-6 mt-4"):
                    ui.button("Nova unitat", on_click=new_unit)

            with ui.card().classes("w-full mt-4 p-0 overflow-hidden"):
                units = ui.table(columns=UNIT_COLUMNS, rows=[], row_key="id").classes(
                    "w-full"
                ).props(TABLE_PROPS)
                if is_admin:
                    units.add_slot("body-cell-actions", EDIT_SLOT)
                    units.on("edit", lambda event: edit_unit(event.args))

        with ui.tab_panel("Pendents").classes("p-0"):
            ui.label(
                "Sensors que han enviat una magnitud que encara no està catalogada. "
                "Prem una fila per a donar-la d'alta: les seues lectures deixaran "
                "d'estar marcades."
            ).classes("text-grey mx-6 mt-4")

            with ui.card().classes("w-full mt-4 p-0 overflow-hidden"):
                pending = ui.table(
                    columns=PENDING_COLUMNS, rows=[], row_key="id"
                ).classes("w-full").props(TABLE_PROPS)
                if is_admin:
                    pending.on(
                        "rowClick", lambda event: new_type(event.args[1]["name"])
                    )

    await load()