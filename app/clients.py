from datetime import date
from typing import Optional, Dict, Any, List
import httpx
from app.config import settings

class EventsProviderClient:
    def __init__(self, base_url: str = settings.events_provider_base_url,
                 api_key: str = settings.events_provider_api_key):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(headers={"x-api-key": self.api_key})
        return self._client

    async def list_events(self, changed_at: date, cursor: Optional[str] = None) -> Dict[str, Any]:
        client = await self._get_client()
        url = f"{self.base_url}/api/events/"
        params = {"changed_at": changed_at.isoformat()}
        if cursor:
            # cursor уже включён в URL, если передан полный URL
            # Но мы передаём cursor как параметр
            url = f"{self.base_url}/api/events/?changed_at={changed_at.isoformat()}&cursor={cursor}"
        else:
            params = {"changed_at": changed_at.isoformat()}
        response = await client.get(url, params=params if not cursor else None)
        response.raise_for_status()
        return response.json()

    async def get_seats(self, event_id: str) -> List[str]:
        client = await self._get_client()
        url = f"{self.base_url}/api/events/{event_id}/seats/"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("seats", [])

    async def register(self, event_id: str, first_name: str, last_name: str,
                       seat: str, email: str) -> str:
        client = await self._get_client()
        url = f"{self.base_url}/api/events/{event_id}/register/"
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "seat": seat,
            "email": email,
        }
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()["ticket_id"]

    async def unregister(self, event_id: str, ticket_id: str) -> None:
        client = await self._get_client()
        url = f"{self.base_url}/api/events/{event_id}/unregister/"
        payload = {"ticket_id": ticket_id}
        response = await client.request("DELETE", url, json=payload)
        response.raise_for_status()

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None