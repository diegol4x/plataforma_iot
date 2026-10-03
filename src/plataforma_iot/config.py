"""Configuración centralizada de la aplicación, vía variables de entorno."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Configuración de la aplicación."""

    database_url: str
    mqtt_host: str
    mqtt_port: int
    silent_after_seconds: int
    sweep_interval_seconds: int


def load_settings() -> Settings:
    """Carga la configuración desde variables de entorno, con valores por defecto para desarrollo local."""
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://appuser:appuser@localhost:5432/iot_monitoring",
        ),
        mqtt_host=os.environ.get("MQTT_HOST", "localhost"),
        mqtt_port=int(os.environ.get("MQTT_PORT", "1883")),
        silent_after_seconds = int(os.environ.get("SILENT_AFTER_SECONDS", 3600)),
        sweep_interval_seconds = int(os.environ.get("SWEEP_INTERVAL_SECONDS", 300)),
    )


settings = load_settings()