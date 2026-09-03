"""Esquemas Pydantic para la API."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LecturaOut(BaseModel):
    """Representación de una lectura para la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: str
    valor: float
    timestamp: datetime