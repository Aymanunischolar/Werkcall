# ADR 0002: In-memory repository fallback for the free demo path

## Status
Accepted

## Context
The blueprint's build principle requires the repository to "work in a free
browser-first mode." Requiring a Supabase project, Google OAuth app, and
HubSpot private app just to `git clone && run` would contradict that.

## Decision
`backend/app/db/repository.py` exposes a `Repository` Protocol. If
`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set, it returns the real
`SessionRepository` (Supabase-backed). Otherwise it returns
`InMemoryRepository`, which implements the identical interface. The same
pattern is used for Google Calendar and HubSpot
(`backend/app/services/calendar.py`, `crm.py`): an in-memory stand-in
generates deterministic slots and enforces no-double-booking / upsert
semantics until real OAuth/API credentials are supplied.

## Consequences
- `docker-compose up` with an empty `.env` (just `VOICE_PROVIDER=mock`)
  produces a fully working demo: sessions, tool calls, evals, dashboard.
- Data does not survive a process restart in this mode — acceptable for a
  demo, explicitly called out in SECURITY.md.
- When real credentials are added, no API or conversation-controller code
  changes; only the factory functions (`get_repository`, `get_calendar_client`,
  `get_crm_client`) swap implementations.
