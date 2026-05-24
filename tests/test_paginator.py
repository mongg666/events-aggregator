from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.paginator import EventsPaginator


@pytest.mark.asyncio
async def test_paginator_single_page():
    client = MagicMock()
    client.list_events = AsyncMock(
        return_value={"next": None, "results": [{"id": 1}, {"id": 2}]}
    )
    paginator = EventsPaginator(client, date(2020, 1, 1))
    items = [item async for item in paginator]
    assert len(items) == 2
    client.list_events.assert_awaited_once()


@pytest.mark.asyncio
async def test_paginator_multiple_pages():
    client = MagicMock()
    client.list_events = AsyncMock(
        side_effect=[
            {"next": "http://test?cursor=abc", "results": [{"id": 1}]},
            {"next": "http://test?cursor=def", "results": [{"id": 2}]},
            {"next": None, "results": [{"id": 3}]},
        ]
    )
    paginator = EventsPaginator(client, date(2020, 1, 1))
    items = [item async for item in paginator]
    assert len(items) == 3
    assert client.list_events.await_count == 3
