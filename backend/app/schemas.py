from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class TelemetryIn(BaseModel):
    device_id: str
    ts: Optional[datetime] = None
    metric: Dict[str, Any]


class TelemetryOut(BaseModel):
    id: int
    device_id: str
    ts: datetime
    metric_name: str
    metric_value: float

    class Config:
        from_attributes = True


class ConfigPush(BaseModel):
    config: Dict[str, Any] = Field(..., description="Configuration payload to push")


class ConfigOut(BaseModel):
    id: int
    device_id: str
    config_payload: str
    state: str
    created_at: datetime
    applied_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeviceOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
