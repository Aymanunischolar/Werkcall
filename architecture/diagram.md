# Reference architecture

Figure 1 (blueprint §5): provider-adapter architecture — free browser mode
first, telephony and OpenAI optional.

```mermaid
flowchart LR
    subgraph Client
        B[Browser client\nmic capture, consent UI, transcript]
        T[Twilio trial number\noptional telephone channel]
    end

    subgraph Backend[FastAPI voice gateway]
        WS[Session + WebSocket API]
        CC[Conversation controller\nstate machine, policies]
        TR[Tool router\nvalidation, retries, idempotency]
    end

    subgraph Providers[VoiceModel adapters]
        GL[Gemini Live\nfree-first default]
        OA[OpenAI Realtime\noptional paid]
    end

    subgraph Data
        SB[(Supabase\nsessions, turns, tools, bookings, handoffs)]
    end

    subgraph External[External services]
        GC[Google Calendar API]
        HS[HubSpot Free CRM]
        GM[Gmail API]
    end

    subgraph N8N[n8n Community Edition]
        W1[booking-confirmation]
        W2[crm-sync]
        W3[failed-call-review]
        W4[follow-up-reminder]
    end

    subgraph Dashboard
        D[React trace dashboard\nfilter, replay, eval results]
    end

    B <-- WebRTC/WebSocket --> WS
    T -.optional.-> WS
    WS --> CC --> TR
    CC <--> GL
    CC -.optional.-> OA
    TR --> GC
    TR --> HS
    TR --> SB
    WS --> SB
    Backend -- webhook, HMAC-signed --> N8N
    W1 --> GM
    W2 --> HS
    W3 --> HS
    W3 --> GM
    W4 --> HS
    N8N --> SB
    D --> WS
    D --> SB
```

## Component responsibilities (blueprint §5)

| Component | Responsibility |
|---|---|
| Browser client | Microphone capture, audio playback, consent UI, live transcript, reconnect controls |
| FastAPI voice gateway | Session auth, WebSocket handling, rate limits, redaction, model adapter lifecycle |
| Conversation controller | State machine, language detection, policy prompts, approved knowledge retrieval |
| Tool router | Pydantic schema validation, authorization, retries, timeouts, idempotency keys |
| n8n workflow layer | Post-call orchestration, visible/editable by a non-Python operator |
| Supabase | Structured sessions, audit events, metrics, deletion status; raw audio off by default |
| React dashboard | Filter calls, replay transcripts, inspect tool traces, display measured eval results |

## Why the split

Low-latency conversation control, deterministic validation, and safety
policy enforcement live in Python because they're on the critical path of a
live voice turn (blueprint §8). Everything after a session ends — emailing a
confirmation, syncing a CRM record, chasing a follow-up — is business
orchestration that should stay inspectable by a non-engineer, so it lives in
n8n as exported, importable JSON workflows instead of backend code.
