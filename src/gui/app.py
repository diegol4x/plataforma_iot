"""Interfície web de la plataforma.

És un client més de l'API REST: no importa res de plataforma_iot i parla amb
ella per HTTP, com ho faria qualsevol altre consumidor.
"""

import os

from nicegui import ui

from gui import auth
from gui.layout import layout
from gui.pages import (
    catalog,
    devices,
    diagnostics,
    home,
    login,
    projects,
    readings,
    spaces,
    users,
    workgroups,
)

from pathlib import Path

from nicegui import app as nicegui_app

nicegui_app.add_static_files("/static", str(Path(__file__).parent / "static"))

ROUTES = {
    "/": home.content,
    "/devices": devices.content,
    "/spaces": spaces.content,
    "/projects": projects.content,
    "/workgroups": workgroups.content,
    "/users": users.content,
    "/catalog": catalog.content,
    "/readings": readings.content,
    "/diagnostics": diagnostics.content,
}


@ui.page("/")
@ui.page("/{_:path}")
def shell() -> None:
    me = layout()
    if me is None:
        return

    ui.sub_pages(ROUTES).classes("w-full")


auth.install()

ui.run(
    host="0.0.0.0",
    port=8080,
    title="Plataforma IoT",
    storage_secret=os.environ["JWT_SECRET"],
    reload=False,
)