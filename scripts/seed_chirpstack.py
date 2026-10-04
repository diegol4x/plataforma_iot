"""Carrega lectures de prova"""

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import paho.mqtt.publish as publish

TOPIC = (
    "application/fc081e09-a142-44f5-8a33-ef44c1e9ff62"
    "/device/804f6944ce5483dd/event/up"
)
FIXTURE = Path("tests/fixtures/chirpstack_uplink.json")
HOURS = 12
STEP_MINUTES = 15


def main() -> None:
    event = json.loads(FIXTURE.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    published = 0

    for minutes_ago in range(0, HOURS * 60, STEP_MINUTES):
        event["time"] = (now - timedelta(minutes=minutes_ago)).isoformat()
        event["object"] = {
            "temperatureSensor": {"1": round(random.uniform(18.0, 26.0), 2)},
            "humiditySensor": {"2": round(random.uniform(40.0, 70.0), 2)},
            "barometer": {"3": round(random.uniform(1005.0, 1020.0), 1)},
        }
        publish.single(TOPIC, json.dumps(event), hostname="localhost", port=1883)
        published += 1

    print(f"{published} uplinks publicats")


if __name__ == "__main__":
    main()