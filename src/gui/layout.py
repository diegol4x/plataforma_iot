"""Capçalera i navegació comunes a totes les pàgines."""

from datetime import datetime

from nicegui import app, ui

from gui import client

BLOCK_HEADER = "w-full items-center bg-primary text-white px-4 py-3 rounded-t"

PAGES = [
    ("Taulell", "/", None),
    ("Dispositius", "/devices", None),
    ("Espais", "/spaces", None),
    ("Projectes", "/projects", None),
    ("Grups", "/workgroups", "admin"),
    ("Usuaris", "/users", "admin"),
    ("Catàleg", "/catalog", None),
    ("Lectures", "/readings", None),
    ("Diagnòstic", "/diagnostics", "admin"),
]


def format_moment(moment: str | None) -> str:
    """Data i hora llegibles, sense la T ni la Z de l'ISO."""
    if moment is None:
        return ""
    return datetime.fromisoformat(moment).strftime("%d/%m/%Y %H:%M")


def profile() -> dict | None:
    """El perfil de qui ha entrat, demanat una sola volta per sessió.

    Amb la navegació interna la capçalera ja no es reconstruïx en cada clic,
    però el perfil es guarda igualment: és informació que no canvia mentres
    dura la sessió, i estalvia una consulta a la base de dades per visita.
    """
    cached = app.storage.user.get("profile")
    if cached is not None:
        return cached

    try:
        me = client.get("/users/me")
    except client.ApiError:
        return None

    app.storage.user["profile"] = me
    return me


def change_password() -> None:
    """Canvi de la pròpia contrasenya, disponible des de qualsevol pàgina."""
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("Canviar la contrasenya").classes("text-lg")

        current = ui.input("Contrasenya actual", password=True).classes("w-full")
        new = ui.input("Nova contrasenya", password=True).classes("w-full")
        ui.label("Mínim 8 caràcters").classes("text-grey text-xs")

        def save() -> None:
            try:
                client.patch(
                    "/users/me",
                    {"current_password": current.value, "new_password": new.value},
                )
                dialog.close()
                ui.notify("Contrasenya canviada")
            except client.ApiError as error:
                ui.notify(error.detail, color="negative")

        with ui.row().classes("w-full justify-end"):
            ui.button("Cancel·lar", on_click=dialog.close).props("flat")
            ui.button("Canviar", on_click=save)

    dialog.open()


def logout() -> None:
    client.logout()
    app.storage.user.pop("profile", None)
    ui.navigate.to("/login")


def layout() -> dict | None:
    """Dibuixa la capçalera i comprova la sessió.

    Torna l'usuari autenticat, o None si no n'hi ha: qui la crida ha de fer
    return immediatament en eixe cas.
    """
    if not client.is_logged_in():
        ui.navigate.to("/login")
        return None

    me = profile()
    if me is None:
        ui.navigate.to("/login")
        return None

    with ui.header().classes("items-center"):
        ui.image("/static/logo.png").classes("w-32 mr-4")

        for label, path, required in PAGES:
            if required and me["role"] != required:
                continue
            ui.button(label, on_click=lambda p=path: ui.navigate.to(p)).props(
                "flat color=white no-caps"
            )

        ui.space()
        ui.button(
            f"{me['username']} ({me['role']})", on_click=change_password
        ).props("flat color=white no-caps")
        ui.button("Eixir", on_click=logout).props("flat color=white no-caps")

    return me