"""Connexió MQTT compartida pels scripts de proves."""

import paho.mqtt.publish as publish

from plataforma_iot.config import settings


def send(topic: str, payload: str, hostname: str = "localhost") -> None:
    """Publica un missatge en el broker de la plataforma"""
    
    auth = None
    if settings.mqtt_username is not None:
        auth = {
            "username": settings.mqtt_username,
            "password": settings.mqtt_password,
        }

    publish.single(
        topic, payload, hostname=hostname, port=settings.mqtt_port, auth=auth
    )