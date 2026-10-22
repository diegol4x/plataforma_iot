from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_validator

def _to_utc(instant: datetime) -> datetime:
    """Normalitza una marca temporal a UTC."""
    if instant.tzinfo is None:
        return instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(timezone.utc)


class CanonicalRecord(BaseModel):

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=64)
    value: float
    unit: str = Field(min_length=1, max_length=16)
    time: datetime

    @field_validator("time")
    @classmethod
    def _normalize_time(cls, instant: datetime) -> datetime:
        return _to_utc(instant)

class CanonicalUplink(BaseModel):

    model_config = ConfigDict(frozen=True)

    source: str = Field(min_length=1, max_length=32)
    device_id: str = Field(min_length=1, max_length=64)
    received_at: datetime
    records: list[CanonicalRecord] = Field(min_length=1)

    # Sac lliure: cada transformador decidix què va dins
    uplink_metadata: dict = Field(default_factory=dict)


    @field_validator("received_at")
    @classmethod
    def _normalize_received_at(cls, instant: datetime) -> datetime:
        return _to_utc(instant)