from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator

from schemas.founder_schema import FounderProfileResponse
from schemas.mentor_schema import MentorProfileResponse


class MatchRequestCreate(BaseModel):
    """Founder requests a connection with a mentor (by MentorProfile id)."""
    mentor_id: int


class MatchActionUpdate(BaseModel):
    """Mentor responds to a request."""
    action: str  # "confirm" | "decline"

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v not in ("confirm", "decline"):
            raise ValueError("action must be 'confirm' or 'decline'")
        return v


class AdminMatchCreate(BaseModel):
    """Admin override: force/confirm a pairing by the two emails."""
    founder_email: EmailStr
    mentor_email: EmailStr
    status: str = "confirmed"

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        from utils.constants import MATCH_STATUSES
        if v not in MATCH_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(MATCH_STATUSES)}")
        return v


class AdminMatchUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        from utils.constants import MATCH_STATUSES
        if v not in MATCH_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(MATCH_STATUSES)}")
        return v


class FounderSideMatch(BaseModel):
    """A match as the founder sees it (who their mentor is + status)."""
    id: int
    status: str
    is_admin_override: bool = False
    created_at: Optional[datetime] = None
    mentor: Optional[MentorProfileResponse] = None

    class Config:
        from_attributes = True


class MentorSideMatch(BaseModel):
    """A match as the mentor sees it (which founder + status)."""
    id: int
    status: str
    is_admin_override: bool = False
    created_at: Optional[datetime] = None
    founder: Optional[FounderProfileResponse] = None

    class Config:
        from_attributes = True
