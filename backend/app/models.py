import enum
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ConfigState(str, enum.Enum):
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"


class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    telemetry = relationship("Telemetry", back_populates="device", cascade="all, delete-orphan")
    configs = relationship(
        "DeviceConfig",
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="DeviceConfig.created_at.desc()",
    )


class Telemetry(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False, index=True)
    ts = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)

    device = relationship("Device", back_populates="telemetry")


class DeviceConfig(Base):
    __tablename__ = "device_configs"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False, index=True)
    config_payload = Column(Text, nullable=False)
    state = Column(String, default=ConfigState.PENDING.value)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)

    device = relationship("Device", back_populates="configs")
