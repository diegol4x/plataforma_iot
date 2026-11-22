"""Comprovació de sessió abans de servir qualsevol pàgina protegida."""

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app
from starlette.middleware.base import BaseHTTPMiddleware

PUBLIC = {"/login"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Redirigix al login abans de construir cap pàgina protegida.

    Fer-ho amb ui.navigate.to() dins de la pàgina no és fiable: la pàgina ja
    s'ha enviat al navegador i l'ordre pot perdre's, deixant una pantalla en
    blanc sense cap explicació.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if not path.startswith("/_nicegui") and path not in PUBLIC:
            if "token" not in app.storage.user:
                return RedirectResponse("/login")

        return await call_next(request)


def install() -> None:
    app.add_middleware(AuthMiddleware)