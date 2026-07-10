# Security & Privacy

WerkCall AI is a portfolio demo for a fictional company (NordWerk Haustechnik
GmbH). It is not a certified production system and does not process real
customer or medical data. See blueprint §10 for the full design rationale.

## Data handling

- **Synthetic data only.** All customer identities, phone numbers, addresses
  and appointments in this repository (see `sample-data/`) are fictional.
  Do not submit real personal information, real medical details, or
  confidential company documents through the demo — the Gemini free tier may
  use submitted content to improve Google's products.
- **No raw audio by default.** `STORE_RAW_AUDIO=false` in `.env.example`;
  the voice gateway processes audio in memory and never writes it to disk
  or Supabase.
- **Redaction.** Phone numbers, email addresses and postal codes are
  redacted before any transcript text is written to `conversation_turns`
  (see `backend/app/policies/redaction.py`).
- **Deletion.** `DELETE /api/sessions/{id}` soft-deletes a session's data on
  request (dashboard "Delete this session's data" button).
- **Retention.** `DEMO_DATA_RETENTION_DAYS` bounds how long demo sessions
  are kept; there is no automated backup of the free-tier Supabase project.

## Secrets

- Never commit a populated `.env` file, n8n credentials, Supabase service
  role keys, or OAuth client secrets. `.env.example` documents every
  variable with a blank value.
- OAuth refresh tokens (Google Calendar) should be encrypted at rest in
  whatever credential store you use for a real deployment; this demo scaffold
  keeps them out of source control entirely by using in-memory stand-ins
  (`backend/app/services/calendar.py`, `crm.py`) until real OAuth is wired in.
- n8n webhooks are signed with an HMAC secret (`N8N_WEBHOOK_SIGNING_SECRET`)
  so n8n can reject unsigned requests (`backend/app/services/n8n_client.py`).

## Application-layer controls

- **Rate limiting.** Per-IP fixed-window limiter on all HTTP requests
  (`backend/app/main.py`), default 20 requests/minute — tune via
  `SESSION_RATE_LIMIT_PER_MINUTE`.
- **Origin checks.** The WebSocket audio endpoint rejects connections from
  origins not in `ALLOWED_ORIGINS`.
- **CORS.** Restricted to `ALLOWED_ORIGINS`; update it before deploying the
  dashboard anywhere other than `localhost`.
- **Idempotency.** Every mutating tool call (`book_appointment`,
  `reschedule_appointment`, `cancel_appointment`, `create_crm_record`)
  requires an idempotency key so a retried or replayed webhook cannot create
  a duplicate booking or CRM record (`backend/app/tools/router.py`).
- **Deterministic validation.** Dates, German postal codes, and phone
  numbers are validated with Pydantic before any tool executes — the model
  never gets to pass unvalidated arguments through to Calendar/HubSpot.

## Known limitations

This is a demo, not a compliance certification. In particular:

- The in-memory repository (used when Supabase is not configured) does not
  survive a process restart and is not encrypted at rest.
- The in-memory Calendar/CRM stand-ins are for the free-tier demo path only
  — see the `NotImplementedError` markers in `backend/app/services/` for
  where the real Google Calendar / HubSpot clients need to be implemented.
- No formal threat model or third-party audit has been performed.

## Reporting a concern

This is a personal portfolio project. If you find a security issue, please
open a GitHub issue rather than exploiting it.
