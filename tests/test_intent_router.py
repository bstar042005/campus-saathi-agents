import pytest
from fastapi.testclient import TestClient

from backend.intent_router import classify
from backend.main import app


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("hi", "greeting"),
        ("hello there", "greeting"),
        ("thanks for your help", "greeting"),
        ("where can I see the timetable", "link"),
        ("academic calendar", "link"),
        ("show me the exam date", "link"),
        ("fastest way to finish all procedures", "navigation"),
        ("what is the shortest path", "navigation"),
        ("what is the best route to complete all", "navigation"),
        ("who is the hostel warden", "knowledge"),
        ("how do I join the coding club", "knowledge"),
        ("where is the library", "knowledge"),
    ],
)
def test_classify(query, expected):
    assert classify(query) == expected


@pytest.fixture
def client():
    return TestClient(app)


def test_navigation_does_not_call_knowledge(monkeypatch, client):
    knowledge = lambda *args, **kwargs: pytest.fail("knowledge should not be called")
    monkeypatch.setattr("backend.main.answer_knowledge_query", knowledge)
    monkeypatch.setattr("backend.main.query_campus_helper", lambda *args: "Take this route.")

    response = client.post("/api/chat", json={"query": "fastest way to finish all procedures"})

    assert response.status_code == 200
    assert response.json()["answer_type"] == "navigation"


def test_knowledge_does_not_call_simulation(monkeypatch, client):
    simulation = lambda *args, **kwargs: pytest.fail("simulation should not be called")
    monkeypatch.setattr("backend.main.query_campus_helper", simulation)
    monkeypatch.setattr(
        "backend.main.answer_knowledge_query",
        lambda *args, **kwargs: type("Result", (), {"answer": "A grounded answer.", "found": True, "links": []})(),
    )

    response = client.post("/api/chat", json={"query": "how do I join the coding club"})

    assert response.status_code == 200
    assert response.json()["answer_type"] == "knowledge"


def test_timetable_returns_exact_link_without_knowledge(monkeypatch, client):
    knowledge = lambda *args, **kwargs: pytest.fail("knowledge should not be called")
    monkeypatch.setattr("backend.main.answer_knowledge_query", knowledge)
    timetable_url = "https://example.test/timetable.pdf"
    monkeypatch.setattr(
        "backend.main.get_link_by_key",
        lambda key: {"key": key, "url": timetable_url, "label": "Timetable"} if key == "timetable" else None,
    )

    response = client.post("/api/chat", json={"query": "Where can I see the timetable?"})

    assert response.status_code == 200
    data = response.json()
    assert data["answer_type"] == "link"
    assert data["links"][0]["url"] == timetable_url
    assert timetable_url in data["response"]


def test_missing_timetable_returns_main_website(monkeypatch, client):
    monkeypatch.setattr("backend.main.get_link_by_key", lambda key: None if key == "timetable" else {"url": "https://main.test"})

    response = client.post("/api/chat", json={"query": "Where can I see the timetable?"})

    assert response.status_code == 200
    data = response.json()
    assert data["found"] is False
    assert data["answer_type"] == "not_available"
    assert data["links"][0]["url"] == "https://main.test"


def test_knowledge_error_returns_not_available(monkeypatch, client):
    monkeypatch.setattr("backend.main.answer_knowledge_query", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("failed")))

    response = client.post("/api/chat", json={"query": "who is the principal's spouse"})

    assert response.status_code == 200
    data = response.json()
    assert data["found"] is False
    assert data["answer_type"] == "not_available"
    assert "I don't have that information" in data["response"]
