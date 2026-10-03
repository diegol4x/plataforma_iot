"""Procés que executa les tasks periòdicament."""

import time
from datetime import timedelta

from plataforma_iot.config import settings
from plataforma_iot.db import get_session
from plataforma_iot.tasks.sweep import sweep_silent_devices


def run() -> None:
    threshold = timedelta(seconds=settings.silent_after_seconds)
    interval = settings.sweep_interval_seconds

    print(f"Agranada cada {interval}s, temps màxim en silenci: {threshold}")

    while True:
        try:
            with get_session() as session:
                silenced = sweep_silent_devices(session, threshold)
            for device in silenced:
                print(f"Silenciat: {device.source}/{device.device_id}")
        except Exception as exc:
            print(f"Error en l'agranada: {exc}")

        time.sleep(interval)


if __name__ == "__main__":
    run()
