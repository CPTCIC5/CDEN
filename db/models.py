import os
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, Float, JSON
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime
from sqlalchemy import create_engine
from passlib.context import CryptContext
from dotenv import load_dotenv
from sqlalchemy import UniqueConstraint
from utils.constants import ROLE_FOUNDER, MATCH_REQUESTED

load_dotenv()

# Database connection. Defaults to local SQLite; set DATABASE_URL (e.g. a
# Postgres URL) in the environment to point at a managed database.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Managed Postgres (e.g. Render) requires SSL; pre-ping avoids stale conns.
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__= 'users'

    id= Column(Integer, primary_key=True)
    email= Column(String(255), unique=True, nullable=False)
    password= Column(String(255), nullable=False)
    joined_at= Column(DateTime, default=datetime.now)
    is_verified= Column(Boolean, default=False)
    is_active= Column(Boolean, default=True)
    is_admin= Column(Boolean, default=False)
    # One of: "founder" | "mentor" | "admin"
    role= Column(String(20), default=ROLE_FOUNDER, nullable=False)

    # Relationships
    profile= relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    founder_profile= relationship("FounderProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.password)

    def set_password(self, password):
        self.password = pwd_context.hash(password)

    def __repr__(self):
        return self.email

class Profile(Base):
    __tablename__= 'profiles'

    nickname= Column(String(255), nullable=True)
    id= Column(Integer, primary_key=True)
    user_id= Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), unique=True, nullable=False)

    avatar= Column(String(255))

    # Relationship
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return self.nickname or f"Profile {self.id}"
    

class VerificationOTP(Base):
    __tablename__ = 'verification_otps'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    otp = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)

    def is_valid(self):
        """Check if the OTP is still valid (not expired and not used)"""
        return datetime.now() < self.expires_at and not self.is_used

    def mark_as_used(self):
        """Mark this OTP as used"""
        self.is_used = True


class FounderProfile(Base):
    """Onboarding data captured for a founder after signup.

    Lists (sector, communication/accessibility preferences) are stored as
    JSON arrays so they can hold multiple selections and feed rule-based
    matching directly.
    """
    __tablename__ = 'founder_profiles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), unique=True, nullable=False)

    full_name = Column(String(255), nullable=True)
    business_name = Column(String(255), nullable=True)
    province = Column(String(2), nullable=True)              # e.g. "ON"
    business_stage = Column(String(50), nullable=True)       # one of BUSINESS_STAGES
    sectors = Column(JSON, default=list)                     # list[str] from SECTORS
    communication_preferences = Column(JSON, default=list)   # list[str]
    accessibility_preferences = Column(JSON, default=list)   # list[str]
    bio = Column(Text, nullable=True)

    is_onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="founder_profile")

    def __repr__(self):
        return self.business_name or f"FounderProfile {self.id}"


class MentorProfile(Base):
    """Profile for a mentor (a User with role 'mentor').

    expertise / sectors / provinces are JSON arrays so a mentor can cover
    several of each, which the rule-based matcher scores against founders.
    """
    __tablename__ = 'mentor_profiles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), unique=True, nullable=False)

    full_name = Column(String(255), nullable=True)
    background = Column(Text, nullable=True)            # short professional bio
    expertise = Column(JSON, default=list)              # list[str] from EXPERTISE_AREAS
    sectors = Column(JSON, default=list)                # list[str] from SECTORS
    provinces = Column(JSON, default=list)              # provinces they can mentor in
    availability = Column(String(20), nullable=True)    # one of AVAILABILITY
    lived_experience = Column(Text, nullable=True)      # free description
    shares_lived_experience = Column(Boolean, default=False)  # identifies as a disabled entrepreneur

    is_accepting = Column(Boolean, default=True)        # currently taking founders
    is_onboarded = Column(Boolean, default=False)       # has completed their profile
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User")

    def __repr__(self):
        return self.full_name or f"MentorProfile {self.id}"


class MentorInvite(Base):
    """A tokenized invitation for someone to join as a mentor.

    Created by an admin. The token is emailed as a link; accepting it creates
    the mentor's User account (role 'mentor') and consumes the invite.
    """
    __tablename__ = 'mentor_invites'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(20), default="pending")      # pending | accepted | revoked
    invited_by = Column(Integer, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)

    def is_valid(self):
        """Pending and not expired."""
        return self.status == "pending" and datetime.now() < self.expires_at

    def __repr__(self):
        return f"MentorInvite {self.email} ({self.status})"


class FundingProgram(Base):
    """A funding opportunity founders can be matched to.

    Empty `provinces` means the program is available nationally. Empty
    `sectors` / `business_stages` means it is open to all of those.
    """
    __tablename__ = 'funding_programs'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=True)
    provider_type = Column(String(50), nullable=True)   # one of FUNDING_PROVIDER_TYPES
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)

    amount_min = Column(Integer, nullable=True)          # CAD
    amount_max = Column(Integer, nullable=True)          # CAD
    sectors = Column(JSON, default=list)                 # eligible sectors ([] = all)
    provinces = Column(JSON, default=list)               # eligible provinces ([] = national)
    business_stages = Column(JSON, default=list)         # eligible stages ([] = all)
    accessibility_focused = Column(Boolean, default=False)  # targets disabled entrepreneurs
    application_deadline = Column(String(100), nullable=True)  # free text, e.g. "Rolling" or a date

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return self.name


class Event(Base):
    """A community event to display to founders.

    `embed_link` is typically a Luma embed URL the frontend renders inline;
    `url` is the plain link to the event page.
    """
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    venue = Column(String(255), nullable=True)          # venue name or "Online"
    city = Column(String(120), nullable=True)
    province = Column(String(2), nullable=True)         # optional, one of PROVINCES
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    embed_link = Column(String(500), nullable=True)     # e.g. Luma embed URL
    url = Column(String(500), nullable=True)            # event page link

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return self.title


class MentorMatch(Base):
    """A persisted founder<->mentor connection and its lifecycle status.

    Identified by the two users so it survives profile edits. A given founder
    and mentor can only be paired once (unique constraint).
    """
    __tablename__ = 'mentor_matches'
    __table_args__ = (
        UniqueConstraint('founder_user_id', 'mentor_user_id', name='uq_founder_mentor'),
    )

    id = Column(Integer, primary_key=True)
    founder_user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    mentor_user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    status = Column(String(20), default=MATCH_REQUESTED, nullable=False)  # one of MATCH_STATUSES
    is_admin_override = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"MentorMatch f{self.founder_user_id}-m{self.mentor_user_id} ({self.status})"