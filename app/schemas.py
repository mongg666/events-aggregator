from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class PlaceSchema(BaseModel):
    id: UUID
    name: str
    city: str
    address: str
    seats_pattern: Optional[str] = None
    model_config = {"from_attributes": True}


class EventSchema(BaseModel):
    id: UUID
    name: str
    place: PlaceSchema
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int
    model_config = {"from_attributes": True}


class PaginatedEvents(BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[EventSchema]


class SeatsResponse(BaseModel):
    event_id: UUID
    available_seats: List[str]


class TicketCreate(BaseModel):
    event_id: UUID
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    seat: str = Field(min_length=1)


class TicketResponse(BaseModel):
    ticket_id: UUID


class SuccessResponse(BaseModel):
    success: bool = True
