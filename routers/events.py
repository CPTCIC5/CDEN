from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import asc
from sqlalchemy.orm import Session

from db.models import get_db, User, Event
from schemas.event_schema import EventResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=List[EventResponse])
async def list_events(
    upcoming_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List active events, soonest first. By default only upcoming ones."""
    query = db.query(Event).filter(Event.is_active == True)
    if upcoming_only:
        query = query.filter((Event.start_at == None) | (Event.start_at >= datetime.now()))
    return query.order_by(asc(Event.start_at)).all()


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single event's details."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event
