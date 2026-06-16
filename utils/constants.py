"""Shared domain constants for CDEN.

Kept as plain tuples/sets so they can be reused for validation, seeding,
and rule-based matching without pulling in a DB dependency.
"""

# Canadian provinces & territories (ISO-style short codes)
PROVINCES = {
    "AB": "Alberta",
    "BC": "British Columbia",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "NS": "Nova Scotia",
    "NT": "Northwest Territories",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "Prince Edward Island",
    "QC": "Quebec",
    "SK": "Saskatchewan",
    "YT": "Yukon",
}

# Business lifecycle stages a founder can be in
BUSINESS_STAGES = (
    "idea",
    "pre_seed",
    "early_revenue",
    "growth",
    "scaling",
)

# Sectors used for both founders and mentors / funding matching
SECTORS = (
    "technology",
    "healthcare",
    "retail",
    "manufacturing",
    "agriculture",
    "creative_arts",
    "professional_services",
    "social_enterprise",
    "food_beverage",
    "education",
    "other",
)

# How a founder prefers to be contacted
COMMUNICATION_PREFERENCES = (
    "email",
    "phone",
    "video_call",
    "text",
    "in_person",
)

# Accessibility needs / preferences (multi-select)
ACCESSIBILITY_PREFERENCES = (
    "screen_reader",
    "captions",
    "asl_interpretation",
    "large_text",
    "plain_language",
    "flexible_scheduling",
    "quiet_environment",
    "none",
)

# Mentor availability buckets
AVAILABILITY = (
    "low",       # ~1 hr / month
    "medium",    # ~2-4 hrs / month
    "high",      # 5+ hrs / month
)

# Areas a mentor can offer guidance in
EXPERTISE_AREAS = (
    "fundraising",
    "grants_funding",
    "marketing",
    "sales",
    "operations",
    "product",
    "legal",
    "finance_accounting",
    "hiring_hr",
    "technology",
    "accessibility",
    "go_to_market",
    "scaling",
)

# Type of organization offering a funding program
FUNDING_PROVIDER_TYPES = (
    "government",
    "nonprofit",
    "private",
    "accelerator",
    "financial_institution",
)

# User roles
ROLE_FOUNDER = "founder"
ROLE_MENTOR = "mentor"
ROLE_ADMIN = "admin"
ROLES = (ROLE_FOUNDER, ROLE_MENTOR, ROLE_ADMIN)

# Lifecycle of a founder<->mentor match
MATCH_SUGGESTED = "suggested"   # proposed by the algorithm/admin
MATCH_REQUESTED = "requested"   # founder asked to connect
MATCH_CONFIRMED = "confirmed"   # mentor (or admin) accepted -> active pairing
MATCH_DECLINED = "declined"     # mentor/admin declined
MATCH_STATUSES = (MATCH_SUGGESTED, MATCH_REQUESTED, MATCH_CONFIRMED, MATCH_DECLINED)
