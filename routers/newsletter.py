from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from db.models import get_db, NewsletterSubscriber
from schemas.newsletter_schema import NewsletterCreate, NewsletterResponse

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])


@router.post("", response_model=NewsletterResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(data: NewsletterCreate, db: Session = Depends(get_db)):
    """Subscribe an email to the newsletter (public)."""
    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == data.email
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="This email is already subscribed.")

    subscriber = NewsletterSubscriber(email=data.email)
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber
