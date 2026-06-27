import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import engine, get_db, Base, AsyncSessionLocal
from app.models import Device, Telemetry, DeviceConfig, ConfigState
from app.schemas import TelemetryIn, ConfigPush, TelemetryOut, ConfigOut, DeviceOut
from app.websocket import manager
from app.telemetry_service import ingest_telemetry
from app.config_service import push_config, ack_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Device))
        if not result.scalars().all():
            devices = [
                Device(id="dev-001", name="Temperature Sensor A"),
                Device(id="dev-002", name="Humidity Sensor B"),
                Device(id="dev-003", name="Pressure Sensor C"),
            ]
            for d in devices:
                session.add(d)
            await session.commit()
            logger.info("Seeded 3 devices")

    yield
    await engine.dispose()


app = FastAPI(title="Edge Device Monitor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")


@api_router.get("/health")
async def health():
    return {"status": "ok"}


@api_router.get("/devices", response_model=list[DeviceOut])
async def list_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device))
    return result.scalars().all()


@api_router.post("/telemetry", status_code=201)
async def post_telemetry(data: TelemetryIn, db: AsyncSession = Depends(get_db)):
    try:
        await ingest_telemetry(db, data.device_id, data.metric, data.ts)
        return {"status": "accepted"}
    except Exception as e:
        logger.exception("Telemetry ingestion failed")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/devices/{device_id}/telemetry", response_model=list[TelemetryOut])
async def get_telemetry(device_id: str, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Telemetry)
        .where(Telemetry.device_id == device_id)
        .order_by(Telemetry.ts.desc())
        .limit(limit)
    )
    return result.scalars().all()


@api_router.post("/devices/{device_id}/config", response_model=ConfigOut, status_code=201)
async def post_config(device_id: str, data: ConfigPush, db: AsyncSession = Depends(get_db)):
    try:
        record = await push_config(db, device_id, data.config)
        return record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Config push failed")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/devices/{device_id}/config/latest", response_model=ConfigOut)
async def get_latest_config(device_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DeviceConfig)
        .where(DeviceConfig.device_id == device_id)
        .order_by(DeviceConfig.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="No config found")
    return record


app.include_router(api_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        init_msg = await websocket.receive_text()
        init_data = json.loads(init_msg)
        client_type = init_data.get("type")

        if client_type == "frontend":
            await handle_frontend(websocket)
        elif client_type == "device":
            device_id = init_data.get("device_id")
            if not device_id:
                await websocket.close(code=4001, reason="Missing device_id")
                return
            await handle_device(websocket, device_id)
        else:
            await websocket.close(code=4002, reason="Invalid type")
    except Exception as e:
        logger.warning("WebSocket setup error: %s", e)
        try:
            await websocket.close()
        except Exception:
            pass


async def handle_frontend(websocket: WebSocket):
    await manager.connect_frontend(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_frontend(websocket)
    except Exception as e:
        logger.warning("Frontend WS error: %s", e)
        manager.disconnect_frontend(websocket)


async def handle_device(websocket: WebSocket, device_id: str):
    await manager.connect_device(device_id, websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            msg_type = data.get("type")

            if msg_type == "telemetry":
                async with AsyncSessionLocal() as db:
                    metric = data.get("metric", {})
                    ts_str = data.get("ts")
                    ts = None
                    if ts_str:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    await ingest_telemetry(db, device_id, metric, ts)

            elif msg_type == "config_ack":
                config_id = data.get("config_id")
                success = data.get("success", True)
                if config_id:
                    async with AsyncSessionLocal() as db:
                        await ack_config(db, device_id, config_id, success)

            elif msg_type == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_device(device_id)
    except Exception as e:
        logger.warning("Device WS error: %s", e)
        manager.disconnect_device(device_id)
