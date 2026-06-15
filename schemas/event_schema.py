from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator

from utils.constants import PROVINCES


class EventCreate(BaseModel):
    """Payload to create an event (admin). Only title is required."""
    title: str
    description: Optional[str] = None
    venue: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    embed_link: Optional[str] = None
    url: Optional[str] = None
    is_active: bool = True

    @field_validator("province")
    @classmethod
    def validate_province(cls, v):
        if v is not None and v not in PROVINCES:
            raise ValueError(f"Invalid province. Must be one of: {', '.join(PROVINCES)}")
        return v


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    venue: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    embed_link: Optional[str] = None
    url: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True
