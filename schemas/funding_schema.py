from typing import List, Optional
from pydantic import BaseModel, field_validator

from utils.constants import (
    SECTORS,
    PROVINCES,
    BUSINESS_STAGES,
    FUNDING_PROVIDER_TYPES,
)


class FundingProgramCreate(BaseModel):
    """Payload to create a funding program (admin). Lists default to empty,
    which means 'open to all' for sectors/stages and 'national' for provinces.
    """
    name: str
    provider: Optional[str] = None
    provider_type: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    amount_min: Optional[int] = None
    amount_max: Optional[int] = None
    sectors: List[str] = []
    provinces: List[str] = []
    business_stages: List[str] = []
    accessibility_focused: bool = False
    application_deadline: Optional[str] = None
    is_active: bool = True

    @field_validator("provider_type")
    @classmethod
    def validate_provider_type(cls, v):
        if v is not None and v not in FUNDING_PROVIDER_TYPES:
            raise ValueError(f"Invalid provider_type. Allowed: {', '.join(FUNDING_PROVIDER_TYPES)}")
        return v

    @field_validator("sectors")
    @classmethod
    def validate_sectors(cls, v):
        invalid = [x for x in v if x not in SECTORS]
        if invalid:
            raise ValueError(f"Invalid sectors: {invalid}. Allowed: {', '.join(SECTORS)}")
        return v

    @field_validator("provinces")
    @classmethod
    def validate_provinces(cls, v):
        invalid = [x for x in v if x not in PROVINCES]
        if invalid:
            raise ValueError(f"Invalid provinces: {invalid}. Allowed: {', '.join(PROVINCES)}")
        return v

    @field_validator("business_stages")
    @classmethod
    def validate_stages(cls, v):
        invalid = [x for x in v if x not in BUSINESS_STAGES]
        if invalid:
            raise ValueError(f"Invalid business_stages: {invalid}. Allowed: {', '.join(BUSINESS_STAGES)}")
        return v


class FundingProgramResponse(BaseModel):
    id: int
    name: str
    provider: Optional[str] = None
    provider_type: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    amount_min: Optional[int] = None
    amount_max: Optional[int] = None
    sectors: List[str] = []
    provinces: List[str] = []
    business_stages: List[str] = []
    accessibility_focused: bool = False
    application_deadline: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class FundingRecommendation(BaseModel):
    """A funding program plus the score and reasons it was matched."""
    program: FundingProgramResponse
    score: int
    match_reasons: List[str] = []
