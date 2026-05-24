from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories import EventRepository
from app.clients import EventsProviderClient
from app.schemas import EventSchema, PaginatedEvents, SeatsResponse
from app.config import settings

router = APIRouter()

@router.get("/events", response_model=PaginatedEvents)
async def list_events(
    date_from: Optional[date] = Query(None, alias="date_from"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    repo = EventRepository(session)
    events, total = await repo.list_events(
        date_from=datetime.combine(date_from, datetime.min.time()) if date_from else None,
        page=page,
        page_size=page_size,
    )
    next_url = None
    if page * page_size < total:
        next_url = f"/api/events?page={page+1}&page_size={page_size}"
        if date_from:
            next_url += f"&date_from={date_from.isoformat()}"
    return PaginatedEvents(
        count=total,
        next=next_url,
        previous=None,
        results=[EventSchema.model_validate(e) for e in events],
    )

@router.get("/events/{event_id}", response_model=EventSchema)
async def get_event(event_id: str, session: AsyncSession = Depends(get_session)):
    from uuid import UUID
    repo = EventRepository(session)
    event = await repo.get_by_id(UUID(event_id))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventSchema.model_validate(event)

# Кэш для мест (в памяти на 30 секунд)
seats_cache = {}

@router.get("/events/{event_id}/seats", response_model=SeatsResponse)
async def get_seats(event_id: str, session: AsyncSession = Depends(get_session)):
    from uuid import UUID
    import time
    event_uuid = UUID(event_id)
    # Проверяем существование события и его статус
    event_repo = EventRepository(session)
    event = await event_repo.get_by_id(event_uuid)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status != "published":
        raise HTTPException(status_code=400, detail="Event is not published")

    cache_key = str(event_uuid)
    now = time.time()
    if cache_key in seats_cache:
        cached_time, seats = seats_cache[cache_key]
        if now - cached_time < 30:
            return SeatsResponse(event_id=event_uuid, available_seats=seats)

    client = EventsProviderClient()
    try:
        seats = await client.get_seats(event_id)
    finally:
        await client.close()
    seats_cache[cache_key] = (now, seats)
    return SeatsResponse(event_id=event_uuid, available_seats=seats)