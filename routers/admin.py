from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.models import get_db, User, MentorInvite, FundingProgram, Event, MentorMatch, MentorProfile, FounderProfile
from schemas.mentor_schema import InviteCreate, MentorInviteResponse
from schemas.funding_schema import FundingProgramCreate, FundingProgramResponse
from schemas.event_schema import EventCreate, EventResponse
from schemas.match_schema import AdminMatchCreate, AdminMatchUpdate, MentorSideMatch
from utils.auth import require_role
from utils.constants import ROLE_ADMIN, ROLE_FOUNDER, ROLE_MENTOR
from utils.invites import create_mentor_invite, invite_link
from utils.matches import to_mentor_side

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


@router.post("/matches", response_model=MentorSideMatch, status_code=status.HTTP_201_CREATED)
async def admin_create_match(
    data: AdminMatchCreate,
    current_user: User = Depends(require_role(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin override: force/confirm a founder<->mentor pairing by email.
    If a match already exists for the pair, its status is updated instead."""
    founder = db.query(User).filter(User.email == data.founder_email).first()
    if not founder or founder.role != ROLE_FOUNDER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="founder_email does not belong to a founder account")
    mentor = db.query(User).filter(User.email == data.mentor_email).first()
    if not mentor or mentor.role != ROLE_MENTOR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="mentor_email does not belong to a mentor account")

    match = db.query(MentorMatch).filter(
        MentorMatch.founder_user_id == founder.id,
        MentorMatch.mentor_user_id == mentor.id,
    ).first()
    if match:
        match.status = data.status
        match.is_admin_override = True
    else:
        match = MentorMatch(
            founder_user_id=founder.id,
            mentor_user_id=mentor.id,
            status=data.status,
            is_admin_override=True,
            created_by=current_user.id,
        )
        db.add(match)
    db.commit()
    db.refresh(match)
    return to_mentor_side(match, db)


@router.get("/matches", response_model=List[MentorSideMatch])
async def admin_list_matches(
    current_user: User = Depends(require_role(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin lists all matches across the platform."""
    return [to_mentor_side(m, db) for m in db.query(MentorMatch).all()]


@router.patch("/matches/{match_id}", response_model=MentorSideMatch)
async def admin_update_match(
    match_id: int,
    data: AdminMatchUpdate,
    current_user: User = Depends(require_role(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin changes a match's status (override)."""
    match = db.query(MentorMatch).filter(MentorMatch.id == match_id).first()
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    match.status = data.status
    match.is_admin_override = True
    db.commit()
    db.refresh(match)
    return to_mentor_side(match, db)


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
