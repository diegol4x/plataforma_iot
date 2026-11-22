"""Client MQTT. Reb missatges, els transforma i els persistix."""

import json
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from plataforma_iot.config import settings
from plataforma_iot.db import get_session
from plataforma_iot.domain.exceptions import IngestionError

from plataforma_iot.ingestion.persistence import persist
from plataforma_iot.ingestion.router import Router
from plataforma_iot.ingestion.sources import SOURCES, build_router

from plataforma_iot.models.telemetry import Discard
from plataforma_iot.models.device import Device


def on_connect(client, userdata, flags, reason_code, properties=None) -> None:
    print(f"Connectat a MQTT ({settings.mqtt_host}:{settings.mqtt_port}): {reason_code}")
    for source in SOURCES:
        client.subscribe(source.topic_filter)
        print(f"Subscrit a: {source.topic_filter}")


def on_message(client, userdata, msg: mqtt.MQTTMessage) -> None:
    print(f"Rebut: {msg.topic}")
    received_at = datetime.now(timezone.utc)
    router: Router = userdata

    try:
        uplink = router.transform(msg.topic, msg.payload, received_at)
        with get_session() as session:
            persist(session, uplink)
        print(f"Ingerit: {msg.topic} ({len(uplink.records)} lectures)")
    except IngestionError as exc:
        _discard(msg, received_at, exc)
        print(f"Descartat [{exc.reason}]: {msg.topic}")

def _discard(msg: mqtt.MQTTMessage, received_at: datetime, exc: IngestionError) -> None:
    """Guarda el missatge que no s'ha pogut ingerir"""

    with get_session() as session:
        session.add(
            Discard(
                received_at=received_at,
                topic=msg.topic,
                source=exc.source,
                device_id=exc.device_id,
                raw_payload=msg.payload.decode("utf-8", errors="replace"),
                reason=exc.reason,
                detail={"message": str(exc)},
            )
        )
        if exc.source is not None and exc.device_id is not None:
            device = session.get(Device, (exc.source, exc.device_id))
            if device is not None:
                device.last_seen = received_at
                
        session.commit()


def run() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=build_router())
    client.on_connect = on_connect
    client.on_message = on_message

    if settings.mqtt_username is not None:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    run()