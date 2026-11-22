"""Jerarquia i adjacència d'espais."""

from nicegui import ui

from gui import client
from gui.layout import profile

SPACE_TYPES = {
    "site": "Emplaçament",
    "building": "Edifici",
    "storey": "Planta",
    "space": "Espai",
}

TYPE_COLORS = {
    "site": "purple",
    "building": "blue",
    "storey": "teal",
    "space": "green",
}

COLUMNS = [
    {"name": "name", "label": "Espai", "field": "name", "align": "left", "style": "width: 23%"},
    {"name": "type", "label": "Tipus", "field": "type", "align": "left", "style": "width: 12%"},
    {"name": "path", "label": "Dins de (jerarquia)", "field": "path", "align": "left", "style": "width: 25%"},
    {"name": "adjacent", "label": "Adjacent a", "field": "adjacent", "align": "left", "style": "width: 22%"},
    {"name": "devices", "label": "Dispositius", "field": "device_count", "align": "left", "style": "width: 10%"},
    {"name": "actions", "label": "", "field": "actions", "align": "right", "style": "width: 8%"},
]

NAME_SLOT = """
<q-td :props="props" :colspan="props.row.group ? 6 : 1"
      :class="props.row.group ? 'bg-blue-1 text-weight-medium text-primary' : ''">
    <span v-if="!props.row.group"
          :style="'padding-left: ' + (props.row.depth * 20) + 'px'">
        <span v-if="props.row.depth" class="text-grey">└ </span>{{ props.row.name }}
    </span>
    <span v-else>{{ props.row.name }}</span>
</q-td>
"""

TYPE_SLOT = """
<q-td v-if="!props.row.group" :props="props">
    <q-badge :color="props.row.type_color" outline>{{ props.row.type_label }}</q-badge>
</q-td>
"""

PATH_SLOT = """
<q-td v-if="!props.row.group" :props="props">
    <span :title="props.row.path_full">
        <span class="text-grey text-caption">{{ props.row.path_prefix }}</span>
        <span class="text-weight-medium">{{ props.row.path_last }}</span>
    </span>
</q-td>
"""

ADJACENT_SLOT = """
<q-td v-if="!props.row.group" :props="props">
    <q-badge v-for="n in props.row.adjacent_list" :key="n" color="grey-3"
             text-color="grey-9" class="q-mr-xs">{{ n }}</q-badge>
    <span v-if="!props.row.adjacent_list.length" class="text-grey text-caption">
        sense adjacències
    </span>
</q-td>
"""

DEVICES_SLOT = """
<q-td v-if="!props.row.group" :props="props">
    <span :class="props.row.device_count ? '' : 'text-grey'">
        {{ props.row.device_count }}
    </span>
</q-td>
"""

ACTIONS_SLOT = """
<q-td v-if="!props.row.group" :props="props">
    <q-btn flat dense icon="edit" @click="() => $parent.$emit('edit', props.row)" />
</q-td>
"""


def _path_parts(path: list[str]) -> dict:
    """La ruta retallada: els trams de dalt es resumixen amb ···

    El que importa és on està l'espai, no tota la cadena des de l'arrel, i així
    la columna no creix amb la profunditat. La ruta sencera queda en el title.
    """
    full = " › ".join(path)

    if len(path) == 1:
        return {"path_prefix": "", "path_last": path[0], "path_full": full}

    trail = path[:-1]
    if len(trail) > 2:
        trail = ["···"] + trail[-2:]

    return {
        "path_prefix": " › ".join(trail) + " › ",
        "path_last": path[-1],
        "path_full": full,
    }


async def content() -> None:
    if profile() is None:
        return

    state: dict = {"spaces": [], "projects": {}}

    def decorate(space: dict, depth: int, path: list[str]) -> dict:
        return (
            space
            | {
                "depth": depth,
                "type_label": SPACE_TYPES.get(space["type"], space["type"]),
                "type_color": TYPE_COLORS.get(space["type"], "grey"),
                "group": False,
            }
            | _path_parts(path)
        )

    def flatten(spaces: list[dict]) -> list[dict]:
        """Aplana l'arbre en ordre de lectura, agrupat per projecte.

        Una fila per espai, amb la jerarquia llegible per la sagnia i per la
        ruta, i una capçalera sintètica davant de cada projecte.
        """
        children: dict[int | None, list[dict]] = {}
        for space in spaces:
            children.setdefault(space["parent_id"], []).append(space)

        rows: list[dict] = []

        def walk(parent_id: int, depth: int, trail: list[str]) -> None:
            for space in sorted(children.get(parent_id, []), key=lambda s: s["name"]):
                path = trail + [space["name"]]
                rows.append(decorate(space, depth, path))
                walk(space["id"], depth + 1, path)

        by_project: dict[int, list[dict]] = {}
        for space in spaces:
            by_project.setdefault(space["project_id"], []).append(space)

        for project_id, members in sorted(
            by_project.items(), key=lambda item: state["projects"].get(item[0], "")
        ):
            rows.append(
                {
                    "id": f"project-{project_id}",
                    "group": True,
                    "name": f"Projecte · {state['projects'].get(project_id, project_id)}",
                }
            )

            for root in sorted(
                (s for s in members if s["parent_id"] is None), key=lambda s: s["name"]
            ):
                rows.append(decorate(root, 0, [root["name"]]))
                walk(root["id"], 1, [root["name"]])

        return rows

    async def load() -> None:
        try:
            state["projects"] = {p["id"]: p["name"] for p in client.get("/projects")}
            state["spaces"] = client.get("/spaces")
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        rows = flatten(state["spaces"])
        names = {s["id"]: s["name"] for s in state["spaces"]}

        for row in rows:
            if row["group"]:
                continue
            row["adjacent_list"] = [
                names.get(i, i) for i in row["adjacent_ids"]
            ]

        table.rows = rows
        table.update()
        count.text = f"{len([r for r in rows if not r['group']])} espais"

    def create() -> None:
        try:
            projects = client.get("/projects")
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        if not projects:
            ui.notify("Primer cal un projecte", color="warning")
            return

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("Nou espai").classes("text-lg")

            name = ui.input("Nom").classes("w-full")
            kind = ui.select(SPACE_TYPES, label="Tipus", value="space").classes("w-full")
            project = ui.select(
                {p["id"]: p["name"] for p in projects}, label="Projecte"
            ).classes("w-full")
            parent = ui.select({None: "Cap (arrel)"}, label="Dins de", value=None).classes(
                "w-full"
            )
            ui.label("El pare ha de ser del mateix projecte.").classes(
                "text-xs text-grey"
            )

            def parents_of(project_id: int | None) -> dict:
                return {None: "Cap (arrel)"} | {
                    s["id"]: s["name"]
                    for s in state["spaces"]
                    if s["project_id"] == project_id
                }

            project.on_value_change(
                lambda event: (
                    parent.set_options(parents_of(event.value)),
                    parent.set_value(None),
                )
            )

            def confirm() -> None:
                submit.disable()
                try:
                    client.post(
                        "/spaces",
                        {
                            "name": name.value,
                            "type": kind.value,
                            "project_id": project.value,
                            "parent_id": parent.value,
                        },
                    )
                    dialog.close()
                    ui.notify("Espai creat")
                except client.ApiError as error:
                    ui.notify(error.detail, color="negative")
                    submit.enable()

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel·lar", on_click=dialog.close).props("flat")
                submit = ui.button("Crear", on_click=confirm)

            dialog.on("hide", load)

        dialog.open()

    def edit(row: dict) -> None:
        space_id = row["id"]

        with ui.dialog() as dialog, ui.card().classes("w-[32rem]"):
            ui.label(row["name"]).classes("text-lg")
            ui.label(state["projects"].get(row["project_id"], "")).classes(
                "text-sm text-grey"
            )

            with ui.tabs().classes("w-full") as tabs:
                ui.tab("Dades")
                ui.tab("Dispositius")
                ui.tab("Adjacències")

            with ui.tab_panels(tabs, value="Dades").classes("w-full"):
                with ui.tab_panel("Dades"):
                    name = ui.input("Nom", value=row["name"]).classes("w-full")
                    kind = ui.select(
                        SPACE_TYPES, label="Tipus", value=row["type"]
                    ).classes("w-full")

                    siblings = {None: "Cap (arrel)"} | {
                        s["id"]: s["name"]
                        for s in state["spaces"]
                        if s["project_id"] == row["project_id"] and s["id"] != space_id
                    }
                    parent = ui.select(
                        siblings, label="Dins de", value=row["parent_id"]
                    ).classes("w-full")

                    def save() -> None:
                        try:
                            client.patch(
                                f"/spaces/{space_id}",
                                {
                                    "name": name.value,
                                    "type": kind.value,
                                    "parent_id": parent.value,
                                },
                            )
                            dialog.close()
                            ui.notify("Espai actualitzat")
                        except client.ApiError as error:
                            ui.notify(error.detail, color="negative")

                    def remove() -> None:
                        try:
                            client.delete(f"/spaces/{space_id}")
                            dialog.close()
                            ui.notify("Espai esborrat")
                        except client.ApiError as error:
                            ui.notify(error.detail, color="negative")

                    with ui.row().classes("w-full justify-between mt-4"):
                        ui.button("Esborrar", on_click=remove).props(
                            "flat dense color=negative"
                        )
                        ui.button("Guardar", on_click=save)

                with ui.tab_panel("Dispositius"):
                    devices = ui.column().classes("w-full")
                    _refresh_devices(space_id, devices)

                with ui.tab_panel("Adjacències"):
                    ui.label(
                        "L'adjacència és simètrica i només entre espais del "
                        "mateix projecte."
                    ).classes("text-xs text-grey mb-2")
                    adjacent = ui.column().classes("w-full")
                    _refresh_adjacent(space_id, row["project_id"], state, adjacent)

            dialog.on("hide", load)

        dialog.open()

    with ui.row().classes("items-center mx-6 mt-4 gap-3"):
        ui.button("Nou espai", on_click=create)
        ui.button("Refrescar", icon="refresh", on_click=load).props("flat dense")
        ui.space()
        count = ui.label("").classes("text-grey text-sm")

    with ui.card().classes("w-full mt-4 p-0 overflow-hidden"):
        table = ui.table(columns=COLUMNS, rows=[], row_key="id").classes(
            "w-full"
        ).props('flat table-header-class="bg-primary text-white"')

        table.add_slot("body-cell-name", NAME_SLOT)
        table.add_slot("body-cell-type", TYPE_SLOT)
        table.add_slot("body-cell-path", PATH_SLOT)
        table.add_slot("body-cell-adjacent", ADJACENT_SLOT)
        table.add_slot("body-cell-devices", DEVICES_SLOT)
        table.add_slot("body-cell-actions", ACTIONS_SLOT)
        table.on("edit", lambda event: edit(event.args))

    await load()


def _refresh_adjacent(space_id: int, project_id: int, state: dict, container) -> None:
    """Llista els veïns amb els botons per a afegir-ne i llevar-ne."""
    container.clear()

    try:
        current = client.get(f"/spaces/{space_id}/adjacent")
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")
        return

    taken = {n["id"] for n in current} | {space_id}

    with container:
        if not current:
            ui.label("Cap adjacència").classes("text-grey")

        for neighbour in current:
            with ui.row().classes("w-full items-center gap-2"):
                ui.label(neighbour["name"])
                ui.space()
                ui.button(
                    icon="close",
                    on_click=lambda n=neighbour: _remove_adjacent(
                        space_id, project_id, n["id"], state, container
                    ),
                ).props("flat dense")

        available = {
            s["id"]: s["name"]
            for s in state["spaces"]
            if s["project_id"] == project_id and s["id"] not in taken
        }

        if available:
            ui.separator().classes("my-2")
            with ui.row().classes("w-full items-center gap-2"):
                choice = ui.select(available, label="Espai").classes("flex-grow")
                ui.button(
                    "Afegir",
                    on_click=lambda: _add_adjacent(
                        space_id, project_id, choice.value, state, container
                    ),
                ).props("outline dense")


def _add_adjacent(
    space_id: int, project_id: int, other_id: int | None, state: dict, container
) -> None:
    if other_id is None:
        return

    try:
        client.put(f"/spaces/{space_id}/adjacent/{other_id}")
        _refresh_adjacent(space_id, project_id, state, container)
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")


def _remove_adjacent(
    space_id: int, project_id: int, other_id: int, state: dict, container
) -> None:
    try:
        client.delete(f"/spaces/{space_id}/adjacent/{other_id}")
        _refresh_adjacent(space_id, project_id, state, container)
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")


def _refresh_devices(space_id: int, container) -> None:
    """Dispositius ubicats en l'espai."""
    container.clear()

    try:
        assigned = client.get(f"/spaces/{space_id}/devices")
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
                    on_click=lambda d=device: _remove_device(space_id, d, container),
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
                    on_click=lambda: _add_device(space_id, choice.value, container),
                ).props("outline dense")


def _add_device(space_id: int, identity: str | None, container) -> None:
    if identity is None:
        return

    try:
        client.put(f"/spaces/{space_id}/devices/{identity}")
        _refresh_devices(space_id, container)
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")


def _remove_device(space_id: int, device: dict, container) -> None:
    try:
        client.delete(
            f"/spaces/{space_id}/devices/{device['source']}/{device['device_id']}"
        )
        _refresh_devices(space_id, container)
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")