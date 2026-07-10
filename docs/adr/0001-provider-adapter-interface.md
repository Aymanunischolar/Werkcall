# ADR 0001: Provider-adapter interface for voice models

## Status
Accepted

## Context
The blueprint requires a free-first browser demo (Gemini Live) while keeping
a paid, commercially credible adapter (OpenAI Realtime) available without a
rewrite. Recruiters need to see the interface is real, not hard-coded to one
vendor.

## Decision
Define a single `VoiceModel` Protocol (`backend/app/voice/provider.py`) with
`connect`, `send_audio`, `send_tool_result`, `receive_events`, `close`. Three
implementations exist: `GeminiLiveProvider`, `OpenAIRealtimeProvider`, and
`MockVoiceProvider` (offline, deterministic, used by tests/evals/CI). The
active provider is chosen by a single `VOICE_PROVIDER` env var via
`get_provider()`; the conversation controller and tool router never branch
on which one is active.

## Consequences
- Adding a new provider means implementing one Protocol, not touching the
  conversation controller, tool router, or API layer.
- CI and the eval runner never need real API keys — `MockVoiceProvider`
  gives deterministic, reproducible tool-call behaviour for the labelled
  scenarios (blueprint §9).
- The mock provider is a small rule-based classifier standing in for the
  real model's tool-calling judgement; it is intentionally not a language
  model and should not be mistaken for one when reading eval results.
