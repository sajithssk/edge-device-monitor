#!/usr/bin/env python3
"""Edge Device Simulator. Simulates 3 devices sending telemetry and ack-ing config changes."""
import asyncio
import json
import random
import logging
from datetime import datetime
from websockets import connect

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("simulator")

BACKEND_WS = "ws://localhost:8000/ws"
DEVICES = [
    {"id": "dev-001", "metrics": ["temperature", "cpu_percent"]},
    {"id": "dev-002", "metrics": ["humidity", "battery"]},
    {"id": "dev-003", "metrics": ["pressure", "vibration"]},
]


async def device_loop(device_info):
    device_id = device_info["id"]
    metrics = device_info["metrics"]

    while True:
        try:
            async with connect(BACKEND_WS) as ws:
                await ws.send(json.dumps({"type": "device", "device_id": device_id}))
                logger.info("[%s] Connected", device_id)

                telemetry_task = asyncio.create_task(send_telemetry(ws, device_id, metrics))
                listen_task = asyncio.create_task(listen(ws, device_id))

                done, pending = await asyncio.wait(
                    [telemetry_task, listen_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                for task in done:
                    exc = task.exception()
                    if exc:
                        raise exc
        except Exception as e:
            logger.warning("[%s] Connection lost: %s. Reconnecting in 3s...", device_id, e)
            await asyncio.sleep(3)


async def send_telemetry(ws, device_id, metrics):
    while True:
        metric = {name: round(random.uniform(10, 100), 2) for name in metrics}
        msg = {
            "type": "telemetry",
            "ts": datetime.utcnow().isoformat() + "Z",
            "metric": metric,
        }
        await ws.send(json.dumps(msg))
        await asyncio.sleep(2)


async def listen(ws, device_id):
    async for message in ws:
        try:
            data = json.loads(message)
            if data.get("type") == "config_push":
                config_id = data.get("config_id")
                config = data.get("config")
                logger.info("[%s] Received config %s: %s", device_id, config_id, config)
                await asyncio.sleep(random.uniform(0.5, 2.0))
                await ws.send(json.dumps({
                    "type": "config_ack",
                    "config_id": config_id,
                    "success": True,
                }))
                logger.info("[%s] Acked config %s", device_id, config_id)
        except Exception as e:
            logger.warning("[%s] Error handling message: %s", device_id, e)


async def main():
    await asyncio.gather(*(device_loop(d) for d in DEVICES))


if __name__ == "__main__":
    asyncio.run(main())
