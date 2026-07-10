"""Tool router (blueprint §5): Pydantic schema validation, authorization,
retries, timeouts and idempotency keys around every tool call the model
makes. The model never touches Calendar/HubSpot/Supabase directly."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from app.models.tools import TOOL_SCHEMAS, ResultCode
from app.tools.implementations import TOOL_IMPLEMENTATIONS

DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_RETRIES = 2
RETRYABLE_RESULT_CODES = {ResultCode.UPSTREAM_ERROR}

# Tools that mutate state must carry an idempotency key so a replayed webhook
# or a retried call never produces a duplicate write (blueprint §9 "Duplicate
# writes: 0").
MUTATING_TOOLS = {"book_appointment", "reschedule_appointment", "cancel_appointment", "create_crm_record"}


@dataclass
class ToolCallResult:
    tool: str
    result_code: str
    output: dict[str, Any]
    retries: int
    duration_ms: int
    validated_input: dict[str, Any]
    idempotency_key: str | None = None


class ToolValidationError(Exception):
    def __init__(self, tool: str, errors: list[dict[str, Any]]):
        self.tool = tool
        self.errors = errors
        super().__init__(f"invalid arguments for {tool}: {errors}")


class _IdempotencyCache:
    """Per-process duplicate-write guard, keyed on (tool, idempotency_key).
    Backed by the tool_executions unique constraint at the persistence layer;
    this is the fast in-process check before that round trip."""

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str], ToolCallResult] = {}

    def get(self, tool: str, key: str | None) -> ToolCallResult | None:
        if key is None:
            return None
        return self._seen.get((tool, key))

    def put(self, tool: str, key: str | None, result: ToolCallResult) -> None:
        if key is not None:
            self._seen[(tool, key)] = result


_idempotency_cache = _IdempotencyCache()


async def call_tool(tool_name: str, raw_args: dict[str, Any]) -> ToolCallResult:
    if tool_name not in TOOL_SCHEMAS:
        raise ToolValidationError(tool_name, [{"msg": "unknown tool"}])

    input_model, _output_model = TOOL_SCHEMAS[tool_name]
    try:
        validated = input_model.model_validate(raw_args)
    except ValidationError as exc:
        raise ToolValidationError(tool_name, exc.errors()) from exc

    idempotency_key = getattr(validated, "idempotency_key", None)
    if tool_name in MUTATING_TOOLS:
        cached = _idempotency_cache.get(tool_name, idempotency_key)
        if cached is not None:
            return cached

    implementation = TOOL_IMPLEMENTATIONS[tool_name]
    retries = 0
    start = time.monotonic()
    last_output: dict[str, Any] = {}
    result_code = ResultCode.UPSTREAM_ERROR

    while retries <= MAX_RETRIES:
        try:
            output = await asyncio.wait_for(implementation(validated), timeout=DEFAULT_TIMEOUT_SECONDS)
            last_output = output.model_dump(mode="json")
            result_code = output.result_code
            if result_code not in RETRYABLE_RESULT_CODES:
                break
        except (asyncio.TimeoutError, Exception):  # noqa: BLE001 - upstream failures are expected and handled by retry
            result_code = ResultCode.UPSTREAM_ERROR
            last_output = {"result_code": ResultCode.UPSTREAM_ERROR.value}
        retries += 1
        if retries <= MAX_RETRIES:
            await asyncio.sleep(min(0.25 * 2**retries, 2.0))

    duration_ms = int((time.monotonic() - start) * 1000)
    result = ToolCallResult(
        tool=tool_name,
        result_code=str(result_code),
        output=last_output,
        retries=retries,
        duration_ms=duration_ms,
        validated_input=validated.model_dump(mode="json"),
        idempotency_key=idempotency_key,
    )
    if tool_name in MUTATING_TOOLS:
        _idempotency_cache.put(tool_name, idempotency_key, result)
    return result
