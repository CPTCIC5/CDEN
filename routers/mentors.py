from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session

from db.models import get_db, User, FounderProfile, MentorProfile, MentorInvite
from schemas.mentor_schema import (
    MentorProfileResponse,
    MentorRecommendation,
    MentorOnboardingModel,
    InviteAccept,
)
from utils.auth import get_current_user, create_session
from utils.matching import recommend_mentors
from utils.constants import ROLE_MENTOR, ROLE_FOUNDER

router = APIRouter(prefix="/api/mentors", tags=["mentors"])

# Fields a mentor must provide for their profile to count as complete
MENTOR_REQUIRED_FOR_COMPLETION = ("expertise", "sectors", "provinces", "availability")


def _get_or_create_mentor_profile(db: Session, user: User) -> MentorProfile:
    profile = db.query(MentorProfile).filter(MentorProfile.user_id == user.id).first()
    if not profile:
        profile = MentorProfile(user_id=user.id)
        db.add(profile)
    return profile


@router.get("/recommendations", response_model=List[MentorRecommendation])
async def mentor_recommendations(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recommend mentors for the current founder using rule-based matching."""
    if current_user.role != ROLE_FOUNDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mentor recommendations are only available to founder accounts.",
        )
    founder = db.query(FounderProfile).filter(
        FounderProfile.user_id == current_user.id
    ).first()
    if not founder or not founder.is_onboarded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your founder onboarding to get mentor recommendations.",
        )

    mentors = db.query(MentorProfile).all()
    ranked = recommend_mentors(founder, mentors, limit=limit)

    return [
        MentorRecommendation(mentor=mentor, score=score, match_reasons=reasons)
        for score, reasons, mentor in ranked
    ]


@router.get("", response_model=List[MentorProfileResponse])
async def list_mentors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all mentors (directory view)."""
    return db.query(MentorProfile).all()


@router.get("/invite/{token}")
async def get_invite(token: str, db: Session = Depends(get_db)):
    """Validate a mentor invite token (used by the accept page to prefill email)."""
    invite = db.query(MentorInvite).filter(MentorInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    return {
        "email": invite.email,
        "valid": invite.is_valid(),
        "status": invite.status,
    }


@router.post("/invite/{token}/accept", status_code=status.HTTP_201_CREATED)
async def accept_invite(
    token: str,
    data: InviteAccept,
    request: Request,
    db: Session = Depends(get_db),
):
    """Accept a mentor invite: create the mentor's account and log them in.

    The invited email is trusted (the token proves ownership), so the new
    mentor is marked verified and can move straight to onboarding.
    """
    invite = db.query(MentorInvite).filter(MentorInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if not invite.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invite is no longer valid (expired or already used).",
        )
    if data.password != data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
    if db.query(User).filter(User.email == invite.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    new_user = User(email=invite.email, role=ROLE_MENTOR, is_verified=True)
    new_user.set_password(data.password)
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Start an empty mentor profile and consume the invite
    db.add(MentorProfile(user_id=new_user.id, is_onboarded=False))
    invite.status = "accepted"
    invite.accepted_at = datetime.now()
    db.commit()

    # Log the new mentor in so they can go straight to onboarding
    create_session(request, new_user)

    return {
        "detail": "Invite accepted. Please complete your mentor profile.",
        "user": {"id": new_user.id, "email": new_user.email, "role": new_user.role},
    }


@router.post("/onboarding", response_model=MentorProfileResponse)
async def submit_mentor_onboarding(
    data: MentorOnboardingModel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update the current mentor's own profile (also used for edits)."""
    if current_user.role != ROLE_MENTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors can complete mentor onboarding",
        )

    profile = _get_or_create_mentor_profile(db, current_user)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    profile.is_onboarded = all(bool(getattr(profile, f)) for f in MENTOR_REQUIRED_FOR_COMPLETION)

    try:
        db.commit()
        db.refresh(profile)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return profile


@router.get("/me", response_model=MentorProfileResponse)
async def get_my_mentor_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current mentor's own profile."""
    if current_user.role != ROLE_MENTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors have a mentor profile",
        )
    profile = db.query(MentorProfile).filter(MentorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor profile not found")
    return profile


@router.get("/{mentor_id}", response_model=MentorProfileResponse)
async def get_mentor(
    mentor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single mentor's profile."""
    mentor = db.query(MentorProfile).filter(MentorProfile.id == mentor_id).first()
    if not mentor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")
    return mentor
