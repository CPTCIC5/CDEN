from fastapi import Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from db.models import User, get_db
from typing import Optional

# Configuration
SECRET_KEY = "your-secret-key-keep-it-secret"  # Use environment variable in production

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def create_session(request: Request, user: User):
    request.session["user_id"] = user.id

def end_session(request: Request):
    request.session.clear()


def require_role(*allowed_roles: str):
    """Dependency factory that enforces the current user has one of the given roles.

    Usage:  current_user: User = Depends(require_role("admin"))
    """
    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return _checker