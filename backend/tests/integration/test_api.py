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
