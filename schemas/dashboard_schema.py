from typing import List
from pydantic import BaseModel

from schemas.founder_schema import FounderProfileResponse
from schemas.mentor_schema import MentorRecommendation, MentorProfileResponse
from schemas.funding_schema import FundingRecommendation
from schemas.event_schema import EventResponse
from schemas.match_schema import FounderSideMatch, MentorSideMatch


class DashboardResponse(BaseModel):
    """Everything the founder dashboard needs in a single call."""
    founder: FounderProfileResponse
    mentor_recommendations: List[MentorRecommendation] = []
    funding_recommendations: List[FundingRecommendation] = []
    events: List[EventResponse] = []
    matches: List[FounderSideMatch] = []


class FounderMatch(BaseModel):
    """A founder a mentor is well-suited to help, with score and reasons."""
    founder: FounderProfileResponse
    score: int
    match_reasons: List[str] = []


class MentorDashboardResponse(BaseModel):
    """Everything the mentor dashboard needs in a single call."""
    mentor: MentorProfileResponse
    matched_founders: List[FounderMatch] = []      # algorithm ranking (discovery)
    matches: List[MentorSideMatch] = []            # actual connections + requests
    events: List[EventResponse] = []
