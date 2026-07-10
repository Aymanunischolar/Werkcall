# WerkCall AI — Bilingual AI Telephone Receptionist

Built a bilingual (German/English) AI voice receptionist for a fictional
heating and repair company — grounded FAQs, appointment booking/reschedule/
cancel, CRM sync via n8n, and human/emergency escalation, running entirely
on free-tier infrastructure until you choose to add paid adapters.

> **Status:** early-stage scaffold (backend + browser demo + n8n workflows
> are implemented and tested; see [Implemented vs. roadmap](#implemented-vs-roadmap)
> below for exactly what's real today).

## Try the browser demo

```bash
cp .env.example .env            # defaults to VOICE_PROVIDER=mock — no API keys needed
docker compose up backend frontend
```

Open `http://localhost:4173`, accept the consent dialog, and type (or say,
once a real voice provider is configured):

> "Meine Heizung ist ausgefallen. Ich brauche morgen einen Termin."

Change the date mid-conversation, ask an unknown-price question, or say
"Ich rieche Gas" to see the emergency escalation path. A trial telephone
number via Twilio is an optional, clearly-labelled add-on — the browser
demo is the foundation (see [Scope](#scope)).

## Architecture

See [`architecture/diagram.md`](architecture/diagram.md) for the full
provider-adapter diagram. Summary: browser client ↔ FastAPI voice gateway ↔
Gemini Live (free-first) or OpenAI Realtime (optional paid) ↔ a validating
tool router ↔ Google Calendar / HubSpot / Supabase, with n8n handling
post-call orchestration (Gmail confirmations, CRM sync, failed-call review,
follow-ups) as inspectable, importable workflow JSON.

## Measured evaluation results

Run the labelled scenario suite yourself:

```bash
cd backend
pip install -r requirements.txt
VOICE_PROVIDER=mock python evals/runner/run.py
```

Latest committed run (`backend/evals/scenarios/scenarios.yaml`, 8 scenarios,
`mock` provider, 2026-07-10): **8/8 passed (100%)**. This is a small
representative slice, not the 40-scenario set the Definition of Done
requires before a v1.0.0-demo tag — see [Roadmap](#implemented-vs-roadmap).
Do not read "100%" as a claim about a real LLM provider; it reflects the
deterministic mock provider used in CI.

## Quick start (full stack)

```bash
cp .env.example .env
# optionally set VOICE_PROVIDER=gemini_live and GEMINI_API_KEY for real speech
docker compose up
```

- Backend: `http://localhost:8000` (`/health`, `/api/sessions`, `/api/tools/*`)
- Frontend: `http://localhost:4173`
- n8n: `http://localhost:5678` (import the JSON files in `n8n-workflows/`)

Local development without Docker:

```bash
# backend
cd backend && python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
VOICE_PROVIDER=mock uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm run dev
```

## Screenshots

_To be added: n8n execution list, Google Calendar booking, HubSpot contact/
ticket, Gmail confirmation, and the trace dashboard — see Definition of Done._

## Security, privacy, limitations

See [`SECURITY.md`](SECURITY.md). Short version: synthetic data only, no
raw audio retention, redacted logs, per-session delete action, rate limiting
and origin/CORS checks, idempotent mutating tools. The Gemini free tier may
use submitted content to improve Google's products — never submit real
customer data through this demo.

## Scope

| MVP — must ship | Stretch goal | Not building yet |
|---|---|---|
| Browser audio (WebRTC/WebSocket) | Twilio trial number | Full PBX/SIP rollout |
| German + English | Code-switching benchmark | Ten-language support |
| Book/move/cancel appointment | Technician skill routing | Payments/invoicing |
| FAQ grounding from approved files | Admin FAQ editor | Open web browsing during calls |
| Human handoff + emergency policy | Live operator console | Autonomous emergency decisions |
| CRM, email, calendar, audit log | SMS confirmation | Real customer/medical data |

The browser-first MVP ships before any money is spent on a public phone
number — the telephone adapter demonstrates integration skill, it is not
the foundation.

## Repository structure

```
werkcall-ai/
├── backend/            FastAPI voice gateway, tools, policies, evals, tests
├── frontend/            React call UI, trace viewer, eval dashboard
├── n8n-workflows/       Exported, importable n8n workflow JSON
├── knowledge-base/      Approved FAQ grounding source (DE/EN)
├── sample-data/         Synthetic customer identities for demo/testing
├── architecture/        Reference architecture diagram
├── docs/adr/            Architecture decision records
├── docker-compose.yml
├── .env.example
├── SECURITY.md
└── README.md
```

## Implemented vs. roadmap

**Implemented and tested today:**
- FastAPI voice gateway: session create/get/delete, WebSocket audio/event
  protocol, direct tool HTTP endpoints, eval-run endpoint
- Provider-adapter interface with Gemini Live, OpenAI Realtime, and an
  offline mock provider (used by CI/evals)
- Conversation state machine, disclosure/emergency/handoff/redaction
  policies, grounded FAQ search over `knowledge-base/`
- Pydantic-validated tool router with retries, timeouts, idempotency keys
- In-memory-or-Supabase repository and in-memory Calendar/CRM stand-ins, so
  the whole stack runs with zero external accounts
- React browser call UI, session trace viewer, eval dashboard — verified
  end-to-end against the mock backend
- 4 importable n8n workflows, Docker Compose, CI (pytest + eval run + frontend build)
- 18 backend unit/integration tests, 8 labelled eval scenarios (100% pass on mock)

**Not yet implemented (see blueprint's 14-day plan for full sequencing):**
- Real Google Calendar OAuth / HubSpot API / Gmail sending (currently
  in-memory stand-ins with `NotImplementedError` markers where the real
  client goes — see `backend/app/services/`)
- Twilio telephone adapter
- Full 40-scenario labelled eval set and threat model writeup
- Recorded demo video, dashboard screenshots, tagged `v1.0.0-demo` release

## Two-minute recruiter demo script

1. "Meine Heizung ist ausgefallen. Ich brauche morgen einen Termin."
2. Change the date during confirmation; ask for an unknown price — the
   agent must refuse to invent it and confirm the final slot instead.
3. Open Calendar, HubSpot, Gmail, and the matching n8n execution (once real
   credentials are configured).
4. Replay the booking webhook and confirm no duplicate booking is created.
5. Say "Ich rieche Gas" and confirm immediate escalation.
