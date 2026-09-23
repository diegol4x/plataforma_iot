"""Proves del transformador de la font pròpia."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from plataforma_iot.domain.exceptions import (
    InvalidTimestamp,
    InvalidValue,
    MissingField,
    UnreadablePayload,
)
from plataforma_iot.ingestion.transformers.own import OwnTransformer

FIXTURES = Path(__file__).parent / "fixtures"
TOPIC = "plataforma/v1/node-00/up"
RECEIVED_AT = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)

@pytest.fixture
def transformer() -> OwnTransformer:
    return OwnTransformer()

@pytest.fixture
def payload() -> bytes:
    return (FIXTURES / "own_uplink.json").read_bytes()

def test_transforms_a_complete_uplink(transformer, payload):
    uplink = transformer.transform(TOPIC, payload, RECEIVED_AT)

    assert uplink.source == "own"
    assert uplink.device_id == "node-00"
    assert uplink.received_at == RECEIVED_AT
    assert len(uplink.records) == 2

    temperature = next(record for record in uplink.records if record.name == "temperature")
    assert temperature.value == 30.82
    assert temperature.unit == "Cel"
    assert temperature.time.tzinfo is not None

def test_device_id_comes_from_topic(transformer, payload):
    uplink = transformer.transform("plataforma/v1/altre-node/up", payload, RECEIVED_AT)
    assert uplink.device_id == "altre-node"

def test_rejects_malformed_topic(transformer, payload):
    with pytest.raises(MissingField):
        transformer.transform("un/topic/malformat", payload, RECEIVED_AT)

def test_rejects_non_json_payload(transformer):
    with pytest.raises(UnreadablePayload):
        transformer.transform(TOPIC, b"json que realment no es json", RECEIVED_AT)

def test_rejects_message_without_timestamp(transformer):
    payload = json.dumps({"readings": []}).encode()
    with pytest.raises(MissingField):
        transformer.transform(TOPIC, payload, RECEIVED_AT)

def test_rejects_invalid_timestamp(transformer):
    payload = json.dumps({"time": "ahir per la vesprada", "readings": []}).encode()
    with pytest.raises(InvalidTimestamp):
        transformer.transform(TOPIC, payload, RECEIVED_AT)

def test_rejects_non_numeric_value(transformer):
    payload = json.dumps(
        {
            "time": "2026-09-19T09:33:43+00:00",
            "readings": [{"name": "temperature", "unit": "Cel", "value": "calor"}],
        }
    ).encode()
    with pytest.raises(InvalidValue):
        transformer.transform(TOPIC, payload, RECEIVED_AT)

def test_rejects_empty_readings_list(transformer):
    payload = json.dumps({"time": "2026-09-19T09:33:43+00:00", "readings": []}).encode()
    with pytest.raises(InvalidValue):
        transformer.transform(TOPIC, payload, RECEIVED_AT)

def test_error_after_identity_carries_it(transformer):
    payload = json.dumps({"readings": []}).encode()
    with pytest.raises(MissingField) as info:
        transformer.transform(TOPIC, payload, RECEIVED_AT)
    assert (info.value.source, info.value.device_id) == ("own", "node-00")


def test_malformed_topic_has_no_identity(transformer, payload):
    with pytest.raises(MissingField) as info:
        transformer.transform("un/topic/malformat", payload, RECEIVED_AT)
    assert info.value.device_id is None
