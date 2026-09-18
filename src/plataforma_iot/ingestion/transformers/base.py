from typing import Protocol

from plataforma_iot.domain.canonical import CanonicalUplink

class Transformer(Protocol):
    """Format que ha de tindre un transformador."""
    source: str

    def transform(self, topic: str, payload: bytes) -> CanonicalUplink:
        """Convertix un missatge cru al format canònic."""