"""Helpers to render a MentorMatch from each side's perspective."""
from db.models import MentorProfile, FounderProfile
from schemas.mentor_schema import MentorProfileResponse
from schemas.founder_schema import FounderProfileResponse
from schemas.match_schema import FounderSideMatch, MentorSideMatch


def to_founder_side(match, db):
    """Render a match as the founder sees it (their mentor + status)."""
    mentor = db.query(MentorProfile).filter(
        MentorProfile.user_id == match.mentor_user_id
    ).first()
    return FounderSideMatch(
        id=match.id,
        status=match.status,
        is_admin_override=match.is_admin_override,
        created_at=match.created_at,
        mentor=MentorProfileResponse.model_validate(mentor) if mentor else None,
    )


def to_mentor_side(match, db):
    """Render a match as the mentor sees it (which founder + status)."""
    founder = db.query(FounderProfile).filter(
        FounderProfile.user_id == match.founder_user_id
    ).first()
    return MentorSideMatch(
        id=match.id,
        status=match.status,
        is_admin_override=match.is_admin_override,
        created_at=match.created_at,
        founder=FounderProfileResponse.model_validate(founder) if founder else None,
    )
