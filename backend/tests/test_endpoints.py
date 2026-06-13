from fastapi.testclient import TestClient
from app.main import app
from app.services.storage import store

client = TestClient(app)
auth_headers = {}


def setup_module() -> None:
    # Reset store for tests
    store.clear()
    
    # Create test user
    signup_resp = client.post(
        "/api/v1/auth/signup",
        json={"username": "test_student", "password": "securepassword123"}
    )
    assert signup_resp.status_code == 200
    
    # Authenticate user
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "test_student", "password": "securepassword123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    
    global auth_headers
    auth_headers = {"Authorization": f"Bearer {token}"}


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "mindmate-ai"}


def test_unauthorized_access_fails() -> None:
    # Access without auth header
    response = client.get("/api/v1/journals")
    assert response.status_code in {401, 403}


def test_create_journal_endpoint() -> None:
    payload = {
        "content": "I feel extremely anxious and behind everyone else preparing for mock exams.",
        "exam_context": "JEE"
    }
    response = client.post("/api/v1/journals", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["content"] == payload["content"]
    assert data["analysis"]["primary_emotion"] == "anxiety"
    assert "peer comparison" in data["analysis"]["triggers"]


def test_list_journals_endpoint() -> None:
    response = client.get("/api/v1/journals", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_create_mood_log_endpoint() -> None:
    payload = {
        "mood_score": 8,
        "energy_level": 7,
        "sleep_hours": 7.5,
        "study_hours": 6.0,
        "stress_level": 3,
        "note": "A productive day"
    }
    response = client.post("/api/v1/mood-logs", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["mood_score"] == 8


def test_dashboard_endpoint() -> None:
    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "mood_average" in data
    assert "wellness_progress" in data
    assert data["journal_streak"] >= 1


def test_chat_endpoint() -> None:
    payload = {"message": "I feel like quitting this exam."}
    response = client.post("/api/v1/chat", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "suggested_action" in data
    
    
def test_chat_crisis_endpoint() -> None:
    payload = {"message": "I want to end my life."}
    response = client.post("/api/v1/chat", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["crisis_detected"] is True
    assert data["risk_level"] == "crisis"
