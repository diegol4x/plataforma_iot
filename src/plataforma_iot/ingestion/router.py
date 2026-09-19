"""Routing dels missatges cap al transformador que toca"""

from datetime import datetime
from plataforma_iot.domain.canonical import CanonicalUplink
from plataforma_iot.domain.exceptions import UnknownTopic
from plataforma_iot.ingestion.transformers.base import Transformer
from plataforma_iot.ingestion.transformers.own import OwnTransformer


class Router:

    def __init__(self, routes: dict[str, Transformer]) -> None:
        self._routes = routes

    def transform(self, topic: str, payload: bytes, received_at: datetime) ->  CanonicalUplink:
        """Delega en el transformador encarregat del topic"""

        transformer = self._resolve(topic)
        return transformer.transform(topic, payload, received_at)

    def _resolve(self, topic:str) -> Transformer:
        for prefix, transformer in self._routes.items():
            if(topic.startswith(prefix)):
                return transformer
        raise UnknownTopic(f"cap transformador registrat per a {topic}")