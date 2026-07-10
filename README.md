# WerkCall AI

**Bilingual AI Voice Receptionist and n8n Developer Platform**

Target roles: Community Software Engineer, TypeScript Developer, Workflow Automation Engineer, AI Integration Engineer.

WerkCall AI is a bilingual AI receptionist that manages heating-service calls, books and changes appointments, synchronizes business systems through n8n, and includes a custom TypeScript n8n node plus automated tooling for reviewing community-node quality.

> **Status:** early-stage, actively-developed scaffold. The browser demo, backend, n8n workflows, custom node, and reviewer CLI below are implemented and tested; see [Implemented vs. roadmap](#implemented-vs-roadmap) for exactly what's real today versus what the detailed spec still calls for.

## Try the browser demo

```bash
cp .env.example .env            # defaults to VOICE_PROVIDER=mock — no API keys needed
docker compose up backend frontend
```

Open `http://localhost:4173`, accept the consent dialog, and type (or say, once a real voice provider is configured):

> "Meine Heizung ist ausgefallen. Ich brauche morgen einen Termin."

Change the date mid-conversation, ask an unknown-price question, or say "Ich rieche Gas" to see the emergency escalation path. A trial telephone number via Twilio is an optional, clearly-labelled add-on — the browser demo is the foundation (see [Scope](#scope)).

## Architecture

See [`architecture/diagram.md`](architecture/diagram.md) for the full diagram. Summary: browser client ↔ FastAPI voice gateway ↔ conversation controller + safety policies ↔ a validating tool router ↔ Google Calendar / HubSpot / FAQ retrieval / human handoff, with n8n handling post-call orchestration (Gmail confirmations, Supabase audit writes, follow-up tasks, failed-call review) as inspectable, importable workflow JSON.

The core decision: low-latency conversation control, deterministic validation, and safety-policy enforcement live in Python because they're on the critical path of a live voice turn. Everything after a session ends is business orchestration that should stay inspectable by a non-engineer, so it lives in n8n.

## The two developer-tooling components

Beyond the voice product itself, this repository includes two standalone TypeScript packages aimed squarely at n8n's own engineering needs:

- **[`packages/n8n-nodes-werkcall`](packages/n8n-nodes-werkcall/)** — a production-style native n8n community node (Appointment/Session/Handoff/Evaluation resources) with API-key and OAuth2 credentials, exponential-backoff retry on 429/5xx, idempotency-protected writes, client-side validation, and secret redaction. 13 unit tests, builds and typechecks cleanly.
- **[`tools/community-node-reviewer`](tools/community-node-reviewer/)** — a CLI that analyses any n8n community node repository (local path, GitHub repo/PR, or npm package) across six categories — package structure, code quality, credential security, API handling, node UX/docs, testing — and produces terminal/Markdown/JSON reports with a score and an Approved/Changes-required decision. Verified against a deliberately broken fixture (scores 41/100, catches every planted issue) and dogfooded against the real `n8n-nodes-werkcall` package (scores 95/100 after the reviewer's first run caught a genuine missing test).

## Measured evaluation results

Run the labelled scenario suite yourself:

```bash
cd backend
pip install -r requirements.txt
VOICE_PROVIDER=mock python evals/runner/run.py
```

Latest committed run (`backend/evals/scenarios/scenarios.yaml`, 8 scenarios, `mock` provider, 2026-07-11): **8/8 passed (100%)**. This is a small representative slice, not the 40-scenario set the Definition of Done requires before a `v1.0.0-demo` tag — see [Roadmap](#implemented-vs-roadmap). Do not read "100%" as a claim about a real LLM provider; it reflects the deterministic mock provider used in CI, and exists precisely so the eval harness itself is provably correct before it's pointed at a real model.

## Quick start (full stack)

```bash
cp .env.example .env
# optionally set VOICE_PROVIDER=gemini_live and GEMINI_API_KEY for real speech
docker compose up
```

- Backend: `http://localhost:8000` (`/health`, `/api/sessions`, `/api/tools/*`, `/api/handoffs`, `/api/evaluations/*`)
- Frontend: `http://localhost:4173`
- n8n: `http://localhost:5678` (import the JSON files in `n8n-workflows/`, then install `packages/n8n-nodes-werkcall` as a community node)

Local development without Docker:

```bash
# backend
cd backend && python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
VOICE_PROVIDER=mock uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm run dev

# custom n8n node
cd packages/n8n-nodes-werkcall && npm install && npm test && npm run build

# community-node reviewer
cd tools/community-node-reviewer && npm install && npm test && npm run build
node dist/cli.js ../../packages/n8n-nodes-werkcall
```

## Screenshots

_To be added: n8n execution list, Google Calendar booking, HubSpot contact/ticket, Gmail confirmation, the trace dashboard, and a community-node-reviewer terminal run — see [Definition of Done](#definition-of-done)._

## Security, privacy, limitations

See [`SECURITY.md`](SECURITY.md). Short version: synthetic data only, no raw audio retention, redacted logs, per-session delete action, rate limiting and origin/CORS checks, idempotent mutating tools, masked credential fields in the n8n node, signed and timestamp-checked n8n webhooks. The Gemini free tier may use submitted content to improve Google's products — never submit real customer data through this demo.

## Scope

| MVP — must ship | Stretch goal | Not building yet |
|---|---|---|
| Browser audio (WebRTC/WebSocket) | Twilio trial number | Full PBX/SIP rollout |
| German + English | Code-switching benchmark | Ten-language support |
| Book/move/cancel appointment | Technician skill routing | Payments/invoicing |
| FAQ grounding from approved files | Admin FAQ editor | Open web browsing during calls |
| Human handoff + emergency policy | Live operator console | Autonomous emergency decisions |
| CRM, email, calendar, audit log | SMS confirmation | Real customer/medical data |
| Custom n8n node (this repo) | — | — |
| Community-node reviewer CLI (this repo) | — | — |

The browser-first MVP ships before any money is spent on a public phone number — the telephone adapter demonstrates integration skill, it is not the foundation.

## Repository structure

```
werkcall-ai/
├── backend/                    FastAPI voice gateway, tools, policies, evals, tests
├── frontend/                   React/TypeScript call UI, dashboard, trace viewer
├── packages/
│   └── n8n-nodes-werkcall/     Custom TypeScript n8n community node
├── tools/
│   └── community-node-reviewer/ TypeScript CLI reviewing community-node repos
├── n8n-workflows/              Exported, importable n8n workflow JSON
├── knowledge-base/             Approved FAQ grounding source (DE/EN)
├── sample-data/                Synthetic customer identities for demo/testing
├── architecture/                Reference architecture diagram
├── docs/adr/                   Architecture decision records
├── docker-compose.yml
├── .env.example
├── SECURITY.md
├── CONTRIBUTING.md
├── CODEOWNERS
├── CHANGELOG.md
└── README.md
```

## Implemented vs. roadmap

**Implemented and tested today:**
- FastAPI voice gateway: session create/list/get/delete, WebSocket audio/event protocol, direct tool HTTP endpoints, handoff tracking, evaluation-run endpoints
- Provider-adapter interface with Gemini Live, OpenAI Realtime (optional, paid, off by default), and an offline mock provider used by CI/evals
- Conversation state machine (including `FAILED_INTERACTION`/`CALLER_CANCELLED` escalation states), disclosure/emergency/handoff/redaction policies, grounded FAQ search over `knowledge-base/`
- Pydantic-validated tool router with retries, timeouts, idempotency keys
- In-memory-or-Supabase repository and in-memory Calendar/CRM stand-ins, so the whole stack runs with zero external accounts
- React/TypeScript browser call UI, session trace viewer, evaluation dashboard — verified end-to-end against the mock backend
- 4 importable n8n workflows with signature verification, idempotency checks, retry-with-backoff, and failure classification
- A production-style custom TypeScript n8n node (`packages/n8n-nodes-werkcall`) — 13 tests, builds and typechecks cleanly
- A community-node-reviewer CLI (`tools/community-node-reviewer`) — 15 tests, verified against both broken and correct fixtures and dogfooded against the real node package
- Docker Compose, CI (backend pytest + eval run, frontend build, both TS packages' typecheck/test/build), repo governance (CONTRIBUTING, CODEOWNERS, issue/PR templates, Dependabot)
- 22 backend tests, 13 node-package tests, 15 reviewer tests, 8 labelled eval scenarios (100% pass on the mock provider)

**Not yet implemented (see the detailed spec's 14-day plan for full sequencing):**
- Real Google Calendar OAuth / HubSpot API / Gmail sending (currently in-memory stand-ins with `NotImplementedError` markers where the real client goes — see `backend/app/services/`)
- Twilio telephone adapter
- Full 40-scenario labelled eval set and threat-model writeup
- `Appointment > Get` in the custom n8n node (documented limitation — see the [node's README](packages/n8n-nodes-werkcall/README.md#known-limitations))
- Recorded demo video, dashboard/n8n/reviewer screenshots, tagged `v1.0.0-demo` release

## Definition of Done

- [x] Browser voice flow works from disclosure to confirmation
- [ ] Google Calendar, Gmail, HubSpot and Supabase use real demo accounts
- [x] At least three n8n workflows import and run without manual rebuilding
- [x] The custom TypeScript n8n node supports core appointment operations
- [x] The community-node reviewer produces terminal, Markdown and JSON output
- [ ] At least 40 labelled scenarios and raw evaluation outputs are committed (8/40 so far)
- [x] Secrets are absent from Git history
- [x] The README clearly separates implemented features, optional adapters and roadmap items
- [ ] A German demo video and architecture image appear near the top of the README
- [x] The repository includes meaningful commits and CI status (issues/tagged release: not yet)

## Two-minute recruiter demo script

1. Open the browser call interface and start a German call.
2. Say the heating system has failed and request an appointment for tomorrow.
3. Change the requested date during confirmation.
4. Ask for an unknown price — the assistant refuses to invent one.
5. Confirm the final slot.
6. Open Calendar, HubSpot, Gmail, and the matching n8n execution (once real credentials are configured).
7. Replay the booking webhook and confirm no duplicate booking is created.
8. Say "Ich rieche Gas" and confirm immediate escalation.
9. Open the custom WerkCall n8n node in an n8n workflow.
10. Run the community-node reviewer and show the generated terminal/Markdown feedback.

## Portfolio description

WerkCall AI is a bilingual German-English voice receptionist and workflow-automation platform for a fictional heating-service company. The system handles customer enquiries, emergency escalation, appointment booking, rescheduling and cancellation through a browser-based voice interface. A FastAPI gateway manages real-time conversation state, validation and safety policies, while n8n orchestrates business workflows across Google Calendar, Gmail, HubSpot and Supabase.

The repository also includes a production-style TypeScript n8n community node with API-key and OAuth 2.0 support, retries, idempotency and structured errors. An accompanying community-node reviewer analyses third-party n8n packages for code quality, credential security, documentation, testing and API reliability, and generates actionable pull-request feedback.

The project is evaluated against labelled German and English scenarios covering appointment changes, API failures, duplicate webhook delivery, invalid customer data, prompt injection, human handoff and emergency escalation. All demo data is synthetic, raw-audio storage is disabled by default and sensitive fields are redacted from logs.

## CV project entry

**WerkCall AI — Bilingual Voice Receptionist and n8n Developer Platform**
*TypeScript, n8n, Node.js, Python, FastAPI, OAuth 2.0, Google APIs, HubSpot, Supabase*

- Built a bilingual AI voice receptionist that handled heating-service enquiries, appointment booking, rescheduling, cancellation and human escalation through a state-controlled German and English conversation flow.
- Developed four importable n8n workflows connecting Google Calendar, Gmail, HubSpot and Supabase, including retry branches, failed-interaction review and idempotent webhook processing.
- Created a custom TypeScript n8n node with API-key and OAuth 2.0 authentication, dynamic operation fields, structured errors and automated tests for rate limits, token expiry and external API failures.
- Built a community-node review CLI that checked package structure, credential handling, documentation, testing and API reliability, producing automated Markdown feedback for pull requests.
- Evaluated the system across labelled scenarios covering appointment changes, duplicate requests, emergency escalation, invalid inputs and partial third-party-service failures.

*Note: the final bullet above should be replaced with measured numbers only after the full 40-scenario labelled dataset has been run and the raw results committed publicly — see [Measured evaluation results](#measured-evaluation-results).*
