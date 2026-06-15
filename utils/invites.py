"""Shared mentor-invite logic, used by both the admin API router and the
SQLAdmin panel form so the behaviour stays identical.
"""
import os
import secrets
from datetime import datetime, timedelta

from db.models import User, MentorInvite
from utils.email_sender import send_mentor_invite_email

# Where the mentor accept page lives on the frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
INVITE_EXPIRY_DAYS = 7


def invite_link(token: str) -> str:
    return f"{FRONTEND_URL}/mentor/accept?token={token}"


def create_mentor_invite(db, email: str, invited_by_id=None):
    """Create a tokenized mentor invite.

    Returns (invite, error_message). On success error_message is None;
    on failure invite is None. Best-effort emails the invite link.
    """
    if db.query(User).filter(User.email == email).first():
        return None, "A user with this email already exists"

    # Keep only one live invite per email
    pending = db.query(MentorInvite).filter(
        MentorInvite.email == email,
        MentorInvite.status == "pending",
    ).all()
    for inv in pending:
        inv.status = "revoked"

    invite = MentorInvite(
        email=email,
        token=secrets.token_urlsafe(32),
        invited_by=invited_by_id,
        expires_at=datetime.now() + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    db.add(invite)
    try:
        db.commit()
        db.refresh(invite)
    except Exception as e:
        db.rollback()
        return None, str(e)

    # Best-effort email; callers also get the link back so nothing blocks on SMTP
    try:
        send_mentor_invite_email(invite.email, invite_link(invite.token))
    except Exception as e:
        print(f"Error sending mentor invite email: {e}")

    return invite, None
