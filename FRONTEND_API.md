# CDEN Backend — Frontend API Guide

Reference for the frontend developer (and for pasting into an AI assistant as context).
CDEN is a community platform connecting **founders** (disabled entrepreneurs in Canada)
with **mentors**, **funding programs**, and **events**, with an **admin** back-office.

- **Stack:** FastAPI + SQLAlchemy + PostgreSQL.
- **Base URL (local):** `https://cden.onrender.com`
- **Content type:** JSON (`Content-Type: application/json`) for all bodies unless noted.
- **Interactive API docs:** `GET /docs` (Swagger UI) — always the live source of truth.

---

## 1. Authentication model — READ THIS FIRST

Auth is **cookie-based sessions**, not JWT/bearer tokens.

- On `login` / `register` / invite-accept, the server sets a **`session_cookie`**.
- The browser must **send that cookie on every request**. With `fetch`/`axios` you MUST set:
  - `fetch(url, { credentials: "include" })`
  - axios: `axios.defaults.withCredentials = true`
- There is **no `Authorization` header**. Don't send one.
- Logout: `POST /api/auth/logout`.

### ⚠️ CORS gotcha (important)
The backend currently uses `allow_origins=["*"]` **with** `allow_credentials=True`.
Browsers **reject** credentialed requests against a wildcard origin. For the frontend to
send the session cookie, the backend must echo your **exact** origin (e.g.
`http://localhost:5173`). If you hit "CORS error" or the cookie isn't sent, tell the
backend dev to set the specific origin in `main.py` CORS config. (Server-to-server / curl
is unaffected — this only bites browsers.)

### Roles
Every user has one role: `founder`, `mentor`, or `admin`.
- **Public signup is always a `founder`.**
- **Mentors** join only via an admin invite link.
- **Admins** are seeded server-side.

Endpoints are role-gated. Calling a founder-only endpoint as a mentor returns **403** with
a clear message (and vice versa).

### Error format
All errors are FastAPI standard:
```json
{ "detail": "Human readable message" }
```
Validation errors (bad enum value, missing field) return **422** with a `detail` array.
Common codes: `400` (bad request / business rule), `401` (not logged in),
`403` (wrong role), `404` (not found), `422` (validation).

---

## 2. The user journeys at a glance

**Founder:** `register` → `verify-email` → `founders/onboarding` → `founders/dashboard`
(mentor recs + funding recs + events) → request a mentor → see status.

**Mentor:** open invite link → `invite/{token}/accept` (sets password, auto-logged-in) →
`mentors/onboarding` → `mentors/dashboard` (matched founders + incoming requests + events)
→ confirm/decline requests → toggle availability.

**Admin:** `login` → use REST endpoints or the `/admin` panel to invite mentors, create
funding programs & events, and override matches.

---

## 3. Enums / dropdown values

Fetch these live from **`GET /api/founders/options`** (no auth needed) so dropdowns never
drift. Current values:

| Field | Allowed values |
|---|---|
| `province` | `AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, QC, SK, YT` (2-letter codes) |
| `business_stage` | `idea, pre_seed, early_revenue, growth, scaling` |
| `sectors` | `technology, healthcare, retail, manufacturing, agriculture, creative_arts, professional_services, social_enterprise, food_beverage, education, other` |
| `communication_preferences` | `email, phone, video_call, text, in_person` |
| `accessibility_preferences` | `screen_reader, captions, asl_interpretation, large_text, plain_language, flexible_scheduling, quiet_environment, none` |
| `expertise` (mentor) | `fundraising, grants_funding, marketing, sales, operations, product, legal, finance_accounting, hiring_hr, technology, accessibility, go_to_market, scaling` |
| `availability` (mentor) | `low, medium, high` |
| `provider_type` (funding) | `government, nonprofit, private, accelerator, financial_institution` |
| match `status` | `suggested, requested, confirmed, declined` |

`sectors`, `communication_preferences`, `accessibility_preferences`, `expertise`,
`provinces` (mentor/funding) are **arrays** (multi-select).

---

## 4. Auth & account endpoints (`/api/auth`)

| Method | Path | Auth | Body | Notes |
|---|---|---|---|---|
| POST | `/api/auth/register` | – | `{ email, password, confirm_password }` | Creates a **founder**, emails a 6-digit OTP, logs in. |
| POST | `/api/auth/verify-email` | – | `{ email, otp }` | Marks email verified. |
| POST | `/api/auth/resend-verification` | – | `{ email }` | Resend OTP. |
| POST | `/api/auth/login` | – | `{ email, password }` | Sets session cookie. Returns `{ user: {id,email,role}, message }`. |
| POST | `/api/auth/logout` | yes | – | Clears session. |
| GET | `/api/auth/verification-status` | yes | – | `{ is_verified, email, message }` |
| POST | `/api/auth/request-password-reset` | – | `{ email }` | Emails reset OTP (always 200, no email enumeration). |
| POST | `/api/auth/reset-password` | – | `{ email, otp, new_password, confirm_password }` | |
| POST | `/api/auth/change-password` | yes | `{ current_password, new_password, confirm_new_password }` | |
| PATCH | `/api/auth/profile/update/user-email` | yes | `{ email }` | |
| GET | `/api/auth/user/me` | yes | – | Generic profile (`nickname`, `avatar`). |
| GET | `/api/auth/user/{id}` | yes | – | Another user's generic profile. |
| DELETE | `/api/auth/delete-user` | yes | – | Deletes current user. |

**Register response (201):**
```json
{ "detail": "User created. Please check your email for verification code.",
  "user": { "id": 1, "email": "x@y.com", "is_verified": false, "role": "founder" } }
```

---

## 5. Founder endpoints (`/api/founders`)

| Method | Path | Auth | Body |
|---|---|---|---|
| GET | `/api/founders/options` | – | – (dropdown values, see §3) |
| POST | `/api/founders/onboarding` | founder | `FounderOnboarding` (below) — partial allowed, doubles as edit |
| GET | `/api/founders/me` | founder | – |
| GET | `/api/founders/onboarding/status` | yes | – → `{ is_verified, has_profile, is_onboarded }` |
| GET | `/api/founders/dashboard` | founder | – → `Dashboard` (below) |
| POST | `/api/founders/matches` | founder | `{ mentor_id }` — request a mentor |
| GET | `/api/founders/matches` | founder | – → `[FounderSideMatch]` |

**FounderOnboarding body** (all optional; `province` + `business_stage` + `sectors`
required for `is_onboarded` to flip true):
```json
{
  "full_name": "Jo Founder",
  "business_name": "AccessTech",
  "province": "ON",
  "business_stage": "pre_seed",
  "sectors": ["technology", "social_enterprise"],
  "communication_preferences": ["email", "video_call"],
  "accessibility_preferences": ["captions", "flexible_scheduling"],
  "bio": "..."
}
```

**FounderProfileResponse:**
```json
{ "id": 1, "user_id": 7, "full_name": "...", "business_name": "...",
  "province": "ON", "business_stage": "pre_seed", "sectors": ["technology"],
  "communication_preferences": ["email"], "accessibility_preferences": ["captions"],
  "bio": null, "is_onboarded": true }
```

**Dashboard response (one call powers the whole founder home):**
```json
{
  "founder": { ...FounderProfileResponse },
  "mentor_recommendations": [
    { "mentor": { ...MentorProfile }, "score": 8,
      "match_reasons": ["Works in your sector(s): technology", "Available in ON"] }
  ],
  "funding_recommendations": [
    { "program": { ...FundingProgram }, "score": 8,
      "match_reasons": ["Eligible in ON", "Designed for disabled entrepreneurs"] }
  ],
  "events": [ { ...Event } ],
  "matches": [ { ...FounderSideMatch } ]
}
```

**FounderSideMatch** (how a founder sees a connection):
```json
{ "id": 1, "status": "confirmed", "is_admin_override": false,
  "created_at": "2026-06-16T12:00:00", "mentor": { ...MentorProfile } }
```

---

## 6. Mentor endpoints (`/api/mentors`)

| Method | Path | Auth | Body / Notes |
|---|---|---|---|
| GET | `/api/mentors/recommendations` | **founder** | `?limit=5` → `[ { mentor, score, match_reasons } ]` |
| GET | `/api/mentors` | yes | Directory → `[MentorProfile]` |
| GET | `/api/mentors/{mentor_id}` | yes | One mentor |
| GET | `/api/mentors/invite/{token}` | – (public) | Validate invite → `{ email, valid, status }` |
| POST | `/api/mentors/invite/{token}/accept` | – (public) | `{ password, confirm_password }` → creates mentor, logs in |
| POST | `/api/mentors/onboarding` | mentor | `MentorOnboarding` (below) — partial allowed |
| GET | `/api/mentors/me` | mentor | Own profile |
| GET | `/api/mentors/dashboard` | mentor | → `MentorDashboard` (below) |
| PATCH | `/api/mentors/availability` | mentor | `{ is_accepting: true|false }` |
| GET | `/api/mentors/matches` | mentor | → `[MentorSideMatch]` (incoming + connections) |
| PATCH | `/api/mentors/matches/{match_id}` | mentor | `{ action: "confirm" | "decline" }` |

> **Route note:** `/api/mentors/recommendations` is for the **founder** viewing ranked
> mentors. A mentor calling it gets 403. Mentors use `/api/mentors/dashboard`.

**MentorOnboarding body** (`expertise` + `sectors` + `provinces` + `availability`
required for completion):
```json
{
  "full_name": "Amara Okafor",
  "background": "Former fintech founder...",
  "expertise": ["fundraising", "operations"],
  "sectors": ["technology"],
  "provinces": ["ON", "QC"],
  "availability": "high",
  "lived_experience": "Built a company while managing a chronic illness",
  "shares_lived_experience": true,
  "is_accepting": true
}
```

**MentorProfileResponse:**
```json
{ "id": 1, "user_id": 2, "full_name": "Amara Okafor", "background": "...",
  "expertise": ["fundraising"], "sectors": ["technology"], "provinces": ["ON"],
  "availability": "high", "lived_experience": "...", "shares_lived_experience": true,
  "is_accepting": true, "is_onboarded": true }
```

**MentorDashboard response:**
```json
{
  "mentor": { ...MentorProfileResponse },
  "matched_founders": [
    { "founder": { ...FounderProfile }, "score": 7,
      "match_reasons": ["Building in your sector(s): technology", "Based in ON, a region you cover"] }
  ],
  "matches": [ { ...MentorSideMatch } ],
  "events": [ { ...Event } ]
}
```
`matched_founders` = algorithm ranking (discovery). `matches` = real connection records
(filter by `status` to show incoming `requested` vs active `confirmed`).

**MentorSideMatch:**
```json
{ "id": 1, "status": "requested", "is_admin_override": false,
  "created_at": "...", "founder": { ...FounderProfile } }
```

---

## 7. Funding endpoints (`/api/funding`)

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/funding` | yes | All active programs |
| GET | `/api/funding/recommendations` | **founder** | `?limit=10` → `[ { program, score, match_reasons } ]` |
| GET | `/api/funding/{program_id}` | yes | One program |

**FundingProgramResponse:**
```json
{ "id": 1, "name": "Canada Small Business Financing Program", "provider": "Government of Canada",
  "provider_type": "government", "description": "...", "url": "https://...",
  "amount_min": 5000, "amount_max": 1000000, "sectors": [], "provinces": [],
  "business_stages": ["pre_seed","early_revenue"], "accessibility_focused": false,
  "application_deadline": "Rolling", "is_active": true }
```
Empty `provinces` = national. Empty `sectors`/`business_stages` = open to all.

---

## 8. Events endpoints (`/api/events`)

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/events` | yes | `?upcoming_only=true` (default) — soonest first |
| GET | `/api/events/{event_id}` | yes | One event |

**EventResponse:**
```json
{ "id": 1, "title": "CDEN Founder Mixer (Toronto)", "description": "...",
  "venue": "MaRS Discovery District", "city": "Toronto", "province": "ON",
  "start_at": "2026-07-09T18:00:00", "end_at": "2026-07-09T21:00:00",
  "embed_link": "https://lu.ma/embed/event/.../simple", "url": "https://lu.ma/...",
  "is_active": true }
```
`embed_link` is meant to be dropped into an `<iframe>` (Luma embed). `url` is the plain link.

---

## 9. Admin endpoints (`/api/admin`) — all require `admin` role

| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/api/admin/mentor-invites` | `{ email }` | Creates tokenized invite, emails it. Returns `{ id, email, token, status, invite_link }` |
| GET | `/api/admin/mentor-invites` | – | List invites |
| POST | `/api/admin/funding-programs` | `FundingProgramCreate` | Only `name` required; same fields as FundingProgramResponse |
| POST | `/api/admin/events` | `EventCreate` | Only `title` required; `start_at`/`end_at` are ISO datetimes |
| POST | `/api/admin/matches` | `{ founder_email, mentor_email, status? }` | **Override**: force/confirm a pairing (status defaults to `confirmed`) |
| GET | `/api/admin/matches` | – | All matches → `[MentorSideMatch]` |
| PATCH | `/api/admin/matches/{match_id}` | `{ status }` | Override a match's status |

### Admin panel (server-rendered, not for the SPA)
There's also a built-in admin UI at **`/admin`** (SQLAdmin) for CRUD on every table, plus
an "Invite a Mentor" form at `/admin/invite-mentor`. It has its **own** login
(`/admin/login`) separate from the API session. Use this for back-office data entry; the
SPA should use the `/api/admin/*` endpoints above.

---

## 10. The match lifecycle (how connections work)

```
Founder sees ranked mentors (dashboard)              ← discovery, nothing stored
   → POST /api/founders/matches { mentor_id }         → match created, status "requested"
   → mentor sees it on their dashboard / matches      → emailed automatically
   → PATCH /api/mentors/matches/{id} {action}         → "confirmed" or "declined"
   → founder emailed on confirm; both dashboards show the connection
Admin can POST /api/admin/matches to force a pairing  → status "confirmed", is_admin_override=true
```
- A founder can only request a given mentor **once** (409-style 400 if duplicate).
- A mentor must be `is_accepting: true` and onboarded to be requestable.
- **Emails are automatic & non-blocking:** mentor notified on new request, founder notified
  on accept. (No notification on decline — by design.)
- **Out of scope (don't build UI for these):** in-app messaging, session booking/scheduling.
  A confirmed match means "introduced — continue off-platform."

---

## 11. Quick frontend integration checklist

1. Set `credentials: "include"` (or `withCredentials`) on **every** request.
2. Have the backend dev set the exact CORS origin (see §1 gotcha) before testing in-browser.
3. After login/register, read `user.role` to route to the right home
   (founder dashboard vs mentor dashboard vs admin).
4. Gate the founder flow on `GET /api/founders/onboarding/status` (`is_onboarded`).
5. Populate all dropdowns from `GET /api/founders/options`.
6. Founder home = one call to `GET /api/founders/dashboard`.
   Mentor home = one call to `GET /api/mentors/dashboard`.
7. Render `match_reasons` arrays verbatim — they're human-readable ("why this match").
8. Embed events via the `embed_link` in an `<iframe>`.
