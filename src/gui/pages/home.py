"""Taulell principal."""

from datetime import datetime, timedelta, timezone

from nicegui import ui

from gui import client
from gui.layout import BLOCK_HEADER, profile

STATE_COLORS = {
    "active": "green",
    "silent": "orange",
    "unprovisioned": "red",
    "retired": "grey",
}

STATE_LABELS = {
    "active": "Actiu",
    "silent": "Silenciós",
    "unprovisioned": "Sense provisionar",
    "retired": "Retirat",
}

PERIODS = {24: "últimes 24 h", 168: "últims 7 dies", 720: "últims 30 dies"}


def _ago(moment: str | None) -> str:
    """Temps transcorregut en paraules: més llegible que una marca de temps."""
    if moment is None:
        return "mai"

    delta = datetime.now(timezone.utc) - datetime.fromisoformat(moment)
    minutes = int(delta.total_seconds() // 60)

    if minutes < 1:
        return "ara mateix"
    if minutes < 60:
        return f"fa {minutes} min"
    if minutes < 1440:
        return f"fa {minutes // 60} h {minutes % 60} min"
    return f"fa {minutes // 1440} dies"


def _thousands(value: int) -> str:
    """Separador de milers a l'espanyola."""
    return f"{value:,}".replace(",", ".")


def _metric(label: str, value, detail: str = "", color: str = "") -> tuple:
    """Una xifra gran amb la seua etiqueta.

    Torna les dues etiquetes perquè les mètriques que depenen del període
    s'han de poder refrescar sense reconstruir la targeta.
    """
    with ui.card().classes("min-w-36 flex-grow p-0 overflow-hidden"):
        with ui.row().classes(BLOCK_HEADER):
            ui.label(label).classes("text-xs uppercase")

        with ui.column().classes("p-3 gap-0"):
            number = ui.label(str(value)).classes(f"text-3xl {color}")
            caption = ui.label(detail).classes("text-xs text-grey")

    return number, caption


async def content() -> None:
    me = profile()
    if me is None:
        return

    is_admin = me["role"] == "admin"
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    answers = await client.gather(
        [
            "/devices?limit=200",
            "/spaces",
            "/projects",
            "/sensors?pending=true",
            "/workgroups",
        ]
    )

    devices = answers[0] or []
    spaces = answers[1] or []
    projects = answers[2] or []
    pending = answers[3] or []
    groups = (answers[4] or []) if is_admin else []

    try:
        readings_24h = client.count("/readings", since=since)
        invalid_24h = client.count("/readings", since=since, invalid=True)
        discards_24h = client.count("/discards", since=since) if is_admin else 0
    except client.ApiError as error:
        ui.notify(error.detail, color="negative")
        return

    counts: dict[str, int] = {}
    for device in devices:
        counts[device["status"]] = counts.get(device["status"], 0) + 1

    def projects_of(group_id: int | None) -> dict:
        return {None: "Tots"} | {
            p["id"]: p["name"]
            for p in projects
            if group_id is None or p["workgroup_id"] == group_id
        }

    def spaces_of(project_id: int | None) -> dict:
        return {
            s["id"]: s["name"]
            for s in spaces
            if project_id is None or s["project_id"] == project_id
        }

    with ui.row().classes("items-end mx-6 mt-4 gap-4"):
        group = None
        if groups:
            group = ui.select(
                {None: "Tots"} | {g["id"]: g["name"] for g in groups},
                label="Workgroup",
                value=None,
            ).classes("w-56").props("dense")

        project = ui.select(projects_of(None), label="Projecte", value=None).classes(
            "w-56"
        ).props("dense")
        space = ui.select({}, label="Espai").classes("w-56").props("dense")

        period = ui.select(
            {24: "24 h", 168: "7 dies", 720: "30 dies"}, label="Període", value=24
        ).classes("w-36").props("dense")

    with ui.row().classes("w-full px-6 py-4 gap-4 no-wrap"):
        _metric(
            "Dispositius actius",
            counts.get("active", 0),
            f"de {len(devices)} totals",
            "text-green",
        )
        _metric(
            "Silenciosos", counts.get("silent", 0), "sense uplink recent", "text-orange"
        )
        _metric(
            "Sense provisionar",
            counts.get("unprovisioned", 0),
            "reben dades, sense reclamar",
            "text-red",
        )

        readings_metric = _metric("Lectures", _thousands(readings_24h), PERIODS[24])
        invalid_metric = _metric(
            "Amb avís", invalid_24h, PERIODS[24], "text-orange" if invalid_24h else ""
        )
        _metric(
            "Magnituds pendents",
            len(pending),
            "per catalogar",
            "text-orange" if pending else "",
        )

        discards_metric = None
        if is_admin:
            discards_metric = _metric(
                "Descarts",
                discards_24h,
                PERIODS[24],
                "text-red" if discards_24h else "",
            )

    with ui.row().classes("w-full px-6 pb-6 gap-4 no-wrap items-stretch"):
        with ui.card().classes("w-2/3 p-0 overflow-hidden"):
            with ui.row().classes(BLOCK_HEADER):
                ui.label("Sèrie temporal per magnitud")
                ui.space()
                window_label = ui.label(PERIODS[24]).classes("text-xs")

            with ui.column().classes("w-full p-4"):
                tabs_area = ui.row().classes("gap-2")
                chart = ui.echart(
                    {"xAxis": {"type": "time"}, "yAxis": {"type": "value"}, "series": []}
                ).classes("h-64 w-full")

        with ui.card().classes("w-1/3 p-0 overflow-hidden"):
            with ui.row().classes(BLOCK_HEADER):
                ui.label("Dispositius")
                ui.space()
                ui.label(f"{len(devices)} total").classes("text-xs")

            with ui.column().classes("w-full p-4 gap-2"):
                for device in devices[:8]:
                    with ui.row().classes("w-full items-center gap-2"):
                        ui.label(device["device_id"]).classes("font-mono text-sm")
                        ui.space()
                        ui.icon("circle", size="0.6rem").classes(
                            f"text-{STATE_COLORS.get(device['status'], 'grey')}"
                        )
                        ui.label(
                            STATE_LABELS.get(device["status"], device["status"])
                        ).classes("text-sm w-32")
                        ui.label(_ago(device["last_seen"])).classes(
                            "text-xs text-grey w-24"
                        )

    state: dict = {"series": [], "magnitude": None}

    def draw() -> None:
        rows = [r for r in state["series"] if r["name"] == state["magnitude"]]

        chart.options.update(
            {
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "time"},
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "name": state["magnitude"],
                        "type": "line",
                        "data": [[r["bucket"], r["avg"]] for r in rows],
                    }
                ],
            }
        )
        chart.update()

    def refresh_metrics(window: str, caption: str) -> None:
        """Les xifres d'interval segueixen el selector de període."""
        try:
            readings_metric[0].text = _thousands(
                client.count("/readings", since=window)
            )
            readings_metric[1].text = caption

            invalid_metric[0].text = str(
                client.count("/readings", since=window, invalid=True)
            )
            invalid_metric[1].text = caption

            if discards_metric is not None:
                discards_metric[0].text = str(client.count("/discards", since=window))
                discards_metric[1].text = caption
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")

    def load_series(space_id: int | None) -> None:
        tabs_area.clear()
        state["series"] = []
        state["magnitude"] = None

        hours = period.value
        window_label.text = PERIODS[hours]
        window = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        refresh_metrics(window, PERIODS[hours])

        if space_id is None:
            draw()
            return

        bucket = "hour" if hours <= 168 else "day"

        try:
            state["series"] = client.get(
                f"/spaces/{space_id}/readings",
                bucket=bucket,
                include_descendants=True,
                **{"from": window},
            )
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        magnitudes = sorted({r["name"] for r in state["series"]})
        state["magnitude"] = magnitudes[0] if magnitudes else None

        with tabs_area:
            if not magnitudes:
                ui.label(
                    "Cap lectura en este espai ni en els que conté durant el període triat"
                ).classes("text-sm text-grey")

            for name in magnitudes:
                ui.button(
                    name.title(),
                    on_click=lambda n=name: (state.update(magnitude=n), draw()),
                ).props("flat dense no-caps")

        draw()

    if group is not None:
        group.on_value_change(
            lambda event: (
                project.set_options(projects_of(event.value)),
                project.set_value(None),
                space.set_options(spaces_of(None)),
                space.set_value(None),
            )
        )

    project.on_value_change(
        lambda event: (space.set_options(spaces_of(event.value)), space.set_value(None))
    )
    space.on_value_change(lambda event: load_series(event.value))
    period.on_value_change(lambda: load_series(space.value))

    space.set_options(spaces_of(None))