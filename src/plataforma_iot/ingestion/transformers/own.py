"""Transformador de font pròpia"""

import json
from datetime import datetime

from plataforma_iot.domain.canonical import CanonicalRecord, CanonicalUplink
from plataforma_iot.domain.exceptions import (
    IngestionError,
    InvalidTimestamp,
    InvalidValue,
    MissingField,
    UnreadablePayload
)

SOURCE = "own"
TOPIC_PREFIX = "plataforma/v1/"
TOPIC_SUFFIX = "/up"

class OwnTransformer:
    """Convertix de la font pròpia a canònic"""

    source = SOURCE

    def transform(self, topic: str, payload: bytes, received_at: datetime) -> CanonicalUplink:
        device_id = self._device_id_from_topic(topic)
        try:
            return self._build(payload, device_id, received_at)
        except IngestionError as exc:
            exc.with_identity(SOURCE, device_id)
            raise

    def _build(self, payload: bytes, device_id: str, received_at: datetime) -> CanonicalUplink:
        """Construïx el canònic un cop coneguda la identitat del dispositiu."""
        data = self._decode(payload)
        time = self._parse_time(data)
        records = self._build_records(data, time)

        return CanonicalUplink(
            source=SOURCE,
            device_id=device_id,
            received_at=received_at,
            records=records,
        )

    def _device_id_from_topic(self, topic: str) -> str:
        """Extrau l'identificador del dispositiu de la ruta del topic"""

        if not topic.startswith(TOPIC_PREFIX) or not topic.endswith(TOPIC_SUFFIX):
            raise MissingField(f"topic amb format inesperat: {topic}")

        device_id = topic[len(TOPIC_PREFIX) : -len(TOPIC_SUFFIX)]

        if not device_id or "/" in device_id:
            raise MissingField(f"no s'ha pogut extraure el device_id de {topic}")

        return device_id

    def _decode(self, payload: bytes) -> dict:
        """Descodifica el payload i comprova que siga un JSON."""

        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise UnreadablePayload(str(exc)) from exc

        if not isinstance(data, dict):
            raise UnreadablePayload("s'esperava un JSON")

        return data

    def _parse_time(self, data: dict) -> datetime:
        """Interpreta la marca temporal del missatge"""
        raw = data.get("time")

        if raw is None:
            raise MissingField("falta el camp \"time\"")

        try:
            return datetime.fromisoformat(raw)
        except(TypeError, ValueError) as exc:
            raise InvalidTimestamp(f"marca temporal invàlida: {raw!r}") from exc


    def _build_records(self, data:dict, time: datetime) -> list[CanonicalRecord]:
        """Construïx un registre canònic per cada lectura del missatge."""

        readings = data.get("readings")

        if readings is None:
            raise MissingField("falta el camp 'readings'")
        if not isinstance(readings, list) or not readings:
            raise InvalidValue("'readings' ha de ser una llista no buida")

        records = []

        for reading in readings:
            if not isinstance(reading, dict):
                raise InvalidValue(f"lectura amb format inesperat: {reading!r}")

            name = reading.get("name")
            unit = reading.get("unit")
            value = reading.get("value")

            if name is None or unit is None or value is None:
                raise MissingField(f"lectura incompleta: {reading!r}")

            try:
                value = float(value)
            except (TypeError, ValueError) as exc:
                raise InvalidValue(f"valor no numèric: {value!r}") from exc

            records.append(
                CanonicalRecord(name = name, value = value, unit = unit, time = time)
            )

        return records