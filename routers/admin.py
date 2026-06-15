from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.models import get_db, User, MentorInvite, FundingProgram, Event
from schemas.mentor_schema import InviteCreate, MentorInviteResponse
from schemas.funding_schema import FundingProgramCreate, FundingProgramResponse
from schemas.event_schema import EventCreate, EventResponse
from utils.auth import require_role
from utils.constants import ROLE_ADMIN
from utils.invites import create_mentor_invite, invite_link

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/mentor-invites", response_model=MentorInviteResponse,
             status_code=status.HTTP_201_CREATED)
async def post_mentor_invite(
    data: InviteCreate,
    current_user: User = Depends(require_role(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin creates a tokenized invite for a prospective mentor."""
    invite, error = create_mentor_invite(db, data.email, invited_by_id=current_user.id)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return MentorInviteResponse(
        id=invite.id,
        email=invite.email,
        token=invite.token,
        status=invite.status,
        invite_link=invite_link(invite.token),
    )


@router.post("/funding-programs", response_model=FundingProgramResponse,
             status_code=status.HTTP_201_CREATED)
async def create_funding_program(
    data: FundingProgramCreate,
    current_user: User = Depends(require_role(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin creates a funding program. Usable from any external form/script,
    not just the admin panel."""
    program = FundingProgram(**data.model_dump())
    db.add(program)
    try:
        db.commit()
        db.refresh(program)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return program


@router.post("/events", response_model=EventResponse,
             status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    current_user: User = Depends(require_role(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin creates an event. Usable from any external form/script."""
    event = Event(**data.model_dump())
    db.add(event)
    try:
        db.commit()
        db.refresh(event)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return event


@router.get("/mentor-invites", response_model=List[MentorInviteResponse])
async def list_mentor_invites(
    current_user: User = Depends(require_role(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin lists all mentor invites, newest first."""
    invites = db.query(MentorInvite).order_by(desc(MentorInvite.created_at)).all()
    return [
        MentorInviteResponse(
            id=inv.id,
            email=inv.email,
            token=inv.token,
            status=inv.status,
            invite_link=invite_link(inv.token),
        )
        for inv in invites
    ]
