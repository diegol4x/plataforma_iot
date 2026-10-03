"""Script periòdic que marca com a silenciosos els dispositius que no transmeten"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from plataforma_iot.domain.device_status import DeviceStatus
from plataforma_iot.models.device import Device


def sweep_silent_devices(session: Session, threshold: timedelta) -> list[Device]:
    """Passa a SILENT els dispositius ACTIVE sense senyal des de fa massa temps"""
    deadline = datetime.now(timezone.utc) - threshold

    devices = session.scalars(
        select(Device).where(
            Device.status == DeviceStatus.ACTIVE,
            Device.last_seen < deadline,
        )
    ).all()

    for device in devices:
        device.status = DeviceStatus.SILENT

    session.commit()
    return list(devices)