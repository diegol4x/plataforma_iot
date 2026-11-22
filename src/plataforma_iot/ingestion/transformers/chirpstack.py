"""Transformer de ChirpStack v4: esdeveniments event/up amb còdec CayenneLPP."""

import json
from datetime import datetime

from pydantic import ValidationError

from plataforma_iot.domain.canonical import CanonicalRecord, CanonicalUplink
from plataforma_iot.domain.exceptions import (
    IngestionError,
    InvalidTimestamp,
    InvalidValue,
    MissingField,
    UnreadablePayload,
)

SOURCE = "chirpstack"

CAYENNE_TYPES: dict[str, tuple[str, str]] = {
    "temperatureSensor": ("temperature", "Cel"),
    "humiditySensor": ("humidity", "%RH"),
    "barometer": ("pressure", "hPa"),
}

# El còdec CayenneLPP de ChirpStack només descodifica els tipus bàsics, i la
# bateria arriba com a entrada analògica. Sols es llig en aquest canal: una
# entrada analògica en un altre canal no se sap què mesura.
BATTERY_TYPE = "analogInput"
BATTERY_CHANNEL = "4"


class ChirpStackTransformer:
    """Convertix un event/up de ChirpStack a format canònic"""

    source = SOURCE

    def transform(self, topic: str, payload: bytes, received_at: datetime) -> CanonicalUplink:
        data = self._decode(payload)
        device_id = self._device_id(data)
        try:
            return self._build(data, device_id, received_at)
        except IngestionError as exc:
            exc.with_identity(SOURCE, device_id)
            raise

    def _build(self, data: dict, device_id: str, received_at: datetime) -> CanonicalUplink:
        """Construïx el canònic un cop coneguda la identitat del dispositiu."""
        time = self._parse_time(data)
        records = self._build_records(data, time)

        metadata = self._metadata(data)
        battery = self._battery(data)
        if battery is not None:
            metadata["battery_level"] = battery

        try:
            return CanonicalUplink(
                source=SOURCE,
                device_id=device_id,
                received_at=received_at,
                records=records,
                uplink_metadata=metadata,
            )
        except ValidationError as exc:
            raise InvalidValue(f"uplink no vàlid: {exc.error_count()} errors") from exc

    def _decode(self, payload: bytes) -> dict:
        """Descodifica el payload i comprova que siga un JSON"""

        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise UnreadablePayload(str(exc)) from exc

        if not isinstance(data, dict):
            raise UnreadablePayload("s'esperava un objecte JSON")

        return data

    def _device_id(self, data: dict) -> str:
        """Obté el DevEUI"""

        dev_eui = (data.get("deviceInfo") or {}).get("devEui")

        if not dev_eui:
            raise MissingField('falta el camp "deviceInfo.devEui"')

        return dev_eui

    def _parse_time(self, data: dict) -> datetime:
        """Interpreta el camp 'time'"""

        raw = data.get("time")

        if raw is None:
            raise MissingField("falta el camp 'time'")

        try:
            return datetime.fromisoformat(raw)
        except (TypeError, ValueError) as exc:
            raise InvalidTimestamp(f"Marca temporal invàlida: {raw!r}") from exc

    def _build_records(self, data: dict, time: datetime) -> list[CanonicalRecord]:
        """Construïx un registre per cada lectura CayenneLPP suportada"""

        obj = data.get("object")

        if obj is None:
            raise MissingField("Falta el camp 'object' (dispositiu sense còdec o còdec fallit)")
        if not isinstance(obj, dict):
            raise InvalidValue(f"'object' amb format inesperat: {obj!r}")

        records = []
        ignored = []

        for lpp_type, channels in obj.items():
            mapping = CAYENNE_TYPES.get(lpp_type)

            if mapping is None or not isinstance(channels, dict):
                ignored.append(lpp_type)
                continue

            name, unit = mapping

            for value in channels.values():
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise InvalidValue(f"Valor no numèric a {lpp_type}: {value!r}")

                records.append(
                    CanonicalRecord(name=name, value=float(value), unit=unit, time=time)
                )

        if not records:
            raise InvalidValue(f"cap lectura CayenneLPP suportada; tipus ignorats: {ignored}")

        return records

    def _battery(self, data: dict) -> int | None:
        """Nivell de bateria en percentatge, si el node l'envia."""

        channels = (data.get("object") or {}).get(BATTERY_TYPE)
        if not isinstance(channels, dict):
            return None

        value = channels.get(BATTERY_CHANNEL)
        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidValue(f"Bateria no numèrica: {value!r}")

        return max(0, min(100, round(value)))

    def _metadata(self, data: dict) -> dict:
        """Aplana rxInfo i txInfo dins del sac de metadades"""

        rx_info = [rx for rx in data.get("rxInfo") or [] if isinstance(rx, dict)]
        best = max(rx_info, key=lambda rx: rx.get("rssi", float("-inf")), default=None)
        lora = ((data.get("txInfo") or {}).get("modulation") or {}).get("lora") or {}

        metadata = {
            "gateway_id": best.get("gatewayId") if best else None,
            "rssi": best.get("rssi") if best else None,
            "snr": best.get("snr") if best else None,
            "spreading_factor": lora.get("spreadingFactor"),
            "f_cnt": data.get("fCnt"),
            "f_port": data.get("fPort"),
        }

        return {key: value for key, value in metadata.items() if value is not None}