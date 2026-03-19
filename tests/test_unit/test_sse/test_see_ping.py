import asyncio
from collections.abc import AsyncIterator
from http import HTTPStatus
from typing import Any

import pytest
from django.http import HttpRequest

from dmr.plugins.pydantic import PydanticSerializer
from dmr.serializer import BaseSerializer
from dmr.sse import SSEContext, SSEResponse, SSEStreamingResponse, SSEvent, sse
from dmr.test import DMRAsyncRequestFactory
from tests.infra.streaming import get_streaming_content

MsgspecSerializer: type[BaseSerializer] | None
try:
    from dmr.plugins.msgspec import MsgspecSerializer
except ImportError:  # pragma: no cover
    MsgspecSerializer = None


async def _valid_events() -> AsyncIterator[SSEvent[Any]]:
    yield SSEvent('First Message')

    await asyncio.sleep(1.05)

    yield SSEvent('Message after ping 10 ping')


@sse(PydanticSerializer, ping_interval=0.1)
async def _valid_sse_with_ping(
    request: HttpRequest,
    context: SSEContext,
) -> SSEResponse[SSEvent[Any]]:
    return SSEResponse(_valid_events())


@pytest.mark.asyncio
@pytest.mark.skipif(
    MsgspecSerializer is None,
    reason='regular json formats it differently',
)
async def test_all_sse_events_props(
    dmr_async_rf: DMRAsyncRequestFactory,
) -> None:
    """Ensures that sse produces valid results with ping events."""
    request = dmr_async_rf.get('/whatever/')

    response = await dmr_async_rf.wrap(_valid_sse_with_ping.as_view()(request))

    assert isinstance(response, SSEStreamingResponse)
    assert response.streaming
    assert response.status_code == HTTPStatus.OK
    assert await get_streaming_content(response) == (
        b'data: "First Message"\r\n\r\n'
        b'ping\r\n\r\n'
        b'ping\r\n\r\n'
        b'ping\r\n\r\n'
        b'ping\r\n\r\n'
        b'ping\r\n\r\n'
        b'ping\r\n\r\n'
        b'ping\r\n\r\n'
        b'ping\r\n\r\n'
        b'ping\r\n\r\n'
        b'ping\r\n\r\n'
        b'data: "Message after ping 10 ping"\r\n\r\n'
    )
