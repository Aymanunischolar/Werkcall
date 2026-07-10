-- WerkCall AI Supabase schema (blueprint §7 minimum tables).
-- Synthetic demo data only. Raw audio is never stored (see SECURITY.md).

create extension if not exists "pgcrypto";

create table if not exists voice_sessions (
    id                uuid primary key default gen_random_uuid(),
    started_at        timestamptz not null default now(),
    ended_at          timestamptz,
    language          text not null check (language in ('de', 'en')),
    channel           text not null check (channel in ('browser', 'telephone')),
    consent_at        timestamptz,
    outcome           text not null default 'in_progress'
                        check (outcome in ('in_progress','booked','rescheduled','cancelled','handed_off','emergency','abandoned')),
    state             text not null default 'DISCLOSURE',
    duration_ms       integer,
    model_provider    text not null,
    deleted_at        timestamptz
);

create table if not exists conversation_turns (
    id              uuid primary key default gen_random_uuid(),
    session_id      uuid not null references voice_sessions(id) on delete cascade,
    speaker         text not null check (speaker in ('caller','assistant')),
    redacted_text   text not null,
    timestamp       timestamptz not null default now(),
    latency_ms      integer
);

create table if not exists tool_executions (
    id                uuid primary key default gen_random_uuid(),
    session_id        uuid not null references voice_sessions(id) on delete cascade,
    tool              text not null,
    validated_input   jsonb not null,
    result_code       text not null,
    retries           integer not null default 0,
    duration_ms       integer not null,
    idempotency_key   text,
    created_at        timestamptz not null default now(),
    unique (tool, idempotency_key)
);

create table if not exists bookings (
    booking_id            uuid primary key default gen_random_uuid(),
    session_id            uuid not null references voice_sessions(id) on delete cascade,
    service                text not null,
    start_at              timestamptz not null,
    end_at                timestamptz not null,
    status                text not null default 'confirmed'
                            check (status in ('confirmed','rescheduled','cancelled')),
    external_calendar_id  text,
    created_at            timestamptz not null default now(),
    updated_at            timestamptz not null default now()
);

create table if not exists handoffs (
    id           uuid primary key default gen_random_uuid(),
    session_id   uuid not null references voice_sessions(id) on delete cascade,
    reason       text not null,
    urgency      text not null,
    ticket_id    text,
    created_at   timestamptz not null default now()
);

create table if not exists evaluation_runs (
    id             uuid primary key default gen_random_uuid(),
    scenario_id    text not null,
    model          text not null,
    date           timestamptz not null default now(),
    expected       jsonb not null,
    actual         jsonb,
    pass           boolean,
    notes          text
);

create index if not exists idx_conversation_turns_session on conversation_turns(session_id);
create index if not exists idx_tool_executions_session on tool_executions(session_id);
create index if not exists idx_bookings_session on bookings(session_id);
create index if not exists idx_handoffs_session on handoffs(session_id);

-- Row Level Security: service role only. This project never exposes anon
-- read/write on these tables — the dashboard talks to the FastAPI backend,
-- not directly to Supabase.
alter table voice_sessions enable row level security;
alter table conversation_turns enable row level security;
alter table tool_executions enable row level security;
alter table bookings enable row level security;
alter table handoffs enable row level security;
alter table evaluation_runs enable row level security;
