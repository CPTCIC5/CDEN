"""Seed sample admin, mentors, Canadian funding programs, and events for the demo.

Idempotent: skips records that already exist (matched by email / name / title).
Run with:  python seed.py
"""
from datetime import datetime
from db.models import (
    SessionLocal, Base, engine,
    User, MentorProfile, FundingProgram, Event,
)
from utils.constants import ROLE_MENTOR, ROLE_ADMIN

Base.metadata.create_all(bind=engine)

ADMIN_EMAIL = "admin@cden.demo"
ADMIN_PASSWORD = "admin-demo-password"


MENTORS = [
    {
        "email": "amara.okafor@cden.demo",
        "full_name": "Amara Okafor",
        "background": "Former fintech founder (exited 2021). 12 years in startup operations and fundraising.",
        "expertise": ["fundraising", "operations", "go_to_market"],
        "sectors": ["technology", "professional_services"],
        "provinces": ["ON", "QC"],
        "availability": "high",
        "lived_experience": "Built and ran a company while managing a chronic illness; mentors on sustainable founder pace.",
        "shares_lived_experience": True,
    },
    {
        "email": "david.tremblay@cden.demo",
        "full_name": "David Tremblay",
        "background": "Grant-writing consultant who has secured $4M+ in government funding for small businesses.",
        "expertise": ["grants_funding", "finance_accounting"],
        "sectors": ["social_enterprise", "agriculture", "manufacturing"],
        "provinces": ["QC", "NB", "NS"],
        "availability": "medium",
        "lived_experience": "Deaf entrepreneur; advocates for accessible funding processes.",
        "shares_lived_experience": True,
    },
    {
        "email": "priya.sharma@cden.demo",
        "full_name": "Priya Sharma",
        "background": "Marketing lead turned founder coach. Specializes in early-stage GTM and brand.",
        "expertise": ["marketing", "sales", "product"],
        "sectors": ["retail", "food_beverage", "creative_arts"],
        "provinces": ["BC", "AB"],
        "availability": "high",
        "lived_experience": "",
        "shares_lived_experience": False,
    },
    {
        "email": "michael.bear@cden.demo",
        "full_name": "Michael Bear",
        "background": "Operations and scaling advisor; previously COO of a 200-person social enterprise.",
        "expertise": ["operations", "scaling", "hiring_hr"],
        "sectors": ["social_enterprise", "healthcare", "education"],
        "provinces": ["MB", "SK", "AB"],
        "availability": "low",
        "lived_experience": "Wheelchair user; built remote-first, accessible workplaces.",
        "shares_lived_experience": True,
    },
    {
        "email": "sophie.chen@cden.demo",
        "full_name": "Sophie Chen",
        "background": "Product and technology mentor, ex-engineering manager at two Canadian SaaS scaleups.",
        "expertise": ["technology", "product", "accessibility"],
        "sectors": ["technology", "education"],
        "provinces": ["ON", "BC"],
        "availability": "medium",
        "lived_experience": "Neurodivergent founder; mentors on building accessible products.",
        "shares_lived_experience": True,
    },
]


FUNDING_PROGRAMS = [
    {
        "name": "Canada Small Business Financing Program (CSBFP)",
        "provider": "Government of Canada",
        "provider_type": "government",
        "description": "Loans to help small businesses purchase equipment, property, and cover startup costs.",
        "url": "https://ised-isde.canada.ca/site/canada-small-business-financing-program/en",
        "amount_min": 5000,
        "amount_max": 1000000,
        "sectors": [],
        "provinces": [],
        "business_stages": ["pre_seed", "early_revenue", "growth"],
        "accessibility_focused": False,
        "application_deadline": "Rolling",
    },
    {
        "name": "Futurpreneur Canada Startup Program",
        "provider": "Futurpreneur Canada",
        "provider_type": "nonprofit",
        "description": "Financing and mentorship for entrepreneurs aged 18-39 launching a new business.",
        "url": "https://www.futurpreneur.ca/en/",
        "amount_min": 0,
        "amount_max": 60000,
        "sectors": [],
        "provinces": [],
        "business_stages": ["idea", "pre_seed", "early_revenue"],
        "accessibility_focused": False,
        "application_deadline": "Rolling",
    },
    {
        "name": "Disability Employment Innovation Grant",
        "provider": "Employment and Social Development Canada",
        "provider_type": "government",
        "description": "Grants supporting businesses led by or employing persons with disabilities.",
        "url": "https://www.canada.ca/en/employment-social-development.html",
        "amount_min": 10000,
        "amount_max": 100000,
        "sectors": [],
        "provinces": [],
        "business_stages": [],
        "accessibility_focused": True,
        "application_deadline": "2026-09-30",
    },
    {
        "name": "Ontario Together Trade Fund",
        "provider": "Government of Ontario",
        "provider_type": "government",
        "description": "Supports Ontario manufacturers and businesses diversifying supply chains.",
        "url": "https://www.ontario.ca/page/business-grants-and-financing",
        "amount_min": 25000,
        "amount_max": 500000,
        "sectors": ["manufacturing", "technology"],
        "provinces": ["ON"],
        "business_stages": ["growth", "scaling"],
        "accessibility_focused": False,
        "application_deadline": "Rolling",
    },
    {
        "name": "Women Entrepreneurship Loan Fund",
        "provider": "Government of Canada",
        "provider_type": "government",
        "description": "Loans for women-owned and women-led businesses to start up and scale.",
        "url": "https://ised-isde.canada.ca/site/women-entrepreneurship-strategy/en",
        "amount_min": 0,
        "amount_max": 50000,
        "sectors": [],
        "provinces": [],
        "business_stages": ["pre_seed", "early_revenue", "growth"],
        "accessibility_focused": False,
        "application_deadline": "Rolling",
    },
    {
        "name": "BC Launch Online Grant",
        "provider": "Government of British Columbia",
        "provider_type": "government",
        "description": "Helps BC small businesses build and improve their online store presence.",
        "url": "https://www.launchonline.ca/",
        "amount_min": 0,
        "amount_max": 7500,
        "sectors": ["retail", "food_beverage", "creative_arts"],
        "provinces": ["BC"],
        "business_stages": ["early_revenue", "growth"],
        "accessibility_focused": False,
        "application_deadline": "Rolling",
    },
    {
        "name": "Rise Asset Development Financing",
        "provider": "Rise (nonprofit)",
        "provider_type": "nonprofit",
        "description": "Low-interest loans and mentorship for entrepreneurs with mental health or addiction challenges.",
        "url": "https://www.riseassetdevelopment.com/",
        "amount_min": 1000,
        "amount_max": 25000,
        "sectors": [],
        "provinces": ["ON"],
        "business_stages": ["idea", "pre_seed", "early_revenue"],
        "accessibility_focused": True,
        "application_deadline": "Rolling",
    },
    {
        "name": "AgriInnovate Program",
        "provider": "Agriculture and Agri-Food Canada",
        "provider_type": "government",
        "description": "Repayable contributions for agri-business innovation and commercialization.",
        "url": "https://agriculture.canada.ca/en/programs/agriinnovate",
        "amount_min": 50000,
        "amount_max": 5000000,
        "sectors": ["agriculture", "manufacturing"],
        "provinces": [],
        "business_stages": ["growth", "scaling"],
        "accessibility_focused": False,
        "application_deadline": "Rolling",
    },
]


EVENTS = [
    {
        "title": "CDEN Founder Mixer (Toronto)",
        "description": "An accessible evening of networking for disabled founders, mentors, and funders. ASL interpretation and captioning provided.",
        "venue": "MaRS Discovery District",
        "city": "Toronto",
        "province": "ON",
        "start_at": datetime(2026, 7, 9, 18, 0),
        "end_at": datetime(2026, 7, 9, 21, 0),
        "embed_link": "https://lu.ma/embed/event/evt-cden-mixer-to/simple",
        "url": "https://lu.ma/cden-mixer-toronto",
    },
    {
        "title": "Funding Your Startup: Grants 101 (Online)",
        "description": "A virtual workshop walking through Canadian grant programs and how to write a winning application.",
        "venue": "Online",
        "city": "Virtual",
        "province": None,
        "start_at": datetime(2026, 7, 22, 13, 0),
        "end_at": datetime(2026, 7, 22, 14, 30),
        "embed_link": "https://lu.ma/embed/event/evt-cden-grants101/simple",
        "url": "https://lu.ma/cden-grants-101",
    },
    {
        "title": "Accessible Product Design Workshop (Vancouver)",
        "description": "Hands-on session on building products that work for everyone, led by CDEN mentors.",
        "venue": "Vancouver Public Library, Central Branch",
        "city": "Vancouver",
        "province": "BC",
        "start_at": datetime(2026, 8, 5, 10, 0),
        "end_at": datetime(2026, 8, 5, 16, 0),
        "embed_link": "https://lu.ma/embed/event/evt-cden-a11y-design/simple",
        "url": "https://lu.ma/cden-accessible-design",
    },
]


def seed_admin(db):
    if db.query(User).filter(User.email == ADMIN_EMAIL).first():
        return 0
    admin = User(email=ADMIN_EMAIL, role=ROLE_ADMIN, is_verified=True, is_admin=True)
    admin.set_password(ADMIN_PASSWORD)
    db.add(admin)
    db.commit()
    return 1


def seed_mentors(db):
    created = 0
    for data in MENTORS:
        user = db.query(User).filter(User.email == data["email"]).first()
        if not user:
            user = User(email=data["email"], role=ROLE_MENTOR, is_verified=True)
            user.set_password("mentor-demo-password")
            db.add(user)
            db.commit()
            db.refresh(user)

        if db.query(MentorProfile).filter(MentorProfile.user_id == user.id).first():
            continue

        db.add(MentorProfile(
            user_id=user.id,
            full_name=data["full_name"],
            background=data["background"],
            expertise=data["expertise"],
            sectors=data["sectors"],
            provinces=data["provinces"],
            availability=data["availability"],
            lived_experience=data["lived_experience"],
            shares_lived_experience=data["shares_lived_experience"],
            is_accepting=True,
            is_onboarded=True,
        ))
        created += 1
    db.commit()
    return created


def seed_funding(db):
    created = 0
    for data in FUNDING_PROGRAMS:
        if db.query(FundingProgram).filter(FundingProgram.name == data["name"]).first():
            continue
        db.add(FundingProgram(**data, is_active=True))
        created += 1
    db.commit()
    return created


def seed_events(db):
    created = 0
    for data in EVENTS:
        if db.query(Event).filter(Event.title == data["title"]).first():
            continue
        db.add(Event(**data, is_active=True))
        created += 1
    db.commit()
    return created


def main():
    db = SessionLocal()
    try:
        a = seed_admin(db)
        m = seed_mentors(db)
        f = seed_funding(db)
        e = seed_events(db)
        print(f"Seeded {a} admin, {m} mentors, {f} funding programs, {e} events.")
        print(f"Admin login: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
