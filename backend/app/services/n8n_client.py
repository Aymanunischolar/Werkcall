"""Posts events to n8n webhooks with HMAC signing so n8n can verify the
request came from this backend (blueprint §10 "signature validation for
webhooks"). n8n owns cross-system orchestration (Gmail, HubSpot follow-ups,
audit writes); Python owns low-latency conversation control (blueprint §8)."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import httpx

from app.config import get_settings


def _sign(body: bytes, secret: str, timestamp: str) -> str:
    message = timestamp.encode() + b"." + body
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


async def trigger_workflow(workflow_path: str, payload: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.n8n_webhook_base_url:
        return  # n8n not configured — demo still works without post-call automation
    body = json.dumps(payload).encode()
    timestamp = str(int(time.time()))
    headers = {"Content-Type": "application/json", "X-Werkcall-Timestamp": timestamp}
    if settings.n8n_webhook_signing_secret:
        headers["X-Werkcall-Signature"] = _sign(body, settings.n8n_webhook_signing_secret, timestamp)
    url = f"{settings.n8n_webhook_base_url.rstrip('/')}/{workflow_path.lstrip('/')}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, content=body, headers=headers)
        except httpx.HTTPError:
            # Post-call automation is best-effort: a webhook failure must never
            # block or reverse a confirmed booking (see failed-call-review.json).
            pass
