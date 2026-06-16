from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from typing import List
from datetime import datetime
from sqlalchemy import asc
from db.models import get_db, User, FounderProfile, MentorProfile, FundingProgram, Event, MentorMatch
from schemas.founder_schema import FounderOnboardingModel, FounderProfileResponse
from schemas.mentor_schema import MentorRecommendation
from schemas.funding_schema import FundingRecommendation
from schemas.dashboard_schema import DashboardResponse
from schemas.match_schema import MatchRequestCreate, FounderSideMatch
from utils.auth import get_current_user
from utils.matching import recommend_mentors, recommend_funding
from utils.matches import to_founder_side
from utils.email_sender import send_mentor_request_email
from utils.constants import (
    MATCH_REQUESTED,
    ROLE_FOUNDER,
    PROVINCES,
    BUSINESS_STAGES,
    SECTORS,
    COMMUNICATION_PREFERENCES,
    ACCESSIBILITY_PREFERENCES,
)

router = APIRouter(prefix="/api/founders", tags=["founders"])


@router.get("/options")
async def onboarding_options():
    """Allowed values for the onboarding form (drives frontend dropdowns)."""
    return {
        "provinces": [{"code": k, "name": v} for k, v in PROVINCES.items()],
        "business_stages": list(BUSINESS_STAGES),
        "sectors": list(SECTORS),
        "communication_preferences": list(COMMUNICATION_PREFERENCES),
        "accessibility_preferences": list(ACCESSIBILITY_PREFERENCES),
    }

# Fields that must be present for onboarding to count as complete
REQUIRED_FOR_COMPLETION = ("province", "business_stage", "sectors")


def _get_or_create_profile(db: Session, user: User) -> FounderProfile:
    profile = db.query(FounderProfile).filter(FounderProfile.user_id == user.id).first()
    if not profile:
        profile = FounderProfile(user_id=user.id)
        db.add(profile)
    return profile


@router.post("/onboarding", response_model=FounderProfileResponse)
async def submit_onboarding(
    data: FounderOnboardingModel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update the founder's onboarding profile.

    Accepts partial payloads, so it doubles as the profile-edit endpoint.
    Marks the profile onboarded once the required fields are all set.
    """
    if current_user.role != ROLE_FOUNDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only founders can complete founder onboarding",
        )

    profile = _get_or_create_profile(db, current_user)

    # Apply only the fields that were actually provided
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    # Recompute completion status from the persisted values
    def _present(attr):
        val = getattr(profile, attr)
        return bool(val)

    profile.is_onboarded = all(_present(f) for f in REQUIRED_FOR_COMPLETION)

    try:
        db.commit()
        db.refresh(profile)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return profile


@router.get("/me", response_model=FounderProfileResponse)
async def get_my_founder_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current founder's onboarding profile."""
    profile = db.query(FounderProfile).filter(
        FounderProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Founder profile not found. Complete onboarding first.",
        )
    return profile


@router.post("/matches", response_model=FounderSideMatch, status_code=status.HTTP_201_CREATED)
async def request_mentor(
    data: MatchRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Founder requests a connection with a mentor (by MentorProfile id)."""
    if current_user.role != ROLE_FOUNDER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only founders can request a mentor.")

    mentor = db.query(MentorProfile).filter(MentorProfile.id == data.mentor_id).first()
    if not mentor or not mentor.is_onboarded:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")
    if not mentor.is_accepting:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="This mentor is not currently accepting new founders.")

    existing = db.query(MentorMatch).filter(
        MentorMatch.founder_user_id == current_user.id,
        MentorMatch.mentor_user_id == mentor.user_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a connection with this mentor (status: {existing.status}).",
        )

    match = MentorMatch(
        founder_user_id=current_user.id,
        mentor_user_id=mentor.user_id,
        status=MATCH_REQUESTED,
        created_by=current_user.id,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    # Notify the mentor (after the response is sent, so SMTP never blocks the request)
    mentor_user = db.query(User).filter(User.id == mentor.user_id).first()
    founder_profile = db.query(FounderProfile).filter(
        FounderProfile.user_id == current_user.id
    ).first()
    founder_label = (founder_profile.business_name or founder_profile.full_name
                     if founder_profile else None) or current_user.email
    if mentor_user:
        background_tasks.add_task(send_mentor_request_email, mentor_user.email, founder_label)

    return to_founder_side(match, db)


@router.get("/matches", response_model=List[FounderSideMatch])
async def my_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the founder's mentor connections and their statuses."""
    if current_user.role != ROLE_FOUNDER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only founders have mentor connections here.")
    matches = db.query(MentorMatch).filter(
        MentorMatch.founder_user_id == current_user.id
    ).all()
    return [to_founder_side(m, db) for m in matches]


@router.get("/dashboard", response_model=DashboardResponse)
async def founder_dashboard(
    mentor_limit: int = 5,
    funding_limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate the founder's whole dashboard in one call:
    their profile, mentor recommendations, funding recommendations, and events.
    """
    if current_user.role != ROLE_FOUNDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The founder dashboard is only available to founder accounts.",
        )
    founder = db.query(FounderProfile).filter(
        FounderProfile.user_id == current_user.id
    ).first()
    if not founder or not founder.is_onboarded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your founder onboarding to view your dashboard.",
        )

    ranked_mentors = recommend_mentors(founder, db.query(MentorProfile).all(), limit=mentor_limit)
    ranked_funding = recommend_funding(founder, db.query(FundingProgram).all(), limit=funding_limit)

    upcoming_events = db.query(Event).filter(
        Event.is_active == True,
        (Event.start_at == None) | (Event.start_at >= datetime.now()),
    ).order_by(asc(Event.start_at)).all()

    matches = db.query(MentorMatch).filter(
        MentorMatch.founder_user_id == current_user.id
    ).all()

    return DashboardResponse(
        founder=founder,
        mentor_recommendations=[
            MentorRecommendation(mentor=m, score=s, match_reasons=r)
            for s, r, m in ranked_mentors
        ],
        funding_recommendations=[
            FundingRecommendation(program=p, score=s, match_reasons=r)
            for s, r, p in ranked_funding
        ],
        events=upcoming_events,
        matches=[to_founder_side(m, db) for m in matches],
    )


@router.get("/onboarding/status")
async def onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lightweight check the frontend can poll to route a user through the journey."""
    profile = db.query(FounderProfile).filter(
        FounderProfile.user_id == current_user.id
    ).first()
    return {
        "is_verified": current_user.is_verified,
        "has_profile": profile is not None,
        "is_onboarded": bool(profile and profile.is_onboarded),
    }
