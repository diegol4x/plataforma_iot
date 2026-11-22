"""Publicador de proves: envia uplinks sintètics al broker."""

import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from plataforma_iot.config import settings

DEVICE_ID = "node-00"
TOPIC = f"plataforma/v1/{DEVICE_ID}/up"


def build_payload() -> dict:
    return {
        "time": datetime.now(timezone.utc).isoformat(),
        "readings": [
            {"name": "temperature", "unit": "Cel", "value": round(random.uniform(25, 33), 2)},
            {"name": "humidity", "unit": "%RH", "value": round(random.uniform(70, 90), 2)},
        ],
    }


def run(interval: int = 5) -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    if settings.mqtt_username is not None:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
    client.loop_start()

    try:
        while True:
            payload = build_payload()
            client.publish(TOPIC, json.dumps(payload))
            print(f"Publicat en {TOPIC}: {payload}")
            time.sleep(interval)
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()