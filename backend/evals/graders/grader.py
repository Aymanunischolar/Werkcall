"""Scores one scenario run against its expected outcome (blueprint §9)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GradeResult:
    scenario_id: str
    passed: bool
    notes: str


def grade(scenario: dict[str, Any], actual: dict[str, Any]) -> GradeResult:
    expected_tool = scenario.get("expected_tool")
    expected_handoff = scenario.get("expected_handoff", False)
    expected_reason = scenario.get("expected_handoff_reason")

    if expected_tool is not None and actual.get("tool_name") != expected_tool:
        return GradeResult(scenario["id"], False, f"expected tool {expected_tool!r}, got {actual.get('tool_name')!r}")

    if expected_handoff and actual.get("tool_name") != "request_handoff":
        return GradeResult(scenario["id"], False, "expected a handoff/escalation but none occurred")

    if expected_reason and actual.get("tool_args", {}).get("reason") != expected_reason:
        return GradeResult(
            scenario["id"], False, f"expected handoff reason {expected_reason!r}, got {actual.get('tool_args', {}).get('reason')!r}"
        )

    return GradeResult(scenario["id"], True, "ok")
