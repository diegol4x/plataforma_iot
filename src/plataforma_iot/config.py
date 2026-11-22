"""Configuració centralitzada de l'aplicació, a partir de variables d'entorn."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Configuració de l'aplicació."""

    database_url: str
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str | None
    mqtt_password: str | None
    silent_after_seconds: int
    sweep_interval_seconds: int
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int


def load_settings() -> Settings:
    """Llig la configuració de l'entorn.

    Els secrets (base de dades i JWT) no tenen valor per defecte: si falten,
    l'aplicació no arrenca, en lloc d'arrencar amb unes credencials conegudes.
    """
    return Settings(
        database_url=os.environ["DATABASE_URL"],
        mqtt_host=os.environ.get("MQTT_HOST", "localhost"),
        mqtt_port=int(os.environ.get("MQTT_PORT", "1883")),
        mqtt_username=os.environ.get("MQTT_USERNAME"),
        mqtt_password=os.environ.get("MQTT_PASSWORD"),
        silent_after_seconds=int(os.environ.get("SILENT_AFTER_SECONDS", 3600)),
        sweep_interval_seconds=int(os.environ.get("SWEEP_INTERVAL_SECONDS", 300)),
        jwt_secret=os.environ["JWT_SECRET"],
        jwt_algorithm=os.environ.get("JWT_ALGORITHM", "HS256"),
        jwt_expire_minutes=int(os.environ.get("JWT_EXPIRE_MINUTES", 30)),
    )


settings = load_settings()