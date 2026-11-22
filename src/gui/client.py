"""Client de l'API REST per a la interfície."""

import os

import httpx
import asyncio
from dotenv import load_dotenv
from nicegui import app

load_dotenv()

API_URL = os.environ.get("API_URL", "http://localhost:8000")


class ApiError(Exception):
    """Error retornat per l'API, amb el seu missatge original."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


def login(username: str, password: str) -> None:
    """Demana un token i el guarda en la sessió."""
    response = httpx.post(
        f"{API_URL}/auth/token", data={"username": username, "password": password}
    )

    if response.status_code != 200:
        detail = response.json().get("detail", "Usuari o contrasenya incorrectes")
        raise ApiError(response.status_code, str(detail).title())

    app.storage.user["token"] = response.json()["access_token"]


def logout() -> None:
    app.storage.user.pop("token", None)


def is_logged_in() -> bool:
    return "token" in app.storage.user


def request(method: str, path: str, **kwargs):
    """Crida l'API amb el token de la sessió.

    Centralitza la capçalera i la traducció d'errors: si cada pàgina ho fera
    pel seu compte, el maneig del 401 acabaria repetit per tot arreu.
    """
    token = app.storage.user.get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    response = httpx.request(method, f"{API_URL}{path}", headers=headers, **kwargs)

    if response.status_code == 401:
        logout()
        raise ApiError(401, "La sessió ha caducat")

    if response.status_code >= 400:
        detail = response.json().get("detail", "Error desconegut")
        raise ApiError(response.status_code, str(detail))

    return response.json() if response.content else None


def get(path: str, **params):
    """Els paràmetres a None no s'envien: així una pàgina pot passar-los tots."""
    clean = {k: v for k, v in params.items() if v is not None}
    return request("GET", path, params=clean)


def post(path: str, payload: dict):
    return request("POST", path, json=payload)


def patch(path: str, payload: dict):
    return request("PATCH", path, json=payload)


def put(path: str) -> None:
    request("PUT", path)


def delete(path: str) -> None:
    request("DELETE", path)

def count(path: str, **params) -> int:
    """Quantes files hi ha amb estos filtres, sense portar-se'n cap.

    Demana una sola fila i llig el total de la capçalera: és el que permet al
    taulell mostrar xifres sense descarregar milers d'objectes.
    """
    clean = {k: v for k, v in params.items() if v is not None} | {"limit": 1}
    token = app.storage.user.get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    response = httpx.get(f"{API_URL}{path}", headers=headers, params=clean)

    if response.status_code >= 400:
        raise ApiError(response.status_code, "No s'ha pogut comptar")

    return int(response.headers.get("X-Total-Count", 0))

async def gather(paths: list[str]) -> list:
    """Fa totes estes crides alhora en lloc d'una darrere l'altra.

    Amb una llista llarga, el temps passa de ser la suma de totes a ser el de
    la més lenta. És un pedaç: el servidor seguix atenent-les totes, i la
    solució de fons és que l'API torne les dades agregades.
    """
    token = app.storage.user.get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    async with httpx.AsyncClient(headers=headers, base_url=API_URL) as session:
        responses = await asyncio.gather(
            *(session.get(path) for path in paths), return_exceptions=True
        )

    results = []
    for response in responses:
        if isinstance(response, Exception) or response.status_code >= 400:
            results.append(None)
        else:
            results.append(response.json())

    return results