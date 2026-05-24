from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models import Event
from app.usecases import CreateTicketUsecase, EventNotPublished


@pytest.mark.asyncio
async def test_create_ticket_success():
    client = AsyncMock()
    client.register.return_value = str(uuid4())
    event_repo = AsyncMock()
    ticket_repo = AsyncMock()
    event = Event(
        id=uuid4(),
        name="Test",
        status="published",
        registration_deadline=datetime.now(timezone.utc) + timedelta(days=1),
        event_time=datetime.now(timezone.utc) + timedelta(days=2),
        changed_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        status_changed_at=datetime.now(timezone.utc),
    )
    event_repo.get_by_id.return_value = event
    usecase = CreateTicketUsecase(client, event_repo, ticket_repo)
    ticket = await usecase.execute(event.id, "A", "B", "A1", "a@b.com")
    assert ticket is not None
    client.register.assert_awaited_once()
    ticket_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_ticket_event_not_published():
    client = AsyncMock()
    event_repo = AsyncMock()
    ticket_repo = AsyncMock()
    event = Event(
        status="new",
        registration_deadline=datetime.now(timezone.utc) + timedelta(1),
    )
    event_repo.get_by_id.return_value = event
    usecase = CreateTicketUsecase(client, event_repo, ticket_repo)
    with pytest.raises(EventNotPublished):
        await usecase.execute(uuid4(), "A", "B", "A1", "a@b.com")
