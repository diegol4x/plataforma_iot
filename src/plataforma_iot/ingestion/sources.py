"""Taula de fonts de telemetria"""

from typing import NamedTuple

from plataforma_iot.ingestion.router import Router
from plataforma_iot.ingestion.transformers.base import Transformer
from plataforma_iot.ingestion.transformers.chirpstack import ChirpStackTransformer
from plataforma_iot.ingestion.transformers.own import OwnTransformer

class Source(NamedTuple):
    """Font: on se subscriu, com s'encamina i qui la transforma."""

    topic_filter: str
    prefix: str
    transformer: Transformer

SOURCES: tuple[Source, ...] = (
    Source("plataforma/v1/+/up", "plataforma/v1/", OwnTransformer()),
    Source("application/+/device/+/event/up", "application/", ChirpStackTransformer()),
)

def build_router() -> Router:
    """Crea un router a partir de la taula de fonts."""
    return Router({source.prefix: source.transformer for source in SOURCES})