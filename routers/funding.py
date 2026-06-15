from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from db.models import get_db, User, FounderProfile, FundingProgram
from schemas.funding_schema import FundingProgramResponse, FundingRecommendation
from utils.auth import get_current_user
from utils.matching import recommend_funding
from utils.constants import ROLE_FOUNDER

router = APIRouter(prefix="/api/funding", tags=["funding"])


@router.get("/recommendations", response_model=List[FundingRecommendation])
async def funding_recommendations(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recommend funding programs for the current founder using rule-based matching."""
    if current_user.role != ROLE_FOUNDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Funding recommendations are only available to founder accounts.",
        )
    founder = db.query(FounderProfile).filter(
        FounderProfile.user_id == current_user.id
    ).first()
    if not founder or not founder.is_onboarded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your founder onboarding to get funding recommendations.",
        )

    programs = db.query(FundingProgram).all()
    ranked = recommend_funding(founder, programs, limit=limit)

    return [
        FundingRecommendation(program=program, score=score, match_reasons=reasons)
        for score, reasons, program in ranked
    ]


@router.get("", response_model=List[FundingProgramResponse])
async def list_funding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all active funding programs (directory view)."""
    return db.query(FundingProgram).filter(FundingProgram.is_active == True).all()


@router.get("/{program_id}", response_model=FundingProgramResponse)
async def get_funding(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single funding program's details."""
    program = db.query(FundingProgram).filter(FundingProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funding program not found")
    return program
