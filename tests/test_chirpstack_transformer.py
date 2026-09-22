"""Proves transformador ChirpStack"""

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
from plataforma_iot.ingestion.transformers.chirpstack import ChirpStackTransformer

FIXTURES = Path(__file__).parent / "fixtures"
TOPIC = (
    "application/fc081e09-a142-44f5-8a33-ef44c1e9ff62"
    "/device/804f6944ce5483dd/event/up"
)

RECEIVED_AT = datetime(2026, 9, 21, 17, 27, 50, tzinfo=timezone.utc)
BME280_OBJECT = {
    "temperatureSensor": {"1": 21.5},
    "humiditySensor": {"2": 55.0},
    "barometer": {"3": 1013.2},
}

@pytest.fixture
def transformer() -> ChirpStackTransformer:
    return ChirpStackTransformer()


@pytest.fixture
def event() -> dict:
    """Còpia fresca de l'event/up real, com a diccionari modificable."""
    return json.loads((FIXTURES / "chirpstack_uplink.json").read_text(encoding="utf-8"))


def _encode(event: dict) -> bytes:
    return json.dumps(event).encode()


# --- Casos vàlids ---

def test_transforms_a_complete_uplink(transformer, event):
    event["object"] = BME280_OBJECT
    uplink = transformer.transform(TOPIC, _encode(event), RECEIVED_AT)

    assert uplink.source == "chirpstack"
    assert uplink.device_id == "804f6944ce5483dd"
    assert uplink.received_at == RECEIVED_AT
    assert len(uplink.records) == 3

    by_name = {record.name: record for record in uplink.records}
    assert by_name["temperature"].value == 21.5
    assert by_name["temperature"].unit == "Cel"
    assert by_name["humidity"].unit == "%RH"
    assert by_name["pressure"].unit == "hPa"


def test_ignores_unsupported_types_alongside_supported_ones(transformer, event):
    event["object"] = {"analogInput": {"1": 0.15}, "temperatureSensor": {"1": 21.5}}
    uplink = transformer.transform(TOPIC, _encode(event), RECEIVED_AT)

    assert [record.name for record in uplink.records] == ["temperature"]


def test_truncates_nanoseconds_to_utc_microseconds(transformer, event):
    event["object"] = BME280_OBJECT
    uplink = transformer.transform(TOPIC, _encode(event), RECEIVED_AT)

    time = uplink.records[0].time
    assert time.microsecond == 506836
    assert time.utcoffset().total_seconds() == 0


def test_extracts_radio_metadata(transformer, event):
    event["object"] = BME280_OBJECT
    uplink = transformer.transform(TOPIC, _encode(event), RECEIVED_AT)

    assert uplink.gateway_id == "0016c001f116de4d"
    assert uplink.rssi == -49
    assert uplink.snr == 13.75
    assert uplink.spreading_factor == 7
    assert uplink.f_cnt == 1
    assert uplink.f_port == 1


def test_picks_gateway_with_best_rssi(transformer, event):
    event["object"] = BME280_OBJECT
    event["rxInfo"].append({"gatewayId": "aaaaaaaaaaaaaaaa", "rssi": -30, "snr": 9.0})
    uplink = transformer.transform(TOPIC, _encode(event), RECEIVED_AT)

    assert uplink.gateway_id == "aaaaaaaaaaaaaaaa"
    assert uplink.rssi == -30


def test_radio_metadata_is_optional(transformer, event):
    event["object"] = BME280_OBJECT
    event["rxInfo"] = []
    event["txInfo"] = {"frequency": 868800000, "modulation": {"fsk": {"datarate": 50000}}}
    uplink = transformer.transform(TOPIC, _encode(event), RECEIVED_AT)

    assert uplink.gateway_id is None
    assert uplink.rssi is None
    assert uplink.spreading_factor is None


def test_device_id_comes_from_payload_not_topic(transformer, event):
    event["object"] = BME280_OBJECT
    uplink = transformer.transform("application/x/device/un-altre/event/up", _encode(event), RECEIVED_AT)

    assert uplink.device_id == "804f6944ce5483dd"


# --- Rebuigs ---

def test_rejects_real_fixture_with_only_analog_input(transformer, event):
    with pytest.raises(InvalidValue, match="analogInput"):
        transformer.transform(TOPIC, _encode(event), RECEIVED_AT)


def test_rejects_non_json_payload(transformer):
    with pytest.raises(UnreadablePayload):
        transformer.transform(TOPIC, b"json que realment no es json", RECEIVED_AT)


def test_rejects_missing_dev_eui(transformer, event):
    del event["deviceInfo"]["devEui"]
    with pytest.raises(MissingField):
        transformer.transform(TOPIC, _encode(event), RECEIVED_AT)


def test_rejects_message_without_timestamp(transformer, event):
    del event["time"]
    with pytest.raises(MissingField):
        transformer.transform(TOPIC, _encode(event), RECEIVED_AT)


def test_rejects_invalid_timestamp(transformer, event):
    event["time"] = "ahir per la vesprada"
    with pytest.raises(InvalidTimestamp):
        transformer.transform(TOPIC, _encode(event), RECEIVED_AT)


def test_rejects_undecoded_payload(transformer, event):
    del event["object"]
    with pytest.raises(MissingField, match="object"):
        transformer.transform(TOPIC, _encode(event), RECEIVED_AT)


def test_rejects_non_numeric_value(transformer, event):
    event["object"] = {"temperatureSensor": {"1": "calor"}}
    with pytest.raises(InvalidValue):
        transformer.transform(TOPIC, _encode(event), RECEIVED_AT)


def test_invalid_field_becomes_ingestion_error(transformer, event):
    """Un ValidationError de Pydantic no ha d'escapar: tombaria el subscriber."""
    event["object"] = BME280_OBJECT
    event["fCnt"] = "no és un número"
    with pytest.raises(InvalidValue):
        transformer.transform(TOPIC, _encode(event), RECEIVED_AT)