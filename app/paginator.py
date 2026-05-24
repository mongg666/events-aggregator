from datetime import date
from typing import AsyncIterator, Optional
from urllib.parse import parse_qs, urlparse

from app.clients import EventsProviderClient


class EventsPaginator:
    def __init__(self, client: EventsProviderClient, changed_at: date = date(2000, 1, 1)):
        self.client = client
        self.changed_at = changed_at

    async def __aiter__(self) -> AsyncIterator[dict]:
        cursor: Optional[str] = None
        while True:
            page = await self.client.list_events(self.changed_at, cursor)
            results = page.get("results", [])
            for event in results:
                yield event
            next_url = page.get("next")
            if not next_url:
                break
            # Извлекаем cursor из URL
            parsed = urlparse(next_url)
            params = parse_qs(parsed.query)
            cursor = params.get("cursor", [None])[0]
