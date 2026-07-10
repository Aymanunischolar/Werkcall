"""FastAPI voice gateway entrypoint (blueprint §5)."""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import evaluations, sessions, tools
from app.config import get_settings

logging.basicConfig(level=get_settings().log_level)

app = FastAPI(title="WerkCall AI Voice Gateway", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_request_log: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple fixed-window per-IP rate limit (blueprint §10). A single
    in-process limiter is adequate for a portfolio demo; a real deployment
    behind multiple workers would move this to Redis."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = _request_log[client_ip]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.session_rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})
    window.append(now)
    return await call_next(request)


app.include_router(sessions.router)
app.include_router(tools.router)
app.include_router(evaluations.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "voice_provider": settings.voice_provider}
