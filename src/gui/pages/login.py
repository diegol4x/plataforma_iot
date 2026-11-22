"""Pantalla d'entrada."""

from nicegui import ui

from gui import client


@ui.page("/login")
def login_page() -> None:
    def try_login() -> None:
        try:
            client.login(username.value, password.value)
            ui.navigate.to("/")
        except client.ApiError as error:
            ui.notify(error.detail, color="negative")

    with ui.card().classes("absolute-center w-96"):
        ui.label("Plataforma IoT").classes("text-2xl")
        username = ui.input("Usuari").classes("w-full")
        password = ui.input("Contrasenya", password=True).classes("w-full")
        password.on("keydown.enter", try_login)
        ui.button("Entrar", on_click=try_login).classes("w-full")