# CDEN — Designer Notes (from the backend)

What the platform actually *does* and the data/states your designs need to cover. This
isn't a visual spec — it's the ground truth of screens, fields, states, and content the
backend produces, so designs line up with what's really there. CDEN serves **disabled
entrepreneurs across Canada**, so **accessibility is the product, not a polish layer** (see §6).

---

## 1. Three user types → three different homes

| Role | How they arrive | Their home screen shows |
|---|---|---|
| **Founder** | Public signup | Mentor recommendations, funding recommendations, events, their mentor connections |
| **Mentor** | Invited by admin (email link) | Founders they match, incoming requests, events, availability toggle |
| **Admin** | Internal | Back-office (uses a separate built-in panel — minimal design needed) |

After login the app routes by role. Design the founder and mentor experiences as two
distinct products that happen to share auth screens.

---

## 2. Screen inventory & the data each shows

### Shared / auth
- **Sign up** (founder only): email, password, confirm password.
- **Verify email**: 6-digit OTP entry (+ "resend code").
- **Log in**: email, password.
- **Forgot / reset password**: email → OTP → new password.

### Founder journey (the core demo flow)
1. **Onboarding form** — fields: full name, business name, **province** (dropdown),
   **business stage** (dropdown), **sectors** (multi-select), **communication preferences**
   (multi-select), **accessibility preferences** (multi-select), short bio.
2. **Founder dashboard** — four sections in one view:
   - **Recommended mentors** — cards with name, background, expertise tags, a **match score**,
     and a list of **"why matched" reason chips** (e.g. *"Works in your sector: technology"*).
   - **Recommended funding** — cards with program name, provider, amount range, deadline,
     score, reason chips, and an external apply link.
   - **Upcoming events** — title, date/time, venue + city, description, embeddable widget.
   - **My mentors** — connection cards with a **status badge** (see §4).
3. **Mentor detail** — full mentor profile.
4. **Request a mentor** — an action (button) on a mentor card → creates a request.

### Mentor journey
1. **Accept invite** — landing from an email link: shows their email (pre-filled, locked),
   set password.
2. **Mentor onboarding form** — fields: full name, background, **expertise** (multi-select),
   **sectors** (multi-select), **provinces they cover** (multi-select), **availability**
   (low/medium/high), **lived experience** (free text), "I share lived experience as a
   disabled entrepreneur" (toggle).
3. **Mentor dashboard**:
   - **Matched founders** — ranked founder cards (business, sector, stage, reason chips).
   - **Requests & connections** — founders who requested them, with status badges + accept/decline actions.
   - **Upcoming events**.
   - **Availability toggle** — "Accepting new founders" on/off (when off, they disappear
     from founder recommendations — worth a confirmation/explainer).

### Admin
Uses a built-in server-rendered panel — **no custom design needed** for the demo.

---

## 3. Real values to design components around

Design chips/dropdowns/badges against these **actual** values (don't invent labels — but
DO design human-friendly display text; the backend uses snake_case keys):

- **Provinces:** the 13 Canadian provinces/territories (2-letter codes: ON, BC, QC, AB, …).
- **Business stage:** `idea, pre_seed, early_revenue, growth, scaling` (5 chips).
- **Sectors:** technology, healthcare, retail, manufacturing, agriculture, creative arts,
  professional services, social enterprise, food & beverage, education, other (11).
- **Communication prefs:** email, phone, video call, text, in person.
- **Accessibility prefs:** screen reader, captions, ASL interpretation, large text,
  plain language, flexible scheduling, quiet environment, none.
- **Mentor expertise:** fundraising, grants & funding, marketing, sales, operations,
  product, legal, finance & accounting, hiring & HR, technology, accessibility,
  go-to-market, scaling (13 — needs a scalable tag/chip layout).
- **Availability:** low / medium / high (3-state — could be a segmented control).

> Tip: many of these are **multi-select with up to 11–13 options**. Design a tag/chip input
> and a card chip-overflow pattern ("+3 more") now, you'll need it everywhere.

---

## 4. Match status — design a badge for each

A founder↔mentor connection moves through these states. Each needs a distinct visual:

| Status | Meaning | Suggested treatment |
|---|---|---|
| `requested` | Founder asked, mentor hasn't responded | Pending / amber |
| `confirmed` | Mentor (or admin) accepted — active pairing | Success / green |
| `declined` | Mentor said no | Muted / grey |
| `suggested` | Proposed but not yet requested (future use) | Neutral |

Also flag **admin-arranged** matches (an `is_admin_override` flag) — maybe a small
"matched by CDEN" tag, since those weren't founder-initiated.

---

## 5. States to design for EVERY list/card screen

The backend returns these realities — designs must cover them:
- **Empty states** — *no recommendations yet* (e.g. founder hasn't onboarded), *no events*,
  *no connections yet*, *no requests yet*. These are common at demo time; make them warm,
  not blank.
- **Onboarding-incomplete** — recommendations are **blocked** until the founder/mentor
  finishes onboarding (backend returns an error). Design a "finish your profile to unlock
  matches" prompt.
- **Score + reasons are always present on recommendations** — the "why" chips are a key
  differentiator; give them real estate, don't bury them.
- **Loading** — dashboards aggregate several things in one call; a single skeleton is fine.
- **Error / wrong-role** — the backend blocks cross-role access; unlikely in normal UI but
  design a generic error toast.

---

## 6. Accessibility — this is the whole point ♿

The audience is disabled entrepreneurs, and founders literally tell us their access needs
(`accessibility_preferences`). Treat WCAG 2.1 AA as the floor, and specifically:

- **Screen reader** users: semantic structure, labels on every input, meaningful alt text,
  ARIA where needed. The match-reason chips must be readable in sequence.
- **Captions / ASL**: any event or media must accommodate these.
- **Large text / reflow**: layouts must survive 200% zoom and large font sizes without
  breaking — avoid fixed-height cards that clip content.
- **Plain language**: offer clear, jargon-free microcopy. (We expose snake_case keys; you
  design the friendly labels.)
- **Flexible scheduling / quiet environment**: relevant to how events and mentor sessions
  are presented.
- **Color & contrast**: status badges and score indicators must not rely on color alone —
  pair with text/icon.
- **Keyboard**: every action (request mentor, accept, toggle availability) must be fully
  keyboard-operable with visible focus.

Consider designing an **accessibility preferences** affordance prominently in onboarding —
it signals the platform's values and is functionally important.

---

## 7. Out of scope — do NOT design these (for now)

Per the project scope, these don't exist in the backend; designing them would mislead:
- In-app **messaging/chat** between founder & mentor.
- **Session booking/scheduling / calendars.** A "confirmed" match means *introduced —
  continue off-platform*. Design the connection as an introduction, not a booking system.
- Community feed, cohorts, analytics dashboards, partner/government reporting.

A confirmed connection is the **end** of the current flow. The natural CTA is something like
"You're connected — reach out via your preferred channel," not "Book a session."

---

## 8. Content the backend generates (design around real copy)

- **Match reason chips** (shown verbatim): *"Works in your sector(s): technology"*,
  *"Available in ON"*, *"Shares lived experience as a disabled entrepreneur"*,
  *"Designed for disabled entrepreneurs"*. Short, factual — design as small chips/pills.
- **Match scores** are small integers (~0–10). Design as a subtle rank indicator, not a
  precise percentage.
- **Emails** the system sends (so design matching in-app moments): email verification OTP,
  mentor invite, "a founder requested you", "your request was accepted". The in-app
  notification/empty states should echo these moments.
