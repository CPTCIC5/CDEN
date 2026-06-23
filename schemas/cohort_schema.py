from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class CohortCreate(BaseModel):
    """Founder's cohort application. Only first_name + email are required."""
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_name: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    sector: Optional[str] = None
    received_funding: bool = False
    annual_revenue: Optional[int] = None
    num_cofounders: Optional[int] = None
    program_goal: Optional[str] = None
    pitch_deck_url: Optional[str] = None
    consent: bool = False


class CohortResponse(CohortCreate):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
