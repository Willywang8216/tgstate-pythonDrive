from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from ..events import file_update_queue


router = APIRouter()


@router.get("/api/file-updates")
async def file_updates(request: Request):
    async def event_generator():
        subscriber_queue = await file_update_queue.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break

                try:
                    update_json = await asyncio.wait_for(subscriber_queue.get(), timeout=15)
                    yield {"data": update_json}
                except asyncio.TimeoutError:
                    yield {"comment": "keepalive"}
                except asyncio.CancelledError:
                    break
                except Exception:
                    yield {"comment": "keepalive"}
        finally:
            await file_update_queue.unsubscribe(subscriber_queue)

    return EventSourceResponse(event_generator())

