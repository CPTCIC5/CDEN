from typing import List
from pydantic import BaseModel

from schemas.founder_schema import FounderProfileResponse
from schemas.mentor_schema import MentorRecommendation
from schemas.funding_schema import FundingRecommendation
from schemas.event_schema import EventResponse


class DashboardResponse(BaseModel):
    """Everything the founder dashboard needs in a single call."""
    founder: FounderProfileResponse
    mentor_recommendations: List[MentorRecommendation] = []
    funding_recommendations: List[FundingRecommendation] = []
    events: List[EventResponse] = []
