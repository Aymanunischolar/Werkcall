# Contributing to WerkCall AI

Thanks for considering a contribution. This repository models a small but real open-source engineering process — please read this before opening a PR.

## Project layout

See the [README](README.md#repository-structure) for the full repository structure. The three places you'll most likely touch:

- `backend/` — Python/FastAPI voice gateway, tools, policies, evals
- `frontend/` — React/TypeScript browser call UI and dashboards
- `packages/n8n-nodes-werkcall/` and `tools/community-node-reviewer/` — the two standalone TypeScript/Node packages

## Getting set up

```bash
cp .env.example .env   # defaults to VOICE_PROVIDER=mock — no API keys needed
docker compose up backend frontend
```

For the TypeScript packages:

```bash
cd packages/n8n-nodes-werkcall && npm install && npm test
cd tools/community-node-reviewer && npm install && npm test
```

For the Python backend:

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
VOICE_PROVIDER=mock python -m pytest -q
VOICE_PROVIDER=mock python evals/runner/run.py
```

## Before opening a pull request

- [ ] Tests added or updated for the change
- [ ] `pytest` (backend) and/or `vitest` (TypeScript packages) pass locally
- [ ] Documentation updated (README, package README, or docs/adr as relevant)
- [ ] No secrets included — check `git diff` for anything that looks like a key, token, or `.env` value
- [ ] Credential fields in the n8n node stay masked (`typeOptions: { password: true }`)
- [ ] Error cases have been tested, not just the happy path
- [ ] If you changed an n8n workflow JSON, re-export it from a real n8n instance rather than hand-editing, and confirm it still imports cleanly
- [ ] Breaking changes are called out in the PR description and in `CHANGELOG.md`

## Code style

- Python: follow the existing style in `backend/app` — no comments explaining *what* code does, only *why* when it's non-obvious; Pydantic models for every tool boundary; deterministic validation before any external API call.
- TypeScript: strict mode, no `any` without a comment explaining why, prefer small pure functions (see `packages/n8n-nodes-werkcall/nodes/WerkCall/GenericFunctions.ts`) that are easy to unit test without mocking half of n8n.

## Security

Do not open a public issue for a security vulnerability — see [SECURITY.md](SECURITY.md). Never submit real customer data, real credentials, or anything beyond the synthetic identities in `sample-data/`.

## Running the community-node reviewer against your own changes

If you're modifying `packages/n8n-nodes-werkcall`, run the reviewer against it before opening a PR:

```bash
cd tools/community-node-reviewer
npm install && npm run build
node dist/cli.js ../../packages/n8n-nodes-werkcall
```

A `FAIL` in a blocking category (credential security, missing OAuth-refresh tests, etc.) is expected to be fixed before review.
