"""Proves de la taula de fonts."""

from plataforma_iot.ingestion.sources import SOURCES, build_router
from plataforma_iot.ingestion.transformers.chirpstack import ChirpStackTransformer
from plataforma_iot.ingestion.transformers.own import OwnTransformer


def test_every_topic_filter_starts_with_its_prefix():
    for source in SOURCES:
        assert source.topic_filter.startswith(source.prefix)


def test_prefixes_are_unique():
    prefixes = [source.prefix for source in SOURCES]
    assert len(prefixes) == len(set(prefixes))


def test_router_resolves_real_topics():
    router = build_router()

    assert isinstance(router._resolve("plataforma/v1/node-00/up"), OwnTransformer)
    assert isinstance(
        router._resolve(
            "application/fc081e09-a142-44f5-8a33-ef44c1e9ff62"
            "/device/804f6944ce5483dd/event/up"
        ),
        ChirpStackTransformer,
    )