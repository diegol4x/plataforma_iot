"""Proves de l'encaminament de missatges."""

from datetime import datetime, timezone

import pytest

from plataforma_iot.domain.canonical import CanonicalRecord, CanonicalUplink
from plataforma_iot.domain.exceptions import UnknownTopic
from plataforma_iot.ingestion.router import Router

RECEIVED_AT = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)

class FakeTransformer:
    """Transformador de mockup"""

    def __init__(self, source: str) -> None:
        self.source = source
        self.calls: list[tuple[str, bytes]] = []

    def transform(self, topic: str, payload: bytes, received_at: datetime) -> CanonicalUplink:
        self.calls.append((topic, payload))
        return CanonicalUplink(
            source=self.source,
            device_id="dispositiu_fals",
            received_at=received_at,
            records=[
                CanonicalRecord(
                    name="temperature", value=1.0, unit="Cel", time=received_at
                )
            ],
        )

def test_delegates_to_the_matching_transformer():
    own = FakeTransformer("own")
    chirpstack = FakeTransformer("chirpstack")
    router = Router({"plataforma/v1/": own, "application/": chirpstack})

    uplink = router.delegate_transformation(
        "plataforma/v1/node-00/up", b"{}", RECEIVED_AT
    )

    assert uplink.source == "own"
    assert len(own.calls) == 1
    assert chirpstack.calls == []

def test_passes_topic_and_payload_unchanged():
    own = FakeTransformer("own")
    router = Router({"plataforma/v1/": own})

    router.delegate_transformation("plataforma/v1/node-00/up", b"payload", RECEIVED_AT)

    assert own.calls == [("plataforma/v1/node-00/up", b"payload")]

def test_rejects_an_unregistered_topic():
    router = Router({"plataforma/v1/": FakeTransformer("own")})

    with pytest.raises(UnknownTopic):
        router.delegate_transformation("desconegut/node-00", b"{}", RECEIVED_AT)


def test_rejects_any_topic_when_there_are_no_routes():
    router = Router({})

    with pytest.raises(UnknownTopic):
        router.delegate_transformation("plataforma/v1/node-00/up", b"{}", RECEIVED_AT)