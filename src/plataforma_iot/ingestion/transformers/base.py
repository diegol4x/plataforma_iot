from typing import Protocol
from datetime import datetime

from plataforma_iot.domain.canonical import CanonicalUplink

class Transformer(Protocol):
    """Format que ha de tindre un transformador."""
    source: str

    def transform(self, topic: str, payload: bytes, received_at: datetime) -> CanonicalUplink:
        """Convertix un missatge cru al format canònic."""