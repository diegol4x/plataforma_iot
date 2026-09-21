"""Aplicació FastAPI: exposa la telemetria ingerida."""

from fastapi import FastAPI

from plataforma_iot.api.routers import devices, sensors, readings, discards

app = FastAPI(title="Plataforma IoT", version="0.1.0")

app.include_router(devices.router)
app.include_router(sensors.router)
app.include_router(readings.router)
app.include_router(discards.router)