# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- FastAPI voice gateway: provider-adapter interface (Gemini Live / OpenAI Realtime / offline mock), conversation state machine, Pydantic-validated tool router with retries/timeouts/idempotency, disclosure/emergency/handoff/redaction policies.
- Session, tool, handoff and evaluation HTTP/WebSocket endpoints; in-memory-or-Supabase repository so the full demo runs with zero external accounts.
- React/TypeScript browser call UI, session trace viewer, and evaluation dashboard.
- Four importable n8n workflows (booking-confirmation, crm-sync, failed-call-review, follow-up-reminder) with signature verification, idempotency checks, retry-with-backoff, and failure classification.
- `packages/n8n-nodes-werkcall`: a native TypeScript n8n community node covering Appointment/Session/Handoff/Evaluation resources, with API-key and OAuth2 credentials, retry/backoff, idempotency, and secret redaction.
- `tools/community-node-reviewer`: a CLI that reviews an n8n community node repository (local path, GitHub repo/PR, or npm package) across six categories and produces terminal/Markdown/JSON reports with a pass/fail decision.
- Docker Compose stack, `.env.example`, GitHub Actions CI, architecture diagram, ADRs, SECURITY.md.

### Known limitations
- Google Calendar, HubSpot, and Gmail are in-memory stand-ins until real OAuth/API credentials are wired in (see `backend/app/services/`).
- Only 8 of the target 40 labelled evaluation scenarios are committed so far.
- No Twilio telephone adapter yet.

[Unreleased]: https://github.com/ayman/werkcall-ai/compare/v0.1.0...HEAD
