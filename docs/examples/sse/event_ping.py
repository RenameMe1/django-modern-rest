import asyncio
from collections.abc import AsyncIterator

from django.http import HttpRequest

from dmr.plugins.msgspec import MsgspecSerializer
from dmr.sse import (
    SSEContext,
    SSEResponse,
    SSEvent,
    sse,
)


async def produce_user_events() -> AsyncIterator[SSEvent[bytes]]:
    for _ in range(2):
        await asyncio.sleep(1)
        yield SSEvent(b'message')


@sse(MsgspecSerializer, ping_interval=0)
async def user_events(
    request: HttpRequest,
    context: SSEContext,
) -> SSEResponse[SSEvent[bytes]]:
    return SSEResponse(produce_user_events())
