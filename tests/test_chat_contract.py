from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_chat_endpoint_basic():
    response = client.post("/api/chat", json={"query": "hi"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["found"], bool)
    assert data["answer_type"] in ["knowledge", "navigation", "link", "not_available"]
    assert isinstance(data["sources"], list)
    assert isinstance(data["links"], list)

def test_chat_empty_query_fails():
    response = client.post("/api/chat", json={"query": ""})
    assert response.status_code == 422

def test_chat_missing_query_fails():
    response = client.post("/api/chat", json={})
    assert response.status_code == 422

def test_chat_history_max_items_exceeded():
    excessive_history = [{"role": "user", "content": f"msg {i}"} for i in range(7)]
    response = client.post("/api/chat", json={"query": "hello", "history": excessive_history})
    assert response.status_code == 422

def test_chat_valid_history_passes():
    valid_history = [
        {"role": "user", "content": "Where is the canteen?"},
        {"role": "assistant", "content": "The canteen is near the hostel area."}
    ]
    response = client.post("/api/chat", json={"query": "Thanks!", "history": valid_history})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data