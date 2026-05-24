import uuid
from datetime import date, datetime
from typing import Protocol, Optional, List
import logging

from app.clients import EventsProviderClient
from app.models import Event, Place, Ticket
from app.repositories import (
    EventRepositoryProtocol,
    TicketRepositoryProtocol,
    SyncRepositoryProtocol,
)
from app.exceptions import EventNotFound, EventNotPublished

logger = logging.getLogger(__name__)

class SyncEventsUsecase:
    def __init__(self, client: EventsProviderClient,
                 event_repo: EventRepositoryProtocol,
                 sync_repo: SyncRepositoryProtocol):
        self.client = client
        self.event_repo = event_repo
        self.sync_repo = sync_repo

    async def run(self, changed_at: Optional[date] = None) -> None:
        if changed_at is None:
            meta = await self.sync_repo.get_metadata()
            changed_at = meta.last_changed_at.date() if meta and meta.last_changed_at else date(2000, 1, 1)

        logger.info("Starting sync with changed_at=%s", changed_at)
        paginator = EventsPaginator(self.client, changed_at)
        max_changed_at = None
        async for raw_event in paginator:
            event = self._parse_event(raw_event)
            await self.event_repo.upsert(event)
            if max_changed_at is None or event.changed_at > max_changed_at:
                max_changed_at = event.changed_at

        if max_changed_at:
            await self.sync_repo.update_metadata(max_changed_at, "success")
        logger.info("Sync completed successfully")

    def _parse_event(self, data: dict) -> Event:
        place_data = data["place"]
        place = Place(
            id=uuid.UUID(place_data["id"]),
            name=place_data["name"],
            city=place_data["city"],
            address=place_data["address"],
            seats_pattern=place_data["seats_pattern"],
            changed_at=datetime.fromisoformat(place_data["changed_at"]),
            created_at=datetime.fromisoformat(place_data["created_at"]),
        )
        return Event(
            id=uuid.UUID(data["id"]),
            name=data["name"],
            event_time=datetime.fromisoformat(data["event_time"]),
            registration_deadline=datetime.fromisoformat(data["registration_deadline"]),
            status=data["status"],
            number_of_visitors=int(data["number_of_visitors"]),
            changed_at=datetime.fromisoformat(data["changed_at"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            status_changed_at=datetime.fromisoformat(data["status_changed_at"]),
            place=place,
        )

class CreateTicketUsecase:
    def __init__(self, client: EventsProviderClient,
                 event_repo: EventRepositoryProtocol,
                 ticket_repo: TicketRepositoryProtocol):
        self.client = client
        self.event_repo = event_repo
        self.ticket_repo = ticket_repo

    async def execute(self, event_id: uuid.UUID, first_name: str,
                      last_name: str, seat: str, email: str) -> Ticket:
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            raise EventNotFound(f"Event {event_id} not found")
        if event.status != "published":
            raise EventNotPublished("Event is not published")
        if datetime.now(event.registration_deadline.tzinfo) > event.registration_deadline:
            raise ValueError("Registration deadline passed")

        # Регистрируем в провайдере
        ticket_id_str = await self.client.register(str(event_id), first_name, last_name, seat, email)
        ticket = Ticket(
            ticket_id=uuid.UUID(ticket_id_str),
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )
        await self.ticket_repo.create(ticket)
        return ticket

class CancelTicketUsecase:
    def __init__(self, client: EventsProviderClient,
                 ticket_repo: TicketRepositoryProtocol,
                 event_repo: EventRepositoryProtocol):
        self.client = client
        self.ticket_repo = ticket_repo
        self.event_repo = event_repo

    async def execute(self, ticket_id: uuid.UUID) -> None:
        ticket = await self.ticket_repo.get(ticket_id)  # нужно добавить метод get
        if not ticket:
            raise ValueError("Ticket not found")
        event = await self.event_repo.get_by_id(ticket.event_id)
        if not event:
            raise EventNotFound("Associated event not found")
        # Отменяем у провайдера
        await self.client.unregister(str(event.id), str(ticket.ticket_id))
        await self.ticket_repo.delete(ticket_id)