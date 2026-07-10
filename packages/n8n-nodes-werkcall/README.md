# n8n-nodes-werkcall

A native n8n community node for the [WerkCall AI](../../README.md) voice-receptionist backend. Lets an n8n workflow call appointment, session, handoff and evaluation operations without hand-configuring generic HTTP Request nodes for every endpoint.

## Resources and operations

| Resource | Operations |
|---|---|
| Appointment | Check Availability, Create, Get, Reschedule, Cancel |
| Session | Get Session, List Sessions, Get Redacted Transcript, Get Tool Executions, Delete Session |
| Handoff | Create Handoff, Get Status, List Unresolved Handoffs |
| Evaluation | Start Evaluation Run, Get Evaluation Result |

Fields are scoped to the operation that needs them — e.g. **Cancellation Reason** only appears for `Appointment > Cancel`, **New Slot** fields only for `Reschedule`, and **Urgency** only for `Handoff > Create`.

## Setup

1. Build the package: `npm install && npm run build` (from this directory).
2. In n8n, install it as a community node (`n8n-nodes-werkcall`), or for local development, symlink `dist/` into `~/.n8n/custom/`.
3. Add credentials: either **WerkCall API** (base URL + API key, sent as `Authorization: Bearer`) or **WerkCall OAuth2 API** (authorization-code flow with automatic refresh).
4. Point **Base URL** at your running WerkCall backend (e.g. `http://localhost:8000` for the local Docker Compose stack).

## Known limitations

- `Appointment > Get` is not implemented — the backend does not yet expose `GET /api/bookings/{id}` as a standalone endpoint. Use `Session > Get Session` and read the booking out of its `tool_executions` instead. This is surfaced as a clear node error, not a raw 404.
- The in-memory backend repository (used when Supabase isn't configured) does not persist across a backend restart — sessions/handoffs created before a restart will 404.
- Rate limits: the WerkCall backend applies a per-IP fixed-window limit (default 20 req/min); a 429 here is retried automatically for read-only operations, per the backoff behaviour below.

## Reliability behaviour

- **Retries**: read-only operations (Check Availability, Get Session, Get Status, Get Evaluation Result) retry on `429`/`500`/`502`/`503`/`504` with exponential backoff (1s → 2s → 4s → 8s, 4 attempts max). Write operations (Create, Reschedule, Cancel) are **not** retried automatically by the node — they rely on the `idempotencyKey` field so a manual re-run or a workflow-level retry never creates a duplicate booking or CRM record.
- **Credential redaction**: any error message returned to the workflow has API keys, client secrets and access tokens stripped before it reaches node output or the execution log.

## Testing

```bash
npm install
npm run test        # vitest unit tests: validation, retries, redaction, request building
npm run typecheck    # tsc --noEmit
npm run lint
```

Unit tests cover: required-field validation (missing caller confirmation, invalid postal code), request-body construction and response mapping for each resource, 429/5xx retry behaviour, and credential redaction in thrown errors. See `nodes/WerkCall/test/`.

## Example: booking flow in a workflow

1. **WerkCall** node → Resource: Appointment, Operation: Check Availability → returns `slots[]`.
2. Present a slot to the caller/operator, capture explicit confirmation.
3. **WerkCall** node → Resource: Appointment, Operation: Create, with `callerConfirmed: true` and a stable `idempotencyKey` (e.g. `booking-{{$json.sessionId}}-{{$json.confirmedSlot}}`). Replaying this node with the same key returns the original booking instead of creating a duplicate.
