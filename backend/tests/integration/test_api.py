import os

os.environ.setdefault("VOICE_PROVIDER", "mock")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_create_session_requires_consent():
    res = client.post("/api/sessions", json={"language": "de", "channel": "browser", "consent_given": False})
    assert res.status_code == 400


def test_create_session_with_consent():
    res = client.post("/api/sessions", json={"language": "de", "channel": "browser", "consent_given": True})
    assert res.status_code == 200
    body = res.json()
    assert "session_id" in body
    assert "AI" in body["disclosure_text"] or "KI" in body["disclosure_text"]


def test_check_slots_endpoint():
    res = client.post(
        "/api/tools/check-slots",
        json={"service": "heating_repair", "earliest_date": "2026-07-13", "latest_date": "2026-07-20", "postcode": "10115"},
    )
    assert res.status_code == 200
    assert res.json()["result_code"] in ("OK", "NOT_FOUND")


def test_list_sessions_includes_created_session():
    created = client.post("/api/sessions", json={"language": "en", "channel": "browser", "consent_given": True})
    session_id = created.json()["session_id"]
    res = client.get("/api/sessions")
    assert res.status_code == 200
    assert any(s["session_id"] == session_id for s in res.json())


def test_handoff_create_get_list():
    created = client.post("/api/sessions", json={"language": "de", "channel": "browser", "consent_given": True})
    session_id = created.json()["session_id"]

    res = client.post(
        "/api/handoffs", json={"session_id": session_id, "reason": "explicit_request", "urgency": "standard"}
    )
    assert res.status_code == 200
    handoff = res.json()
    assert handoff["resolution_status"] == "open"

    get_res = client.get(f"/api/handoffs/{handoff['id']}")
    assert get_res.status_code == 200

    list_res = client.get("/api/handoffs", params={"unresolved": True})
    assert list_res.status_code == 200
    assert any(h["id"] == handoff["id"] for h in list_res.json())


def test_evaluations_run_and_get_by_id():
    run_res = client.post("/api/evaluations/run")
    assert run_res.status_code == 200
    run_id = run_res.json()["run_id"]

    get_res = client.get(f"/api/evaluations/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["run_id"] == run_id
