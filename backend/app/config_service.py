import json
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import DeviceConfig, ConfigState
from app.websocket import manager

logger = logging.getLogger(__name__)


async def push_config(db: AsyncSession, device_id: str, config: dict) -> DeviceConfig:
    from app.models import Device

    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise ValueError(f"Device {device_id} not found")

    record = DeviceConfig(
        device_id=device_id,
        config_payload=json.dumps(config),
        state=ConfigState.PENDING.value,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    sent = await manager.send_to_device(device_id, {
        "type": "config_push",
        "config_id": record.id,
        "config": config,
    })

    if not sent:
        logger.info("Device %s not online. Config %d queued.", device_id, record.id)

    await manager.broadcast_to_frontends({
        "type": "config_update",
        "device_id": device_id,
        "config_id": record.id,
        "state": record.state,
    })

    return record


async def ack_config(db: AsyncSession, device_id: str, config_id: int, success: bool = True):
    result = await db.execute(
        select(DeviceConfig).where(
            DeviceConfig.id == config_id,
            DeviceConfig.device_id == device_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        logger.warning("Ack for unknown config %d from %s", config_id, device_id)
        return None

    record.state = ConfigState.APPLIED.value if success else ConfigState.FAILED.value
    record.applied_at = datetime.utcnow()
    await db.commit()

    await manager.broadcast_to_frontends({
        "type": "config_update",
        "device_id": device_id,
        "config_id": config_id,
        "state": record.state,
        "applied_at": record.applied_at.isoformat(),
    })

    logger.info("Config %d for %s -> %s", config_id, device_id, record.state)
    return record
