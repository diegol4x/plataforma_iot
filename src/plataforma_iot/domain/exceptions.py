"""Excepcions de domini: els motius pels quals un missatge es descarta."""

from typing import Self

class IngestionError(Exception):
    """Error que impedix ingerir un missatge"""

    reason = "unknown"
    source: str | None = None
    device_id: str | None = None

    def with_identity(self, source: str, device_id: str) -> Self:
        """Associa l'error al dispositiu que ha enviat el missatge."""
        self.source = source
        self.device_id = device_id
        return self


class UnreadablePayload(IngestionError):
    """El payload no es pot descodificar (JSON invàlid, binari corrupte)."""
    
    reason = "unreadable_payload"


class MissingField(IngestionError):
    """Falta un camp obligatori per a construir el canònic."""

    reason = "missing_field"


class InvalidValue(IngestionError):
    """Un valor existix però no és del tipus o del format esperat."""

    reason = "invalid_value"


class InvalidTimestamp(IngestionError):
    """La marca temporal és absent, sense zona o fora del marge admissible."""

    reason = "invalid_timestamp"


class UnknownTopic(IngestionError):
    """Cap transformador registrat atén este topic."""

    reason = "unknown_topic"


class UnknownUnit(IngestionError):
    """La unitat rebuda no està registrada al catàleg"""

    reason = "unknown_unit"