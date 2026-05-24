import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.clients import EventsProviderClient
from app.repositories import EventRepository, TicketRepository
from app.usecases import CreateTicketUsecase, CancelTicketUsecase
from app.schemas import TicketCreate, TicketResponse, SuccessResponse
from app.exceptions import EventNotFound, EventNotPublished

router = APIRouter()

@router.post("/tickets", response_model=TicketResponse, status_code=201)
async def register_ticket(body: TicketCreate, session: AsyncSession = Depends(get_session)):
    client = EventsProviderClient()
    try:
        event_repo = EventRepository(session)
        ticket_repo = TicketRepository(session)
        usecase = CreateTicketUsecase(client, event_repo, ticket_repo)
        ticket = await usecase.execute(
            event_id=body.event_id,
            first_name=body.first_name,
            last_name=body.last_name,
            seat=body.seat,
            email=body.email,
        )
        await session.commit()
        return TicketResponse(ticket_id=ticket.ticket_id)
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotPublished:
        raise HTTPException(status_code=400, detail="Event is not published")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        await session.rollback()
        raise
    finally:
        await client.close()

@router.delete("/tickets/{ticket_id}", response_model=SuccessResponse)
async def cancel_ticket(ticket_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    client = EventsProviderClient()
    try:
        event_repo = EventRepository(session)
        ticket_repo = TicketRepository(session)
        usecase = CancelTicketUsecase(client, ticket_repo, event_repo)
        await usecase.execute(ticket_id)
        await session.commit()
        return SuccessResponse()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        await session.rollback()
        raise
    finally:
        await client.close()