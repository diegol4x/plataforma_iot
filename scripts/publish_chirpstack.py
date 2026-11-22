import json
from datetime import datetime, timezone
from pathlib import Path

from mqtt import send

event = json.loads(Path("tests/fixtures/chirpstack_uplink.json").read_text(encoding="utf-8"))
event["time"] = datetime.now(timezone.utc).isoformat()
event["object"] = {
    "temperatureSensor": {"1": 21.5},
    "humiditySensor": {"2": 55.0},
    "barometer": {"3": 1013.2},
}

topic = "application/fc081e09-a142-44f5-8a33-ef44c1e9ff62/device/804f6944ce5483dd/event/up"
send(topic, json.dumps(event))
print("Publicat")