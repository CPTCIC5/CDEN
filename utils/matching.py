"""Rule-based matching for mentor and funding recommendations (MVP).

Deliberately simple and transparent: each rule adds points and a
human-readable reason, so the dashboard can explain *why* something was
recommended. No ML, no external calls.
"""


def _as_list(value):
    """Tolerate None / non-list JSON column values."""
    return value if isinstance(value, list) else []


def score_mentor(founder, mentor):
    """Score a single mentor against a founder. Returns (score, reasons)."""
    score = 0
    reasons = []

    f_sectors = set(_as_list(founder.sectors))
    m_sectors = set(_as_list(mentor.sectors))
    shared = f_sectors & m_sectors
    if shared:
        score += 3 * len(shared)
        reasons.append(f"Works in your sector(s): {', '.join(sorted(shared))}")

    if founder.province and founder.province in _as_list(mentor.provinces):
        score += 2
        reasons.append(f"Available in {founder.province}")

    if mentor.shares_lived_experience:
        score += 2
        reasons.append("Shares lived experience as a disabled entrepreneur")

    if mentor.availability == "high":
        score += 1
        reasons.append("High availability")

    return score, reasons


def recommend_mentors(founder, mentors, limit=5):
    """Rank accepting mentors for a founder, best first."""
    results = []
    for mentor in mentors:
        if not mentor.is_accepting or not mentor.is_onboarded:
            continue
        score, reasons = score_mentor(founder, mentor)
        results.append((score, reasons, mentor))

    results.sort(key=lambda r: r[0], reverse=True)
    return results[:limit]


def score_funding(founder, program):
    """Score a funding program against a founder. Returns (score, reasons).

    Returns a score of -1 to signal the founder is ineligible (program is
    restricted to provinces the founder is not in), so callers can drop it.
    """
    score = 0
    reasons = []

    program_provinces = _as_list(program.provinces)
    if not program_provinces:
        score += 2
        reasons.append("Available across Canada")
    elif founder.province and founder.province in program_provinces:
        score += 3
        reasons.append(f"Eligible in {founder.province}")
    elif founder.province:
        # Restricted program and founder is outside its provinces -> ineligible
        return -1, []

    f_sectors = set(_as_list(founder.sectors))
    p_sectors = set(_as_list(program.sectors))
    if p_sectors:
        shared = f_sectors & p_sectors
        if shared:
            score += 3 * len(shared)
            reasons.append(f"Targets your sector(s): {', '.join(sorted(shared))}")
    else:
        reasons.append("Open to all sectors")

    p_stages = _as_list(program.business_stages)
    if founder.business_stage and (not p_stages or founder.business_stage in p_stages):
        score += 2
        reasons.append(f"Fits your business stage ({founder.business_stage})")

    if program.accessibility_focused:
        score += 3
        reasons.append("Designed for disabled entrepreneurs")

    return score, reasons


def recommend_funding(founder, programs, limit=10):
    """Rank active funding programs for a founder, best first."""
    results = []
    for program in programs:
        if not program.is_active:
            continue
        score, reasons = score_funding(founder, program)
        if score < 0:
            continue  # ineligible
        results.append((score, reasons, program))

    results.sort(key=lambda r: r[0], reverse=True)
    return results[:limit]
