from typing import List, Optional
from pydantic import BaseModel, field_validator

from utils.constants import (
    PROVINCES,
    BUSINESS_STAGES,
    SECTORS,
    COMMUNICATION_PREFERENCES,
    ACCESSIBILITY_PREFERENCES,
)


class FounderOnboardingModel(BaseModel):
    """Payload submitted to complete founder onboarding.

    All fields are optional so the endpoint can be used for both the initial
    submission and partial updates; required-for-completion fields are checked
    in the router.
    """
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    province: Optional[str] = None
    business_stage: Optional[str] = None
    sectors: Optional[List[str]] = None
    communication_preferences: Optional[List[str]] = None
    accessibility_preferences: Optional[List[str]] = None
    bio: Optional[str] = None

    @field_validator("province")
    @classmethod
    def validate_province(cls, v):
        if v is not None and v not in PROVINCES:
            raise ValueError(f"Invalid province. Must be one of: {', '.join(PROVINCES)}")
        return v

    @field_validator("business_stage")
    @classmethod
    def validate_stage(cls, v):
        if v is not None and v not in BUSINESS_STAGES:
            raise ValueError(f"Invalid business_stage. Must be one of: {', '.join(BUSINESS_STAGES)}")
        return v

    @field_validator("sectors")
    @classmethod
    def validate_sectors(cls, v):
        if v is not None:
            invalid = [s for s in v if s not in SECTORS]
            if invalid:
                raise ValueError(f"Invalid sectors: {invalid}. Allowed: {', '.join(SECTORS)}")
        return v

    @field_validator("communication_preferences")
    @classmethod
    def validate_comm(cls, v):
        if v is not None:
            invalid = [s for s in v if s not in COMMUNICATION_PREFERENCES]
            if invalid:
                raise ValueError(f"Invalid communication_preferences: {invalid}. "
                                 f"Allowed: {', '.join(COMMUNICATION_PREFERENCES)}")
        return v

    @field_validator("accessibility_preferences")
    @classmethod
    def validate_access(cls, v):
        if v is not None:
            invalid = [s for s in v if s not in ACCESSIBILITY_PREFERENCES]
            if invalid:
                raise ValueError(f"Invalid accessibility_preferences: {invalid}. "
                                 f"Allowed: {', '.join(ACCESSIBILITY_PREFERENCES)}")
        return v


class FounderProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    province: Optional[str] = None
    business_stage: Optional[str] = None
    sectors: List[str] = []
    communication_preferences: List[str] = []
    accessibility_preferences: List[str] = []
    bio: Optional[str] = None
    is_onboarded: bool

    class Config:
        from_attributes = True
