"""Aplicació FastAPI: exposa la telemetria ingerida."""

from fastapi import FastAPI

from plataforma_iot.api.routers import (
    devices, 
    sensors, 
    readings, 
    discards, 
    catalog, 
    auth, 
    spaces,
    workgroup,
    project,
    users,
    uplinks
    )

app = FastAPI(title="Plataforma IoT", version="0.1.0")

app.include_router(devices.router)
app.include_router(sensors.router)
app.include_router(readings.router)
app.include_router(discards.router)
app.include_router(catalog.router)
app.include_router(auth.router)
app.include_router(spaces.router)
app.include_router(workgroup.router)
app.include_router(project.router)
app.include_router(users.router)
app.include_router(uplinks.router)