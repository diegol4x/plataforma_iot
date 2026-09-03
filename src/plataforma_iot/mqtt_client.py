"""Cliente MQTT: se suscribe a lecturas de sensores y las persiste."""
import json
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from plataforma_iot.config import settings
from plataforma_iot.db import get_session, init_db
from plataforma_iot.models import Lectura


def on_connect(client: mqtt.Client, userdata: None, flags: dict, reason_code, properties=None) -> None:
    print(f"Conectado a MQTT ({settings.mqtt_host}:{settings.mqtt_port}) con código: {reason_code}")
    client.subscribe(settings.mqtt_topic)
    print(f"Suscrito a: {settings.mqtt_topic}")


def on_message(client: mqtt.Client, userdata: None, msg: mqtt.MQTTMessage) -> None:
    try:
        payload = json.loads(msg.payload.decode())
        sensor_id = payload["sensor_id"]
        valor = float(payload["valor"])
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Mensaje inválido en {msg.topic}: {e}")
        return

    lectura = Lectura(sensor_id=sensor_id, valor=valor, timestamp=datetime.now(timezone.utc))

    with get_session() as session:
        session.add(lectura)
        session.commit()
        print(f"Guardada: {lectura}")


def run() -> None:
    init_db()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
    client.loop_forever()