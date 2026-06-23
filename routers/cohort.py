from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from db.models import get_db, Cohort
from schemas.cohort_schema import CohortCreate, CohortResponse

router = APIRouter(prefix="/api/cohorts", tags=["cohorts"])


@router.post("", response_model=CohortResponse, status_code=status.HTTP_201_CREATED)
async def join_cohort(data: CohortCreate, db: Session = Depends(get_db)):
    """Submit a founder's application to join a cohort (public)."""
    cohort = Cohort(**data.model_dump())
    db.add(cohort)
    try:
        db.commit()
        db.refresh(cohort)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return cohort
