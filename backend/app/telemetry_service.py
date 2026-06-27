import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Telemetry
from app.websocket import manager

logger = logging.getLogger(__name__)


async def ingest_telemetry(db: AsyncSession, device_id: str, metric: dict, ts: datetime = None):
    if ts is None:
        ts = datetime.utcnow()

    records = []
    for name, value in metric.items():
        if isinstance(value, (int, float)):
            rec = Telemetry(
                device_id=device_id,
                ts=ts,
                metric_name=name,
                metric_value=float(value),
            )
            db.add(rec)
            records.append(rec)

    await db.commit()

    for rec in records:
        await manager.broadcast_to_frontends({
            "type": "telemetry",
            "device_id": rec.device_id,
            "ts": rec.ts.isoformat(),
            "metric_name": rec.metric_name,
            "metric_value": rec.metric_value,
        })

    return records
