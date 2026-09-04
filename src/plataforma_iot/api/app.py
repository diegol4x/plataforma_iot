"""API REST: expone las lecturas persistidas."""
from fastapi import FastAPI

from plataforma_iot.db import get_session
from plataforma_iot.models import Lectura
from plataforma_iot.api.schemas import LecturaOut

app = FastAPI(title="Plataforma IoT")


@app.get("/lecturas", response_model=list[LecturaOut])
def listar_lecturas(sensor_id: str | None = None, limit: int = 50) -> list[Lectura]:
    """Devuelve las últimas lecturas, opcionalmente filtradas por sensor."""

    with get_session() as session:
        query = session.query(Lectura)
        if sensor_id is not None:
            query = query.filter(Lectura.sensor_id == sensor_id)
        return query.order_by(Lectura.timestamp.desc()).limit(limit).all()