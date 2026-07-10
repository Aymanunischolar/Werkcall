"""Evaluation runner (blueprint §7 POST /api/evals/run, §9).

Drives the mock provider through each labelled scenario's caller utterance
and grades the resulting tool call / handoff behaviour. Results are meant to
be committed alongside the run date, model name and scenario count — see
blueprint §9: "Targets are not CV claims until the labelled dataset and run
output are committed."
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.voice.mock_provider import MockVoiceProvider
from app.voice.provider import ModelEventType, VoiceSession
from evals.graders.grader import grade

SCENARIOS_PATH = Path(__file__).resolve().parents[1] / "scenarios" / "scenarios.yaml"


async def run_scenario(scenario: dict) -> dict:
    provider = MockVoiceProvider()
    await provider.connect(VoiceSession(session_id="eval", language=scenario["language"], system_prompt="", tool_specs=[]))

    events = provider.receive_events()
    # connect() queues the opening disclosure transcript; discard it before
    # sending the scenario's caller utterance so it isn't mistaken for the result.
    await asyncio.wait_for(events.__anext__(), timeout=2.0)

    await provider.send_text_turn(scenario["utterance"])

    actual = {"tool_name": None, "tool_args": {}}
    try:
        event = await asyncio.wait_for(events.__anext__(), timeout=2.0)
        actual = {"tool_name": event.tool_name, "tool_args": event.tool_args}
    except (StopAsyncIteration, asyncio.TimeoutError):
        pass
    await provider.close()
    return actual


async def main() -> int:
    scenarios = yaml.safe_load(SCENARIOS_PATH.read_text(encoding="utf-8"))
    results = []
    passed = 0
    for scenario in scenarios:
        actual = await run_scenario(scenario)
        result = grade(scenario, actual)
        results.append({"scenario_id": result.scenario_id, "pass": result.passed, "notes": result.notes, "actual": actual})
        passed += int(result.passed)

    summary = {
        "model": "mock",
        "date": datetime.now(timezone.utc).isoformat(),
        "scenario_count": len(scenarios),
        "passed": passed,
        "completion_rate": passed / len(scenarios) if scenarios else 0,
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    return 0 if passed == len(scenarios) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
