from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator

from utils.constants import (
    PROVINCES,
    SECTORS,
    EXPERTISE_AREAS,
    AVAILABILITY,
)


class MentorOnboardingModel(BaseModel):
    """Payload a mentor submits to build/update their own profile.

    All fields optional so it works for partial updates; required-for-completion
    fields are enforced in the router.
    """
    full_name: Optional[str] = None
    background: Optional[str] = None
    expertise: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    provinces: Optional[List[str]] = None
    availability: Optional[str] = None
    lived_experience: Optional[str] = None
    shares_lived_experience: Optional[bool] = None
    is_accepting: Optional[bool] = None

    @field_validator("expertise")
    @classmethod
    def validate_expertise(cls, v):
        if v is not None:
            invalid = [x for x in v if x not in EXPERTISE_AREAS]
            if invalid:
                raise ValueError(f"Invalid expertise: {invalid}. Allowed: {', '.join(EXPERTISE_AREAS)}")
        return v

    @field_validator("sectors")
    @classmethod
    def validate_sectors(cls, v):
        if v is not None:
            invalid = [x for x in v if x not in SECTORS]
            if invalid:
                raise ValueError(f"Invalid sectors: {invalid}. Allowed: {', '.join(SECTORS)}")
        return v

    @field_validator("provinces")
    @classmethod
    def validate_provinces(cls, v):
        if v is not None:
            invalid = [x for x in v if x not in PROVINCES]
            if invalid:
                raise ValueError(f"Invalid provinces: {invalid}. Allowed: {', '.join(PROVINCES)}")
        return v

    @field_validator("availability")
    @classmethod
    def validate_availability(cls, v):
        if v is not None and v not in AVAILABILITY:
            raise ValueError(f"Invalid availability. Must be one of: {', '.join(AVAILABILITY)}")
        return v


class InviteCreate(BaseModel):
    email: EmailStr


class MentorInviteResponse(BaseModel):
    id: int
    email: EmailStr
    token: str
    status: str
    invite_link: Optional[str] = None

    class Config:
        from_attributes = True


class InviteAccept(BaseModel):
    password: str
    confirm_password: str


class MentorProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    background: Optional[str] = None
    expertise: List[str] = []
    sectors: List[str] = []
    provinces: List[str] = []
    availability: Optional[str] = None
    lived_experience: Optional[str] = None
    shares_lived_experience: bool = False
    is_accepting: bool = True
    is_onboarded: bool = False

    class Config:
        from_attributes = True


class MentorRecommendation(BaseModel):
    """A mentor plus the score and human-readable reasons it was matched."""
    mentor: MentorProfileResponse
    score: int
    match_reasons: List[str] = []
