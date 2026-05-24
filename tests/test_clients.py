from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from app.clients import EventsProviderClient


@pytest.mark.asyncio
async def test_list_events():
    mock_response = {
        "next": None,
        "results": [{"id": "some-uuid", "name": "Event1"}],
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = AsyncMock(return_value=mock_response)

        client = EventsProviderClient(base_url="http://test", api_key="key")
        result = await client.list_events(date(2026, 1, 1))
        assert result == mock_response
        mock_get.assert_awaited_once()


@pytest.mark.asyncio
async def test_register():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json = AsyncMock(return_value={"ticket_id": "uuid-1234"})

        client = EventsProviderClient(base_url="http://test", api_key="key")
        ticket_id = await client.register(
            "ev1", "John", "Doe", "A1", "john@example.com"
        )
        assert ticket_id == "uuid-1234"
