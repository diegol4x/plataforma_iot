"""Base comuna dels esquemes GET"""

from pydantic import BaseModel, ConfigDict

class OutSchema(BaseModel):
    """Classe arrel de tots els esquemes de resposta"""

    model_config = ConfigDict(from_attributes=True)


class InSchema(BaseModel):
    """Classe arrel de tots els esquemes d'entrada"""

    model_config = ConfigDict(extra="forbid")