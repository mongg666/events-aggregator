import uuid
from typing import Protocol, List, Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, Place, SyncMetadata, Ticket

class EventRepositoryProtocol(Protocol):
    async def get_by_id(self, event_id: uuid.UUID) -> Optional[Event]: ...
    async def list_events(self, date_from: Optional[datetime] = None,
                          page: int = 1, page_size: int = 20) -> (List[Event], int): ...
    async def upsert(self, event: Event) -> Event: ...

class TicketRepositoryProtocol(Protocol):
    async def create(self, ticket: Ticket) -> Ticket: ...
    async def delete(self, ticket_id: uuid.UUID) -> bool: ...

class SyncRepositoryProtocol(Protocol):
    async def get_metadata(self) -> Optional[SyncMetadata]: ...
    async def update_metadata(self, last_changed_at: datetime, status: str) -> None: ...

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, event_id: uuid.UUID) -> Optional[Event]:
        result = await self.session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def list_events(self, date_from: Optional[datetime] = None,
                          page: int = 1, page_size: int = 20) -> (List[Event], int):
        query = select(Event)
        if date_from:
            query = query.where(Event.event_time >= date_from)
        # Подсчёт общего числа
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        query = query.order_by(Event.event_time).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        events = result.scalars().all()
        return events, total

    async def upsert(self, event: Event) -> Event:
        # Сначала проверим, есть ли уже место в БД
        if event.place:
            existing_place = await self.session.get(Place, event.place.id)
            if existing_place:
                for attr in ('name', 'city', 'address', 'seats_pattern', 'changed_at', 'created_at'):
                    setattr(existing_place, attr, getattr(event.place, attr))
                event.place = existing_place
            else:
                self.session.add(event.place)

        existing_event = await self.session.get(Event, event.id)
        if existing_event:
            # Обновляем поля
            for attr in ('name', 'event_time', 'registration_deadline', 'status',
                         'number_of_visitors', 'changed_at', 'created_at', 'status_changed_at'):
                setattr(existing_event, attr, getattr(event, attr))
            existing_event.place = event.place
            event = existing_event
        else:
            self.session.add(event)
        await self.session.flush()
        return event

class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, ticket: Ticket) -> Ticket:
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def delete(self, ticket_id: uuid.UUID) -> bool:
        ticket = await self.session.get(Ticket, ticket_id)
        if ticket:
            await self.session.delete(ticket)
            await self.session.flush()
            return True
        return False

class SyncRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_metadata(self) -> Optional[SyncMetadata]:
        result = await self.session.execute(select(SyncMetadata).order_by(SyncMetadata.id.desc()).limit(1))
        return result.scalar_one_or_none()

    async def update_metadata(self, last_changed_at: datetime, status: str) -> None:
        meta = SyncMetadata(last_changed_at=last_changed_at, last_sync_time=datetime.utcnow(), status=status)
        self.session.add(meta)
        await self.session.flush()