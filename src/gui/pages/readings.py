"""Consulta i descàrrega de lectures."""

import csv
import io
from datetime import datetime, timezone

from nicegui import ui

from gui import client
from gui.layout import format_moment, profile

COLUMNS = [
    {"name": "time", "label": "Instant", "field": "time", "align": "left", "style": "width: 18%"},
    {"name": "device", "label": "Dispositiu", "field": "device", "align": "left", "style": "width: 22%"},
    {"name": "magnitude", "label": "Magnitud", "field": "magnitude", "align": "left", "style": "width: 15%"},
    {"name": "value", "label": "Valor", "field": "value", "align": "left", "style": "width: 10%"},
    {"name": "unit", "label": "Unitat", "field": "unit", "align": "left", "style": "width: 10%"},
    {"name": "invalid_message", "label": "Avís", "field": "invalid_message", "align": "left", "style": "width: 25%"},
]

INVALID_OPTIONS = {None: "Totes", True: "Només amb avís", False: "Només correctes"}

PAGE_SIZE = 50
EXPORT_BATCH = 1000


def _thousands(value: int) -> str:
    return f"{value:,}".replace(",", ".")


async def content() -> None:
    if profile() is None:
        return

    answers = await client.gather(["/sensors?limit=200", "/devices?limit=200"])
    sensors = answers[0] or []
    devices = answers[1] or []

    by_sensor = {s["id"]: s for s in sensors}
    sources = sorted({d["source"] for d in devices})

    def devices_of(source: str | None) -> dict:
        return {
            d["device_id"]: d["name"] or d["device_id"]
            for d in devices
            if source is None or d["source"] == source
        }

    def to_row(reading: dict) -> dict:
        sensor = by_sensor.get(reading["sensor_id"], {})
        return reading | {
            "time": format_moment(reading["time"]),
            "device": f"{sensor.get('source', '')} / {sensor.get('device_id', '')}",
            "magnitude": sensor.get("name", ""),
        }

    def params() -> dict:
        return {
            "source": source.value,
            "device_id": device.value,
            "since": f"{since.value}T00:00:00Z" if since.value else None,
            "until": f"{until.value}T23:59:59Z" if until.value else None,
            "invalid": invalid.value,
        }

    def fetch(page: int, rows_per_page: int) -> None:
        """Demana a l'API només la pàgina que es veu, i el total per a la paginació."""
        filters = params()
        try:
            total = client.count("/readings", **filters)
            readings = client.get(
                "/readings",
                limit=rows_per_page,
                offset=(page - 1) * rows_per_page,
                **filters,
            )
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        table.rows = [to_row(r) for r in readings]
        table.pagination = {"page": page, "rowsPerPage": rows_per_page, "rowsNumber": total}
        count.text = f"{_thousands(total)} lectures"

    def load() -> None:
        """Una consulta nova sempre torna a la primera pàgina."""
        fetch(1, table.pagination.get("rowsPerPage", PAGE_SIZE))

    def on_request(event) -> None:
        pagination = event.args["pagination"]
        fetch(pagination["page"], pagination["rowsPerPage"])

    def download() -> None:
        """Exporta totes les lectures que complixen els filtres, no sols la pàgina."""
        filters = params()
        filters["until"] = filters["until"] or datetime.now(timezone.utc).isoformat()

        readings: list[dict] = []
        try:
            total = client.count("/readings", **filters)
            for offset in range(0, total, EXPORT_BATCH):
                readings += client.get(
                    "/readings", limit=EXPORT_BATCH, offset=offset, **filters
                )
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")
            return

        if not readings:
            ui.notify("No hi ha res a descarregar", color="warning")
            return

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["time", "source", "device_id", "magnitude", "value", "unit", "invalid_message"]
        )
        for reading in readings:
            sensor = by_sensor.get(reading["sensor_id"], {})
            writer.writerow(
                [
                    reading["time"],
                    sensor.get("source", ""),
                    sensor.get("device_id", ""),
                    sensor.get("name", ""),
                    reading["value"],
                    reading["unit"],
                    reading["invalid_message"] or "",
                ]
            )

        ui.download(buffer.getvalue().encode("utf-8"), "lectures.csv")

    with ui.row().classes("items-end mx-6 mt-4 gap-4"):
        source = ui.select({None: "Totes"} | {s: s for s in sources}, value=None).props(
            'dense outlined placeholder="Font"'
        ).classes("w-40")

        device = ui.select({None: "Tots"} | devices_of(None), value=None).props(
            'dense outlined placeholder="Dispositiu"'
        ).classes("w-56")

        since = ui.input().props('dense outlined type=date placeholder="Des de"').classes(
            "w-40"
        )
        until = ui.input().props('dense outlined type=date placeholder="Fins a"').classes(
            "w-40"
        )

        invalid = ui.select(INVALID_OPTIONS, value=None).props("dense outlined").classes(
            "w-44"
        )

        ui.button("Consultar", on_click=load)
        ui.button("CSV", icon="download", on_click=download).props("flat dense")
        count = ui.label("").classes("text-grey")

    with ui.card().classes("w-full mt-4 p-0 overflow-hidden"):
        table = ui.table(
            columns=COLUMNS,
            rows=[],
            row_key="id",
            pagination={"page": 1, "rowsPerPage": PAGE_SIZE, "rowsNumber": 0},
        ).classes("w-full").props(
            'flat table-header-class="bg-primary text-white" '
            ':rows-per-page-options="[25, 50, 100]"'
        )
        table.on("request", on_request)

    source.on_value_change(
        lambda event: (
            device.set_options({None: "Tots"} | devices_of(event.value)),
            device.set_value(None),
        )
    )

    load()